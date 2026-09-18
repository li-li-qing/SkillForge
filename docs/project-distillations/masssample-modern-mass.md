# Megafunk/MassSample + Epic UE5.8 Mass 源码蒸馏

> 第十一轮外部 UE 项目研究。目标不是把 LGameplayFramework 重写为 ECS，而是判断 UE5.7/5.8 的 MassEntity / MassGameplay / MassAI / MassLOD / MassReplication / StateTree / ZoneGraph / SmartObject 能为大规模 ARPG NPC、宠物、坐骑和世界模拟提供什么，以及哪些部分仍不适合成为 Production Foundation。

## 0. 结论摘要

### 主样本

- Repository：`Megafunk/MassSample`
- Commit：`ca9825861f35ab4f8e152351de2adb893b51ca70`
- Commit date：2026-06-27
- Commit message：`(5.8) Fix missing comments`
- License：MIT
- Repository created：2022-03-15
- 研究时仓库仍活跃，README 已说明代码更新到 UE5.7，固定 commit 又继续更新到 UE5.8。

### 演化对照

- Old fork：`getnamo/MassCommunitySample@1487f0208873acda6fedcfe58a4b1a2f3268192a`
- fork README 主体仍带 UE5.1 时代文档；
- fork 自己说明已经 detached from upstream；
- 只保留为“同一 Mass sample 在版本演化中的旧 API 证据”。

### 官方现代性校准

Epic UE5.8 官方文档 / release notes：

- MassEntity 已进入 Engine Runtime 模块；
- UE5.8 对 Mass processor scheduling/dependency 做重大重构；
- Mass Signals 进入 core；
- entity creation 可以 off game thread；
- 新 sparse/virtual fragment 体系；
- MassCore 进一步解耦核心；
- 新 QueryExecutor 简化/强类型 query API；
- Mass Debugger 大幅增强；
- MassGameplay / MassAI / MassCrowd / ZoneGraph 当前官方仍标 Experimental；
- StateTree 为独立 Gameplay plugin；
- SmartObject 继续以“活动定义 + reservation”为核心；
- MassRepresentation、SimulationLOD、ReplicationLOD 仍是关键规模化机制。

### Freshness 分类

**Megafunk/MassSample current upstream：Current-to-target concepts / Sample caveat**

含义：

- upstream 固定提交已经针对 UE5.8；
- 代码可以用于理解当前 query/processor 形状；
- README 自己承认部分旧代码示例仍需重写，因此 README 不能作为 API authority；
- 它仍是 community sample，不是 Epic 官方 production framework。

**getnamo fork：Historical / API-evolution evidence**

含义：

- 可用于观察 UE5.1 到 5.8 的变化；
- 不再作为目标项目 API 模板。

### 关键结论

最值得吸收的不是某个 `UMassProcessor` 函数签名，而是：

1. data-oriented layout；
2. explicit read/write access；
3. batch/chunk processing；
4. simulation / representation / replication 三层 LOD；
5. stable business identity 与 ephemeral runtime representation 分离；
6. signals/observers 唤醒稀疏工作；
7. Mass 与 Actor/Pawn 的 hybrid promotion/demotion；
8. ZoneGraph / SmartObject / StateTree / Processor 分工；
9. Mass Debugger + Insights 作为架构反馈；
10. Authority server 仍拥有伤害、掉落、奖励、持久状态。

最重要的拒绝项：

1. “Mass 一定比 Actor 快”；
2. `FMassEntityHandle` 当 Save/NPC/Pet 永久 ID；
3. high-res Actor 当唯一业务 state owner；
4. client Mass simulation 当 damage/reward authority；
5. 把 MassGameplay/MassAI Experimental plugin 作为 LGF Foundation 硬依赖；
6. 从 UE5.1 fork 复制 Query/Processor API 到 5.7/5.8；
7. 在并行 Processor 内隐式 SpawnActor/改 UObject；
8. 把 ZoneGraph、SmartObject、StateTree、Processor 写成一个巨型“AI System”；
9. 所有可选状态都通过高频普通 Tag/Fragment structural mutation 表达；
10. 因为 ECS 有多线程就跳过 benchmark。

---

# Part A — 版本与技术时效性

## 1. 为什么这一轮必须先改研究入口

最初候选是 `getnamo/MassCommunitySample`。

仓库元数据看起来并不“死”：

