# MassEntity / MassGameplay 数据导向 AI 与大规模实体合同

> 用于 UE5.7/5.8 的 MassEntity、MassGameplay、MassAI、MassCrowd、MassLOD、MassReplication、ZoneGraph、SmartObject、StateTree 设计审查。目标不是“把 Actor 全换成 ECS”，而是判断哪些状态和行为适合数据导向批处理，哪些必须保留 Actor/Pawn/GAS/Mover 的高交互生命周期。

## 1. 时效性：Mass 必须按目标引擎重新校准

Mass 是 UE5 中变化速度很快的一组系统。旧文章和旧 Sample 的架构思想仍可参考，但具体 API 默认不具备跨版本权威性。

### 1.1 版本证据优先级

从高到低：

1. 目标项目真实 UE 版本与目标平台；
2. 该版本 Engine Source / 官方 5.x 文档与 release notes；
3. 固定 commit 的当前 upstream Sample；
4. 维护中的第三方 Sample；
5. 旧 README、博客、视频、fork；
6. stars、forks、仓库更新时间。

`Megafunk/MassSample` 自己也明确提示 README 中部分 pre-5.6 示例可能已经过时，代码比旧文档更可靠。即使仓库整体更新到 5.8，也要固定 commit 后看当前源码路径。

### 1.2 UE5.8 的重要变化

UE5.8 对 Mass 有架构级更新，迁移旧样例时至少重新检查：

- Mass Signals 进入核心体系；
- entity creation 可以在 game thread 外完成；
- processor execution / dependency resolution 重写；
- 更细粒度的调度与 thread-safe observer notification；
- sparse / virtual fragment 体系，降低可选状态引发的内存与 archetype churn；
- MassCore 进一步把核心 Entity 能力与完整 MassGameplay 栈解耦；
- QueryExecutor 提供可选的简化/强类型 Query API；
- relation、observer、batch API 等持续演进。

因此，看到旧版：

```text
ConfigureQueries()
Query.ForEachEntityChunk(EntityManager, Context, ...)
```

不能直接复制。当前 upstream 5.8 样例已经出现 `ConfigureQueries(const TSharedRef<FMassEntityManager>&)`、query `Initialize(EntityManager)`、`ForEachEntityChunk(Context, ...)` 等变化；目标版本仍要以实际 Engine Header 为准。

### 1.3 成熟度分层

不要把“Mass”当成单一成熟度：

- **MassEntity core**：数据导向 Entity/Fragment/Processor 基础；
- **MassGameplay**：Representation、Spawner、LOD、Replication 等，当前官方仍标 Experimental；
- **MassAI / MassCrowd / ZoneGraph**：当前官方仍有 Experimental/shipping caution；
- **StateTree / SmartObject**：可以独立于 Mass 使用，成熟度与 MassAI 集成要分别判断。

生产项目应按模块 feature-gate，不用“Epic 自己用了”替代发行风险评估。

## 2. 先决定“为什么用 Mass”

Mass 最适合：

- 数量大；
- 数据结构相对同质；
- 同一批实体执行相似计算；
- 大量状态可以放在 POD/UStruct fragment；
- 可以通过 LOD / variable tick / signal 降低更新频率；
- 不要求每个实体常驻完整 Actor/Component/UObject graph。

Mass 不自动适合：

- 少量复杂 Boss；
- 高频独立 RPC；
- 每个实体都有大量独特 UObject/Component；
- 强依赖 Pawn/Mover/GAS/PhysicsControl/复杂 Skeletal Mesh；
- 每帧做大量 World/Actor 查询；
- 只是想“多线程所以会快”。

### 2.1 不按数量单一决策

例如 300 个高交互战斗 NPC：

- 每个有 GAS、装备、碰撞、Pose Search、复杂相机/交互；
- 同时只几十个真的活跃；

可能“Actor + Significance/LOD/AI budget”更简单。

而 5 万个远景行人/动物/环境单位，只有几千需要位置更新，几十个升级成 Actor，则很适合 hybrid。

## 3. Entity identity 与 runtime handle 分开

`FMassEntityHandle` 是 runtime entity handle，不是：

- Save ID；
- 跨 World ID；
- 永久 NPC ID；
- 网络业务 ID；
- 任务/关系/宠物存档 ID。

大规模玩法仍需要稳定业务身份，例如：

```text
StableAgentId
DefinitionId
Population/SpawnSourceId
Persistent progression/state key
```

然后维护 runtime cache：

```text
StableAgentId -> FMassEntityHandle
StableAgentId -> current high-res Actor (optional)
Actor -> StableAgentId + representation generation
```

entity destroy/recreate、archetype migration、LOD representation 变化都不能改变业务 identity。

## 4. Fragment 数据布局：按访问模式，不按对象继承

