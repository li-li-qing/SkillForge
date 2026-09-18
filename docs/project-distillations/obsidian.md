# Obsidian 项目蒸馏：第二轮

检查日期：2026-09-14  
来源：`intrxx/Obsidian`  
固定源码快照：`bbe55b5b4c0ae4761ab57868398aca1c3b6b8c0b`（main）  
许可证：GPL-3.0。

> 本轮学习架构和工程模式，不复制 Obsidian 源码实现到 SkillForge/LGF。GPL-3.0 对直接复制、修改和分发代码有传染性义务；如果目标工程不是 GPL 兼容授权，只能独立重写思想与接口，不得把第三方实现当模板粘贴。

## 1. 项目定位与证据强度

Obsidian 是 UE5 Multiplayer Action RPG 项目，核心方向是 GAS、程序化物品、Grid Inventory、Equipment、Player Stash、Save、AI、UI。README 明确说明大量引用资产被 Git 忽略，因此公开仓库不保证可以直接编译；本轮结论来自源码与项目文档静态审查，不宣称构建或 PIE 已通过。

相比第一轮 ActionRoguelike，Obsidian 对 LGF 更直接的价值在于：**ARPG 物品生命周期如何从掉落生成一路连接到 Inventory -> Equipment/Stash -> GAS -> Save**。

## 2. 模块地图

| 模块 | 观察到的职责 | 蒸馏价值 |
|---|---|---|
| `InventoryItems/Inventory` | Grid Inventory、FastArray、stack、占格、本地索引 | 大集合复制与派生缓存 |
| `InventoryItems/Equipment` | 装备槽、双手武器、weapon swap、spawned equipment、GAS grants | 装备事务、可逆 AbilitySet |
| `InventoryItems/PlayerStash` | Grid/Slots Tab、共享/个人仓库、FastArray | 同一 Item 模型、多容器视图 |
| `InventoryItems/Fragments` | Stack/Appearance/Affix/Equippable/Usable | Definition/Fragment 组合 |
| `InventoryItems/ItemAffixes` | affix、AbilitySet、GrantedHandles | 随机词缀到 GAS 的桥 |
| `InventoryItems/ItemDrop` | Treasure、rarity、affix roll、异步数据加载 | 数据预热与 Authority 随机生成 |
| `AbilitySystem` | ASC、Ability、Task、Attribute、Execution/MMC | 现成 GAS，而非自制 Action 替代 |
| `Game/Save` | Master/Hero/SharedStash Save | 按生命周期/所有权分域 |
| `UI` | Inventory WidgetController、Inventory/Equipment/Stash widgets | 消息驱动投影，不把 UI 当真值 |
| `Characters/Player` | PlayerController 持有 Inventory/Equipment/Stash，ASC 从 PlayerState 获取 | Pawn 重生后的长期状态边界 |

## 3. Item Definition / Instance / Fragment

### 3.1 好的分层

`UObsidianInventoryItemDefinition` 是 `Const, Abstract` UObject，保存 ItemCategory、BaseType、默认 Rarity 和 Instanced ItemFragments。Definition 是设计配置。

`UObsidianInventoryItemInstance` 是玩家真正拥有的 UObject，支持 networking，拥有 ItemUniqueID、等级、当前容器位置、随机 Affix、Stack、鉴定、装备/使用状态等。

Fragment 类似物品能力组件：Appearance、Stacks、Affixes、Equippable、Usable 等在创建 Instance 时初始化相应状态。这种组合比“ItemBase 派生 30 层 Weapon/Sword/UniqueSword”更适合 ARPG。

### 3.2 需要进一步收紧的边界

当前 Instance 复制字段很多，包含 `FText` DisplayName/Description、Texture、StaticMesh、GridSpan、Category/BaseType 等大量可能来自 Definition 的静态数据，源码也留有 TODO 询问哪些字段真的需要复制。

LGF 应采用更严格的网络模型：

`DefinitionId/Class -> local immutable config`  
`ItemId + generated runtime delta -> replicated/persisted instance state`

同一基础剑的图标、描述、基础 Mesh 不应每件都复制。随机词缀值、耐久、绑定、鉴定、当前堆叠和位置才是实例状态。

