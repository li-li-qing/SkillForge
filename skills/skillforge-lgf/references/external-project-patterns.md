# 外部 UE 项目模式迁移到 LGF

用于从 GitHub UE 项目吸收机制时做“二次翻译”。目标不是让 LGF 长成多个样例项目的拼接，而是把外部设计映射到 LGF 现有 Foundation、Request/Authority、GAS、Inventory/FastArray、Mover/GASP、UI 和持久化职责。

## 迁移顺序

1. 固定外部项目的 commit、引擎版本、功能开关和许可；区分默认路径与实验代码。
2. 先写它解决的**问题**和数据所有权，再写实现类名。不要因为外部项目叫 Action/Inventory/Controller 就在 LGF 创建同名层。
3. 在 LGF 找已有真值 owner、Request 入口、复制容器、Feature lifecycle、Asset lifecycle 和消费方。
4. 分类：直接采用原则、仅采用算法/数据结构、需要 LGF 适配、拒绝迁移。
5. 用 Host、Remote、SimulatedProxy、JIP、Travel/Respawn、失败/取消做回归；静态源码一致不等于网络通过。

## ActionRoguelike 第一轮映射（2026-09-14）

源码快照：`tomlooman/ActionRoguelike@a3f9a182c985b1732d9f72ae8b92e4845babfa3f`，README 主分支 UE 5.6。仓库未声明可直接依赖的 License，本技能只吸收机制，不复制实现。

### Replicated UObject

可吸收：

- UObject subobject 的网络生命周期必须包含宿主、网络资格、Add/Remove replicated subobject、属性注册、OnRep、Host 本地刷新、JIP 重建和缓存清理。
- OnRep/collection callback 应重建派生缓存与表现，Authority 本地写入走共享 refresh，不能等待自己的 OnRep。

LGF 边界：

- 不用样例自制 Action 系统替换 GAS/ASC、AbilitySpec、GameplayEffect 和既有 AbilitySet。
- 若 LGF 新增真正需要复制的轻量 UObject，先证明它不能更简单地表示为复制 struct/FastArray item/现有 GAS state，再采用 subobject。

### Interaction / Request

可吸收：owning client 本地选目标和高亮，Authority 决定交互是否合法。

LGF 必须更严格：

- Request 从玩家拥有的 Agent/Pawn/Controller 等真实入口进入；不能把世界门、NPC、共享仓库或 GameState 当 Remote player 的 Server RPC host。
- Authority 重新解析稳定目标身份并验证距离、LOS、权限、成本、状态、频率、会话代次。
- client focus/index 只代表 intent；UI 显示“提交成功”不能当业务成功。

### Data-driven Spawn / Asset

可吸收：轻量表做选择，`FPrimaryAssetId` 连接重配置，AssetManager 异步加载，Authority callback Spawn。

LGF 适配：

- 继续使用 LGF 现有 DataAsset/AssetManager/Feature lifecycle；不在 Tick/能力循环中 `LoadSynchronous`。
- 任何异步授予/换 Avatar/Spawn 回调都比较当前 owner、ASC、Avatar、request generation，拒绝旧回调污染新 Pawn。
- 若先扣成本再发起异步流程，定义 reserve/commit/refund 和幂等键。

### FastArray / Projectile prediction

可吸收：高频位置速度与低频复制 metadata 分离；FastArray Add/Change/Remove 回调负责 Proxy 派生状态。

拒绝照搬：

- client 不修改 LGF authoritative FastArray，也不在 client 上调用 `MarkItemDirty/MarkArrayDirty` 伪造确认。
- 预测数据放本地 transient prediction cache，用稳定 request/prediction key 与 Authority 结果 reconcile。
- FastArray 内部 ReplicationID 不用于保存、Quest、Inventory 或 UI identity。
- 高频数组若每项再线性查 metadata，先做 ID cache/索引失效设计再谈数据导向。

### Save

可吸收：明确 Save participants、只保存标记字段、Load 后执行 rebuild hook。

LGF 边界：

- 不保存 UIData/ViewData 或 FastArray 内部 ID。
- 不把 Actor FName 当长期业务 ID。
- Authority 保存 Inventory/Quest/Progression 等业务真值；恢复通过各模块公开 restore/rebuild contract，并确保复制 dirty、Host refresh 与 JIP 收敛。
- 大世界/频繁 autosave 不做每次全世界 Actor 扫描。

### Pooling / Performance

可吸收：预热、fallback、feature flag、Insights counter、hot/cold 数据拆分。

LGF 边界：

- Pool 对象先写 Reset Contract：GAS/Tag、Timer、Delegate、Niagara、Movement、Owner、replicated subobject、Dormancy、Trace state 全部列清。
- 在联网复用、Travel、死亡/取消、VFX 重置没有实测前不默认启用。
- 不把实验宏下的代码当 LGF 生产基础设施。

### AI

可吸收：AIController/Perception/BT/StateTree 在 Authority 运行，本地 UI 用复制状态或 owner notification 消费；EQS 负责空间选择。

LGF 边界：AI 最终攻击/技能仍通过现有 GAS/Authority 能力执行；客户端提示“被锁定”不是 AI 真值来源。

## Obsidian 第二轮映射（2026-09-14）

源码快照：`intrxx/Obsidian@bbe55b5b4c0ae4761ab57868398aca1c3b6b8c0b`。仓库许可证 GPL-3.0，且 README 说明公开仓库缺少一部分被忽略资产、不能视为可直接构建发行包。本技能只吸收架构思想；LGF 若不是 GPL 兼容分发，禁止直接复制实现。

### Item Definition / Instance / Fragment

可吸收：把不可变物品配置、玩家拥有的运行实例、可组合能力片段拆开。LGF 应让 Definition/DataAsset 持有图标、描述、基础 Mesh、类别和默认规则，运行 Instance/entry 只持有 ItemId、随机词缀、耐久/堆叠、鉴定、位置等变化状态。

LGF 应比样例更紧凑：不要为每个 Instance 重复复制 `FText`、Texture、StaticMesh 和其它可由 Definition 解析的静态展示数据。大批量纯数据 Item 优先紧凑 struct/FastArray，只有真正需要 UObject 行为/子对象复制才创建 replicated UObject。

### Inventory / Equipment / Stash FastArray

可吸收：Authority FastArray 保存条目，`PostReplicatedAdd/Change/PreReplicatedRemove` 重建 Grid/Slot/StashTab 本地 Map、占格和 UI message。派生缓存 `NotReplicated`，JIP 从当前快照恢复。

LGF 边界：

- 稳定 ItemId 与 FastArray ReplicationID 分离；
- Proxy callback 不修改业务真值；
- Inventory -> Equipment -> Stash 转移保持同一 Item identity，并作为一个 Authority transaction 预检/提交/回滚；
- 双手武器替换先验证 sister slot、背包容量和 ActionLock，不能一半卸装、一半失败；
- 共享仓库的 limit/并发由 Authority 基于最终状态校验，不按客户端当前 Tab 判断。

### Replicated Item UObject

可吸收：`IsSupportedForNetworking`、`GetLifetimeReplicatedProps`、registered subobject list、`ReadyForReplication` 补注册、Remove 时注销，以及必要的 legacy `ReplicateSubobjects` fallback。

LGF 使用前先核对 UE5.7/Iris 当前路径。FastArray 条目复制与 Item UObject 属性复制是两个合同；不能因为数组引用到了 UObject 就假定 UObject 字段已经同步，也不能因为 Component replicated 就省略 subobject 生命周期。Listen Host 的本地刷新仍不能等待自己的 OnRep。