- 2025 还有 push；
- README 很详细；
- C++ sample 能看到 movement、projectile、ZoneGraph 等案例。

但 README 顶部直接写明：

- 它是为了 LFS 原因与 upstream 脱离的 fork；
- 文档主体仍以 UE5.1 作为 requirements；
- Mass 当时仍被称为非常 WIP/experimental。

继续查 upstream 后发现：

`Megafunk/MassSample` 已在 2026-06-27 更新到 UE5.8。

所以这轮形成一个新的外部项目审查规则：

> “仓库最后更新时间”只能判断那个 fork 有人动过，不能证明它代表技术主线。

必须先找 upstream。

## 2. Upstream README 自己也提醒“代码优先”

当前 upstream README 顶部记录：

- 5.7 update：代码已更新到 5.7；
- 5.6 update：大量改进与修复；
- README 中很多内容仍有效；
- 但一些代码示例是 pre-5.6，需要重写；
- 有疑问时 current code 比 README 更可靠。

这个声明很重要。

即使作者还在维护：

```text
Current repository
!= current README code block
!= current engine API authority
```

### 2.1 固定源码比 prose 更具体

旧 fork 的 movement processor：

```text
ConfigureQueries()
Query.ForEachEntityChunk(EntityManager, Context, ...)
```

当前 upstream 5.8 fixed commit：

```text
ConfigureQueries(const TSharedRef<FMassEntityManager>& EntityManager)
Query.Initialize(EntityManager)
Query.ForEachEntityChunk(Context, ...)
```

这个差异足以证明：

> Mass 的机制可能稳定，但函数签名/生命周期在持续变化。

Skill 不应写死旧 Sample API。

## 3. UE5.8 是 Mass 的架构级变化版本

Epic 5.8 release notes 不是简单列几个 bugfix，而是明确描述：

### 3.1 Signals 进入核心

过去很多 Mass sample 把 Signals 当 MassGameplay/StateTree 附属概念。

5.8 以后应该把它理解为更核心的 event-driven wakeup 机制。

### 3.2 Off-thread entity creation

Entity creation 可在 game thread 外完成，依赖 archetype-based lock-free scheduling。

这意味着旧文档里“一切 entity mutation 最终都当 GT 串行操作”的心理模型需要重新检查。

但这不等于 UObject/Actor suddenly thread-safe。

### 3.3 Sparse / Virtual fragments

过去频繁增删 Fragment/Tag 可能导致 archetype migration。

5.8 引入 sparse/virtual fragment，解决一部分：

- 可选状态；
- 内存；
- 高频 presence change；

问题。

但它不是“以后 archetype churn 不存在”。

仍需要 profile：

- normal fragment；
- tag；
- sparse/virtual state；
- external store；

哪个更合适。

### 3.4 Processor scheduler / dependency overhaul

5.8 更充分利用现代多核。

因此 Query 的 access declaration 更重要，而不是更不重要。

### 3.5 MassCore

核心 Entity 能力与完整 Gameplay Stack 更解耦。

这对 LGF 特别有价值：

> 可以研究/采用 data-oriented core，而不必一次性绑定 MassGameplay/MassAI/MassCrowd 全家桶。

## 4. QueryExecutor：现代 API 方向

Epic 5.8 新增 Simplified Mass Processor / Query API。

核心是 `UE::Mass::FQueryExecutor` + `FQueryDefinition` 一类更强类型的 declaration。

目的：

- 减少 boilerplate；
- 提升可读性；
- 提升类型安全。

官方同时说明：

- 它是 optional；
- 现有 UMassProcessor 风格仍受支持；
- 当前 QueryExecutor 仍需要被 UMassProcessor 拥有；
- 以后可能继续演化。

所以 Skill 不应写：

> “5.8 必须全面重写为 QueryExecutor。”

而应写：

> “新代码评估 QueryExecutor；已有 Processor 只有在收益明确时迁移。”

---

# Part B — ECS 数据模型

## 5. Entity 不是对象

Mass Entity 本质是：

- runtime handle；
- 指向某个 archetype/chunk 中的 fragment data；
- 没有面向对象的“每 Entity virtual behavior”。

这是它能高性能批处理的根本原因。

如果最后设计成：

```text
Entity
 -> UObject Brain
 -> UObject Inventory
 -> UObject Stats
 -> UObject Animation
 -> UObject Behavior
```

就把 pointer chasing 和 per-object overhead 又引回来了。

