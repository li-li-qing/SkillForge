# RockInventory 项目蒸馏：第三轮

检查日期：2026-09-14  
来源：`brokenrockstudios/RockInventory`  
固定源码快照：`be30b5a4a64c5707efde45c705a2e7011d9834d0`（main）  
许可证：MIT。

> 本轮目的不是选一个新的 Inventory 插件直接替换 LGF，而是用 RockInventory 与上一轮 Obsidian 做结构对照，确定大规模 ARPG 物品在 **Definition、compact Stack、typed State、UObject Instance、FastArray、stable handle、transaction** 之间的正确升级边界。

## 1. 项目状态与证据边界

RockInventory 是 Broken Rock Studios 的 UE Inventory 插件。仓库 README 明确说明项目仍处于 ongoing construction/refactor/redesign；2026-09-10 的最新 main 提交也正是一次 ItemInstance -> ItemState 方向的重构。因此这次把它视为**正在快速演进但包含高价值工程实验的源码库**。

`.uplugin` 将模块拆成：

- `RockInventoryRuntime`：Runtime；
- `RockInventoryEditor`：Editor；
- `RockInventoryUI`：ClientOnly；

并显式启用 Iris，另依赖 CommonUI、ModelViewViewModel 和其自家 Core/GameplayTags/Classification/DragDrop 插件。

本轮结论来自源码静态审查；没有宣称该 commit 已由我们在 UE5.7 完成 UBT、多人 PIE、Dedicated Server、JIP 或性能基准。

## 2. 模块地图

| 模块 | 主要职责 | 蒸馏重点 |
|---|---|---|
| `Item/RockItemDefinition` | PrimaryDataAsset、静态 UI/类型/重量/软资源/Fragments | immutable Definition、静态数据不逐实例复制 |
| `Item/RockItemStack` | FastArray item、stack count、custom values、runtime instance pointer、generation | struct-first 热数据 |
| `Item/RockItemState` | typed mutable runtime state | Fragment/State 分层、FInstancedStruct |
| `Item/RockItemInstance` | replicated UObject escape hatch | 复杂对象、subobject、nested inventory |
| `Inventory/RockInventory` | ItemData、SlotData、Section、FreeIndices、Pending ops | canonical data、布局分离、host refresh |
| `Inventory/RockInventorySlot` | Slot FastArray、ItemHandle、orientation/lock | layout delta |
| `Inventory/RockInventoryQuery` | Section/Slot/Item predicates | early-out、Tag/query hot-path 边界 |
| `Transactions` | Move/Loot/Drop、TransactionID、Undo、prediction skeleton | Authority transaction、并发、风险清单 |
| `Components/RockInventoryComponent` | Authority 创建 Inventory、replicated UObject 宿主 | registered subobject / OnRep |
| `Components/RockInventoryManagerComponent` | Client intent -> Server RPC、history/prediction | owned request route、reconcile 未完成 |
| `Item/ItemRegistry` | PrimaryAsset registry | stable Definition lookup、startup loading tradeoff |
| `RockInventoryUI` | drag/drop、tooltip、client-only UI | presentation 与 runtime load 风险 |

## 3. 最重要的结论：不是 Struct vs UObject，而是成本梯度

Obsidian 的优势是完整 ItemInstance/Fragment/GAS/Save 链，但每件物品 UObject 较重。RockInventory 的价值是把“是否需要 UObject”进一步拆开。

当前源码展示的四层模型：

1. **URockItemDefinition**：静态资产；
2. **FRockItemStack**：常见运行时值类型；
3. **FRockItemState**：按需加入的 typed mutable state；
4. **URockItemInstance**：只有复杂物品需要的 UObject escape hatch。

这比“所有 ItemInstance 都 UObject”和“所有内容都塞一个巨大 struct”都更接近生产系统。

### 3.1 Definition

Definition 是 `UPrimaryDataAsset`，包含：

- stable `ItemId`；
- Name/DisplayName/Description；
- MaxStack/GridSize；
- ItemType、ItemTags、Rarity；
- Weight/ItemValue；
- UI Icon、World Mesh、ActorClass 等 soft refs；
- RuntimeInstanceClass；
- `TArray<FInstancedStruct> Fragments`。

静态展示数据在 Definition 中，正好弥补 Obsidian 当前 ItemInstance 逐实例复制很多 FText/Mesh 的问题。