### Equipment -> GAS 可逆授予

Obsidian 为每个 EquipmentEntry 保存 Authority-only GrantedHandles，装备时记录 AbilitySpecHandle/ActiveGameplayEffectHandle，卸装和 swap-out 精确撤销。这个模式直接适合 LGF：**grant source owns revoke handles**。

不要通过 GameplayTag 或 Ability class 全局扫描后删除，因为同一内容可能来自职业、技能树、Buff 或另一件装备。可用 ItemInstance/Equipment source 做 GAS `SourceObject`，但持久化使用稳定 ItemId，而不是 UObject 地址/handle。

### 资源加载

可吸收 ItemDataLoader 的 DeveloperSettings + AssetManager async preload/cache。拒绝照搬 Equipment affix loop 的 `SoftAbilitySetToApply.LoadSynchronous()` 和掉落未预载时的同步 fallback。LGF 装备/词缀/掉落热路径必须只操作已驻留数据；依赖未就绪时返回 Pending/AssetNotReady 或进入带 generation 的异步事务。

### 程序化掉落

Authority 生成最终 Definition/rarity/stack/affix/value/requirements，并复制或保存结果；client 不 reroll。公共生成入口本身要有 Authority guard，不能只依赖“目前调用者恰好是服务器”。需要重放/测试时用显式随机流/seed，Save 保存最终 roll，必要时记录 generation version/seed 供审计。

### Save 分域

可吸收 Master index / Per-Hero / Shared Stash 分开，以及 Hero Initialization data 与 mutable Gameplay data 分开。LGF 还必须补 schema version、migration、稳定 Definition/Item ID、原子失败恢复和 dirty tracking。

P2P/Listen Server 下 `ULocalPlayerSaveGame` 不改变 Authority：Remote client 不能写共享仓库或在线角色真值；Host/服务器/后端从 authoritative state 构建持久化快照。

### GameplayMessage / UI

FastArray delta 或 Authority local mutation可以发布 typed gameplay message，再由 WidgetController/ViewModel 更新 UI。消息是 presentation projection，不是第二份 Inventory truth。Host 与 Remote 的两条刷新路径要避免双播；JIP initial snapshot 与“玩家刚获得物品”提示应区分。


## RockInventory 第三轮映射（2026-09-14）

源码快照：`brokenrockstudios/RockInventory@be30b5a4a64c5707efde45c705a2e7011d9834d0`。仓库许可证 MIT；当前 README 与源码都显示系统仍在持续重构，因此可以参考/重写实现，但不能把 TODO、prediction stub 或 nested ownership 疑点写成 LGF 已验证能力。插件自身启用 Iris，并把 Runtime、Editor、ClientOnly UI 分模块。

### Definition -> Stack -> State -> optional ItemInstance

RockInventory 对 Obsidian 的最大补充，是把“所有玩家物品都是 UObject”继续往下拆：

- `URockItemDefinition`：PrimaryDataAsset 静态真值；
- `FRockItemStack`：常见运行数据，FastArray value item；
- `FRockItemState` + `FInstancedStruct`：只给需要的实例增加 typed mutable state；
- `URockItemInstance`：只有需要复杂对象身份/生命周期/嵌套容器时才存在。

LGF 应采用这条**成本梯度**，而不是选 Obsidian 或 RockInventory 其中一个极端。材料、货币、普通消耗品、大多数简单装备优先 compact entry；随机词缀/耐久可以 typed struct state；真正需要独立复制对象图、行为对象或 NestedInventory 再升级 UObject。

静态 `FText`、Icon、Mesh、MaxStack 等仍在 Definition，本地通过稳定 DefinitionId/PrimaryAsset 解析。运行保存和复制只传会变的结果。

### Stable Handle 与 FreeIndices

RockInventory 用一个紧凑 handle 把 `Index + Generation` 组合在一起，canonical ItemData 删除时不压缩数组，而是把 index 放入 `FreeIndices`，递增 generation 后复用。LGF 可以吸收这个运行时 identity 模式，用于 UI drag、异步事务和网络请求的 stale detection。

边界：

- 运行 handle 不替代持久化 ItemId/GUID；
- 每次 Authority 解引用都校验 index + generation；
- generation 位宽和 wrap 风险要按最大并发/复用频率选择；
- FastArray ReplicationID 仍不是业务 ID；
- 服务器收到旧 generation 要返回 stale/conflict，而不是让旧请求操作新物品。

### ItemData / SlotData 分离

可吸收：物品属性和布局位置分别复制。`ItemData` FastArray 保存 ItemStack；`SlotData` FastArray 只保存 ItemHandle、SlotHandle、Orientation/Lock 等。内部移动主要改变 SlotData，Stack 变化主要改变 ItemData。

LGF 当前 Inventory 若已有单一 entry，需要先测迁移收益；不要为了模仿项目无条件拆两套数组。若拆分：

- 两个数组都有独立 Dirty/callback/JIP 合同；
- Slot 引用 ItemHandle 时容忍复制到达顺序；
- non-replicated previous-handle/cache 只用于 delta 分类；
- Listen Host Authority mutation 主动发布与 Remote callback 等价的 local delta，不等待 OnRep；
- UI/ViewModel 消费 delta，不保存第二份可写 item truth。

### MutationKey 与写入口

可吸收 passkey/MutationKey 思想：外部系统只拿 const Stack/Handle，极少数被授权逻辑才能调用 gated setter。这样比把所有字段 public 或大量 `friend` 更容易审计。

LGF 不能把 MutationKey 当权限系统。真正业务修改仍必须经过现有 Request/Authority/Inventory transaction：re-resolve stable identity、验证 owner/access/action lock、修改、Dirty、发布结果。批量改动应以 commit 为单位合并 Dirty/message。

### Transaction / reservation

RockInventory 已有 TransactionID、Move/Loot/Drop command、Undo struct、pending slot claim 和 server RPC，说明“拖拽是 transaction，不是直接改 UI 数组”的方向正确。

LGF 只吸收框架思想，不照搬当前实现：源码快照中 prediction/reconcile/undo 仍有 TODO/stub，Move transaction 的参数透传和 Undo 断言也存在需要作者继续修正的疑点。LGF 先保持无预测的 Authority transaction：

`request -> authorize -> re-resolve handles -> reserve -> validate final state -> mutate -> side effects -> commit -> result`

失败释放 reservation 并保持容器/GAS/表现一致。以后只有在 rollback + authoritative resync 可验证后才增加 prediction。

### RPC / P2P 安全边界

RockInventory 的 Loot 已有服务端距离检查，这是好方向；但目标 Inventory 本身还要验证是否属于/授权给 Instigator。Drop 参数使用 NetQuantized Vector 只代表压缩，不代表可信，源码注释也明确 offset/impulse 仍需要服务端限制。

LGF 必须：

- 从 owned Player Agent/Controller/Pawn 的 Request 入口进入；
- client 传入 Inventory/Actor/Slot 只当 candidate；
- Authority 验证访问会话、所有权、距离/LOS、handle generation、当前 item、stack amount、section filter、slot reservation；
- drop offset/impulse 服务器 clamp 或重算；
- TransactionID 有 dedupe/idempotency/expiry；
- P2P/Listen Host 仍是 Authority，不让 Remote peer 写最终 Inventory truth。

### NestedInventory

RockInventory 已把 NestedInventory 表示成 ItemState，并递归注册 replicated subobject，这是很有价值的方向；但该快照的 owner 与多人行为仍有 TODO。LGF 若吸收背包套背包，先补完整合同：