对于数千物品，进一步判断是否每件都值得 UObject。纯数据型条目可以 FastArray struct；复杂行为/子对象复制才升级 UObject。

## 4. Inventory：FastArray 真值 + 本地占格/索引

`FObsidianInventoryEntry : FFastArraySerializerItem` 保存 ItemInstance、StackCount、GridLocation；`LastObservedCount` 标记 NotReplicated。

Serializer 保存：

- replicated Entries；
- non-replicated OwnerComponent；
- `GridLocationToItemMap`；
- `InventoryStateMap`。

Authority Add/Remove/stack change 会 `MarkItemDirty`/`MarkArrayDirty`；Proxy 在 `PostReplicatedAdd/Change/PreReplicatedRemove` 重建 Grid map、占格并发布 inventory change message。

这是非常好的原则：**网络只复制业务条目，查询结构和 UI 投影从条目恢复。** JIP 不应该依赖服务器把缓存 Map 一起复制。

### 4.1 数据结构可继续优化

当前 Grid occupancy 是 `TMap<FIntPoint,bool>`。12x5 小网格完全可以接受，但如果未来做大仓库、多个页签或大量模拟，flat array/bitset/row mask 可能更紧凑、缓存友好。技能不能机械要求替换，必须先测规模与热点。

## 5. ItemInstance 作为 replicated subobject

InventoryComponent 同时支持两种子对象复制路径：

- registered subobject list：Item 进入容器后 `AddReplicatedSubObject`，移除后 `RemoveReplicatedSubObject`；
- legacy/fallback `ReplicateSubobjects`：遍历 FastArray Entries 并 `Channel->ReplicateSubobject`。

`ReadyForReplication()` 会把组件开始复制之前已经存在的 ItemInstance 补注册。这是比“NewObject + UPROPERTY(Replicated)”完整得多的生命周期。

LGF 迁移时必须核对当前 UE5.7/Iris 设置，不能把两套路径无脑并存。FastArray 条目引用和 Item UObject 自己的属性复制也不是一回事；FastArray callback 做表现时要考虑子对象属性到达顺序和有效性。

## 6. Authority 边界

Inventory/Equipment 的变更函数不仅有 `BlueprintAuthorityOnly`，实现里还普遍检查 `GetOwner()->HasAuthority()`，并额外检查 `Inventory_BlockActions` / `Equipment_BlockActions` GameplayTag。这是值得保留的防御层：**编辑器元数据不等于运行时权限检查。**

Inventory/Equipment/Stash 组件挂在 PlayerController，意味着 Remote client 有自然的 owned network route；ASC 则从 PlayerState 取得，使长期 GAS 状态不必绑死当前 Pawn。

### 6.1 RPC 参数仍需重新授权

PlayerController 里也存在 `ServerSpawnItemFromSpawner(AObsidianItemSpawner*)`，实现直接调用传入 Actor 的 SpawnItem。即使 RPC host 是玩家拥有的 Controller，服务端仍需把 `ItemSpawner*` 当候选：检查距离、Spawner 是否允许该玩家、是否已消费、冷却/次数、世界/会话、请求防重放。

结论：**正确 RPC owner 只是必要条件，不是 Authorization。**

## 7. Equipment + GAS：最值得 LGF 吸收的一条链

`FObsidianEquipmentEntry` 除了复制 ItemInstance/Slot，还保存 `NotReplicated FObsidianAffixAbilitySet_GrantedHandles`。装备时根据 Item Affix 向 ASC 授予 GameplayAbility/GameplayEffect，并把 `FGameplayAbilitySpecHandle`、`FActiveGameplayEffectHandle` 记录到该装备条目；卸装和 weapon swap out 使用这些 handle 精确撤销。

这比按 Tag/Class 全局搜索后删除安全：同一技能可能来自技能树、职业默认、Buff 或多件装备。**谁授予，谁持有撤销句柄。**

建议 LGF 进一步把 SourceObject 指向 ItemInstance/Equipment source，形成：

`ItemId -> EquipmentEntry -> GrantedHandles -> ASC`

断线重连、Load、换 Avatar、死亡/重生时都按该来源重建/清理。