### 4.1 Hot fragment

适合每帧/高频批处理的紧凑数据：

- transform/velocity；
- short state enum；
- current target compact ID；
- LOD/significance；
- steering force；
- compact timer/cooldown。

要求：

- 尺寸小；
- 连续访问；
- 少 pointer chasing；
- 不塞大字符串、TMap、大数组、重 UObject 引用。

### 4.2 Shared fragment / config

适合一组 Entity 共用的配置：

- speed tuning；
- archetype definition；
- representation/LOD config；
- shared behavior parameters。

不要放 per-entity mutable truth。共享 fragment 一次错误写入会影响整组实体。

### 4.3 Tag

Tag 表示 presence，不存 payload。

旧 Mass 中频繁 Add/Remove 普通 Tag/Fragment 会改变 archetype composition 并迁移 entity。UE5.8 引入 sparse/virtual fragment 机制后，高 churn optional state 可以重新评估，但仍要：

- 核对目标引擎 API；
- 量 archetype/chunk 变化；
- 不把所有 bool 都机械改 sparse tag。

### 4.4 冷数据与外部状态

大而稀疏、低频访问的数据可放：

- stable store/subsystem；
- sparse/virtual state；
- external map keyed by stable ID；
- DataAsset/Definition；
- Actor-only high fidelity state。

不要为了“Everything in ECS”把冷数据污染 hot chunk。

## 5. Query access 就是并发合同

Mass scheduler 能否安全并行依赖你声明的数据访问。

Query/QueryExecutor 必须准确表达：

- fragment ReadOnly / ReadWrite；
- shared fragment access；
- tag presence；
- external subsystem read/write；
- execution flags / phase / group / order。

错误地少声明一个 write 不只是“代码风格问题”，会破坏依赖分析与并行安全。

### 5.1 并行 Processor 禁止隐式旁路

不要在 parallel chunk loop 中随意：

- `SpawnActor`；
- 修改 Actor/UObject；
- 直接写未声明 Fragment；
- 调 Blueprint event；
- 修改全局 TMap；
- 同步加载资产；
- 直接访问线程不安全 WorldSubsystem。

正确模式：

```text
Mass parallel calculation
 -> compact result / command
 -> deferred command / safe mutation boundary
 -> GameThread or declared-safe phase
 -> Actor/UObject side effect
```

### 5.2 External subsystem traits 不是装饰

如果 Processor 访问 `UWorldSubsystem`：

- subsystem 自己必须实现真实线程安全；
- reader/writer 使用同一锁/immutable snapshot/lock-free 合同；
- traits 声明必须与实现一致。

把 `ThreadSafeRead=true` 写在 traits 里不会自动让 UObject 成为线程安全对象。

## 6. Structural mutation 与 iteration 边界

遍历 archetype/chunk 时，Add/Remove Fragment、Tag、Destroy/Create Entity 等结构性变化可能使当前 view/handle 失效或引起调度冲突。

原则：

- 使用目标版本的 deferred command / entity builder / batch mutation API；
- 不持有 chunk view、fragment reference 跨 deferred commit；
- mutation 后按 stable ID/entity handle generation 重新解析；
- observer/relation callback 可能形成 re-entry，仍按 mutation boundary 处理。

UE5.8 有新的 batch/observer/relation API；旧 `Context.Defer()` 样例只保留“结构变化延期提交”的语义，不把函数签名写死。

## 7. Signal：唤醒，不是 payload 真值

**Signal 只作为 wakeup / 调度提示，不承载 canonical payload。**

现代 Mass Signals 适合：

- StateTree wakeup；
- “这个 Entity 有事要处理”；
- 稀疏的 path refresh；
- reservation/completion notification；
- 低频状态变化触发处理。

不适合：

```text
Signal = Damage(37, Fire, Critical, SourceX)
```

Signal 应更像：

```text
DamagePending
PathInvalidated
SmartObjectChanged
BehaviorWakeup
```

canonical payload 放 Fragment/Authority queue/subsystem。

这样 signal 重复、合并、调度延迟也不会改变业务真值。

### 7.1 避免全量轮询

如果十万实体只有 200 个偶尔需要重新规划：

错误：

```text
Every frame scan 100000 -> if Dirty
```

优先：

- signal；
- observer；
- variable tick / SimulationLOD；
- chunk/group scheduling；
- targeted entity list。

但持续 movement/physics approximation 仍可用周期 processor，不能一刀切“全部事件驱动”。

## 8. Representation LOD：Actor 是临时表示

MassRepresentation 可在 LOD 间使用：

- high-resolution Actor；
- low-resolution Actor；
- ISM；
- no representation。

系统还能 spawn/recycle/pool Actor。

因此 high-res Actor 不能独占长期业务真值：

