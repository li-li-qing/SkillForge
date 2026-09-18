# ActionRoguelike 项目蒸馏：第一轮

检查日期：2026-09-14  
来源：`tomlooman/ActionRoguelike`  
固定源码快照：`a3f9a182c985b1732d9f72ae8b92e4845babfa3f`（master）  
项目 README 标注主分支引擎：UE 5.6。目标 SkillForge / LGF 当前工作以实际消费工程版本为准，不能因该样例使用 5.6 就直接假定 5.7 API 完全一致。

> 本文是源码机制蒸馏，不是代码移植说明。GitHub 仓库元数据没有声明可直接依赖的开源 License；本轮不复制第三方实现，只记录架构、边界、风险与可验证的设计模式。

## 1. 为什么把它放在第一位

ActionRoguelike 不是单一功能插件，而是一个持续更新的 UE C++ 游戏样例。它同时覆盖：多人、Action/Attribute、AI、EQS、StateTree、数据驱动生成、Primary Asset 异步加载、SaveGame、UMG、异步碰撞查询、Actor Pooling、轻量 projectile、FastArray、Insights/Trace、PSO 等。这很适合先建立 SkillForge 的“通用运行时工程审查基线”。

但主分支 README 也明确把若干性能方案标成实验/WIP，并说明部分实验系统不一定完整支持多人。因此本轮采用两层记录：

- **稳定模式**：可作为通用技能的审查原则，但仍需按目标工程版本复核。
- **实验模式**：只提炼设计意图、风险与验证门槛，不当成生产代码模板。

## 2. 源码模块地图

当前 `Source/ActionRoguelike` 至少包含以下重点目录：

| 模块 | 主要职责 | SkillForge 价值 |
|---|---|---|
| `ActionSystem` | Action UObject、ActionComponent、AttributeSet、Tag、Cooldown/Effect | 复制 UObject 子对象、OnRep/Host 刷新、Authority 状态修改 |
| `AI` | AIController、Behavior Tree Task/Service/Decorator、Perception | Server-only brain、事件监听、BT 热路径预算 |
| `StateTrees` | Director Schema / Task / PropertyRef | StateTree 与数据驱动 Director 的现代用法 |
| `Core` | GameMode/GameState、Primary Asset、Deferred Task、通用接口 | 数据选择→异步加载→Authority Spawn；实验任务切片 |
| `SaveSystem` | GameInstanceSubsystem、SaveGame、Actor 二进制序列化 | 保存参与接口、SaveGame 标记、稳定身份/大世界边界 |
| `Performance` | Actor Pool、Tick 聚合等实验 | Pool reset contract、功能开关、Insights 测量 |
| `Projectiles` | Actor projectile、数据导向 projectile、FastArray 元数据 | 高频数据分层、预测缓存、FastArray 回调/Dirty |
| `Player` | Character、InteractionComponent、Async Sweep 等 | Local intent 与 Authority validation 分离 |
| `UI` | UMG、世界空间 UI、异步图标 | 事件驱动刷新、Soft Asset 异步生命周期 |
| `Animation` / Monster Data | Hit react、Animation Budget 等 | 数据配置思路；不是本项目最强的动画框架来源 |

后续专门的 GASP/ALS 项目应负责 Motion Matching、Linked Anim Layer、Mover、Root Motion、动画线程等深度规则；本项目不应被硬扩展成动画权威样例。

## 3. Action System：复制 UObject 子对象

### 3.1 观察到的结构

`URogueActionComponent` 是复制 ActorComponent，关闭自身 Tick，并启用 registered subobject list。服务器在初始化时把 AttributeSet 注册为复制子对象；授予 Action 时服务器创建 `URogueAction` UObject，并把 Action 注册为复制子对象。

`URogueAction` 本身：

- 是 UObject，而不是 Actor；
- 明确支持 networking；
- 复制 owning component、运行状态、开始时间、Cooldown 时间；
- 运行状态使用 `ReplicatedUsing`；
- Proxy 的 OnRep 根据服务器状态重放 Start/Stop 表现。

Component 还复制 `Actions` 和 `AttributeSet` 指针，并通过 OnRep 重建客户端的非复制查询缓存。

### 3.2 可迁移规则

这比“给 UObject 成员加 `Replicated` 就结束”完整得多。SkillForge 应要求同时检查：