- top-level replication owner 与 Outer；
- max depth 与 cycle prevention；
- detach/reparent 的 Add/Remove replicated subobject 顺序；
- stable ContainerId/ItemId 与 Save schema；
- parent move/destroy/JIP/reconnect；
- relevancy/共享查看者，避免整棵 nested tree 广播给所有连接。

### Asset 与查询性能

RockInventory 的 Definition 使用 soft refs/PrimaryAsset 是好基础，但当前仍能看到 NestedInventory、UI sound、fallback visual 等同步加载路径。LGF 延续已有规则：runtime hot path 只消费 resident dependencies，未就绪走 async/Pending，不在 Tick/DragDrop/FastArray callback/批量操作循环同步 Load。

Query 支持 Section -> Slot -> Item 的 predicate early-out，也值得吸收；但复杂 TagQuery/Fragment scan 只在必要时运行。构建可复用 query/cache，禁止在 Tick 或大循环中重复构造复杂 Tag 匹配。反向 ItemHandle -> Slot 若成为热点再增加 compact cache，并明确 generation/reuse 后失效。

### Obsidian + RockInventory 合并后的 LGF 决策

| 问题 | 默认选择 |
|---|---|
| 5 万材料/弹药/货币 | compact struct + FastArray |
| 普通随机装备 | compact entry + typed generated state |
| 耐久/metadata/socket 等可选状态 | `FInstancedStruct` 或 typed state，按需存在 |
| 独立复杂行为/嵌套 replicated container | replicated UObject escape hatch |
| 运行时 UI/transaction 引用 | index+generation handle + stable ItemId |
| 跨 Inventory/Equipment/Stash move | Authority transaction + reservation + rollback |
| Equipment -> GAS | source-owned GrantedHandles |
| UI | FastArray/local commit delta -> ViewModel/GameplayMessage |
| Save | stable ItemId/DefinitionId + schema；runtime handle 重建 |

目标不是让 LGF 同时拥有 ObsidianInventory 和 RockInventory，而是把两者最强的边界合并进 LGF 当前 Inventory/Equipment 体系。

## 外部项目评审输出模板

每次只研究一个项目，最终留下：

- 固定版本/许可；
- 模块地图；
- Authority/Proxy 数据流；
- 复制/存档身份；
- hot path 与资源加载；
- 可迁移模式；
- 明确拒绝项；
- 对 LGF 现有模块的落点；
- 新增行为 eval；
- 未执行的 UBT/PIE/网络/性能验证。

若外部项目本身写有 TODO/experimental 注释，把它保留为风险证据，不替作者“脑补完成”。

## AyaDogGames/GameplayFramework 第四轮映射（2026-09-14）

源码快照：`AyaDogGames/GameplayFramework@9379a85a0ff9d1b29dc22828ef3ed881b4635cf0`，许可证 Apache-2.0。README 把插件描述为 UE 5.7，而仓库的 `CLAUDE.md` 写 UE 5.8；`.uplugin` 没有 EngineVersion，因此本轮把引擎小版本记为**文档冲突，需目标工程/构建证据再定**，不能挑一个版本当已证实事实。

这个项目对 LGF 最有价值的不是某个单独类，而是展示了 GAS、Inventory、Equipment、Input、CommonUI 和 AI Spawn 如何组合成一个 Framework；同时源码也暴露了几类值得 LGF 提前禁止的授权和生命周期问题。

### PlayerState 长期状态 / Pawn Applied State

可吸收：PlayerState 持有 ASC、长期 AttributeSet、Inventory/Loadout、Credits/Level；Pawn 的 EquipmentManager 只保存当前 applied equipment。Pawn 初始化时 `InitAbilityActorInfo(PlayerState, Pawn)` 后 ApplyLoadout；UnPossessed 在链接拆掉前 UnequipAll 并 ReleaseOwnerBindings。

这与 LGF 的 Full Foundation 方向一致，可直接强化吸收变身/骑乘/Prop 形态：

- 长期 Inventory/GAS/Loadout 不随 Pawn 销毁；
- 当前 Mesh/Anim/Mover/Attachment/Trace/装备 Actor 按 Avatar 重建；
- `persistent owner vs replaceable avatar` 明确分层；
- delegate 对 PlayerState-hosted Inventory/ASC 使用 compare-and-rebind；
- 形态不兼容时保留 assignment，不强行 apply equipment；
- 新 Avatar ready 后才重新投影。

不要把 AyaDog 的类名/层级复制进 LGF；LGF 已有 Player Agent、Full Foundation、Avatar Binding 和 Equipment 生命周期，应把这套责任映射到现有 owner。

### AbilitySet 与 copy-empty-handle 反例

AbilitySet 本身的 GrantedHandles 模式值得保留：AbilitySpecHandle、ActiveGameplayEffectHandle、AttributeSet 都可以按 grant source 精确撤销。

但该 commit 的 `UDaAbilitySystemComponent::InitAbilitiesWithPawnData` / `GrantSet` 先把空局部 `FDaAbilitySet_GrantedHandles` 拷入数组，再调用 `GiveToAbilitySystem` 填局部变量，存在 `copy-empty-handle` 风险。LGF 不复制这个顺序。

相反，EquipmentManager 展示了更可靠的路径：

`construct local entry -> spawn source actor -> GiveToAbilitySystem(&Entry.GrantedHandles) -> build reverse map -> publish FastArray entry`

LGF 继续执行“grant source owns revoke handles”，并采用 `construct fully -> publish once`。任何 async/presentation/GAS side effect 会 re-enter 时，不保留指向可扩容数组元素的引用。

### Inventory：Stable ItemID + FastArray + disposable cache

可吸收：Inventory entry 用 `FGuid ItemID` 做持久身份，Definition 用 PrimaryAssetId，FastArray item 保存 stack/stat/AbilitySet assignment。`StatCountMap` 是 NotReplicated 查询加速器；复制和 save copy 后重建，miss 时回退到 canonical StatTags scan，因此 cache stale 只影响速度不影响正确性。

LGF 与上一轮 RockInventory 合并后的选择仍是：

- stable ItemId/GUID 做跨容器/存档身份；
- 大集合 FastArray；
- runtime generation handle 用于短期 stale detection；
- local cache 可重建且永远不是第二份业务真值。

AyaDog 当前单 SlotIndex inventory 比 LGF 的复杂 Grid/Equipment 简化，不应反向降低 LGF 容器能力。

### Client mutation RPC：必须收紧

本轮最重要的拒绝项之一：`UDaInventoryComponent::AddItem` 可以在客户端直接转 `Server_AddItem(ItemDefinitionID, StackCount, SlotHint)`；服务端虽检查 Authority、Definition、数量和容量，但没有 loot/shop/quest/crafting 等“为何有权获得这件物品”的来源证明。

同样，通用 `Server_SetItemStat` / `Server_AddItemStat` 只显式保护 Grade；把整个 `Item.Stat` 父树视为可客户端写，再列少量黑名单，不适合作为 LGF 的生产权限模型。

LGF 采用 `operation-specific default-deny`：

- `RequestLoot(WorldItemId)`：服务器查世界物品、距离、访问权、一次性消费；
- `RequestBuy(ShopOfferId)`：服务器解析价格、库存、货币；
- `RequestCraft(RecipeId)`：服务器验证材料/站点/配方；
- `RequestRepair(ItemId, Points)`：服务器计算价格并修改 Condition；
- Authority 内部才拥有最终 `GrantItem/SetProvenance/CommitReward`。

