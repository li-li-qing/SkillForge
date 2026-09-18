# ARPG 物品、背包、装备与仓库架构审查

用于 UE5 ARPG 中的 Item Definition/Instance、Grid Inventory、Equipment、Stash、Affix、GAS 授予、随机掉落和持久化。参考项目可以提供设计证据，但目标项目的网络拓扑、许可证、数据规模和现有框架始终优先。
> 大规模物品表示、index+generation stable handle、FreeIndices、typed ItemState、MutationKey、ItemData/SlotData 双 FastArray、NestedInventory 和多人 transaction 的更细规则见 [物品值语义、稳定句柄与容器事务](item-value-semantics-and-transactions.md)。


## 1. Item Definition / Instance / Fragment 三层模型

把物品拆成三类职责，而不是把所有数据塞进一个 UObject：

- **Definition**：不可变或近似不可变的设计配置，例如类别、基础类型、默认稀有度、静态描述、图标、Mesh、装备规则、可用 Fragment 列表。优先由 Class Default Object、DataAsset、PrimaryAsset 或稳定 ID 解析。
- **Instance**：玩家真正拥有的运行时物品，只保存每件物品会变化的状态，例如稳定 ItemId、等级、当前堆叠、位置、随机词缀、鉴定状态、耐久、绑定状态等。
- **Fragment**：按能力组合静态行为配置，例如 Stack、Appearance、Equippable、Affix、Usable。Fragment 初始化 Instance 时只写该 Fragment 真正拥有的运行时字段。

生产审查要问：某字段是否对同一 Definition 的每个实例都相同？如果答案是“是”，就不应默认按实例复制 `FText`、Texture、StaticMesh、描述、分类等静态展示数据。网络优先传稳定 Definition 标识和真正变化的随机化结果，客户端从已加载 Definition 解析展示。

不要把“UObject Instance”当默认答案。纯值型、大量物品可以使用紧凑 struct/FastArray；只有需要独立 UObject 生命周期、复杂行为、子对象复制或外部引用时才升级为 UObject。两种表示可以共存，但必须只有一个业务真值。

## 2. Authority 容器 + FastArray + 本地派生索引

大背包、装备、仓库适合把权威条目放进 `FFastArraySerializer`，把查询 Map、占格表和 UI 索引留成本地派生数据。

推荐条目注释至少区分：

```cpp
/** Replicated business identity/state. */
UPROPERTY()
FGuid ItemId;

/** Replicated placement/state required by remote clients. */
UPROPERTY()
FIntPoint GridOrigin;

/** Client/server local observation cache, never authoritative. */
UPROPERTY(NotReplicated)
int32 LastObservedStackCount = INDEX_NONE;
```

Serializer 负责：

- Authority Add/Modify 时 `MarkItemDirty`；结构增删时 `MarkArrayDirty`；
- `PostReplicatedAdd` 重建 ItemId/GridOrigin/Slot 到对象或条目的本地索引；
- `PostReplicatedChange` 更新派生缓存并发布表现事件；
- `PreReplicatedRemove` 在条目离开前清理占格、索引和 UI 投影；
- JIP 能只靠当前完整 FastArray 快照重建所有非复制 Map；
- 不复制纯缓存，也不让 Proxy 回调反向修改 Authority 真值。

Grid Inventory 的占格表可以是二维 bit/grid 或紧凑数组，而不是必须 `TMap<FIntPoint,bool>`。数据规模大时先测 `TMap` 节点分配、缓存局部性和 Grid 扫描成本，再决定 bitset/flat array/row mask。不要为了“更快”在没有基准时重写。

## 3. Replicated Item UObject 的完整生命周期

若 FastArray 条目指向 `UObject` ItemInstance，则数组 delta 和 UObject 子对象复制是两条不同的网络合同：

1. ItemInstance 明确 `IsSupportedForNetworking()`；
2. 重要运行时属性在 `GetLifetimeReplicatedProps` 注册；需要副作用的状态使用 `ReplicatedUsing` + OnRep 或由集合回调进入统一刷新；
3. Authority 创建 ItemInstance，Outer 与拥有它的网络宿主生命周期匹配；
4. registered subobject list 下，在对象进入网络可见集合时 `AddReplicatedSubObject`，离开时 `RemoveReplicatedSubObject`；
5. `ReadyForReplication()` 需要补注册在组件准备复制之前已经存在的对象；
6. 若目标工程还支持旧式 `ReplicateSubobjects` fallback，明确哪个路径在当前 NetDriver/Iris 配置下生效，不重复注册或漏复制；
7. FastArray callback 必须能容忍 UObject 引用尚未具备完整表现依赖，必要时延迟刷新或二次校验；
8. Listen Host 本地 Authority 更新不能等自己的 OnRep，走相同的 change message/refresh contract。