1. **复制宿主**：谁拥有并提供 NetDriver/ActorChannel 语义。
2. **UObject 网络资格**：是否明确支持 networking。
3. **子对象注册**：registered-subobject 路线是否 Add/Remove 成对，或目标工程是否仍走自定义 `ReplicateSubobjects`。
4. **属性注册**：重要属性是否有 `GetLifetimeReplicatedProps`，需要表现更新的属性是否有 OnRep。
5. **Authority 创建/销毁**：实例集合与业务真值只能由 Authority 改。
6. **Host 本地刷新**：OnRep 不是 Listen Host 本地逻辑的替代品；服务器写入真值后应走与 Proxy 一致的共享刷新函数或显式事件。
7. **JIP/重建**：客户端晚加入后能否仅靠复制状态重建缓存、Tag、UI、表现。
8. **清理**：RemoveReplicatedSubObject、数组移除、缓存移除、Action End、对象销毁是否一致。

### 3.3 不应直接复制的部分

样例里的 `ActiveGameplayTags` 不是直接复制真值，而是通过复制 Action 的 Start/Stop 在客户端重建。这个思路在小型 Action 系统中可工作，但不能直接外推到 GAS/LGF：

- 堆叠 Tag 可能发生计数冲突；
- Prediction/rollback 需要更严格的确认语义；
- JIP 必须证明所有持续状态都能由当前复制快照重建；
- 同一 Tag 来自多来源时，简单 Append/Remove 不能代替引用计数或 GAS 的 Tag 管理。

因此对 LGF 的结论是：**吸收“复制子对象生命周期与 Host/Proxy 刷新模式”，不以自制 Action 替换 GAS。**

## 4. Attribute：初始化期反射缓存，而不是热路径反射

AttributeSet 初始化时使用结构属性反射建立 `GameplayTag -> FRogueAttribute*` 缓存，之后查询直接访问缓存。Health 使用 `ReplicatedUsing`，OnRep 根据 OldValue 计算 delta，再统一广播 Attribute changed。

值得保留的机制：

- 反射扫描集中在初始化/重建阶段；
- 热路径走预建缓存；
- OnRep 不直接塞大量 UI 逻辑，而是进入统一事件刷新；
- Authority 改 Attribute，Proxy 消费复制；
- Base 和临时 Modifier 分开，为保存与运行时 Buff 提供不同生命周期。

需要补充的生产边界：

- 缓存中的原始 struct 指针只应被视为 owning UObject 生命周期内的派生索引；重建/重实例后必须重新填充。
- 若属性规模大、频率高，进一步关注布局、访问局部性和无意义 Map/Tag 查找；不能仅因“有缓存”就假定性能足够。
- LGF/GAS 已有 AttributeSet 时，不应复制这套自制属性框架，只吸收初始化缓存、Host/Proxy 通知和保存边界思想。

## 5. 网络交互：Local Candidate 与 Authority Authorization 必须拆开

`URogueInteractionComponent` 挂在 Controller 上。本地 Controller 在 Tick 中搜索候选、打分、显示高亮和 Widget；按交互后通过 Server RPC 发送当前 Focus Actor。

**好的部分**：

- 只有 LocalController 做本地候选搜索，SimulatedProxy 不浪费该查询；
- UI 高亮与候选选择属于本地体验，不要求复制；
- Server RPC 放在玩家拥有的 Controller/Component 路线上，而不是直接要求世界物体被客户端拥有。

**生产级必须补上的部分**：

当前样例的 `ServerInteract` 直接对客户端传入 Actor 调接口，没有看到同一函数内重新验证：距离、LOS、玩家存活、目标是否仍可交互、频率、权限、成本、会话代次等。教学 Demo 可以简化，生产联网游戏不能把客户端 Focus 当授权。

技能规则应固定成：

`Local Candidate -> Owned Request -> Authority Resolve/Revalidate -> Mutate Truth -> Replication/Result -> Local Presentation`

服务器最好根据稳定身份/当前上下文重新解析目标；即便 RPC 参数允许 Actor 引用，也必须把它当“请求候选”，而不是可信事实。

## 6. AI：Server-only Brain 与表现通知

AIController 在服务器/Host 运行。它启动 Behavior Tree，监听 Blackboard `TargetActor` 变化；发现玩家后，服务器调用目标玩家的 Client RPC 显示“被发现”等本地表现。

这提供了清晰边界：

- 感知、目标选择、行为树/StateTree 决策：Authority；
- AIController 不需要复制到客户端；
- 客户端需要看到的长期结果应来自 Pawn/GameState 等复制真值；
- 只属于目标玩家的瞬时通知可以走 owner Client RPC；
- UI 不应从本地推导 AI 真正锁定了谁。

### 6.1 BT Service 的性能与生命周期反例

攻击范围 Service 每次 Tick 计算距离并可能做 LOS；实验分支把 LOS 工作塞进 DeferredTask 队列。DeferredTask 本身按每帧预算处理队列，理念是把非关键 GameThread 工作切片。