## 8. 明确反例：Affix 循环中的 LoadSynchronous

装备条目 `AddItemAffixesToOwner()` 会遍历 Affix，并对每个 `SoftAbilitySetToApply` 调 `LoadSynchronous()`。这在小项目里可能工作，但与生产热路径要求冲突：批量换装、登录恢复、仓库切换或大量装备检查都可能产生同步阻塞。

Obsidian 其实已经有更好的另一半：`UObsidianItemDataLoaderSubsystem` 从 DeveloperSettings 取 Soft refs，用 AssetManager `RequestAsyncLoad` 预载 ItemDataConfig、DefaultAffixAbilitySet 和 common item definitions。

SkillForge 采纳后应统一成：

`Asset configuration -> async preload/cache -> ready gate -> Authority equip/drop transaction`

唯一词缀 AbilitySet 也必须进 preload contract。运行时没驻留时返回 AssetNotReady/Pending 或异步继续，而不是在 Affix for-loop 同步加载。

## 9. Item Drop：随机真值和预加载

ItemDropComponent 自己关闭 Tick，BeginPlay 异步加载 AdditionalTreasureLists；DataLoaderSubsystem 预热 common ItemDefinitions，这是正确方向。

但 `ConstructItemToDrop` 如果 Soft ItemDefinition 没预载成功，会 fallback `LoadSynchronous()`。这说明当前 preload coverage 仍非硬合同。LGF 应把 fallback 当开发告警而不是正常运行路径。

更重要的是，`DropItems` 展示的函数体没有自身 Authority guard，却使用 `FMath::RandRange` 决定 Treasure/rarity/affix。即使当前调用方只在服务器执行，生产 API 也应在公共入口内守住权限。

联网 ARPG 的掉落真值只能由 Authority 产生：Definition、ItemId、level、rarity、stack、affix ids/values、requirements。客户端不重新 roll。需要测试可复现时使用显式 `FRandomStream`/seed；存档保存最终结果，seed 只作为审计辅助。

## 10. Equipment Transaction 与双手武器

装备替换会处理 sister slot：双手武器需要腾出另一手，并把原装备放回 Inventory。这暴露出 ARPG 容器操作最重要的问题——跨系统事务。

生产版本不能依赖多次 `checkf` 假设每一步都成功。应形成：

1. Authority 验证 Item 身份、当前容器和目标 Slot；
2. 预检查 requirements、另一手冲突、Inventory capacity、ActionLock；
3. reserve 所有目标资源/空间；
4. 执行 container move；
5. 撤销旧 GrantedHandles / 授予新 handles；
6. spawn/destroy equipment presentation；
7. 提交 FastArray dirty 与结果；
8. 任一步失败 rollback 到一致快照。

这对于未来 LGF 的换装、双持、宠物装备、变身装备都比“逐个函数成功就继续”更稳。

## 11. Stash：同一 Item 真值，多种 Tab 视图

Player Stash 继续使用 FastArray 条目。StashEntry 保存 ItemInstance、Stack、ItemPosition、OwningStashTab；Serializer 维护 `StashTabsMap` 本地索引。

Tab 配置支持：

- Grid Tab；
- Slots Tab；
- 特定类别/基础类型限制；
- slot stack limit；
- personal/shared item 查询。

可迁移思想是：**普通背包、装备、仓库、专用货币页可以共用 Item identity 与 transaction 规则，只让容器策略不同。** 不要为每种 UI 页复制一套 Item class 或保存格式。

## 12. GameplayMessage：复制回调到 UI 的投影层

Inventory/Equipment FastArray 的 Add/Change/Remove 最后用 `UGameplayMessageSubsystem` 广播 typed message，包含 ItemInstance、位置/Slot、delta 和 ChangeType。

这是一条很健康的 UI 链：

`Authority truth -> replicated delta/local mutation -> GameplayMessage -> WidgetController/ViewModel -> Widget`

Widget 不需要 Tick 扫 Inventory，也不直接改 FastArray。Local Host 的直接 mutation 与 Remote callback 要保证每端只得到一次等价表现事件；JIP 初始 Add 是 snapshot 建立还是用户提示，也应区分。

## 13. Save：Master / Hero / Shared Stash 分域