P2P/Listen Server 只是连接拓扑。库存、装备、掉落仍必须明确 Authority；Remote client 的本地 ItemInstance 不能成为真值源。

## 4. Inventory / Equipment / Stash 使用同一物品身份

物品在 Inventory、Equipment、Stash 之间移动时，优先保持同一个稳定 ItemId/Instance，而不是每移动一次创建“逻辑上相同但身份不同”的新物品。转移事务应明确：

`validate source -> reserve destination -> remove/move source -> insert destination -> apply side effects -> commit`

失败时要定义 rollback。特别是双手武器替换、背包空间不足、共享仓库并发、装备需求变化时，不能做到一半就留下：

- 物品从装备移除但没进背包；
- GAS 效果已撤销但条目仍显示装备；
- 两个容器同时拥有同一 ItemId；
- UI 已广播成功但 Authority transaction 后续失败。

跨容器的 stack limit、unique limit 和共享 stash limit 应由 Authority 对“相关所有容器的最终状态”统一校验；不要只检查当前 Widget 页。

## 5. Equipment + GAS：授予必须可逆

装备带来的 GameplayAbility、GameplayEffect、Attribute/Tag 修饰应由 Authority 授予，并为每个装备来源保存精确 handle：

- `FGameplayAbilitySpecHandle`；
- `FActiveGameplayEffectHandle`；
- 其他项目自定义 grant handle/registration token。

Unequip、weapon swap out、死亡清理、换 Avatar、load/reconnect 时使用**同一来源保存的 handles 精确撤销**。不要通过“遍历所有能力，按类或 Tag 猜着删”来清理，因为同一 Ability/Effect 可能同时来自技能树、Buff、另一件装备或职业默认授予。

推荐把 `GrantedHandles`（grant handles）标成 Authority-only / `NotReplicated` bookkeeping：客户端只需要最终 GAS/装备复制状态与表现，不需要拿服务器句柄执行删除。

若 AbilitySpec 使用 `SourceObject`，可指向稳定的 ItemInstance/装备来源，便于伤害归因、验证和调试；仍不要把 SourceObject 当存档 ID。

## 6. 装备事务禁止热路径同步加载

装备、换装、掉落生成、词缀遍历和 FastArray callback 都不是允许任意磁盘/资产阻塞的地方。

禁止在这些循环/热路径中：

- `StaticLoadObject` / `FObjectFinder`；
- `TSoftObjectPtr::LoadSynchronous()`；
- 每个 Affix 单独同步加载 AbilitySet；
- 每次操作重新构造复杂 GameplayTag 查询或扫描大型 DataAsset 网络。

正确路线：

`DeveloperSettings/PrimaryAsset -> async preload -> validated cache -> gameplay transaction`

唯一/套装/特殊词缀也必须被 preload contract 覆盖。若运行时发现依赖未加载，生产路径应返回 Pending/AssetNotReady、排队异步完成或拒绝操作；`LoadSynchronous` 最多作为开发告警 fallback，不能成为正常成功路径。

异步装备事务要带 generation/request id，并在完成时重校验 owner、ASC、Avatar、ItemId、目标 Slot 与当前请求代次，防止旧加载结果覆盖新换装。

## 7. 随机掉落：Authority 生成最终结果

随机掉落的真值包括：Definition、ItemId、item level、rarity、stack count、affix ids、affix values、requirements、identification state 等。联网游戏中由 Authority 生成并提交，客户端只消费结果。

公共 `DropItems/GenerateItem/SpawnLoot` 入口即使当前只从服务器调用，也最好在实现内明确 Authority guard；不能只靠调用约定。

需要可复现测试、回放、审计或跨进程一致性时使用显式 `FRandomStream` 与 seed；保存**最终生成结果**，必要时额外保存 generation seed/version 用于诊断，但 load 时不要重新 roll。

掉落数据建议：