### 3.2 Compact Stack

`FRockItemStack : FFastArraySerializerItem` 保存常用运行时数据：

- ItemHandle；
- Definition；
- optional RuntimeInstance；
- StackCount；
- CustomValue1/2；
- Generation；
- initialized flag。

它设计成大多数 Item 可以只用 struct 存在，没有 UObject 分配和 GC 生命周期。

LGF 迁移判断：材料、货币、弹药、普通消耗品、简单随机装备优先走类似 compact entry；不能因为未来“可能扩展”就预先让 5 万条物品都成为 UObject。

## 4. Fragment 与 ItemState：静态配置和实例变化再次拆层

`FRockItemFragment` 是静态 Definition 组合能力：

- `OnItemCreated` 初始化 Stack；
- `OnInstanceCreated` 可以为复杂实例增加 runtime state；
- `CanCombineItemStack` 参与 stackability；
- editor validation/asset registry；
- `GetSortOrder` 调整线性数组查询顺序。

`FRockItemState` 则专门表达 mutable runtime state。源码注释直接用“最大耐久 vs 当前耐久”解释两者区别。

### 4.1 FInstancedStruct 的价值

`URockItemInstance::States` 是 `TArray<FInstancedStruct>`，意味着动态多态状态仍保持值类型：

- 某件物品没有 Durability 就不存 Durability state；
- Metadata 可以单独存在；
- NestedInventory 也是独立 State；
- 不需要每个 state 一个 UObject。

这是非常适合 LGF 的中间层。但当前整个 States 数组使用 `ReplicatedUsing=OnRep_States`，源码也留了未来 FastArray 的 TODO。因此高 churn state 要进一步评估按元素增量复制，而不是机械复制整个 InstancedStruct array。

## 5. 热/冷 Fragment 顺序与 cache 思维

Fragment base 提供 `GetSortOrder()`，注释明确：

- SetStats 这类初始化一次的 cold path 可以排后；
- Resource/Usable 这类高频查询排前。

这是小数组的实用优化：让常命中的 Fragment 更早 early-out，而不是为了 O(1) 理论复杂度立刻增加 Hash Map。

LGF 规则：

- 先测 Fragment 数量和调用频率；
- 小而固定的数组优先连续内存；
- 热路径才建立 cache；
- cache 必须跟 Definition reload/Instance change 失效；
- 不在 Tick 中反复构建复杂 TagQuery。

## 6. Stable Handle：Index + Generation 解决 ABA

`FRockItemStackHandle` 用单个 32-bit Handle，当前分配为 16-bit index + 16-bit generation，并显式 `alignas(4)`。

关键不是具体 16/16，而是模式：**数组槽位可以复用，但旧引用不能复活。**

### 6.1 FreeIndices

`URockInventory` 不在删除 Item 时缩小 ItemData。删除流程：

1. unregister RuntimeInstance；
2. 将 index 放回 `FreeIndices`；
3. `Generation++`；
4. 重新生成 Handle；
5. Reset Stack；
6. `MarkItemDirty`。

新增优先 `FreeIndices.Pop(EAllowShrinking::No)`，否则扩展 ItemData。

这样：

- UI 拖拽可持有 Handle；
- async callback 可持有 Handle；
- RPC 可携带 Handle；
- 旧 generation 会在 Authority 解引用时失败。

### 6.2 不要把这个 Handle 存档

它仍然是 runtime reference。跨会话 Item identity 需要 FGuid/业务 ItemId。LGF 如果采用 packed handle，需要自行根据最大 slots 与 churn 选择位宽，并测试 generation wrap。

## 7. MutationKey：把写权限缩到具体 setter

RockInventory 新增的 `FRockItemStackMutationKey` 是 passkey/Attorney-Client 模式。原因写得很明确：直接 `friend` 一个大类会让它永久访问 ItemStack 所有 private 字段，而 MutationKey 只授予“能调用需要 key 的 setter”这一项能力。

这种模式对 FastArray 很有用，因为 Item entry 不应该随便被外部改：每次 mutation 必须知道谁会 MarkItemDirty、谁会广播本地 event。

LGF 可以吸收：

`const view/Handle -> authorized mutation API -> Authority validate -> mutate -> Dirty -> projection`

但 MutationKey 只解决 C++ capability，不解决：

- 网络 Authority；
- Inventory ACL；
- stale handle；
- transaction atomicity。