Remote client 不直接指定最终 reward、rarity、grade、condition、affix、credits。客户端 `true` 只代表 request submitted；最终 UI 等 replicated state/result。

### Re-entry：稳定身份重新解析

AyaDog 的 Inventory/Equipment 多处显式处理 re-entry：

- GameplayEvent 之后不继续相信原 SlotIndex，而用 ItemID re-find；
- sync load 返回后再次按 ItemID 找当前 entry；
- delegate broadcast 可能改 FastArray，先 snapshot，再 re-locate；
- Equipment 本地 entry 完全初始化后才 publish；
- 条件惩罚 effect apply 后重新找 equipment entry 再广播。

这类规则直接适合 LGF：Blueprint event、Ability apply、Message、Asset callback、Spawn 都视为可重入边界。旧 reference/index 不跨边界继续使用。

### Loadout intent 与 Applied Equipment

AyaDog 把 loadout 放在 PlayerState Inventory；Equipment FastArray 在 Pawn。这个语义比“快捷栏等于当前已装备”更稳：

- hotbar consumable 只有 assignment；
- equippable slot 可以 applied；
- Item 离开 Inventory 后 Authority 清理指向它的 assignment；
- Pawn 重生后重新 ApplyLoadout；
- Condition=0 可以临时 unequip，但 assignment 可继续存在，修复后重新 equip。

LGF 对变形/骑乘可采用同一语义：assignment 反映玩家意图，applied state 反映当前 Avatar 能否兑现。

### Enhanced Input / GAS Tag 路由

可吸收 `InputAction -> DataAsset InputTag -> AbilitySpec DynamicSourceTag`，避免 PlayerController 按 AbilityClass 写巨型 switch。

AyaDog 当前 Press/Held/Release 都线性遍历所有 ActivatableAbilities。LGF 数量小时不必提前复杂化；若后期技能/装备/被动使 spec 达到数百且输入成为热点，则维护 `InputTag -> AbilitySpecHandle(s)` local index，在 grant/remove/tag change 后更新。索引只做 lookup，不替代 GAS CanActivate/Prediction/Cost/Cooldown 真值。

### CommonUI / WidgetController / Hotbar

可吸收三层：

1. PrimaryGameLayout 的 GameplayTag layer stack 负责导航、焦点和 input suspension；
2. WidgetController/ViewModel 从 FastArray/ASC 投影 UI snapshot；
3. Gameplay domain command 负责 Use/Equip/Toggle。

最新 hotbar 同时订阅 PlayerState Inventory 与 Pawn Equipment；内容由事件刷新，0.25 秒 timer 只是检测 dependency 是否换了，不是业务刷新率。鼠标点击和 QuickSlot Ability 都调用同一个 slot activation command，所以规则不漂移。

LGF UI 继续坚持 UIData/ViewData 不成为第二份真值。若已有 CommonUI Router/Layer，映射概念而不是新建一套 DaPrimaryGameLayout。

### Attribute Tag -> UI metadata

可吸收：AttributeSet 暴露 GameplayTag -> FGameplayAttribute getter，单独 DataAsset 提供 DisplayName/Icon/描述，WidgetController 绑定 GAS value-change delegates。

LGF 收紧：SetIdentifier 用作“身份”时应唯一、可验证；若使用 parent `MatchesTag` 查 AttributeSet，存在多个匹配时不能靠数组顺序静默选择。加入 startup/editor diagnostic，或者身份场景改 exact match，分类场景才用 parent match。

### AI Spawn Manager

可吸收职责拆分：Authority manager -> population/budget -> lightweight selection metadata -> EQS spatial query -> async PrimaryAsset load -> Spawn。

当前实现每个 timer tick 用 `TActorRange` 数全世界 AI，DataTable 的 Weight/SpawnCost 也没有参与最终随机选择，因此只当样例。LGF 大规模 Director 应由 spawn/death event 维护 registry/count，用 cost/weight/phase 选择候选，异步前 reserve budget，回调按 wave/request generation 重验容量和世界状态。

### Save

AyaDog 的 PlayerState Save 把 Inventory/Loadout 一起持久化，支持“长期玩家状态不跟 Pawn 走”的架构证据。但整个 Save subsystem 当前仍是同步 slot I/O、全世界 Actor iteration、ActorName 匹配，并明确单玩家 `break`，所以不覆盖 LGF 现有更严格的 stable identity/schema/Authority/save participant 规则。

### 同步加载拒绝项

当前 Inventory Definition fallback、Drop PickupActor/DisplayMesh、Equipment Actor/AbilitySet、Hotbar Definition 等路径仍存在 `TryLoad`/`LoadSynchronous`。LGF 不采用。“DataAsset 很小”不是 runtime 同步 load 的通行证。

预热 PrimaryAsset/bundle 或进入有 generation 的 async transaction；若 legacy sync fallback 暂时保留，至少把它视为 re-entry 边界，返回后 re-resolve stable identity。

### AyaDog -> LGF 决策矩阵

| AyaDog 机制 | LGF 处理 |
|---|---|
| PlayerState ASC/Inventory/Loadout | 映射到 Full Foundation 稳定 owner，不复制新体系 |
| Pawn Applied Equipment | 映射当前 Avatar/Equipment presentation，切 Pawn 可重建 |
| AbilitySet GrantedHandles | 保留来源级撤销，修掉 copy-empty-handle 顺序 |
| InputTag ability binding | 保留；大 spec 集按 profile 加 tag->spec index |
| Inventory FastArray + GUID | 保留 identity 思路；不降低 LGF 现有复杂容器能力 |
| generic Server_AddItem | 拒绝，改 operation-specific Authority request |
| generic Item.Stat client writes | 拒绝，default-deny/capability-specific |
| Loadout assignment | 保留，与 applied equipment 分离 |
| WidgetController/ViewModel | 保留只读 projection |
| UI.Layer CommonUI stack | 映射 LGF 现有 UI Router/Layer，不建第二栈 |
| timer TActorRange AI population | 小样例；大规模改 registry/event budget |
| runtime sync loads | 拒绝，预热/async |
| whole-world ActorName Save | 不迁移，LGF 用稳定 identity/schema/save participants |

### 本轮 LGF 特别适用于变身/骑乘

吸收 NPC、变 Prop、骑宠物/车辆都按同一 Avatar contract：

`stable player truth -> prepare old form -> revoke/unbind old applied state -> switch avatar -> initialize movement/animation/ASC actor info -> validate form compatibility -> reapply loadout/presentation`

这样形态数量可以增加，而 Inventory/GAS/Save 不随每个形态复制一份。异步动画/外观/装备加载都携带 avatar generation，旧形态回调晚到时直接丢弃。

## SAM-tak/GASP-ALS-R 第五轮映射（2026-09-14）

源码快照：`SAM-tak/GASP-ALS-R@a227dfecfcb2719c2541218cf026c05dfe3290ec`。该提交于 2026-09-13 合并 `feature/mover`。项目内容存在分许可证边界：UE-only Content 受 Unreal Engine 内容许可约束；README 指定原始 C++ 与 ALS-Refactored 派生 C++ 为 MIT；标记为 Unreal Engine source 派生的源文件继续受 UE EULA 约束。不能把整个仓库统一写成 MIT。

该快照的 Character 文档记录使用 custom UE 5.8.2；LGF 当前目标 UE 5.7，所以这轮只迁移架构思想。Mover、GameplayCameras、PhysicsControl、PoseSearch、NetworkPrediction 的具体 API/字段都需在 LGF 实际 5.7 Engine source 重新发现并编译验证。