错误：

```text
Actor.Health
Actor.InventoryId
Actor.QuestState
Actor.PetProgress
```

Actor 被回收后这些状态就失去 canonical owner。

正确：

```text
Mass/stable authority state
  + StableAgentId
  -> current Representation Actor (ephemeral)
```

### 8.1 Promotion / demotion 是事务

从 Mass 低保真实体升级到 Actor：

```text
resolve StableAgentId + generation
 -> reserve promotion
 -> spawn/reuse Actor
 -> apply canonical snapshot
 -> bind Actor <-> Entity/AgentId
 -> wait required ready state
 -> switch interaction/combat routing
 -> activate high-cost behavior
 -> publish representation ready
```

降级：

```text
freeze new interactive requests
 -> commit Actor state back to canonical state
 -> detach transient grants/delegates
 -> route back to Mass
 -> release/pool Actor
 -> increment representation generation
```

异步 spawn/pool callback 必须检查 generation。

## 9. Simulation LOD、Representation LOD、Replication LOD 不同

不要只设计一个“NPC LOD”。至少区分：

1. **Simulation LOD**：多久算一次 AI/movement；
2. **Representation LOD**：Actor/ISM/None；
3. **Replication LOD**：对每个 connection 发送多少、多久一次。

同一个 NPC 对 Server 可能仍完整 simulation，但对远端客户端：

- 没 Actor；
- 低 representation；
- 低频 replication。

反之，本地画面 high-res 不代表服务器需要每帧做完整高成本 AI。

## 10. MassReplication：server-to-client projection

MassReplication 当前设计是 server -> client 的 one-way entity replication，并用 per-client viewer/ReplicationLOD 控制 relevancy/update frequency。

这不等于：

- client prediction framework；
- peer authoritative simulation；
- GAS replacement；
- reward/inventory replication truth；
- client AI result validation。

Authority 仍决定：

- damage；
- death；
- loot；
- quest/progression；
- ownership；
- persistent state。

自定义 replicated Entity type 要按当前 API实现 Replicator/Replication Processor，并测试：

- DS；
- ≥2 clients；
- per-client LOD；
- JIP；
- relevance in/out；
- packet loss/latency；
- entity destroy/recreate。

MassGameplay/Replication 当前成熟度还需目标版本 feature gate。

## 11. ZoneGraph、SmartObject、StateTree、Processor 分工

### ZoneGraph

负责：

- 设计驱动的 lane/corridor；
- 轻量路径/流向；
- lane tags/annotations；
- crowd/traffic spatial routing。

不是通用 NavMesh 的绝对替代，也不是 AI brain。

### SmartObject

负责：

- “这里有什么活动”；
- spatial query/filter；
- reservation/claim；
- slot/config/behavior definition。

SmartObject **不拥有实际交互执行逻辑**。Agent/Player 自己执行坐下、开门、采集、动画等行为。

### StateTree

负责：

- 分层状态；
- selector + state machine；
- transition；
- task/evaluator；
- 行为编排。

Mass StateTree 应尽量写 fragment/intent，使 batch processor 执行通用数据逻辑；不要把每 Entity 重新变成“一个 UObject brain”。

### Processor

负责：

- 对同构数据做批处理；
- movement/steering；
- cooldown/timer；
- compact state update；
- data transform。

不要在一个 Processor 里同时实现 lane search + SmartObject reservation + animation Actor spawn + quest reward + save。

## 12. SmartObject reservation 是业务资源合同

即使 SmartObject 系统提供 reservation，也要明确：

- claim handle 生命周期；
- timeout/cancel；
- agent death/demotion；
- SmartObject unload/WorldPartition；
- priority；
- double claim；
- save/JIP 是否需要持久化。

对于真正有经济/奖励影响的活动，SmartObject reservation 只证明“slot 被占用”，奖励仍由 Authority operation 验证。

## 13. Mass 与 Actor/Pawn/GAS 的 hybrid 边界

推荐层级：

### Tier 0 — Aggregate / offline

- 不存在逐实体 runtime representation；
- 只按 population/budget 模拟。

### Tier 1 — Mass low fidelity

- StableAgentId；
- transform/velocity/basic state；
- low-frequency AI；
- ISM/none；
- no per-agent GAS。

### Tier 2 — Mass high fidelity / Actor representation

- 仍由 Mass canonical agent state 驱动；
- Actor 只是 representation；
- 可以做复杂动画/碰撞，但长期状态不只放 Actor。

### Tier 3 — Full gameplay Actor/Pawn

- Mover/CMC；
- GAS；
- Equipment；
- complex collision/physics；
- player interaction；
- combat RPC/prediction。

Promotion threshold 由：

- player distance；
- visibility；
- combat/target status；
- interaction reservation；
- quest importance；
- server budget；