## 8. ItemData / SlotData 双 FastArray

这是 RockInventory 相比很多背包实现更强的结构点。

### 8.1 ItemData

`FRockInventoryItemContainer : FIrisFastArraySerializer`，内容是 `TArray<FRockItemStack>`。

### 8.2 SlotData

`FRockInventorySlotContainer : FIrisFastArraySerializer`，SlotEntry 只有：

- ItemHandle；
- SlotHandle；
- Orientation；
- locked flag；
- nonrep LastKnownItemHandle。

因此同一个背包内部把剑从 A4 拖到 B7 时，不需要重发整件剑的 Stack/Definition/Runtime state，只改变布局引用。

这对大仓库、装备页、多 tab 系统有很强参考价值。

## 9. FastArray Previous Handle：把 replication delta 转成语义事件

Item container 使用 `PreviousItemHandles` 本地数组判断：

- invalid -> valid = Added；
- same generation = Changed；
- generation mismatch = Remove old + Add new；
- valid -> invalid = Removed。

Slot container 使用 `LastKnownItemHandle` 判断 ItemAdded/Removed/Changed/PropertiesChanged。

这些 previous values 都不复制，只用于客户端投影。

LGF 可以吸收这种 delta classification，但必须保留：

- JIP current snapshot 能重建；
- 复制顺序容忍；
- Host 本地 mutation 走另一条等价刷新；
- UI delta 不反向成为业务真值。

## 10. Listen Host 的显式本地刷新

`PendingSlotOperations` 使用 `ReplicatedUsing=OnRep_PendingSlotOperations`，Authority 修改后源码会显式调用 OnRep，注释理由就是 listen-server 本地不会因自己的复制字段修改自动收到 OnRep。

这个观察与前两轮一致：**Host 的表现刷新不能依赖网络回环。**

生产 LGF 更推荐把 OnRep 与 Authority mutation 都调用一个 `ApplyPendingOperationsPresentation()`/message helper，而不是把 OnRep 本身当业务函数，这样 Authority/Proxy 语义更清晰。

## 11. Slot reservation：并发控制的第一层

PendingSlotOperation 记录：

- Controller；
- SlotHandle；
- ItemHandle；
- SlotStatus；
- TimeStarted。

源码使用约 30 秒 expiration，并清理过期 claim。这个方向很适合多人仓库/拖拽：操作前先 reserve，避免另一玩家同时搬走同一个 item。

但 claim 不等于授权。还要验证目标 Inventory 是否允许这个玩家访问。

## 12. Transaction 框架：结构值得学，当前实现仍未完成

Transactions 目录把 Move/Loot/Drop 独立成 command struct。Base 有：

- weak Instigator；
- TransactionID。

Move 有：

- Source/Target Inventory；
- Source/Target SlotHandle；
- MoveParams；
- `CanExecute()`；
- `Execute()`；
- Undo snapshot；
- `AttemptPredict()`。

InventoryManagerComponent 提供 owned ActorComponent 上的 Server RPC 和 Client TransactionResult。

### 12.1 可以吸收的框架

`Client intent -> Server CanExecute -> Execute -> record result -> Client result`

以及：

`claim source/target -> mutate -> release claim`

这比 Widget 直接写数组健康很多。

### 12.2 明确不能写成“已生产完成”

当前固定 commit 中仍能看到：

- Move `AttemptPredict()` 只是返回 true；
- client failure resync 只有 TODO；
- Drop/Loot prediction 基本关闭；
- Drop Undo 未实现；
- Move Undo 的断言条件存在明显需要复核的地方；
- Move Transaction 的 `MoveParams` 在一个 Execute 路径没有按预期传给 MoveItem；
- ManagerComponent 开 `bCanEverTick=true`，但当前搜索不到对应 TickComponent 实现；
- transaction history/undo 被注释为 deprioritized。

因此 Skills 只学**命令/验证/结果/claim**的形状，不把当前预测实现搬进 LGF。

## 13. Loot Authority：已有距离验证，但 ACL 还不够

Loot transaction 的优点：Server Execute 再检查对象，并验证 SourceWorldItem 与 TargetInventory owning actor 的最大距离。

不足：客户端同时传 TargetInventory UObject；只满足“距离近”并不能证明该 Inventory 属于 Instigator。共享箱子、另一玩家背包、宠物容器都需要独立 ACL/interaction session 验证。