- 启动/关卡阶段异步预热 Treasure/Affix/ItemDefinition；
- roll 热路径只操作已驻留的轻量候选结构；
- 高频权重查询预计算候选/累计权重或 alias table；
- 稀有物品分支也不能临时同步 Load；
- Spawn/Grant 失败定义 reserve/commit/refund，不静默吞掉掉落。

## 8. Save 按生命周期/所有权分域

不要默认一个巨型 SaveGame 保存所有内容。ARPG 常见的独立域：

- **Master/Profile index**：角色列表、SaveId、名字、职业、等级摘要、离线/在线入口信息；
- **Per-Hero**：角色初始化数据 + 会变化的 Gameplay 数据、Inventory、Equipment、个人仓库；
- **Shared Stash/Account**：多个角色共享的数据与 tab 元数据；
- **World/Session**：只属于本局或世界实例的状态。

进一步把“初始化一次的数据”和“游戏中持续变化的数据”分开，可降低误覆盖和迁移复杂度。

每个 Save 域仍需要：SchemaVersion、稳定 ItemId/DefinitionId、迁移函数、原子/失败恢复策略、async completion、dirty tracking。FastArray 的内部 ReplicationID 不能写成持久化物品身份。

联网/P2P 下，本地 `ULocalPlayerSaveGame` 只说明存储 API，不赋予 Remote client 对共享仓库或在线角色的业务 Authority。Host/服务器/后端必须拥有最终保存权；客户端请求保存意图，Authority 从自己的真值构建快照。

## 9. GameplayMessage 作为表现总线，而不是第二份真值

FastArray Add/Change/Remove 后广播 `GameplayMessageSubsystem` 类型事件，是解耦 UI 的好方式：

`replicated truth -> callback/local mutation -> message -> WidgetController/ViewModel -> Widget`

消息 payload 可以包含 ItemId、Instance 引用、位置、delta、change type，但消息本身不持久化、不作为下一次业务操作的 Authority 数据源。UI 请求仍回到 Inventory/Equipment/Stash Request/Component 入口重新验证。

消息广播要避免重复：Listen Host 本地 Authority mutation 与 Remote FastArray callback 可能走不同路径，应定义“每个客户端一次表现事件”的合同。JIP 初始同步是否发送 Add 事件、UI 是否需要 initial snapshot，也要写清。

## 10. 性能与内存检查

大型 ARPG 物品系统优先检查：

- Definition 静态字段是否被每个 Instance 重复存储/复制；
- ItemInstance 是否真的需要 UObject，还是紧凑 struct 足够；
- Grid occupancy 是否使用大量 `TMap` 节点和 pointer chasing；
- Find/stack/equip 是否在每次操作线性扫描所有条目；是否有稳定 ID/index cache；
- FastArray entry 的 `sizeof`、padding、冷字段混入、`FText`、TagContainer、UObject refs；
- UI 是否每帧扫描所有 Items，而不是消费 delta；
- Asset loader 的 `ParallelFor` 是否有 profile 证据，还是只是把小量路径收集变复杂；
- 多线程路径是否线程安全，是否为了共享 Queue/Map 引入 cache line 竞争。

内存对齐优化以 Unreal Insights/Memory Insights/测量为证据。不要强制 `#pragma pack` 破坏 UE ABI/反射；目标是减少热结构和 pointer chasing，而不是追求最小字节数。

## 11. 外部样例迁移检查表

研究第三方 ARPG 项目时，至少记录：

1. 固定 commit、UE 版本、许可证；GPL/MIT/Apache 等决定能否复制实现。
2. Definition/Instance/Fragment 哪些是配置，哪些是运行真值。
3. Inventory/Equipment/Stash 谁拥有，谁有 Authority，Remote 请求从哪个 owned object 进入。
4. FastArray 的稳定业务 ID、Dirty、callbacks、JIP 与本地派生缓存。
5. Item UObject 的 registered subobject/ReadyForReplication/remove 生命周期。
6. 装备 GAS grants 的 exact handles、SourceObject、swap/unequip/load cleanup。
7. 随机掉落由谁 roll，最终结果如何保存、复制、重放。
8. 所有软资源是否在 gameplay hot path 前驻留。
9. Save 是否按 ownership/lifecycle 分域并支持版本迁移。
10. 用 Host、Remote client、SimulatedProxy/JIP、断线重连、Load、双手替换、库存满、共享仓库并发做验收。