综合决定，不只是距离。

## 14. Combat bridge：一次伤害只有一个 canonical consumer

Hybrid 系统最大风险是：

```text
Mass damage processor
+ promoted Pawn GAS
= double damage
```

每个 Agent 必须有 routing state：

```text
StableAgentId
RepresentationGeneration
CombatOwner = Mass | Actor
```

Damage request 进入 Authority 后：

1. resolve StableAgentId；
2. 读取当前 CombatOwner + generation；
3. 只路由到一个 canonical consumer；
4. 用 DamageId/HitId idempotency；
5. commit result；
6. presentation 从结果投影。

Promotion/demotion commit 时更新 routing fence；旧 Actor callback 或旧 Mass command 检查 generation 后拒绝。

## 15. 宠物、坐骑和形态切换

远处宠物可 Mass；一旦：

- 被玩家骑乘；
- 进入复杂战斗；
- 需要 Mover/PhysicsControl；
- 需要 GameplayCamera；
- 需要 socket/retarget/linked layer；

就应该升级到 Actor/Pawn representation。

长期 identity：

```text
PetId / NPCId / OwnerId
```

不能用：

```text
FMassEntityHandle / Actor pointer
```

当作 Save identity。

## 16. 性能验证：Mass 不是口号

至少测：

- entity count；
- archetype count；
- chunk occupancy；
- fragment bytes/entity；
- structural mutations/frame；
- processors/frame；
- processor worker/GameThread time；
- query overlap/dependencies；
- signal rate；
- StateTree active count；
- SmartObject queries/sec；
- ZoneGraph path requests；
- representation counts：Actor/ISM/None；
- promotion/demotion/sec；
- replication bytes/connection；
- LOD distribution；
- server memory。

工具：

- Mass Debugger；
- Gameplay Debugger；
- Unreal Insights；
- Network Insights；
- `stat` / Trace counters；
- target hardware dedicated server profiling。

### 16.1 必做基线

比较：

1. 当前 Actor/Pawn 方案；
2. Actor 方案 + Significance/AI budget；
3. Mass prototype；
4. Hybrid promotion/demotion。

以相同数量、行为、视距、网络连接测试，不用“Mass 看起来更现代”决定架构。

## 17. Debugger 本身是设计反馈工具

UE5.8 Mass Debugger 可以检查：

- entity fragment data；
- fragment access breakpoints；
- processor data access overlaps；
- processor/query inspection。

如果一个系统无法在 Debugger/trace 中解释：

- 哪个 processor 写了状态；
- 为什么两个 processor 互相串行；
- 为什么 archetype 爆炸；
- 为什么 entity 被高频迁移；

说明数据合同还不够清晰。

## 18. Production adoption checklist

在把 Mass 子系统标记 production-ready 前：

### Engine/Build

- [ ] 目标 UE5.7/5.8 当前源码 API；
- [ ] Win64/Server Target UBT；
- [ ] Cook/Package；
- [ ] Editor-only module 没泄漏 Runtime；
- [ ] 5.7→5.8 compile matrix。

### Correctness

- [ ] StableAgentId；
- [ ] Mass handle generation；
- [ ] structural mutation safe boundary；
- [ ] subsystem thread traits；
- [ ] signal payload ownership；
- [ ] promotion/demotion transaction；
- [ ] Actor pool reuse；
- [ ] combat routing fence；
- [ ] SmartObject reservation cleanup。

### Network

- [ ] DS；
- [ ] listen host；
- [ ] 2+ remote clients；
- [ ] JIP；
- [ ] per-client ReplicationLOD；
- [ ] relevancy in/out；
- [ ] high latency/packet loss；
- [ ] promotion during network update。

### Performance

- [ ] Mass Debugger snapshot；
- [ ] Insights CPU trace；
- [ ] Network Insights；
- [ ] memory/chunk/archetype counters；
- [ ] Actor baseline comparison；
- [ ] worst-case signal/structural churn。

## 19. 不迁移清单

从旧 Mass sample 不直接迁：

- 旧版 API 签名；
- 旧 `ConfigureQueries()` 与 iteration boilerplate 当唯一现代方案；
- “所有 Processor 都自动多线程”的假设；
- “Tag/Fragment 想加就加没有结构成本”的假设；
- client-side replicated Mass 直接承担 Authority gameplay；
- MassEntityHandle 作为 Save/Quest identity；
- Actor representation 持有唯一业务真值；
- ZoneGraph/SmartObject/MassAI Experimental 模块成为 Foundation 硬依赖。

迁移的是：

- data-oriented layout；
- explicit access contract；
- batch processing；
- LOD 分层；
- stable identity + ephemeral representation；
- event/signal wakeup；
- Authority + projection；
- hybrid simulation tiers。