LGF 服务端应从 Instigator/当前交互 session 重新解析允许访问的 container，而不是信任客户端给的 UObject 指针。

## 14. Drop：NetQuantize 不是验证

Drop transaction 用 `FVector_NetQuantize10` / `FVector_NetQuantize` 压缩 DropLocationOffset 和 Impulse，这对带宽是好事。但源码注释直接承认：目前客户端值仍被信任，服务器未来应检查不合理 offset/impulse。

LGF 必须：

- clamp magnitude；
- 由 Authority Pawn/View 重算方向；
- collision trace 确认落点；
- 限制丢弃距离；
- 验证 source inventory + slot + generation；
- 对 place/drop/toss 分不同规则。

量化和安全是两个不同问题。

## 15. MoveItem：同容器和跨容器的不同成本

`URockInventoryLibrary::MoveItem` 的一个好点是区分：

- 同 Inventory full move：只移动 ItemHandle 到新 Slot；
- 跨 Inventory：Target AddItem，Source Remove；
- partial stack：split 后产生新 Handle；
- merge：只改两边 StackCount。

它还明确暂不支持需要 RuntimeInstance 的 partial move，这是一种合理的限制：复杂 Item 不能未经定义就“复制半个 UObject identity”。

LGF 应把这类限制写成 capability contract，而不是悄悄复制 RuntimeInstance 指针。

## 16. NestedInventory：很有潜力，也是本 commit 最大风险之一

NestedInventory Fragment 会在 ItemInstance 的 State 中创建一个 `URockInventory`。ItemInstance 的 replication register 会继续递归注册 NestedInventory。

方向非常好：背包/弹匣/容器本质上复用统一 Inventory。

但源码自己留了多个 owner/multiplayer TODO，说明还没有完全收敛。生产合同必须补：

- Nested Inventory 的 Outer；
- top-level network owner；
- access ACL；
- max depth；
- cycle prevention；
- reparent/transfer ownership；
- parent item drop 到 world 时如何继续复制；
- JIP/reconnect/save；
- 防止递归树无限复制。

这是适合后续专门做一个 LGF Nested Container 子设计的主题，但本轮只把通用规则写入 Skill。

## 17. Subobject 复制闭环

`URockInventoryComponent`：

- `SetIsReplicatedByDefault(true)`；
- registered subobject list；
- `Inventory` 使用 `ReplicatedUsing=OnRep_Inventory`；
- Authority BeginPlay `NewObject<URockInventory>`；
- EndPlay unregister/remove；
- Proxy OnRep 后重绑 ItemData/SlotData owner pointer。

`URockInventory`：

- `IsSupportedForNetworking()`；
- `GetLifetimeReplicatedProps` 注册 Owner、ItemData、SlotData、Sections、PendingOperations；
- Iris RegisterReplicationFragments；
- 注册自己及当前 RuntimeInstances。

`URockItemInstance`：

- `IsSupportedForNetworking()`；
- replicated OwningInventory/ItemHandle/States；
- `OnRep_States`；
- Iris fragments；
- BeginDestroy/unregister。

这条链值得作为“复杂 Inventory UObject 图”的网络审查案例。

## 18. Asset Registry 与同步加载

Definition 是 PrimaryAsset，并有 ItemRegistrySubsystem。Registry 在 Initialize 中枚举 PrimaryAssetId 并发起加载，建立 `ItemId -> Definition` Map。这是稳定 ID lookup 的正确方向。

但当前项目的资源驻留合同仍有混合状态：

- NestedInventory Fragment `InventoryConfig.LoadSynchronous()`；
- DragDrop sound 有同步加载 TODO；
- WorldItem fallback mesh 同步加载；
- Tooltip subsystem 初始化同步缓存 class；
- Editor thumbnail 同步加载（Editor-only，风险不同）。

因此 LGF 只吸收 PrimaryAsset/registry/soft ref 思路，runtime gameplay 热路径继续要求异步预热。

Registry 若未来上万 Definition，也要从“启动时全加载”改成按 bundle/category/玩法加载，并测启动和 resident memory。

## 19. Query：先 Section -> Slot -> Item

`FRockInventoryQuery` 使用三个 predicate，并在 Inventory 遍历中按 Section、Slot、Item 顺序 early-out。这个结构允许调用方把最有选择性/最便宜的条件放前面。