但其中一个 BT 示例使用引用捕获把当前栈变量放进“未来可能才执行”的 Lambda。由于 DeferredTask 明确可能延后到后续帧，任何按引用捕获局部变量都需要当成高风险生命周期错误审查。当前该实验宏默认关闭，所以不能把它看成成熟范式。

技能应增加：

- 延迟执行 Lambda 默认按值捕获必要 POD；
- UObject/Actor 使用弱引用或明确拥有者并在执行时重新验证；
- 请求代次/World/Avatar 变化时拒绝旧任务；
- 把“延迟到以后”视为生命周期边界，即使仍在 GameThread；
- 优化前后用 Unreal Insights/Trace 证明帧时间改善。

## 7. Behavior Tree、EQS 与 StateTree 的职责

项目同时保留 Behavior Tree/EQS，并新增 StateTree Director 相关源码。这说明“新系统出现就全量替换旧系统”不是必须策略。

可借鉴分层：

- **BT / Perception**：单个 AI 的反应与执行流程；
- **EQS**：空间候选与位置选择；
- **StateTree/Director**：更高层的波次、选择、状态机式调度；
- **Action/GAS**：最终执行玩法能力；
- **DataTable / PrimaryDataAsset**：配置，而不是把业务分支塞进蓝图图表。

StateTree 示例也暴露了版本性：源码注释明确某些 PropertyRef 支持范围受 UE 5.6 限制。因此迁移到 5.7 必须重新核对 API/类型支持，不能把 5.6 的限制永久写进通用 Skills。

## 8. 数据驱动 Spawn：轻量选择与重资源加载分层

GameMode 的生成流程是本项目很值得吸收的一条链：

`Director budget -> DataTable weighted selection -> EQS location -> FPrimaryAssetId -> AssetManager async load -> Authority Spawn -> grant actions`

### 8.1 为什么这个结构好

- DataTable 负责便宜的选择数据（权重、成本、ID）；
- PrimaryDataAsset 负责 MonsterClass、Actions、Icon、HitReact、材料等配置；
- 选择时不需要把所有重资产同步加载；
- AssetManager 在异步完成后才 Spawn；
- GameMode 本身是 Authority 路径。

这直接强化 SkillForge 的热路径规则：**禁止在 Tick/高频循环里 `StaticLoadObject`、`FObjectFinder`、`LoadSynchronous` 或反复构造复杂 GameplayTag 查询。**

### 8.2 还应进一步改进

- 当前 Director Tick 间隔 0.1 秒，但到尝试生成时仍会 `GetAllRows` 并遍历权重；数据量扩大后应在表/配置变化时构建候选与累计权重缓存。
- 异步操作要带 generation/request token；回调时重新检查 World、GameMode、Director、当前波次与预算是否仍有效。
- “扣费 → EQS/Load → Spawn”属于异步事务，应明确 reserve / commit / refund；若异步步骤失败，不能静默丢失预算。
- PrimaryDataAsset 中的硬引用/软引用要按加载策略决定，不机械全换一种指针。

## 9. SaveGame：简单可靠的入门模式，但不是大世界生产模板

SaveGameSystem 使用 `UGameInstanceSubsystem` 集中管理槽位。保存世界 Actor 时：

1. 遍历世界 Actor；
2. 只处理实现指定接口的 Actor；
3. 保存 Transform；
4. 用 `FObjectAndNameAsStringProxyArchive` 且 `ArIsSaveGame=true`，只序列化 `UPROPERTY(SaveGame)`；
5. 加载后调用 `OnActorLoaded` 做派生状态重建。

这个模式适合 SkillForge 记录为“简单 SaveGame 机制的清晰职责”。但生产项目必须加限制：

- 全世界 `TActorRange` 扫描只适合低频 Save/checkpoint；不能放 Tick，也不适合无界大世界高频 autosave。
- Actor `FName` 不应视为永久业务身份；动态 Spawn、重命名、World Partition、跨地图都需要稳定 GUID/业务 ID。
- 当前源码明确只保存第一个 PlayerState，不能当多人存档完成方案。
- 同步 `SaveGameToSlot/LoadGameFromSlot` 的卡顿预算需要按数据量测量；大存档考虑异步、分区、脏集或快照队列。
- 联网时 Authority 决定真值和持久化；Remote client 只能请求，不能把自己的 UI/Proxy 状态写成权威存档。
- Load 后修改了复制真值，仍需让复制系统看到变化，并确保 Host、Remote、JIP 最终一致。

## 10. Actor Pooling：真正难点是 Reset Contract