### 最值得吸收的职责图

| GAR 模式 | LGF 落点 |
|---|---|
| APawn + Mover | 映射 LGF 现有 Pawn/Mover 路线，不改成长 CharacterMovement 依赖 |
| GAS Action Ability | 继续由 LGF GAS/Combat policy 拥有合法性和生命周期 |
| Mover Input/Sync | 记录 replay-safe movement state，不在 resim 读取 live mesh/ASC |
| Montage Root -> Layered Move | 保留单一 movement consumer，并补显式 cancel identity |
| Linked Overlay Tasks | 映射动画 presentation layer，不成为 gameplay truth |
| PhysicsControl Ragdoll | 单一 task owner，Physics/Mover/Anim 分域 |
| GameplayCamera PawnComponent | 只保留 local possession context；desired intent 与 active rig 分离 |

### 源码与文档不能机械照抄

- Mover 文档列有 Modifier 体系，但源码当前 `GAR_USE_MOVEMENTMODIFIER=0`；LGF 不能按文档名词强行把 gait/stance 全改成 Modifier。
- Character overview 仍出现旧 PhysicalAnimation 名称，而专门的 PhysicsControl 文档说明它已移除；取材时以当前源码和更具体的新文档为准。
- Mover stance 有 automation tests，但文档自己注明 full gameplay/network validation 仍需要做；不能把 unit/automation 通过等价成 Dedicated/JIP 已验收。
- Overlay component 当前有每 Tick 构建 tag mask/扫描 ASC 的路径；在 LGF 规模放大前要改事件驱动或缓存。
- Traversal TargetData 传输 client-selected montage/ledge/target primitive；LGF 必须增加 Authority envelope validation，不把 demo-friendly prediction 当安全边界。
- Montage -> Layered Move 路线本身值得吸收，但现有源码只 Stop Montage 不能证明所有 Layered Move cancel edge 都覆盖；LGF 要记录并清理真实 Mover handle。

### 对变身/骑乘的价值

该项目证明 Pawn 可以同时承载 Mover、GAS、Linked Layers、PhysicsControl 与 GameplayCamera，因此非常适合拿来校正 LGF 的 Avatar contract；但长期玩家真值仍应继续留在 LGF 的稳定 owner。形态切换只替换并重新装配 Avatar-specific movement/animation/physics/camera/presentation，不复制 Inventory/GAS/Save。

## Sixze/ALS-Refactored 第六轮映射（2026-09-14）

固定源码：`Sixze/ALS-Refactored@b754d6f0f2bb03741d301f8fb88077ebfe561e17`，MIT。当前固定提交的 `ALS.uplugin` 为 VersionName 4.18、EngineVersion 5.8.0；README 的发布支持表仍列 4.17 / UE 5.7，因此版本判断以固定提交源码为主。

### 只吸收网络与动画工程经验，不移植 CMC 主链

| ALS-R 模式 | LGF 翻译 |
|---|---|
| custom CMC SavedMove/MoveData | Mover replay-safe Input/Sync/Persistent State |
| CMC RootMotionSource Mantle | Mover movement transaction / LayeredMove |
| Push Model properties | 保留 dirty + role/condition 合同 |
| Iris custom RootMotionSource support | 目标 UE 的 custom Mover/transaction serializer 审查 |
| GT Anim snapshot + worker thread | 直接吸收线程边界 |
| Linked Anim BP + GameplayTag pose | 继续作为 presentation layer |
| ALSCamera component | 只吸收算法；LGF 保持 GameplayCamera 单 owner |
| CMC copied `PhysWalking` | 拒绝作为 LGF 基础，避免 engine fork debt |

### 这轮新增的生产规则

- CMC `FSavedMove` 的价值是证明 Rotation/Stance/Gait 属于历史 movement prediction 输入；LGF 不把它降级成普通 Replicated tag。
- Push Model 需要项目配置、push-based property 声明、Authority mutation dirty 三段闭环。
- Legacy `NetSerialize` 不自动证明 Iris 兼容；自定义 movement transaction/state 需检查目标引擎 serializer/descriptor。
- SimulatedProxy 的 Actor transform、view rotation、visual mesh 是不同 smoothing channel。
- URO、AlwaysTickPose、absolute mesh rotation 按 network role / visibility / movement base / gameplay need 配置，不能全局套用。
- Linked Anim Property Access 需要字段 write phase；只有 parallel evaluation 前稳定下来的 snapshot 默认可 AnyThread 读取。
- moving-base traversal 用 stable base reference + local-space target + operation handle，动画跟随 movement transaction 时间。

### 明确拒绝照搬

- 整套 `AAlsCharacter/UAlsCharacterMovementComponent` 进入 Pawn+Mover LGF；
- 复制 `PhysWalking` 作为新移动基础；
- ALSCamera 与 GameplayCamera 同时成为 runtime camera owner；
- 客户端传入 Roll Montage/Yaw 或 Mantle Parameters 后只做轻量 server check 的权限边界；
- 把 `a.URO.DisableInterpolation=True`、AlwaysTickPose 或 absolute mesh rotation 当通用项目开关；
- 因 README 写 UE5.7 就忽略当前 main 实际已是 UE5.8。

### 对变身 / 骑乘的额外价值

ALS-R 的 role-aware visual mesh 和 movement-base 处理提醒 LGF：形态或坐骑切换后要同时重建 movement prediction state、view smoothing、visual smoothing、foot-lock history、linked layer cache。坐骑/平台旋转尤其不能沿用针对静态地面 SimProxy 的绝对 mesh rotation workaround。

## tranek/GASDocumentation + GASShooter 第七轮映射（2026-09-14）

固定来源：

- `tranek/GASDocumentation@8f76c5780bdea69e0ea2cc161ab2f435f04182eb`，MIT，文档自述目标 UE5.3；
- `tranek/GASShooter@26295c548a19f221917e4a7232c12e763db64cb1`，MIT，代码主体为 2021 UE4-era advanced sample。

本轮不把二者当 2026 API authority。当前 LGF 的具体函数、AbilityTask 和 prediction API 以目标 UE5.7/实际引擎源码为准。

### 最值得吸收的 GAS 合同

| 外部模式 | LGF 翻译 |
|---|---|
| PlayerState ASC Owner + Character Avatar | 继续 LGF stable player truth / replaceable Avatar；变身重建 ActorInfo，不复制 ASC |
| GameplayAbilitySpec SourceObject | 作为 runtime grant source，与 persistent ItemId 分层 |
| weapon 保存 SpecHandle | Equipment grant source 保存最终 GrantedHandles，卸装精确撤销 |
| PredictionKey window | 每个 latent combo/hit boundary 重新审计 prediction scope |
| custom TargetData | 绑定 activation identity 的紧凑 request；Authority sanitize/retrace |
| TargetData delegate + consume | 处理 data-before-listener race、consume-once、cancel cleanup |
| reusable TargetActor | 只吸收 reset/lifecycle；LGF 不复制 Actor targeter hierarchy |
| Ability RPC batching | profile 驱动的 transport optimization，不替代 Authority transaction |
| item ammo as replicated fields | 证明 item-local runtime state 不必 AttributeSet-per-item |
| custom EffectContext | 只保存本次 damage provenance / compact target info |
| multi-mesh montage prediction reject | LGF 用 AvatarGeneration + Mesh/Layer/MontageInstance 统一回滚 presentation |

### 与 Codex 最新双刀规则的合并

Codex 已针对实际工程建立 PartId、TraceSourceBinding、HitWindow、Sequence 和真实伤害夹具。GAS 本轮只补足下面一层：