Item tag helper 本身只是对 Definition cached tags 做 `HasTag`，但复杂 `SectionFilter.Matches(ItemTags)` 仍可能位于大量遍历中。

LGF 原则：

- query object 构建一次复用；
- static type/tag cache 在 Definition；
- 不在 Tick 或内层循环反复构造 TagQuery；
- FindAll O(N) 明确标 expensive；
- 只有 profile 后才加反向索引。

## 20. Cache / 数据布局

可借鉴的 cache-friendly 意图：

- ItemStack 与 SlotEntry 都是连续 struct 数组；
- SlotEntry 不嵌整 Item；
- handle 单个 int32；
- FreeIndices 使用不 shrink pop；
- Fragment hot/cold 排序；
- occupancy grid 一笔操作预计算。

仍需目标项目自己测：

- ItemStack `sizeof/alignof`；
- TObjectPtr Definition/RuntimeInstance 对 cache line 的影响；
- FInstancedStruct State 的堆/间接访问；
- 两套 FastArray 的复制 key 成本；
- reverse lookup O(N) 是否真是瓶颈；
- PendingSlotOperations 线性扫描最大规模。

不要直接复制 `alignas(4)` 或 bit allocation，当成“RockInventory 用了所以最佳”。

## 21. Obsidian vs RockInventory：不是二选一

| 主题 | Obsidian | RockInventory | LGF 建议 |
|---|---|---|---|
| Item runtime | UObject Instance 为核心 | Stack value 为核心，UObject optional | 成本梯度 |
| 可组合配置 | UObject Fragments | FInstancedStruct Fragments | 优先轻量 typed config |
| 可变模块状态 | Instance 大量字段 | ItemState/FInstancedStruct | typed state |
| 集合复制 | Inventory/Equipment/Stash FastArray | ItemData + SlotData FastArray | 按变化频率拆分 |
| 运行身份 | ItemUniqueID | index+generation Handle | ItemId + runtime Handle 双身份 |
| GAS装备 | GrantedHandles 很成熟 | 非本插件核心 | 继续用 Obsidian 来源级撤销模式 |
| 事务 | 多步骤函数，需加强 rollback | 独立 transaction/claim，但未完成 | 合并成 LGF Authority transaction |
| Save | Master/Hero/SharedStash 分域 | 不是本轮强项 | 保留 Obsidian 分域 + Rock runtime handle 重建 |
| Nested container | 非核心 | 明确 State/Inventory 递归 | 采用思路，补生产合同 |

真正值得 LGF 吸收的是二者组合：

`Definition -> compact entry -> optional typed state -> optional UObject`  
`stable ItemId + runtime generation handle`  
`Authority FastArray + derived UI`  
`Equipment source -> GAS GrantedHandles`  
`transaction/reservation -> commit/rollback`  
`Save domains -> runtime handle rebuild`

## 22. 明确拒绝/待修模式

本轮不会写进正式 Skill 为“推荐实现”的部分：

1. prediction `AttemptPredict()` stub；
2. failure resync TODO；
3. Drop Undo TODO；
4. Move Undo 断言疑点；
5. MoveParams 某路径未完整透传；
6. NestedInventory owner/multiplayer TODO；
7. client drop offset/impulse 未充分验证；
8. runtime `LoadSynchronous`；
9. 无 profile 证据的所有 O(N) cache 优化猜测；
10. component 可 Tick 但当前没有实际 Tick 行为。

## 23. 写回 SkillForge

本轮正式写回：

- `skillforge-ue-cpp`：新增“大规模物品值语义、稳定句柄与容器事务”参考；ARPG reference 增加入口；
- `skillforge-lgf`：External Project Patterns 增加 RockInventory，并与 Obsidian 合并成 LGF decision matrix；
- 新增 CPP-12..17 和 LGF-18 行为样本；
- 项目蒸馏索引增加本报告。

## 24. 当前未验证范围

- 未在目标 LGF 工程中编译 RockInventory；
- 未运行 RockInventory 自己的 Automation/PIE tests；
- 未验证 UE5.7 对其 Iris API 的所有兼容差异；
- 未实测 5 万 Item 的 GC/Net/Memory 对照；
- 未实测 NestedInventory 多层 JIP/重连；
- 未执行其 prediction/undo，因为源码本身仍在开发；
- 未把 MIT 实现直接拷贝到 LGF，Skills 只蒸馏设计和风险。