Actor Pooling Subsystem 用 `TMap<Class, Pool>` 保存空闲 Actor，并用接口给 Actor `PoolBeginPlay/PoolEndPlay` 生命周期回调。它还提供预热，以减少首次 Spawn 抖动和碎片。

但作者把 Pool 默认关闭，并明确写出黑洞 projectile 的 VFX reset 仍有问题；同时当前实现只在 Standalone 启用。这是很好的教学点：

**“对象池存在”不等于“对象池可用于生产多人”。**

生产 Reset Contract 至少检查：

- collision / hidden / transform / owner / instigator；
- MovementComponent 的 velocity、updated component、activation；
- Niagara/Audio/Decal/Trail；
- timers、latent actions、async callbacks；
- delegates、input handles、GameplayTag/effects；
- replicated properties、subobjects、dormancy、NetGUID 语义；
- damage history、hit ignore lists、prediction IDs；
- BeginPlay/EndPlay 语义是否被业务代码假设为“一生一次”。

池化前必须用 Insights/内存/Spawn 峰值证明收益，并以完整复用循环做回归，不以“少 Spawn 了”当成功。

## 11. Data-Oriented Projectile：值得吸收的结构与明确不能照搬的网络部分

这是本项目最值得深入研究、也最需要标记“实验”的模块。

### 11.1 值得吸收的结构

源码把 projectile 数据拆成两层：

- **per-frame hot data**：Position、Velocity、ID，紧凑存在轻量数组中；
- **低频 replicated metadata**：InitialPosition、InitialDirection、Config、Instigator、Hit 等，使用 `FFastArraySerializer`。

FastArray 回调：

- `PostReplicatedAdd`：在 Proxy 创建本地 projectile 表现；
- `PreReplicatedRemove`：清理本地实例；
- `PostReplicatedChange`：消费服务器 Hit 并播放 impact。

这个拆分符合数据导向思路：把每帧频繁遍历的最小工作集与重量级 UObject/Hit/VFX 状态分开，有利于缓存局部性和后续 SoA/批处理演进。

### 11.2 必须标红的实验问题

当前代码本身留下了这些未决点：

- client path 会对复制 FastArray 本地添加/MarkItemDirty；这会混淆“本地预测缓存”与“服务器权威容器”。生产方案应把预测临时数据放独立本地容器，并在 authoritative FastArray 到达后 reconcile。
- hit path 有 Authority 判断 TODO；伤害/命中真值不能由 SimulatedProxy/普通 client 写。
- Remote client 尝试通过 GameState Server RPC 创建 projectile；GameState 通常不是远端玩家拥有的 RPC 宿主。生产 Request 应从 PlayerController/Pawn/PlayerState/专用 Agent 等客户端拥有对象进入 Authority。
- 每帧通过 `FindByPredicate` 在元数据数组按 ID 查询，多 projectile 时可能形成 O(N²) 热点；应该用 ID→index/cache 或把 hot/cold 数据组织得更紧凑，并设计删除后的索引失效策略。
- 每 projectile 创建 `TArray<FHitResult>` 等临时容器可能造成分配压力；需要 profiling 后考虑 stack allocator、复用缓冲或批量查询。
- 当前数据结构仍是 AoS；若规模进一步扩大，再评估 SoA、SIMD、批量 sweep、Mass/自定义 manager，而不是先做微优化。

### 11.3 FastArray 在 Skills 中的正确表述

FastArray 适合大量/高 churn 复制集合，但不是“只要数组就用 FastArray”。结构体内应清晰注释：

- 哪些字段真正复制；
- 哪些字段仅服务器；
- 哪些字段仅本地表现；
- Item 的稳定业务 ID 与 FastArray 内部 ReplicationID 不是一回事；
- Add/Modify 用 `MarkItemDirty`，结构增删用 `MarkArrayDirty`；
- 回调只做派生缓存/表现，不让 Proxy 二次写 Authority 真值；
- JIP 如何从完整数组重建。

## 12. UI：事件驱动 + Soft Asset 异步

Effect Widget 订阅 Action 停止事件；图标使用 Soft Object Path 异步加载。这个方向比“Widget Tick 每帧读取状态 + 同步加载图标”健康。

需要补全的通用审查：

- Widget 销毁/重建后，旧异步结果是否还对应当前 Effect/请求代次；
- Async callback 结果类型/失败是否检查；
- 事件绑定是否随生命周期解除或至少保证 UObject 弱绑定不产生业务残留；
- 大量相同图标是否由 AssetManager/缓存合并请求；
- UI 只消费状态，不成为 gameplay truth。