- HitWindow identity 与 PredictionKey identity 不互相替代；
- 同一 Section 的左右刀可以共享 Ability activation，但保持独立 Part/Trace/Hit dedup；
- 下一 Section 进入 latent continuation 后不能假设首段 PredictionKey 仍有效；
- client `Submitted` 还需要记录 scoped prediction 与 Authority termination reason；
- damage callback 的 synchronous re-entry 继续用 run/window generation 防止旧引用。

### 明确拒绝照搬

- UE4 InputID 绑定体系；
- GASShooter 整套 1P/3P custom ASC Montage fork；
- TargetActor Actor-based targeting 作为 LGF 唯一目标系统；
- `StaticLoadClass` 硬路径；
- 每 Item 一个 ASC/AttributeSet；
- firing 时关 ammo replication 但没有 correction/reconciliation；
- `FScopedServerAbilityRPCBatcher` 等旧类名不经 UE5.7 源码核验直接写生产代码；
- NetSerialize 成功就信任客户端 TargetData；
- batching 成功就删除 idempotency/权限/rollback。

### 对变身/骑乘的附加价值

GASDocumentation 的 OwnerActor/AvatarActor 区分进一步证明：LGF 的 PlayerState/稳定 Player Agent 可以保留 ASC，而任意 NPC/Prop/Mount 只作为 Avatar。Avatar generation 必须参与 TargetData、AbilityTask、预测 Montage 和装备 presentation 的迟到回调拒绝；否则旧形态的 reject/cancel 可能误停新形态同名 Ability/Montage。

## Lyra Starter Game：现代性门与模块化框架

Lyra 与前述社区项目不同：它随 UE 大版本持续更新，因此研究时必须绑定 UE 版本。Epic 5.1 已将 5.0 的 Pawn 初始化重写为 Init State 体系来修复复制竞态；当前官方 5.8 文档仍保留 PawnExtension/HeroComponent readiness、PlayerState ASC、AbilitySet、PawnData、Experience/GameFeature、Inventory/Equipment 生命周期和 Enhanced Input 组合思想。

LGF 不复制 Lyra 运行时。可吸收：

- 显式 Avatar readiness state；
- stable PlayerState ASC + replaceable Avatar；
- Pawn/Form DataAsset composition；
- async Experience-like readiness barrier；
- feature grant/input/UI 的可逆 lifecycle；
- Inventory item 与 equipped generation 分域；
- CommonUI router 与 gameplay input 分层。

拒绝整套迁移：LGF 已有 Foundation、Request/Authority、Inventory、Equipment、GASP/Mover、GameplayCamera 与 UI platform。当前 GameFeatures 官方 5.8 API 仍标 Beta，若没有动态玩法包/DLC/mod 等真实收益，不应仅因为 Lyra 使用就成为 LGF Production 硬依赖。

详细映射见 [Lyra 现代框架经验映射](lyra-modern-framework-mapping.md)。

## XistCommonGameSample（UE5.7 CommonUI / Input）

固定快照 `XistGG/XistCommonGameSample@7e01e1fed344a741f80fa82b7161c86c494a410b`，MIT，`.uproject` 明确 UE5.7。对 LGF 当前 5.7 目标属于 Current-to-target；对 5.8+ 升级应重新核对 CommonUI/CommonGame/EnhancedInput API。README 明确项目是 single-player Lyra-like UI/Input 教学样例，因此不作为多人 Authority/GAS/JIP 证据。

可吸收：LocalPlayer Root Layout/Policy、GameplayTag layer、InputAction->InputTag DataAsset、UI Action exact handle、transition suspend token、GameplayMessage projection、streamed optional page。

拒绝直接迁移：Pawn Possess 中 `ClearAllMappings()`、全局 `GetFirstPlayerController()`、Pawn 永久拥有 Root HUD、blank widget 作为通用 modal policy、message 替代 replication。LGF 现有 UINavigation 和 FoundationUIInput 继续拥有唯一逻辑路由/输入仲裁，CommonUI 只做 Presenter。

## nulla-sutra/unreal-combee 第十轮映射（2026-09-14）

固定源码：`nulla-sutra/unreal-combee@971fa227179a99d308956b7031d5422634cefbfd`，MPL-2.0，2026-06-30；插件 descriptor 标记 Experimental 且未固定 EngineVersion，因此分类为 `Current source / Experimental adoption`。

### 可吸收机制

- Unique / Shared / Link 三种 item 语义提醒 LGF 区分“有独立实例状态”“只需 Definition/stack”“只引用 canonical item”的不同成本。
- Link item 的 source accessibility + source-container mutation listener 可映射为 LGF Hotbar/收藏按 stable ItemId re-resolve，而不是复制 Item truth。
- FastArray canonical mutation 立即 Dirty，UI mutation notification next-tick coalesce，可用于减少 view refresh churn，但只属于 projection。
- registered subobject list 适合少量复杂 Item UObject；Outer/network host/business owner 必须显式分层。
- TransactionId、owner-only Bridge、server-side child transaction 与 `FInstancedStruct` payload 是有价值的 command skeleton。
- Push Model 只在值真正变化时 dirty 的方向继续采用。

### 固定源码暴露的拒绝项

- Hive include Iris FastArray，但 active inheritance 被 `#if 0` 关闭；不能写“当前使用 FIrisFastArraySerializer”。
- plugin descriptor 本身是 Experimental；不能因 2026 年仍维护就直接标 Production-ready。
- `FRWLock` 只看见 writer lock，没有 read lock；不能称 UObject container thread-safe。
- `AddReplicatedSubObject` 有 active path，但 remove helper 在固定提交中只找到声明/定义，没有 caller；复杂 Item transfer 的对称 unregister 证据不足。
- README 写 rollback/atomic swap，但 base Transaction 的 rollback 被注释；Swap 是多步 child mutation，失败 bubbling 不等于 rollback。
- Assign transaction 对底层 `AssignCell()` failure 的检查被注释；Eject 也不检查 child clear result 就继续 reparent。
- Bridge 接受客户端 `TSubclassOf<Transaction>`；另有 client-selected `RemoteClass + FuncName` generic server ProcessEvent。LGF 不采用这种 server dispatch。
- Snapshot active code 没有 stable ItemId/ContainerId/SchemaVersion；ApplyContainerSnapshot 先 Clear live container，也没有完成从 ItemClassPath 重建 item graph 的 active 路径。
- UCombeeItem::GetWorld 使用 global current play world；多 PIE/DS 不作为 LGF 模板。

### LGF 迁移结论

本轮不引入 Combee runtime。只补以下现有架构合同：

1. server-owned inventory operation registry / default-deny；
2. container capability/access revalidation；
3. cross-container before-image/write-set + real atomic commit/rollback；
4. child mutation result 显式 gate；
5. replicated Item subobject 对称 transfer + JIP/reconnect；
6. Hotbar/link by stable ItemId；
7. frame-coalesced UI delta 不承载 business truth；
8. GameThread UObject ownership + honest threading evidence；
9. versioned snapshot graph rebuild；
10. external README feature 必须有 active-code evidence。

细节见 [LGF Container Transaction 合同](container-transaction-contracts.md)。

## Megafunk/MassSample + Epic Mass 5.8 第十一轮映射（2026-09-14）

主样本固定为 `Megafunk/MassSample@ca9825861f35ab4f8e152351de2adb893b51ca70`，MIT，commit message 明确标记 `(5.8)`。`getnamo/MassCommunitySample@1487f020...` 是脱离 upstream 的旧 fork，README 主体仍以 UE5.1 时代说明为主，因此只保留为 API 演化对照，不作为 LGF 当前接口来源。