## 6. StableAgentId 必须单独存在

`FMassEntityHandle` 适合：

- 当前 World；
- 当前 entity manager；
- runtime lookup。

不适合：

- Save；
- Quest tracking；
- Pet identity；
- Party member identity；
- NPC persistent state；
- cross-world travel。

大地图 ARPG 应保持：

```text
StableAgentId
DefinitionId
SpawnSourceId
Persistent progression/state
```

Mass handle 只是 cache。

## 7. Fragment 不是“Component 类”

Fragment 设计关键不是“这个功能属于谁”，而是：

> 哪些数据会一起被哪个 processor 高频访问？

### 7.1 Hot data

Movement processor 需要：

- Transform；
- Velocity；
- Force。

这类数据紧凑且连续。

### 7.2 冷数据

Quest text、长字符串、复杂 loot table、UI metadata、动画资产 soft path：

不应该每 Entity 热存。

### 7.3 Shared fragment

速度 tuning、representation config 等可以 shared。

但 per-agent Health 不能 shared。

## 8. Archetype 是性能工具，也可能成为性能问题

每种 unique fragment/tag composition = archetype。

如果设计：

```text
IsAlert
IsTalking
IsQuestRelevant
IsMounted
IsHungry
IsNearShop
IsRecentlyDamaged
...
```

全部都做成高频 add/remove 普通 Tag：

组合会膨胀。

5.8 sparse/virtual fragment 提供了新选择，但仍应测：

- archetype count；
- chunk occupancy；
- structural migrations；
- processor cache；
- memory。

---

# Part C — Processor、Query、线程

## 9. Current upstream movement sample

当前 fixed commit 的 `UMSGravityProcessor`：

- `ExecutionFlags = All`；
- 排在 Movement group 前；
- query 需要 gravity tag；
- velocity fragment ReadWrite。

BasicMovement：

- Transform ReadWrite；
- Force ReadOnly；
- Velocity ReadWrite；
- chunk iteration；
- 连续数组循环。

这是 Mass 最标准的价值：

> 对一组同构数据做简单、密集、可声明的批处理。

## 10. Query declaration 是 scheduler 输入

ReadOnly/ReadWrite 不只是 const correctness。

Scheduler 需要知道：

- 谁读某 Fragment；
- 谁写；
- 谁访问外部 subsystem；
- 哪些 Processor 有 dependency；
- 哪些可以并行。

如果真实代码：

```text
声明 ReadOnly
实际旁路写
```

或者：

```text
没声明 WorldSubsystem
lambda 直接写 Subsystem
```

会破坏调度假设。

## 11. Processor 不是自动线程安全

不要从：

```text
Mass = multithreaded
```

推出：

```text
Processor 里任意 UObject 操作都是安全的
```

仍然必须区分：

- fragment POD；
- Mass entity manager mutation；
- thread-safe subsystem；
- Actor/UObject；
- physics/nav/world query；
- Blueprint。

## 12. External subsystem traits

旧 sample 已经展示：

`TMassExternalSubsystemTraits<Subsystem>`

用于声明 thread-safe read/write。

这个思想继续保留：

> Scheduler 必须知道外部依赖。

但具体 trait API 仍按目标引擎核对。

更重要的是：

**trait declaration 必须与 subsystem 实现一致。**

只有 `ThreadSafeRead=true`，但内部返回无锁 mutable TArray，仍然是错误。

## 13. Structural mutation

遍历 chunk 时直接改变 composition 可能使当前 view 失效。

旧 sample 强调 deferred mutation。

5.8 又新增更多 batch/entity builder/observer 能力。

迁移的不是某个 `Defer()` API，而是：

> structural mutation 必须发生在框架允许的安全提交边界。

---

# Part D — Signal 与稀疏工作

## 14. 为什么 Signals 重要

假设 100,000 NPC：

- 90,000 idle；
- 8,000 low-rate moving；
- 1,800 regular behavior；
- 200 当前事件活跃。

如果每帧：

```text
scan 100k -> Dirty?
```

即使每个 check 很轻，也会浪费大量 bandwidth/cache。

Signal 可以让少量 Entity 被唤醒。

## 15. Signal 不带业务真值

推荐：

```text
PathInvalidated
DamagePending
SmartObjectChanged
BehaviorWakeup
```

数据放：

- Fragment；
- Authority queue；
- subsystem。