Obsidian 没把所有内容塞进一个 USaveGame：

- Master Save：角色索引、SaveId、名字、职业、等级摘要、online/offline；
- Hero Save：InitializationData 与 GameplayData 分开，后者保存等级、位置、通用属性、Inventory、Equipment、Personal Stash；
- Shared Stash Save：共享物品与 stash tab metadata；
- SaveGameSubsystem：持有不同 Save 对象并提供 async/sync 请求。

这个分域非常值得 LGF 学习，因为不同数据的 owner、加载时机、修改频率不同。

LGF 还应补上 Obsidian 代码中未明显体现的生产要求：SchemaVersion、迁移、原子写、稳定 Item/Definition ID、dirty tracking、失败恢复、在线数据 Authority。`ULocalPlayerSaveGame` 不意味着 Remote client 可以在 P2P 中成为共享仓库真值作者。

## 14. 性能与缓存观察

值得保留：

- Inventory/Equipment/Drop Component 都关闭 Tick；
- FastArray 发送 delta，UI 消费 message；
- ItemData Loader 用异步 AssetManager；
- 本地 Map/占格避免每次从 UI 重新推导；
- common definitions 预热。

需要谨慎：

- `ParallelFor` 只是收集 SoftObjectPath，目前源码也写明需要重新比较性能；没有 profile 前不要当通用规则；
- ItemInstance 复制大量展示字段会扩大带宽和冷数据工作集；
- TMap Grid/Slot 索引适合当前规模，不自动适合万级数据；
- 多个线性 `for Entries` 搜索应按真实 hot path 决定是否建立 ItemId -> index cache；
- 缓存必须定义 FastArray swap/remove 后的失效与重建。

## 15. 对 LGF 的直接映射

| Obsidian 模式 | LGF 应吸收 | LGF 应收紧/拒绝 |
|---|---|---|
| Definition + Instance + Fragment | 静态配置/运行实例/组合能力分层 | 不按实例复制静态展示数据 |
| Inventory/Equipment/Stash FastArray | Authority entries + callbacks + local indexes | 不复制 cache，不让 Proxy Dirty 真值 |
| Item UObject subobject | ReadyForReplication、Add/Remove subobject 完整生命周期 | 不为纯值型物品强制 UObject |
| PlayerController 容器 + PlayerState ASC | owned request route 与 Pawn-independent state | Controller RPC 参数仍要 Authority revalidate |
| GrantedHandles | exact grant/revoke、SourceObject、swap cleanup | 不按 Tag/Class 猜着删 GAS 内容 |
| ItemDataLoader async preload | AssetManager/ready gate/cache | 不在 Affix/equip/drop loop `LoadSynchronous` |
| procedural loot | server-generated final result | client reroll、未 guard 的公共掉落入口 |
| split Save domains | Master/Hero/SharedStash 生命周期分区 | LocalPlayer save 不等于 online Authority |
| GameplayMessage | delta -> presentation 解耦 | message/UI 不成为业务真值 |

## 16. 本轮写入 SkillForge 的内容

- `skillforge-ue-cpp`：新增 `arpg-item-inventory-patterns.md`，覆盖物品三层模型、FastArray + derived cache、replicated Item UObject、跨容器事务、GrantedHandles、异步资源、Authority loot、Save 分域、GameplayMessage、性能。
- `skillforge-lgf`：在外部项目迁移参考中加入 Obsidian 专节，明确 GPL-3.0、LGF 现有 Inventory/GAS/Request 的适配边界。
- 新增 CPP-08..11 与 LGF-17 行为样本，覆盖过度复制、跨容器事务、装备 GAS/同步加载、P2P 存档/随机掉落。

## 17. 当前未验证范围

- 没有构建公开 Obsidian 仓库；README 已说明依赖忽略资产，不能把源码审查写成构建通过。
- 没有运行其 packaged release、多人 PIE、Dedicated Server、JIP、断线重连。
- 没有基准测量 TMap Grid、ParallelFor、ItemInstance 复制带宽或大仓库规模。
- 没有对仓库全部 AI/Animation/Combat 源码逐行审查；这些主题留给更专门的项目或后续 Obsidian 补轮。