### 现代性判断

Epic UE5.8 release notes 对 Mass 做了大规模重构：Signals 进入 core、支持 off-thread entity creation、sparse/virtual fragments、processor scheduler/dependency overhaul、MassCore 解耦；官方同时新增 QueryExecutor 简化 API。另一方面，MassGameplay、MassAI、MassCrowd、ZoneGraph 当前官方插件页仍标 Experimental。LGF 因此采用 `MassEntity core 可评估 + Experimental gameplay/AI modules feature-gated`，不把整套 Mass 设成 Foundation 硬依赖。

### 迁入 LGF 的机制

- StableAgentId 与 `FMassEntityHandle` / Actor representation 分层；
- Mass low-fidelity + LGF Pawn/Mover/GAS high-fidelity 的 simulation tiers；
- promotion/demotion 是带 generation 的 Authority transaction；
- CombatOwner routing fence 保证 Mass damage 与 Pawn GAS 只消费一次 DamageId；
- Representation/Simulation/Replication 三种 LOD 分开；
- Signal 只做 wakeup，payload 仍在 canonical fragment/Authority state；
- ZoneGraph 做 lane/corridor，SmartObject 做 reservation，StateTree 做 behavior orchestration，Processor 做 batch data transform；
- Mass Debugger/Insights 量 archetype/chunk/processor/LOD/replication，不用“ECS 会更快”代替 profile；
- 宠物/坐骑远处可 Mass，被骑乘/复杂战斗时 promotion 到完整 LGF Avatar。

### 明确拒绝

- 从 UE5.1 fork 复制旧 Processor/Query API 到 UE5.7/5.8；
- `FMassEntityHandle` 作为 Save/Quest/Pet identity；
- high-res Actor/ISM 持有唯一业务真值；
- client Mass simulation 决定伤害/掉落/奖励；
- 每个 bool 都通过频繁普通 Tag/Fragment Add/Remove 表达而不测 archetype churn；
- Processor 中未声明线程访问就 SpawnActor/改 UObject/WorldSubsystem；
- MassGameplay/MassAI/ZoneGraph Experimental 模块成为 LGF 核心 public API。

完整 LGF 迁移合同见 [Mass AI Scaling](mass-ai-scaling.md)。

## Epic StateTree 5.8 + bohdon/UtilityAIPlugin 第十二轮映射（2026-09-14）

主证据采用 Epic UE5.8 StateTree 当前文档/API；Utility AI 对照固定为 `bohdon/UtilityAIPlugin@0f49e0c6d420497d3102c3975601360dc120bf15`（MIT，2025-04-06）。后者没有固定 EngineVersion，且 `CalculateDataScore()` 在固定源码仍为 TODO，因此分类为 `Stable-but-old mechanism sample`，不能作为 UE5.8 接口权威。

### 现代性判断

- UE5.8 StateTree 本体是当前通用分层状态机，具备 active path、Tasks、Transitions、Events、Parameters、linked/external tree、AIComponent/Schema 等现代能力。
- UE5.8 已提供 `Try Select Children with Highest Utility` 与 weighted utility selector，child state 可配置 Considerations 与 Weight；但 `FStateTreeConsiderationBase` 当前 API 明确标 Experimental。LGF 因此允许 target-version adapter 使用它，却不把 experimental consideration 类型暴露为 Foundation public ABI。
- UtilityAIPlugin 的 25ms `TickComponent()` 会对所有 Action `UpdateScore()` 后选最高分，适合学习评分、迟滞、busy/interruption 与 debugger，不作为大量 NPC 默认调度模型。

### 迁入 LGF 的机制

- 一个 Agent/Avatar 同一时刻只有一个 high-level Decision Owner；默认是 StateTree，Utility scorer 只返回候选分数，不另起第二套 CurrentAction 真值。
- Decision / Execution / Authority 三层分离：StateTree 选择 intent，GAS/Mover/SmartObject 执行，Authority 重新验证并决定伤害、Cost、Cooldown、Loot、Inventory。
- Utility scorer 必须纯函数化：输入 DecisionContext snapshot，输出 normalized score + reason breakdown；评分阶段禁止激活 Ability、移动 Pawn、Claim SmartObject 或写 canonical state。
- 采用 hysteresis / switch penalty / minimum dwell / cooldown 等稳定策略，避免候选分数在阈值附近每帧抖动切换。
- StateTree active path 上多个 Task 是并行参与者，不按 BehaviorTree Sequence 心智解释；明确 `ANY` / `ALL` completion 和 cancel/exit cleanup。
- 异步 Task/Ability/Move 必须带 `DecisionGeneration` 或等价 request identity，旧 completion 在状态已切换、Avatar 已更换、Agent 已 demote/promote 后必须被拒绝。
- 大量 Mass Agent 使用 event/signal/dirty-bucket/LOD budget 做低频决策；进入高交互后 promotion 到完整 LGF Avatar，可重建 StateTree runtime，但业务 intent/cooldown/target 通过稳定 DecisionState 继续，不序列化内部 StateTree execution frame。
- 玩家对宠物/坐骑的 Follow/Stay/Attack/Mount/Dismount 命令属于更高优先 command layer；自动 Utility 不得立即把玩家命令抢回。

### 明确拒绝

- `UtilityAIComponent` 和 StateTree 同时拥有 CurrentAction/CurrentState；
- 每个 AI 固定 0.025 秒全量扫描所有 Action，不先 profile/预算；
- Blueprint utility scorer 在成千上万实体的热路径无预算运行；
- selector/consideration 直接应用伤害、奖励或库存；
- `bBusy` 一个布尔值替代可取消性、GAS tag、移动请求和异步 completion 的显式 interruption protocol；
- 把 StateTree Task 列表当成传统 BehaviorTree Sequence；
- Save/Promotion 时序列化/恢复 StateTree 内部 frame、node instance pointer 或 transient execution handle；
- 因 UE5.8 编辑器已有 Utility selector 就把 Experimental consideration API 固化到 LGF Foundation。

完整迁移合同见 [AI 决策编排](ai-decision-orchestration.md)。


## MothCocoon/FlowGraph 第十三轮映射（2026-09-14）

双锚点研究：最新设计固定 `MothCocoon/FlowGraph@c616a5d2afa8124cb7c1d66b1071fd499f2be7db`（Flow 2.4 in works，首个 UE5.9 release）；LGF 当前 UE5.7 的直接兼容边界固定 `v2.3-5.7@8211b25999068407cb7b40b8c97e18b52d4832ca`。MIT，仓库 2026-08-31 仍活跃。不能把默认 `5.x` 分支等价为 UE5.7 API。

### 可吸收机制

- FlowAsset template 与 transient runtime instance 分离，runtime instance 绑定 owner、ActiveNodes、RecordedNodes、SubGraph tree；
- UObject Flow Node 作为 latent feature lifecycle owner，而不是函数式节点；
- `NodeGuid` + SaveGame node state 说明 authored node identity 一旦发布就进入 save ABI；
- `Keep / Abort` finish policy；
- SubGraph node 拥有 child graph lifecycle，并用 soft asset/params 表达定义依赖；
- deferred transition scope + execution gate 作为 reentrancy boundary；
- SaveGame hooks 分布在 subsystem / component / asset / node，允许项目自定义 save container；
- SignalMode Enabled/Disabled/PassThrough 为 shipped graph patch 提供 tombstone/pass-through 机制；
- runtime debugger、editor validation、active wire/node visualization；
- Identity GameplayTag registry 适合 authored world 的低频语义发现；
- 2.3 的 staged Data Pin migration/resave 证明资产升级可能需要 stepping-stone version。