本项目 UI 不是 CommonUI/MVVM 架构样例，因此不把它扩展成 UI 平台规则；CommonUI 深度应留给 LyraUI/Xist/ArcUI 等后续项目。

## 13. 性能工程：比“禁 Tick”更重要的是可测量的预算

本项目展示了几种不同层级的性能手段：

- ActionComponent 直接关闭 Tick；
- GameMode 把 Tick interval 设成 0.1 秒，并在内部继续按 NextTickTime 做调度；
- Async Sweep 避免把部分碰撞查询结果同步阻塞在当前路径；
- Insights `TRACE_CPUPROFILER_EVENT_SCOPE` / counters 标记热点；
- Actor Pooling、aggregate/deferred ticking、data-only projectile 用编译宏/CVar 隔离实验。

SkillForge 应从中吸收的是“**先定义频率和预算，再选机制**”：

1. 能事件驱动就不 Tick；
2. 必须 Tick 时先缩小执行对象、角色和频率；
3. 高频循环只处理紧凑热数据；
4. 加载/反射/复杂 Tag 解析挪到初始化、缓存构建或异步阶段；
5. 可延后任务必须有生命周期与最大延迟合同；
6. 任何优化用 Insights/Trace/Counter 前后对照，而不是凭实现看起来高级。

## 14. 内存与缓存局部性：从该项目继续向前推

轻量 projectile 的 hot/cold 数据拆分说明作者已经在减少 Actor/UObject per-instance 成本。但 SkillForge 要比样例再多一步审查：

- 高频 struct 的字段顺序、padding、`sizeof`、数组访问模式；
- bool/enum/ID 是否导致意外 padding；
- 热数组不要混入 `TObjectPtr`、`FHitResult`、大 TagContainer 等冷字段；
- 多线程读写时避免多个线程反复写同一 cache line；
- 优先让 worker 写各自分片，最终归并，而不是共享计数器/状态频繁抖动；
- 优化前用 Unreal Insights、LLM/Memory Insights、硬件计数器可用信息确认瓶颈。

这不是要求所有 Gameplay struct 手工 pack。错误对齐或 packed struct 可能让访问更慢；原则是“测量并保持热数据紧凑”，不是牺牲 UE ABI/反射安全。

## 15. 对 LGF 的直接映射

| ActionRoguelike 观察 | LGF 应采用 | LGF 不应采用 |
|---|---|---|
| replicated UObject Action | 子对象生命周期、OnRep/Host 统一刷新、JIP 重建检查 | 用自制 Action 替换 GAS/ASC |
| ActionComponent RPC | Request 由客户端拥有 Agent 进入 Authority | 世界对象/GameState 直接承载 Remote client Server RPC |
| Local interaction focus | 本地候选/UI，高亮不复制 | 客户端 Focus 直接成为 Authority 授权 |
| DataTable -> PrimaryAsset -> async load | 数据轻重分层、AssetManager、generation token | Tick 内同步加载 |
| FastArray projectile metadata | 大集合 delta、回调重建、hot/cold split | client 修改 authoritative FastArray / ReplicationID 当业务 ID |
| SaveGame archive | SaveGame 字段、post-load rebuild、Subsystem | Actor FName 当长期 ID、全世界高频扫描、UIData 当存档 |
| Pooling | reset contract、profiling、fallback | 未证明网络/VFX reset 就启用 |
| BT/EQS/StateTree | AI 决策/空间查询/Director 分层 | 为“统一框架”强行把所有 AI 改一种图 |

## 16. 本轮对 SkillForge 的落地

这轮不新增“ActionRoguelike Skill”，而是把可复用经验写回已有技能：

- `skillforge-ue-cpp`：新增运行时 Gameplay 架构参考，覆盖 replicated subobjects、Authority revalidation、PrimaryAsset async pipeline、SaveGame、FastArray hot/cold、pool reset、deferred task lifetime、性能/缓存检查。
- `skillforge-lgf`：新增外部项目模式迁移参考，要求先映射到 LGF 现有 GAS/Request/Authority/Inventory/FastArray/Avatar/UI 契约，再决定是否吸收。
- 两个技能都增加行为评测场景，专门防止“只看样例能跑就照搬”的错误。

## 17. 下一轮研究时保持的格式

每个后续 GitHub 项目都继续按相同维度：

`版本/许可 -> 模块地图 -> 数据所有权 -> Authority/Proxy -> 复制闭环 -> 数据结构 -> 热路径 -> 资源生命周期 -> 可迁移模式 -> 反例/实验 -> LGF 映射 -> Skills 补丁 -> 定向 eval`

这样最终得到的是可组合的知识库，而不是项目链接收藏夹。