不推荐把 signal 当 event payload bus：

```text
DamageSignal(Damage=125, ItemDrop=...)
```

否则 signal scheduling/loss/duplicate 会进入业务一致性。

---

# Part E — LOD：三个不同问题

## 16. Representation LOD

Epic MassGameplay 当前定义：

- High-res Actor；
- Low-res Actor；
- ISM；
- None。

Representation subsystem 还能：

- spawn Actor；
- recycle Actor；
- pool Actor。

结论：

**Actor 是 representation，不是长期 entity identity。**

## 17. Simulation LOD

决定：

- behavior 是否更新；
- 更新频率；
- 哪些 Processor 工作；
- variable tick。

远处 Entity 可以：

- 1 Hz；
- 0.2 Hz；
- event only；
- aggregate。

## 18. Replication LOD

这是对每个连接独立计算的网络 LOD。

Player A 靠近 NPC：

- high update。

Player B 很远：

- low update / irrelevant。

所以 replication LOD 不能由 Entity 自己保存为一个全局 enum。

## 19. 三种 LOD 不能合并

错误：

```text
LOD=Low
=> low AI
=> low visual
=> low network
```

实际可能：

- Quest NPC 远处仍 server high simulation；
- 但 client no visual；
- network low frequency。

或者：

- local crowd visible high visual；
- behavior 仍 low-rate；
- server replication moderate。

---

# Part F — Actor promotion / demotion

## 20. 为什么 hybrid 比“全 Mass”更适合 ARPG

ARPG 高交互 NPC 需要：

- Mover；
- GAS；
- Equipment；
- weapon traces；
- root motion；
- Pose Search/GASP；
- complex hit collision；
- physics/ragdoll；
- SmartObject interaction；
- camera/lock-on；
- Blueprint gameplay callbacks。

这些全部塞进低保真 Mass 会抵消 Mass 的优势。

## 21. 推荐 simulation tiers

### Tier 0 Aggregate

只有 population/budget。

### Tier 1 Mass

compact simulation + ISM/none。

### Tier 2 Mass + Actor representation

Actor 是表示，Mass 仍是 simulation owner。

### Tier 3 Gameplay Pawn

完整 Pawn/Mover/GAS。

## 22. Promotion 是 transaction

必须带：

- StableAgentId；
- RepresentationGeneration；
- reservation；
- spawn/reuse Actor；
- state handoff；
- readiness；
- routing switch。

不能：

```text
SpawnActor
Mass entity继续跑
Pawn GAS也开始跑
```

否则双 simulation。

## 23. Demotion 也要 commit

Actor 在销毁/回收前：

- Health；
- transform；
- high-level behavior；
- inventory/equipment semantic state；
- death/loot status；

必须回写 canonical Agent record。

---

# Part G — Network / MassReplication

## 24. MassReplication 的正确定位

官方当前描述：

- server to clients；
- one-way projection；
- relevance/update frequency 由 replication LOD 协助。

所以它不是：

- client prediction；
- rollback netcode；
- GAS；
- P2P authority；
- reward validation。

## 25. Client Mass 不能决定业务真值

客户端可：

- interpolation；
- visual movement；
- local LOD；
- cue；
- cosmetic simulation。

客户端不可：

- 最终 damage；
- loot roll；
- quest progression；
- Inventory grant；
- NPC ownership；
- persistent death。

## 26. Per-client viewer 是关键

大规模 replication 的目标不是“复制所有 Entity”。

而是：

```text
Connection / Viewer
 -> relevance
 -> replication LOD
 -> add/modify/remove projection
```

因此网络测量必须 per client。

---

# Part H — StateTree / ZoneGraph / SmartObject

## 27. StateTree

StateTree：

- hierarchical state machine；
- selector；
- task；
- transition；
- evaluator。

它适合 high-level behavior orchestration。

Mass StateTree 应倾向：

```text
select intent
 -> write compact target/state
 -> Processor 批处理执行
```

而不是每个 Task 重新做一套 Actor gameplay system。

## 28. ZoneGraph

适合：

- 道路；
- corridor；
- crowd lanes；
- traffic；
- designer-authored route topology。

当前官方仍把 ZoneGraph 标 Experimental。

生产必须 adapter/feature gate。

## 29. SmartObject

官方当前核心定义：

> activities + reservation。

SmartObject 不执行最终交互逻辑。

例如“椅子”：

