# UE Gameplay 运行时架构审查

用于 Gameplay runtime、联网交互、复制 UObject、数据驱动 Spawn、存档、对象池与高频数据系统。先以当前工程和引擎版本为准；社区样例只提供机制证据，不能替代目标项目验证。

## 1. Replicated UObject / Subobject 闭环

当 Actor/ActorComponent 持有需要独立复制的 UObject 实例时，不要只检查成员是否写了 `Replicated`：

1. 确认复制宿主是实际进入网络复制图的 Actor/Component，且对象 Outer/生命周期与宿主一致。
2. UObject 需要明确支持 networking；目标工程若使用 registered subobject list，新增/移除对象要调用对应注册/注销路径。旧式 `ReplicateSubobjects` 只能按当前工程实际实现使用，不能两套机制混着猜。
3. 重要属性声明 `ReplicatedUsing` 时实现 OnRep，并在 `GetLifetimeReplicatedProps` 调 `Super` 后注册真实字段与条件。宿主中保存的子对象引用/集合若也需复制，同样检查注册。
4. Authority 创建、授予、销毁和修改业务真值。Remote client 只发送请求；SimulatedProxy 不创建第二份权威对象。
5. OnRep 负责派生缓存与表现刷新。Listen Host 的 Authority 本地写入通常不能依赖“等自己的 OnRep”，应抽出共享 `RefreshFromState`/事件，让服务器本地和 Remote Proxy 收敛到同一表现。
6. 集合 OnRep 或 FastArray Add/Change/Remove 后重建非复制缓存；不要复制纯索引缓存。检查 JIP 能否仅靠当前快照重建完整状态。
7. 子对象结束时同时审查：业务 End、Delegate/Timer/Async、`RemoveReplicatedSubObject`、宿主集合、查询缓存与 GC 可达性。

P2P/Listen Server 拓扑不会取消 Authority/AutonomousProxy/SimulatedProxy 的职责。连接方式可以是 peer-hosted，Gameplay 真值仍要有明确 Authority。

## 2. Local Intent 与 Authority Authorization

本地目标选择、准星候选、交互高亮可以只在 owning client 计算；这属于输入意图与表现，不是权限结论。

推荐链：

`Local candidate -> client-owned request host -> Authority re-resolve/revalidate -> mutate truth -> replication/result -> presentation`

服务器至少按功能检查：稳定目标身份、距离/LOS、玩家和目标当前状态、队伍/权限、资源成本、数量、冷却、频率、会话/请求代次。客户端传来的 Actor、Index、Option、价格、伤害结果都只当候选参数。

世界门、NPC、宝箱、GameState 通常不是 Remote player 拥有对象；不要因为这些对象有 Server RPC 就假定客户端可以合法调用。请求优先从 PlayerController、Pawn、PlayerState 或项目的 owned Agent 进入，再由 Authority 操作目标世界对象。

## 3. FastArray：权威集合与本地预测分离

对大量/高 churn 复制集合优先考虑 `FFastArraySerializer`；小型低频列表不机械迁移。

结构体注释应明确四类字段：

- replicated business data；
- server-only bookkeeping；
- client-only presentation/cache；
- stable business identity。

检查 `FFastArraySerializerItem`、Serializer、`NetDeltaSerialize`、Traits、Add/Modify 的 `MarkItemDirty`、结构增删的 `MarkArrayDirty`、以及 `PostReplicatedAdd/Change/PreReplicatedRemove`。

FastArray 内部 `ReplicationID/Key` 不是存档或业务 ID。Proxy 回调更新派生缓存/VFX/UI，不在回调里二次提交业务修改。

若需要 client prediction：把预测对象放独立本地容器，以 ClientRequestId/PredictionKey/稳定业务键关联；Authority FastArray 到达后 reconcile。不要让 client 对 authoritative replicated array 调 Dirty 并把“本地看见了”当服务器确认。

## 4. Hot / Cold 数据分层

高频成百上千实例不要把每帧所需的 Position/Velocity 与 UObject 指针、`FHitResult`、TagContainer、UI/VFX 状态混成一个巨大热结构。

先按访问频率分：

- **Hot**：每帧/高频遍历的最小 POD/小 struct；
- **Cold**：配置、资产引用、命中详情、表现对象、低频网络元数据。

检查：

- 高频循环中是否 O(N) 再 `FindByPredicate` 到另一数组，导致总体 O(N²)；必要时维护 ID→index/cache，并定义 swap-remove 后失效规则。
- 是否每项创建临时 `TArray`/分配；先 profile，再复用缓冲、inline allocator 或批处理。
- struct `sizeof`、padding、字段顺序与数组局部性；不要为追求紧凑使用破坏 UE ABI/反射的强制 pack。
- 多线程是否反复写共享计数/相邻字段造成 cache line 抖动；优先分片写入后归并。

## 5. Tick 与任务预算

禁止在 Tick 或高频循环执行 `StaticLoadObject`、`FObjectFinder`、`LoadSynchronous`、全世界 Actor 扫描、反复反射或复杂 Tag 构造/匹配。