### 需要 LGF 强化

- project-owned `SaveSchemaVersion + GraphDefinitionVersion + StableOwnerId + QuestInstanceId`；
- Authority quest snapshot/revision 与 transient Flow Notify 分离，JIP 先 snapshot 再 delta；
- Graph node 通过 typed domain command 调 Inventory/GAS/World/Reward service，不能直接成为第二个 Authority；
- irreversible reward/spawn/unlock 使用 stable idempotency ledger；
- active-world load 采用 quiesce + staging restore + atomic switch；
- historical save fixtures、NodeId tombstone/redirect/pass-through migration；
- async preload adapter，拒绝在热路径意外 `LoadSynchronous()`；
- Mass/StateTree/FlowGraph/GAS 各自拥有不同层次真值。

### 明确拒绝/不直接迁移

- 直接把 2.4/UE5.9-only API 写成 UE5.7 可用；
- 用 runtime UObject name、WorldName、ActorInstanceName 作为唯一长期 Quest identity；
- 用 replicated notify tag 替代 durable quest state；
- client-only graph 直接发奖励、改库存或完成 Authority 任务；
- 每个 Mass NPC 创建一个 Flow UObject graph 作为 per-frame brain；
- 因 `TSoftObjectPtr` 就声称 SubGraph runtime async；当前 active `CreateSubFlow()` 仍有同步加载路径；
- shipped Save 已使用的 NodeGuid 被直接删除/复用而无 migration。

完整 LGF 合同见 [Quest / World Flow 编排](quest-world-flow-orchestration.md)。


## TheGeebus/SimpleQuest 第十四轮映射（2026-09-14）

主样本固定为 `TheGeebus/SimpleQuest@46978ad2c81ba90f21836e7c468141523dedb95d`（0.8.1，MIT，2026-09-14）。该提交对应 tree `daf658bd6c86f54ca024d76e58a9a81908635617`；commit/tree 必须分开记录。README 明确覆盖 UE5.6–5.8，Runtime / UncookedOnly / Editor 模块边界清晰，因此分类为 `Current-to-target`，但仍以 active code path 而非 README 宣称作为生产证据。

### 可吸收机制

- authoring Quest Graph 在编译期扁平化为 Runtime definition，Shipping 不遍历 UEdGraph；
- `QuestlineID / QuestContentGuid / ObjectiveGuid / PathIdentity / OutcomeTag` 与 DisplayName/Pin Label 分离；
- `UQuestManagerSubsystem` 作为 opaque sole writer，`UQuestStateSubsystem` 作为 public read-side registry；
- Objective UObject 是 runtime behavior/lifecycle，save identity 仍是 stable GUID + domain snapshot；
- event-driven Objective + late registration synthetic catch-up；
- durable lifecycle state 与 transient progress/refusal event 明确分层；
- named outcome + authored PathIdentity 取代 bool branch explosion；
- scoped `FQuestAdvancementHold` handle 让 cinematic/audio/vote 等 pacing 可组合；
- `FSimpleQuestSaveSnapshot` 用 schema version、WorldFacts、entry/resolution history、soft graph paths、DeferredActivations 与 ObjectiveStates 重建 runtime；
- dedicated server manager + client mirror/read model，JIP 不靠历史 notify 重放；
- linked questline 编译 inlining、canonical tag/alias、source hash/stale compile 检测；
- reward 描述与 grant 解耦，LGF 继续要求 domain transaction + stable idempotency ledger。

### LGF 强化/拒绝

- 不把当前 Pawn/AIController 作为 durable quest owner；Player/Party/World/Shared scope 使用 stable owner key；
- 不允许客户端直接提交任意 OutcomeTag/Objective progress 作为真值；Authority 重验 phase/revision/objectives/conditions/holds/path；
- Quest Condition 必须纯读，消费物品/奖励/GAS side effect 走通过条件后的 Authority transaction；
- Signal/Observer catch-up 不能双算 progress，定义 QuestInstance+ObjectiveGuid+OriginatingEventID 的 dedupe；
- Save schema version 与 quest content/definition migration 分开；
- display/event/pin rename 不改变 stable GUID；语义拆分/合并必须显式 redirect/migration；
- Journal/Map/NPC marker/Dialog 统一从 Quest read model 派生，不各自维护隐藏进度；
- 外部 SimpleQuest API 经 adapter 接 LGF，避免把第三方 plugin 类型固化进 Foundation public ABI。

完整 LGF 合同见 [Quest / Objective 合同](quest-objective-contracts.md)。

## jinyuliao/GenericGraph 第十六轮映射（2026-09-14）

固定源码：`jinyuliao/GenericGraph@f9b8fe3de6bc2ef39ee771658ac4a8bf48c2e078`（MIT，2023-07-15）。默认分支最后明确迁移只到 UE5.1，README 仍为 UE4 描述，因此分类为 `Historical architecture sample`，不作为 LGF UE5.7/5.8 Editor API 权威。

### 可吸收机制

- authoring Graph / runtime data 分层；
- extensible Graph / Node / Edge；
- Schema 集中拖线规则 + Node domain hook；
- explicit Edge 作为有业务语义的连接对象；
- Editor graph rebuild/compile 到 runtime topology；
- cycle checking、auto-layout、custom editor 作为独立作者工具；
- Graph domain class 可决定允许的 node type/policy。

### LGF 必须强化

- 显式 `GraphDefinitionId / NodeStableId / EdgeStableId`；
- canonical node+edge records，incoming/outgoing/root/level 为 derived cache；
- parallel edge policy 与 stable choice/transition identity；
- per-domain `DomainSchema/TopologyPolicy`，不能只有 `bCanBeCyclical`；
- DAG 与 general graph/SCC 算法分开；rootless SCC 不得被 RootNodes 模型丢失；
- editor `CanCreateConnection` 只做早期反馈，compiler/cook/CI 全图复验；
- parse→validate→stage→atomic publish，失败保留 last-known-good 或 block save/cook；
- source/compiled fingerprint + revision 保护 stale artifact 和 live session；
- copy/paste 新 ID，rename/move 保 ID，split/merge/remove 走 redirect/tombstone/migration；
- Graph runtime 不依赖 UnrealEd/GraphEditor/Slate editor chain；
- UE5.7/5.8 editor 入口优先评估当前 `UAssetDefinition` / ToolMenus，legacy AssetTypeActions 仅兼容层；
- cached node registry、headless semantic compile、layout budget/cancel，避免右键菜单全局扫描与 O(N²) 无预算布局。

### 明确拒绝

- 因 770 stars 或 repo 未 archive 就称其为现代 UE5.7/5.8 模板；
- raw UObject pointer/array position 作为 Save/Network identity；
- `TMap<ChildNode, Edge>` 作为支持平行语义边的 canonical edge store；
- `RootNodes` 为空即视为空图；
- cycle-enabled graph 继续使用无 visited 的 tree traversal；
- SaveAsset 时先 clear 当前 runtime artifact 再就地 rebuild；
- 一个 `UniversalGraphRuntime` 接管 Quest/Dialogue/AI/GAS 的业务真值；
- Runtime Foundation 公共 ABI 暴露第三方 GenericGraph 类型。

完整 LGF 合同见 [Graph Authoring Foundation](graph-authoring-foundation.md)。