SmartObject 提供：

- seat location；
- tags；
- reservation slot；
- behavior definition。

NPC 自己：

- 移动；
- 对齐；
- 播动画；
- 结束；
- release reservation。

## 30. 四层组合

城市 NPC：

```text
StateTree: 我现在想休息
ZoneGraph: 怎么沿 lane 到休息区
SmartObject: 哪张椅子可 claim
Mass Processor: 批处理 movement/steering/state
Actor/Anim representation: 近景时展示坐下
```

职责非常清楚。

---

# Part I — LGF ARPG 映射

## 31. LGF 不替换 Foundation

Mass 应是：

```text
Optional Simulation Module
```

而不是：

```text
New Foundation
```

LGF stable systems 保留：

- Authority；
- Request；
- Inventory；
- Equipment；
- GAS；
- Mover；
- Save；
- UI；
- GameplayCamera。

## 32. Stable Agent Registry

建议服务：

```text
StableAgentId -> canonical record
                 |- DefinitionId
                 |- persistent state
                 |- current Mass handle
                 |- current Actor
                 |- representation generation
                 |- combat owner
```

不要让 Mass entity manager 变 persistent database。

## 33. 城镇人群

第一批最适合 Mass：

- civilian；
- merchant crowd；
- animals；
- background soldiers；
- decoration NPC。

先不迁：

- Boss；
- active combat mobs；
- quest cinematic NPC；
- mount in use。

## 34. 战斗 NPC

远处：

- Mass。

进入 combat bubble：

- promotion 到 LGF Pawn；
- Mover/GAS/Equipment/GASP ready；
- CombatOwner 切 Actor。

退出一段时间：

- commit state；
- demote。

## 35. AoE 跨 representation

AoE query 得到一组 StableAgentId。

每个：

```text
Resolve current generation
 -> if CombatOwner Actor: GAS
 -> else Mass server damage processor
 -> DamageId dedup
```

同帧 promotion 也不会双扣。

## 36. 宠物

未激活：

- Mass low fidelity。

跟主人：

- 可能 high-res representation。

战斗/骑乘：

- full LGF Pawn。

PetId 永远不变。

## 37. 骑任意 NPC

玩家发 `RideIntent(PetId/NpcId)`。

Authority：

- owner/access；
- range；
- alive；
- state；
- cooldown；
- current generation。

然后：

- promotion；
- mount Avatar ready；
- Mover；
- GameplayCamera；
- socket/retarget；
- mount abilities；
- mounted state。

这与前面 Avatar/Transformation 规则直接兼容。

## 38. 吸收 NPC 变身

不要把玩家变成 Mass entity。

吸收的是：

- NPC Definition；
- shape recipe；
- animation/ability data。

玩家 stable owner/ASC 不变。

原 Mass NPC 由 Authority 正常 despawn/death transaction。

---

# Part J — 性能与调试

## 39. Mass Debugger

5.8 的 Mass Debugger 可以：

- 实时 fragment inspection；
- entity fragment access breakpoint；
- Gameplay Debugger integration；
- processor inspection；
- data access overlap。

这让“哪个 processor 阻塞了哪个 processor”变得可以验证。

## 40. 真正要量什么

### ECS layout

- Entity count；
- archetype count；
- chunk occupancy；
- bytes/entity；
- sparse/virtual fragment usage。

### Runtime

- worker time；
- GameThread time；
- processor count；
- query/chunk scans；
- structural mutation count；
- signal rate。

### AI

- StateTree active；
- SmartObject searches；
- ZoneGraph path；
- perception/events。

### Representation

- Actor high；
- Actor low；
- ISM；
- none；
- promotion/demotion/sec。

### Network

- bytes/connection；
- entity add/modify/remove；
- replication LOD distribution；
- JIP burst。

## 41. 必须有 Actor baseline

测试至少：

```text
A. Current Actor AI
B. Actor AI + Significance/Budget
C. Pure Mass prototype
D. Hybrid
```

相同 gameplay workload。

如果 B 已经满足预算，不必为了架构时尚迁 C/D。

---

# Part K — 风险与拒绝项

## 42. Experimental plugin 依赖风险

当前官方仍把：

- MassGameplay；
- MassAI；
- MassCrowd；
- ZoneGraph；

标 Experimental。

对 Free/Production plugin 的 LGF：