按顺序优化：

1. 能事件驱动就关闭 Tick。
2. 只对 LocalController/Authority/相关对象 Tick。
3. 设置合理 interval 或业务 NextUpdateTime，而不是默认每帧。
4. 初始化时构建反射、Tag、DataTable、权重和 ID 索引缓存，明确失效条件。
5. 可异步的 I/O/Asset/Trace 使用异步接口；回调必须带生命周期和代次验证。
6. 非关键 GameThread 工作可做预算切片，但“延后执行”就是生命周期边界：Lambda 不按引用捕获即将离开栈的局部变量；UObject 用弱引用/有效性检查，旧 generation 不得覆盖新状态。
7. 用 Unreal Insights、Trace counter、Memory Insights 等前后对照，不用“代码更复杂/用了 Pool/Mass”证明性能提高。

## 6. DataTable + PrimaryAsset + Async Load

需要从大量类型中按规则选一个并 Spawn 时，可把轻量选择数据与重量级配置拆开：

`cheap selection metadata -> stable PrimaryAssetId -> async AssetManager load -> callback validation -> Authority spawn/commit`

DataTable/Registry 可存 cost/weight/ID；PrimaryDataAsset 存 class、ability/config、视觉等。避免为了做一次权重选择把所有角色资产同步载入。

异步链必须记录事务语义：

- reserve 何时发生；
- EQS/Load/Spawn 任一步失败是否 refund；
- callback 到达时 World、owner、wave、request generation 是否仍有效；
- 重复回调/重试如何幂等；
- Authority 是否是唯一 Spawn/Grant 真值入口。

高频 weighted selection 不应每次重新扫描大表；在配置变化时预计算候选/累计权重或 alias table，再按实际规模决定。

## 7. SaveGame：稳定身份和恢复协议

简单项目可以用 `UGameInstanceSubsystem` 管槽位，并用 `FObjectAndNameAsStringProxyArchive` + `ArIsSaveGame` 序列化 `UPROPERTY(SaveGame)`，再通过接口执行 post-load rebuild。

生产审查必须额外确认：

- ActorName/FName 不是天然稳定存档 ID；动态对象、跨地图和 World Partition 使用稳定 GUID/业务键。
- 全世界 `TActorRange` 只适合低频、小规模 checkpoint；autosave/大世界使用注册表、脏集、分区快照或明确 save participants。
- 同步磁盘 I/O 是否会卡帧；大数据按平台能力设计 async/worker serialization 与 game-thread snapshot 边界。
- Multiplayer 由 Authority 保存业务真值；Remote request 不能提交本地 UI/Proxy 快照为真值。
- Load 顺序与 replication 初始化要一致；恢复后需要触发复制 dirty/刷新，使 Listen Host、Remote、JIP 最终一致。
- Save version/schema migration、缺资产、旧 ID、部分加载失败必须有兼容策略。

## 8. Actor Pooling：先写 Reset Contract

池化不是把 `Destroy` 换成 `Hidden=true`。为每种可池对象定义 Acquire/Release contract：

- Transform、Owner、Instigator、Collision、Visibility；
- movement velocity/activation；
- Niagara/Audio/Trail/Decal；
- Timer/Latent/Async；
- Delegate/Input binding；
- GameplayEffect/Tag/Hit history；
- replicated subobjects/dormancy/owner relevance；
- BeginPlay/EndPlay 是否被业务假设为单次。

先保留普通 Spawn/Destroy fallback 和 CVar/feature flag，完成复用多轮、Travel/EndPlay、VFX、网络回归后再默认启用。若池只在 Standalone 工作，明确写成局部优化，不宣称网络安全。

## 9. AI 的 Authority / Presentation 分层

AIController、Perception、BT/StateTree 的决策通常只在 Authority。客户端不需要复制 AIController；需要长期可见的结果放在 Pawn/State 等复制状态，只针对某个 owner 的瞬时 UI 提示可走 Client RPC。

不要把 BehaviorTree、StateTree、EQS 当互斥替代品：

- StateTree/Director：高层状态与调度；
- BT/Utility：单体行为决策；
- EQS：空间候选；
- GAS/Action：玩法执行。

按目标项目已有框架组合，不为“统一”重写所有 AI。

## 10. 社区样例迁移门槛

看到能运行的 GitHub 样例，先问：

1. 目标 UE 版本是否相同；实验 API 是否变化。
2. 该功能是默认生产路径还是宏/CVar 关闭的实验。
3. 样例网络拓扑是否覆盖 Remote client、Listen Host、Dedicated Server、JIP。
4. RPC host 是否真的被调用者拥有；客户端有没有写 authoritative replicated state。
5. 数据规模是否与目标项目相当；样例的线性扫描是否仍可接受。
6. 资产/代码许可是否允许复制。许可不清楚时只学机制，不搬实现。
7. 目标工程已有 GAS/Mover/CommonUI/Inventory 等成熟系统时，优先映射设计意图，不另起第二套真值。