- 不在 Foundation public header 暴露这些类型；
- optional module；
- adapter；
- feature flag；
- fallback；
- 每次 UE upgrade 重新审查。

## 43. ISM animation 也不是“全功能 Skeletal Mesh”

官方当前文档仍提示 MassGameplay ISM animation 不是所有 use case 都完整支持。

因此近景 ARPG weapon combat 不能只为了省 Actor 强塞到 ISM animation。

## 44. World Partition / streaming

大地图要额外考虑：

- Agent persistent identity；
- ZoneGraph data load/unload；
- SmartObject registration；
- Entity despawn vs persistent save；
- promotion Actor 所在 level；
- async late callback。

“Entity still valid”不能只看 handle。

## 45. 存档

不要 Save：

- MassEntityHandle；
- archetype pointer；
- chunk index；
- Actor pointer；
- representation LOD。

Save：

- StableAgentId；
- DefinitionId；
- position/zone semantic；
- persistent stats；
- pet owner；
- quest state；
- inventory link IDs。

load 时重建 runtime Mass/Actor representation。

---

# Part L — 第一阶段 LGF 实施建议

## 46. Phase 0：只做 adapter + benchmark

不改 gameplay。

建立：

- optional Mass module；
- StableAgentId fragment；
- basic movement；
- debug counter；
- Actor baseline map。

## 47. Phase 1：环境人群

- 1k/5k/20k；
- no combat；
- representation LOD；
- simple ZoneGraph；
- Mass Debugger profiling。

## 48. Phase 2：promotion/demotion

- pooled simple Actor；
- stable mapping；
- generation；
- repeated enter/exit；
- JIP。

## 49. Phase 3：LGF high fidelity bridge

- LGF Pawn；
- Mover；
- GASP；
- Equipment visual；
- no damage first。

## 50. Phase 4：combat routing

- DamageId；
- CombatOwner；
- promotion during hit；
- AoE；
- death/loot。

## 51. Phase 5：pets/mounts

- PetId；
- owner；
- ride transaction；
- GameplayCamera；
- socket/retarget；
- reconnect/save。

---

# Part M — 验收矩阵

## 52. Build

- UE5.7 Editor target；
- UE5.7 Server target；
- UE5.8 Editor target；
- UE5.8 Server target；
- Cook/Package。

## 53. Network

- Standalone；
- Listen Host；
- 2 Remote clients；
- Dedicated Server；
- JIP；
- reconnect；
- latency；
- packet loss；
- relevancy enter/exit。

## 54. Promotion

- 100 Entity 同时 promotion；
- same agent double request；
- death during promotion；
- target removed；
- level unload；
- old callback；
- pool Actor reused；
- demote while hit pending。

## 55. Combat

- Mass only hit；
- Actor only hit；
- same-frame promotion + hit；
- AoE across mixed representations；
- death + loot；
- duplicate DamageId；
- stale generation。

## 56. Performance

- low/medium/high entity counts；
- actor baseline；
- same behavior coverage；
- same network clients；
- worst signal storm；
- structural churn；
- representation churn。

---

# 57. 最终迁移决策

## 直接写回 Skills

- version/upstream freshness；
- Mass 5.8 overhaul awareness；
- fragment layout/access contract；
- signal wakeup；
- three LOD axes；
- representation Actor ephemeral；
- server-only business authority；
- ZoneGraph/SmartObject/StateTree/Processor separation；
- hybrid tiers；
- promotion/demotion generation；
- CombatOwner routing；
- Pet/Mount hybrid；
- Mass Debugger benchmark。

## 仅项目报告保留

- Sample-specific cone parade；
- sample projectile code；
- experimental Niagara representation examples；
- historical README code blocks；
- exact current sample module layout。

## 不写回生产默认

- old UE5.1 API；
- community sample README 作为 Engine authority；
- pure Mass rewrite；
- Experimental plugin hard dependency；
- client authoritative Mass gameplay。

---

# 58. 本轮未验证

本轮没有：

- 下载/构建 MassSample LFS assets；
- UBT UE5.7/5.8；
- Editor PIE；
- Dedicated Server；
- MassReplication 实机网络；
- StateTree/ZoneGraph asset compile；
- 1k/10k/100k entity benchmark；
- World Partition streaming；
- Pet/Mount prototype。

所以本轮结论是：

**源码/官方文档级架构蒸馏 + Skill 行为合同，不是 LGF Mass implementation acceptance。**
