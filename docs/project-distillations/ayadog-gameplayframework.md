# AyaDogGames/GameplayFramework 项目蒸馏：第四轮

检查日期：2026-09-14  
来源：`AyaDogGames/GameplayFramework`  
固定源码快照：`9379a85a0ff9d1b29dc22828ef3ed881b4635cf0`（main）  
许可证：Apache-2.0。

> 本轮目的不是让 LGF 依赖或复制 AyaDog 的 GameplayFramework，而是研究一个现代 UE Gameplay Framework 如何把 **GAS、PlayerState/Pawn 生命周期、Inventory、Equipment、Enhanced Input、CommonUI、UI projection、AI spawning、Save** 组合起来，并同时提炼其源码中的正确模式与需要拒绝的工程债。

## 1. 项目状态与证据边界

仓库 README 把项目描述为 UE 5.7 C++ Gameplay Framework；仓库根 `CLAUDE.md` 写 UE 5.8；`GameplayFramework.uplugin` 没有 `EngineVersion`。因此本轮不会在 Skill 中把“5.7”或“5.8”单独写成已经验证的工程事实，而是记录为**文档版本冲突**，真实目标版本需通过消费工程 `.uproject`、实际 UBT/Editor 或作者构建证据确认。

当前固定 commit 是主分支 `9379a85a...`，提交信息是合并 hotbar UI / loadout notifications。`.uplugin` 包含：

- `GameplayFramework` Runtime module；
- `Collectibles` Runtime module；
- 插件依赖 GameplayAbilities、EnhancedInput、CommonUI、ModelViewViewModel。

仓库没有提供一个能证明所有功能通过的自动化测试套件；存在 specs、Python/工程说明等开发资料，但本轮结论来自**源码静态审查**，没有宣称该 commit 已在我们环境完成 UBT、Editor PIE、Dedicated Server、JIP 或性能 benchmark。

## 2. 模块地图

| 模块 | 主要职责 | 本轮重点 |
|---|---|---|
| `DaPlayerState` | ASC、长期 AttributeSet、Inventory、Credits、Level、Save | persistent owner |
| `DaCharacter` | 当前 Avatar、ASC ActorInfo、HUD、Interaction | replaceable Pawn lifecycle |
| `AbilitySystem/DaAbilitySet` | DataAsset grant Abilities/GEs/Attributes | GrantedHandles 可逆副作用 |
| `AbilitySystem/DaAbilitySystemComponent` | GAS 输入、PawnData grant、AttributeSet lookup | handle bug、InputTag hot path |
| `DaInputConfig/DaInputComponent` | Enhanced Input Action -> GameplayTag | data-driven input |
| `Inventory/DaInventoryEntry` | FastArray item、GUID、PrimaryAssetId、StatTags | canonical item state |
| `Inventory/DaInventoryList` | FastArray wrapper | delta replication |
| `Inventory/DaInventoryComponent` | Authority CRUD、Use/Drop、Stats、Loadout、Save | RPC authorization、re-entry |
| `Equipment/DaEquipmentManagerComponent` | Pawn applied equipment、GAS grants、spawn actors | construct/publish、teardown/rebind |
| `UI/DaPrimaryGameLayout` | CommonUI tag layer stack | navigation/focus/input suspension |
| `UI/DaWidgetController` | ASC/Attribute -> UI adapter | event-driven projection |
| `Inventory/DaInventoryWidgetController` | FastArray -> transient item view-models | UI not truth |
| `UI/DaHotbarWidget` | Loadout + Equipment projection | shared domain command |
| `DaActorSpawnManager` | AI/Pickup spawn manager、EQS、Asset load | Director 分层与性能 |
| `DaSaveGameSubsystem` | slot save、world actor serialization | 教学式 save 边界 |

## 3. 核心架构：PlayerState 是长期玩家身份，Pawn 是当前 Avatar

这一项目最适合 LGF 的架构证据不是某个 UI，而是 PlayerState/Pawn 的生命周期分层。

`ADaPlayerState` 构造：

- `UDaAbilitySystemComponent`；
- `UDaInventoryComponent`；
- Character/Combat AttributeSet；
- Credits/Level 等长期值。

ASC 使用 Mixed replication，PlayerState NetUpdateFrequency 提高；Inventory 也跟 PlayerState 生命周期存在。

`ADaCharacter::InitAbilitySystem` 则把：

`OwnerActor = PlayerState`  
`AvatarActor = current Character`

传给 ASC。随后 PlayerState 初始化 PawnData/属性，当前 Pawn 再 `ApplyLoadout()`。

### 3.1 为什么这对 LGF 变身很重要

用户未来需求包括：

- 吸收 NPC 后变成任意 NPC；
- 变成树桩、车、灯等 Prop；
- 骑乘大量不同宠物/NPC；
- Pawn + Mover；
- GASP/PSS/PSD 按 Avatar 变化。

如果 ASC、Inventory、Loadout 都放在 Pawn：每次形态切换就会面对复制、Save、Ability 重新授予、旧 delegate、旧装备 Actor 和 UI 重新绑定问题。

稳定 owner 路线允许：

```text
Player identity (persistent)
├── ASC
├── Inventory
├── Loadout
├── Progression / Credits
└── stable item identity

Current Avatar (replaceable)
├── Pawn / Character / Vehicle / Prop
├── Mover / collision
├── Mesh / AnimInstance / GASP layer
├── current equipment presentation
└── avatar-specific bindings
```

这与 LGF 已有 Full Foundation 的方向一致，因此要**强化现有边界**，不是创建 DaPlayerState clone。

## 4. UnPossessed 顺序：先撤回旧 Avatar 副作用，再断链

`ADaCharacter::UnPossessed()` 在调用 `Super::UnPossessed()` 前：

1. `Equipment->UnequipAll()`；
2. `Equipment->ReleaseOwnerBindings()`；
3. 然后才让 Pawn 与 PlayerState/Controller 关系进入下一生命周期。

源码注释明确解释：装备能力实际上授予在 PlayerState ASC，如果旧 Pawn 没有先撤回，重生 Pawn `ApplyLoadout()` 会再次 grant，造成重复能力。

这是一条很强的生命周期规则：

> **Teardown source-owned side effects before losing the owner needed to revoke them.**

同理适用于：

- 武器 AbilitySet；
- Condition penalty GE；
- 动画/装备 delegate；
- 输入 mapping；
- Mover callback；
- Pawn-specific async load。

## 5. Compare-and-rebind：重 Possess 不是“BeginPlay 绑定一次”

`UDaEquipmentManagerComponent` 保存：

- `BoundInventory`；
- `BoundASC`；
- delegate handle。

`EnsureInventoryBinding` / `EnsureAbilityDecayBinding` 不是简单：

```cpp
if (!Bound) Bind();
```

而是：

```text
Resolve current dependency
if same -> no-op
if different -> unbind previous -> bind current -> store current
```

理由是同一个 Pawn 可能被另一个 Controller/PlayerState 重新 Possess。旧 ASC 可能活得比 Pawn 更久，如果不解绑，新玩家使用能力时可能继续修改上一位玩家的 Item Condition。

LGF 的变身、宠物骑乘、车辆 Possess、AI/玩家控制切换都应该采用同样的 compare-and-rebind contract。

## 6. AbilitySet：好的可逆模型

`UDaAbilitySet : UPrimaryDataAsset` 包含：

- GameplayAbility class + level + InputTag；
- GameplayEffect class + level；
- AttributeSet class。

`FDaAbilitySet_GrantedHandles` 保存：

- `FGameplayAbilitySpecHandle`；
- `FActiveGameplayEffectHandle`；
- granted AttributeSet references。

`GiveToAbilitySystem()` 只在 Authority grant，并把 InputTag 写进 spec dynamic source tags；`TakeFromAbilitySystem()` 精确回收。

这与前两轮 Obsidian 的“grant source owns revoke handles”互相印证。

## 7. AbilitySystemComponent 中发现的 copy-empty-handle bug

当前 commit 的 `UDaAbilitySystemComponent::InitAbilitiesWithPawnData()` 与 `GrantSet()` 存在一个重要顺序问题：

概念上是：

```cpp
FDaAbilitySet_GrantedHandles Handle;
OutGrantedAbilityHandlesArray.Add(Handle);
AbilitySet->GiveToAbilitySystem(this, &Handle);
```

`TArray::Add(Handle)` 拷贝的是当时的**空 Handle**；后续 `GiveToAbilitySystem()` 修改的是局部 `Handle`。因此 `ClearAbilitySets()` 后续遍历 `OutGrantedAbilityHandlesArray` 时，保存的 handle 可能没有真正被填充。

这不是 AbilitySet 模型错误，而是**registry 与实际被填对象不是同一份状态**。

### 7.1 正确模式

可选择：

```text
A. local handle -> Give -> Move into registry
B. construct stable registry entry -> Give directly into it
C. handle stored in business entry -> fully construct entry -> publish
```

条件是：最终 registry 保存的必须是被 `GiveToAbilitySystem()` 真正填过的那一份。

## 8. Equipment 给出了正确对照：construct fully -> publish once

`UDaEquipmentManagerComponent::Internal_EquipItem()` 的实现反而很成熟。

它先构建局部 `FDaAppliedEquipmentEntry NewEntry`：

1. ItemID / DefinitionID / SlotTag；
2. spawn equipment actors；
3. 解析 AbilitySet；
4. `GiveToAbilitySystem(..., &NewEntry.GrantedHandles, SourceObject)`；
5. 用真正的 AbilitySpecHandle 建 `AbilityToItemMap`；
6. 最后 `EquipmentList.Entries.Add(MoveTemp(NewEntry))`；
7. `MarkItemDirty`；
8. 刷新 Condition penalty；
9. re-locate 后 authority broadcast。

这就是本轮写回 Skill 的：

`construct fully -> publish once`

避免 listener 看到半初始化装备。

## 9. Unequip：snapshot -> broadcast -> re-locate -> teardown

`Internal_UnequipSlot()` 做了：

1. 找到 FastArray entry；
2. 拷贝 `Removed` snapshot；
3. **先广播** `HandleUnequipped(Removed)`；
4. 因为 listener 可能 re-enter，重新按 ItemID + SlotTag 查 index；
5. 从 canonical FastArray remove；
6. 清理 AbilityToItemMap；
7. 清 Condition penalty；
8. `GrantedHandles.TakeFromAbilitySystem()`；
9. Destroy spawned equipment actors。

这里“先 broadcast 再 teardown”不是普遍定律，而是它明确选择了一个事件合同：监听者在 OnUnequipped 中仍能读取活着的 SpawnedActor/Grant source。

真正可复用的是：

- 事件发生在 pre 还是 post state 要写清；
- delegate 可能 re-enter；
- 不跨 delegate 保存数组 reference/index；
- teardown 用 snapshot 中的 revoke handles。

## 10. Re-entry 被当成一等公民

AyaDog 多处源码主动处理了“调用一个扩展点后，世界可能变了”。

### UseItem

`Internal_UseItem()`：

- 先 snapshot Entry 和 ItemID；
- 发送 GameplayEvent；
- Ability 可能在事件中消费/移动/丢弃物品；
- 返回后按 ItemID re-find；
- 不继续信任原 SlotIndex/entry pointer。

### DropItem

同步 Load Pickup class 之后，源码专门再次按 ItemID 找当前 entry，因为 sync load 可能 pump loading/tick 执行任意代码。

### Equipment

Apply GE、spawn actor、delegate 都可能重入，因此 publish/broadcast 前重新找 entry。

这比单纯“避免悬空指针”更广：Gameplay Framework 中很多扩展点都应该被视为 transaction boundary。

## 11. Inventory FastArray：canonical entry 很紧凑

`FDaInventoryEntry : FFastArraySerializerItem` 主要字段：

- `FGuid ItemID`：跨 save/load 的实例身份；
- `FPrimaryAssetId ItemDefinitionID`；
- `SlotIndex`；
- StackCount / MaxStackCount；
- runtime Tags；
- AbilitySetID；
- `TArray<FDaTagStack> StatTags`。

相比 Obsidian 的“大 Item UObject”，这更接近 struct-first；相比 RockInventory，它没有独立 ItemData/SlotData、generation handle 和 optional ItemInstance，但作为简单 slot inventory 足够清楚。

LGF 不应因为这套更简单就降低自己已有复杂 Grid/Equipment 能力。

## 12. Canonical replicated data + disposable accelerator

Entry 有一个不复制、不序列化的：

`TMap<FGameplayTag, int32> StatCountMap`

但 canonical 数据仍是 `StatTags` array。

规则：

- Authority `SetStatCount` 同步维护 map；
- save load、RPC-carried copy、FastArray callback rebuild；
- `GetStatCount` 仍可 fallback scan；
- stale map 最坏只是慢，不会得到错误业务答案。

这是非常值得推广的 cache 设计：

> Cache should be rebuildable from truth; cache corruption/staleness should degrade speed before correctness.

可推广到：

- ItemId -> index；
- InputTag -> AbilitySpecHandle；
- Slot -> Item；
- UI ViewModel lookup。

## 13. FastArray Owner 指针要在 BeginPlay 前准备

Inventory/Equipment constructor 都设置：

`List.OwnerComponent = this`

注释指出首个 replication bunch 可能在 BeginPlay 前应用，FastArray callback 已经需要 OwnerComponent 去发布事件。

这是一个容易漏的网络生命周期细节：

- NotReplicated owner/backref 可以在 constructor 初始化；
- OnRep/FastArray callback 不能默认 BeginPlay 已执行；
- JIP/initial bunch 尤其要检查。

## 14. Move in-place 保持 FastArray identity

Inventory Move 对空目标 slot 时，不 remove/add entry，而是更新 Entry 的 SlotIndex，从而产生 change delta 并保留 FastArray identity。

这种做法适合 slot 是 entry 的 placement field 的模型。

RockInventory ItemData/SlotData 分离则让移动主要改变 Slot FastArray。两种都可，选择由数据模型决定，不应机械统一。

## 15. Loadout 是 intent，不是 applied state

`FDaLoadoutEntry` 只保存：

- `SlotTag`；
- `ItemID`。

它放在 PlayerState Inventory 侧，跨 Pawn 保存/复制。

Equipment FastArray 则表示当前 Pawn 真正已应用的：

- ItemID；
- DefinitionID；
- SlotTag；
- SpawnedActors；
- server-only GrantedHandles。

这使：

- consumable hotbar assignment 不需要“装备”；
- death/respawn loadout 留存；
- broken weapon 可以被临时卸下但 assignment 保留；
- repaired 后可再次激活；
- 当前 Avatar 不兼容时可以不 apply。

对 LGF 未来变身非常关键。

## 16. OnRep Loadout：不知道 delta 就不要假造 delta

`OnRep_Loadout()` 只是广播 parameterless `OnLoadoutChanged`。

源码注释解释：Authority mutation 时能知道哪个 slot 变了，但 client 的普通 RepNotify 只看到“数组已经变成新状态”；若不维护 shadow copy，发送一个 payload 可能让 server/client 事件语义不一致。

因此消费者重新读取 canonical loadout。

这是比“事件一定要带所有字段”更成熟的接口设计。

如果未来 loadout 很大、变更很频繁，可以升级 FastArray/diff；在此之前不需要伪造具体 delta。

## 17. 通用 Server_AddItem 是重大授权缺口

`UDaInventoryComponent::AddItem(ItemDefinitionID, StackCount, SlotHint)`：

- Authority 直接 Internal_AddItem；
- Client 直接发 `Server_AddItem`。

服务器验证：

- DefinitionID valid；
- StackCount > 0；
- Definition 可解析；
- Inventory capacity/stack rules。

但看不到：

- 这件物品来自哪个世界掉落；
- 是否购买；
- 是否有材料；
- 是否是任务奖励；
- 客户端为何有权获得任意 DefinitionId/Count。

因此通用 `AddItem` 不适合作为 owning client 的 public mutation RPC。

### 17.1 生产 API 应拆开

Client request：

```text
RequestLoot(WorldItemIdentity)
RequestBuy(ShopOfferIdentity)
RequestCraft(RecipeIdentity)
RequestClaimReward(RewardContext)
```

Authority 内部：

```text
GrantItem(ResolvedDefinition, ResolvedCount, Provenance)
```

客户端表达**意图/来源**，服务器决定最终 reward。

## 18. 通用 Item.Stat 写入也应 default-deny

项目已经意识到 Grade 是 provenance，因此 `IsClientWritableStat()` 把 Grade 列为 protected。

但当前长期模型是：

`Item.Stat` 父树总体可写，少数叶子黑名单。

如果 Condition 是 repair economy 的关键输入，客户端却可以通过 generic stat RPC 调高 Condition，就绕过 RepairItem 的收费流程。

未来再增加 Rarity/AffixPower/Binding 等字段也容易忘记黑名单。

生产规则应该倒过来：

> operation-specific default-deny

客户端不直接 `SetItemStat(Tag, Value)`；它调用 `RequestRepair`, `RequestSocket`, `RequestRenameCosmetic` 等被允许操作，Authority 决定哪些 stat 变化。

## 19. Delta request 优于 stale absolute

项目 `AddItemStat` 有一条正确规则：客户端发 `Delta`，服务器读取自己最新的当前值，再 read-modify-write。

因为 Proxy 可能落后一帧，若客户端算：

`NewCondition = LocalCondition - 1`

再发 absolute，两条并发更新可能覆盖。

这条可以推广到：

- charge；
- ammo；
- stack consumption；
- counter；

但最终仍要 Authority 验证“客户端是否有权发这个 delta”。

## 20. Bounding untrusted collection growth

Inventory cpp 对客户端可驱动数据设了：

- `MaxStatTagsPerEntry = 32`；
- `MaxLoadoutEntries = 16`。

这是很好的防御：即使一个 RPC 逻辑允许某类数据变化，也不能让恶意客户端无限扩大 replicated array。

LGF 对 custom metadata、socket、hotbar、favorites 等用户驱动集合也要有上限。

## 21. Condition acquisition：先初始化，再 publish

创建 condition-enabled item 时，代码不先 AddEntry 再调用两个 stat mutation，而是在局部 NewEntry 上先写：

- Grade；
- full Condition。

再 `InventoryList.AddEntry(NewEntry)`。

理由：如果先发布默认 0 Condition，listener 会短暂看到一件刚掉落的装备是 Broken，然后后续两个 changed event 才修正。

这是 `construct fully -> publish once` 的又一个实例。

## 22. Repair：经济操作带补偿

RepairItem：

1. Authority 计算缺失 Condition；
2. 服务器按 Grade/Config 计算价格；
3. 校验 Credits；
4. 扣钱；
5. 写 Condition；
6. 如果 stat write 意外失败，Credits refund。

这是小型 transaction 思维：跨两个 authoritative state mutation 时，至少有补偿，不让玩家“付钱但没修”。

LGF 更复杂交易继续使用 transaction/reservation/rollback 规则。

## 23. Full-stack drop 保留 Item identity；partial stack 产生新 identity

Drop 完整 stack 时，World Pickup 保存原 `FDaInventoryEntry` snapshot；重新拾取走 `RestoreEntry`，保留：

- ItemID；
- StatTags；
- Tags；
- AbilitySet override；
- stack state。

partial stack 则原 entry 留在 inventory，因此地面那一份未来获取新 ItemID。

这是很清楚的 identity 规则。

`ADaItemActor` 还用 `bPickedUp` / `bHasDroppedSnapshot` 防同帧 double pickup / snapshot 二次消费，避免 clone。

## 24. Dropped snapshot 是一次性能力，不应 fallback 成免费新品

当前 `ADaItemActor::AddToInventory` 如果 dropped snapshot restore 失败，会日志后 fallback `AddItem(ItemDefinitionID)`。

这对“库存满等正常失败”可能产生语义风险：一个本该保持身份的一次性实例 restore 失败后，改成新实例就改变 provenance/随机 state。

LGF 更严格：

- dropped unique instance restore 失败应保持 world item/返回明确失败；
- 是否允许转换成新实例必须是明确设计，不做通用 fallback；
- snapshot 使用后原子失效；
- 多玩家竞争由 Authority single-consume/claim 处理。

## 25. 同步加载仍然遍布 Gameplay hot path

当前项目多个 runtime 路径有：

- Definition `TryLoad()`；
- Drop PickupActorClass `LoadSynchronous()`；
- DisplayMesh `LoadSynchronous()`；
- Equipment Actor class `LoadSynchronous()`；
- AbilitySet `TryLoad/LoadSynchronous()`；
- hotbar resolve definition `TryLoad()`。

源码部分位置已经意识到同步 load 会 re-enter，因此之后 re-find ItemID，这是很好的防御；但性能上 LGF 仍不采用 sync fallback 作为主路径。

PrimaryAsset preload/bundle/async transaction 才是生产方向。

## 26. Input：Action -> DataAsset -> InputTag -> GAS

`UDaInputConfig` 将 InputAction 与 GameplayTag 配对；`UDaInputComponent` 把 Action 的 Started/Triggered/Completed 绑定到 Controller handler，并携带 tag；ASC 从 AbilitySpec DynamicSpecSourceTags 匹配 InputTag。

优点：

- 不按 AbilityClass 硬编码 key；
- PawnData/AbilitySet 可组合；
- 不同角色可换配置；
- UI 显示也可以围绕 tag 描述 input。

## 27. Input 热路径：每次线性扫描全部 ActivatableAbilities

当前 ASC 的 Pressed/Held/Released 都遍历 `GetActivatableAbilities()`，对每个 spec 检查 `DynamicSpecSourceTags.HasTagExact(InputTag)`。

对 10~30 个能力很可能足够简单。

但用户的 ARPG 长期可能有：

- 技能；
- 装备授予；
- 被动；
- 形态；
- Buff 临时 ability；
- 宠物/载具切换；

如果达到 150~300 spec，并且 Held 每帧触发，应该 profile。

达到阈值后可维护：

`InputTag -> TArray<FGameplayAbilitySpecHandle>`

grant/remove/tag change 同步更新，或从 spec list rebuild。它只是 lookup accelerator，不取代 GAS 激活真值。

## 28. CommonUI：Tag Layer Stack 是导航层，不是 Gameplay 层

`UDaPrimaryGameLayout`：

- `TMap<FGameplayTag, UCommonActivatableWidgetContainerBase>` Layers；
- `PushWidgetToLayerStack`；
- transition 时 suspend/resume input token。

这与 Lyra 思路一致。

可吸收：

- `UI.Layer.*` 做 layer identity；
- root layout 负责 stack/focus；
- 业务状态仍在 controller/view-model；
- 多个 suspend 需要 token 配对。

项目将 transition duration 设为 0 是为规避其 gamepad focus 问题，**不是通用最佳实践**。

## 29. WidgetController：Attribute model / display metadata / view 分开

`UDaBaseAttributeSet` 维护：

`GameplayTag -> static FGameplayAttribute getter`

`UDaWidgetController`：

- 根据 SetIdentifierTag 找 AttributeSet；
- 给每个 Attribute 绑定 GAS value-change delegate；
- 从 `UDaAttributeInfo` 解析 UI metadata；
- 广播 `FDaAttributeData`。

可以理解为：

```text
AttributeSet = gameplay model
AttributeInfo DataAsset = display metadata
WidgetController = adapter
Widget = view
```

这比每个 HUD Widget 自己找 ASC/属性/图标更干净。

## 30. AttributeSet Identifier 要防歧义

ASC `GetAttributeSetForTag` 使用 `MatchesTag`，如果两个 spawned AttributeSet Identifier 处于重叠父子 tag 关系，返回哪一个可能依赖容器顺序。

如果 Tag 表达“唯一身份”，LGF 应：

- exact match；或
- startup/editor validation 保证没有重叠；或
- 返回 multiple/ambiguous error。

Parent tag matching 适合分类，不适合静默唯一解析。

## 31. Inventory ViewModel 是 disposable projection

`UDaInventoryItemBase` 明确写成 transient client-side UI view-model：

- 从 FastArray entry + Definition 创建；
- 不复制；
- 不保存 authoritative gameplay state；
- entry changed 时重新生成；
- 展示 condition、grade、stack、icon、equip flags。

这很好地解决“Blueprint 旧 UI 需要 UObject”而不把 canonical inventory 重新改成 UObject-per-item。

规则：

> UI UObject 可以每个可见 item 一个；Gameplay canonical item 不需要因此每个都 UObject。

## 32. InventoryWidgetController：Initial snapshot + delta event

Controller：

- Initialize 时绑定 Inventory；
- 初始 rebuild；
- 监听 Add/Remove/Change；
- 维护 ViewModel 数组；
- Use/Drop 仍调用 domain API。

这样 UI 不每帧轮询整个 Inventory。

## 33. Hotbar：事件驱动，低频 timer 只解决 dependency replacement

`UDaHotbarWidget`：

- Inventory loadout/entry events 驱动 refresh；
- Equipment events 驱动 refresh；
- 0.25 秒 timer 的目的只是 `EnsureBindings()` 检查 PlayerState/Pawn 是否换了；
- timer 不是业务数据 refresh source。

这是一个重要区分：

低频 resolver 可以做 lifecycle fallback，但不能被误解成“UI 应每 0.25 秒轮询全部 gameplay state”。

## 34. Mouse 与 keyboard 使用 same domain command

Hotbar `ActivateSlot()` 调：

`UDaEquipmentManagerComponent::ActivateItemSlotForPawn(Pawn, SlotTag)`

QuickSlot GameplayAbility 也调用同一个 domain decision。

内部根据 Item Definition 决定：

- equippable -> equip/unequip toggle；
- otherwise -> Inventory UseItem。

因此鼠标与键盘不会各自漂移出一套业务规则。

这条已写入 UI Skill：`same domain command`。

## 35. Client optimistic bool 不是成功结果

Equipment/Inventory public API 在客户端经常：

```text
send Server RPC
return true
```

源码注释自己明确提醒这是 optimistic return。

UI 不能根据这个 `true` 永久显示“装备成功”。最终状态应来自：

- FastArray/RepNotify；
- Client Result；
- request/transaction confirmation。

## 36. AI Spawn Manager：正确分层的雏形

`UDaAISpawnManager`：

1. timer；
2. count alive bots；
3. DifficultyCurve / max count；
4. EQS location；
5. DataTable select PawnData ID；
6. AssetManager LoadPrimaryAsset；
7. callback Spawn Actor；
8. init abilities。

这里已经有：

- spatial query 与 asset load 分离；
- PrimaryAssetId；
- async load；
- Authority/GameMode 语义。

## 37. AI Director 当前不适合大规模照搬

问题：

### 37.1 周期性 TActorRange

每 2 秒遍历所有 `ADaAICharacter` 统计 alive。少量 AI 没问题；数百 AI、多区域、多 Director 时应该用 spawn/death/register 事件维护 count/registry。

### 37.2 DataTable metadata 未真正使用

`FMonsterInfoRow` 有：

- Weight；
- SpawnCost；
- KillReward。

但当前选择是均匀 `RandRange` row index；Weight/SpawnCost 没进入 selection/budget。

### 37.3 并发 reserve

如果多个 EQS/load request 同时发起，它们都可能在旧的 alive count 下认为容量有空位。生产 Director 应在 async 前 reserve population/budget，在回调失败时 refund。

### 37.4 callback generation

异步 callback 应带 wave/request generation，返回后确认当前 level/phase/director 仍有效。

## 38. Spawn Director 推荐四层

LGF/其他 UE 项目可抽象：

```text
Population/Budget
    ↓
Selection metadata (weight/cost/type/level)
    ↓
Spatial query (EQS/ZoneGraph/Nav)
    ↓
Realization (async asset load + spawn)
```

每层单独 trace 与测试。

## 39. Save：只吸收“长期玩家状态保存”证据

`ADaPlayerState::SavePlayerState` 会保存：

- Credits/Level；
- Pawn transform（如果 alive）；
- Inventory entries；
- Loadout assignment。

这再次印证 loadout/inventory 属于长期 player identity。

## 40. Save subsystem 当前仍是教学/单机边界

`UDaSaveGameSubsystem` 当前：

- 同步 `LoadGameFromSlot/SaveGameToSlot`；
- `WriteSaveGame` 中遍历全部 Actor；
- `ActorName` 作为保存匹配身份；
- Load 时每 Actor 遍历 SavedActors；
- PlayerState loop 有 `break // single player only at this point`。

因此不能把它当成 LGF multiplayer/save production reference。

SkillForge 已有更严格规则：

- stable GUID/business identity；
- schema migration；
- save participant registry；
- dirty snapshot；
- async I/O；
- Authority owns online truth。

## 41. 资源加载：好架构也会有热路径债务

这个项目 PrimaryAsset/DataAsset 架构不错，但 gameplay runtime 仍有大量 sync fallback。说明：

> 使用 AssetManager 并不自动等于资源生命周期已经异步化。

审查时必须看**调用现场**，不是看类型是不是 `TSoftObjectPtr`。

LGF 继续保持：

- equip/drop/use/input/UI callback 热路径不 sync load；
- preload 或 Pending async transaction；
- async result 校验 owner/avatar/item/request generation。

## 42. 性能与内存观察

优点：

- 多数 Actor/Component Tick 关闭；
- Inventory FastArray 是 struct canonical state；
- UI UObject 只在 ViewModel 层；
- Delegate 驱动 UI；
- PrimaryAssetId 代替直接硬 class 依赖；
- local map 做 stat acceleration。

风险/需要 profile：

- ASC InputTag 每输入扫描全部 specs；
- FindEntryByItemID 多处线性遍历；
- Equipment slot/item lookup 线性；
- Hotbar refresh 每次创建多个 transient VM（只有 4 slot，通常可接受）；
- AI timer TActorRange；
- runtime sync load；
- Save world O(N×M) 匹配。

不要因为有 `TMap` 就自动比数组快；small N 时连续数组/linear scan 常常更好。按实际规模决定。

## 43. 对 LGF 的最终映射

| 项目机制 | LGF 吸收 | LGF 拒绝/收紧 |
|---|---|---|
| PlayerState ASC/Inventory/Loadout | 稳定 owner / Full Foundation | 不复制 DaPlayerState |
| Pawn Equipment | applied Avatar projection | 不把长期 truth 搬回 Pawn |
| AbilitySet GrantedHandles | source-owned revoke | 修 copy-empty-handle |
| FastArray GUID Inventory | stable identity + delta | 不降低现有复杂 Grid 能力 |
| StatCountMap | rebuildable accelerator | cache 不成为 truth |
| Loadout intent | assignment/applied 分离 | 不把 hotbar=equipment |
| InputTag -> GAS | data driven | 大 spec 按 profile 索引 |
| CommonUI Layer | navigation/focus | 不新建第二套 LGF UI stack |
| WidgetController | read-only projection | UI 不改 gameplay truth |
| generic client AddItem | 无 | operation-specific default-deny |
| generic stat setter | 无 | capability/operation-specific |
| sync TryLoad/LoadSync | 无 | preload/async |
| AI Spawn Manager | budget/select/spatial/load 分层 | 不用 TActorRange + uniform random 做大规模 Director |
| Save player inventory/loadout | long-lived owner evidence | 不迁移 ActorName whole-world save |

## 44. 对用户未来变身/骑乘功能的直接意义

### NPC 吸收变身

玩家 stable owner 不变，切换 Avatar。Inventory/ASC/loadout 保持；旧 Pawn applied equipment/动画/移动 teardown；新 NPC shape 根据 Skeleton/Socket/能力兼容规则 reapply。

### Prop 形态

Prop Pawn 可能不支持 humanoid equipment。Loadout assignment 保留，applied equipment 暂停；退出 Prop 后恢复。不要为了 Prop 建第二个 Inventory。

### 宠物/载具骑乘

如果控制权真的切换到 pet/vehicle Pawn，Owner/Avatar ActorInfo、输入、镜头和 Mover 随 Pawn 变；player progression/inventory/loadout 仍由稳定 owner 持有。Pet 自己的独立 inventory/abilities 若存在，则是另一条明确 identity，不与玩家长期状态混写。

### 异步动画/外观

每次 shape switch 递增 AvatarGeneration；异步 Mesh/AnimSet/PSS/PoseSearch/Attachment 完成时同时核对：

- stable player identity；
- 当前 Avatar；
- AvatarGeneration；
- request id。

旧形态回调晚到直接丢弃。

## 45. 明确拒绝/不直接迁移项

1. AbilitySet handles 先 copy empty 后 fill local；
2. 客户端通用 `Server_AddItem` 授予；
3. Item.Stat 父树默认可客户端写；
4. Equipment/Drop/Definition runtime sync load；
5. 以客户端 optimistic bool 当最终结果；
6. InputTag 热路径无限线性扩展而无 profile；
7. 大规模 AI 每 timer 全世界扫描；
8. DataTable Weight/SpawnCost 不参与 selection 却宣称 budget director；
9. whole-world ActorName save；
10. 把项目 transition duration=0 当 CommonUI 通用规则；
11. 把 UE5.7/5.8 文档冲突擅自选一边；
12. 整套复制 GameplayFramework 到 LGF 形成第二套 Foundation。

## 46. 写回 SkillForge

本轮正式写回：

- `skillforge-ue-cpp`：新增 Gameplay Framework 组合与生命周期参考；
- `skillforge-ui-design`：新增 Gameplay UI projection / CommonUI layer / same domain command 参考；
- `skillforge-lgf`：External Project Patterns 增加 AyaDog 映射，并强化 Avatar persistent/applied contract；
- 新增 CPP-18..23；
- 新增 LGF-19..20；
- 新增 UI-04；
- 项目蒸馏索引加入本报告。

## 47. 当前未验证范围

- 未在本地 clone/build AyaDog 项目；
- 未运行 UE5.7/5.8 UBT，因此版本冲突未由构建消解；
- 未运行 Multiplayer PIE/Dedicated Server；
- 未实测 `Server_AddItem`/generic stat RPC 的攻击路径，只基于公开调用面和服务端授权代码做安全审查；
- 未 profile 300 Ability specs 的 InputTag scan；
- 未 profile 500 AI 的 TActorRange/EQS；
- 未验证 Save 的多人扩展；
- 未复制任何 Apache-2.0 源码实现进 LGF；SkillForge 只记录可复用模式、风险和迁移边界。

## 48. 本轮最终结论

AyaDogGames/GameplayFramework 的最大价值不是“另一个 UE 框架”，而是提供了很清楚的**组合证据**：

`Persistent PlayerState truth`  
`-> replaceable Pawn projection`  
`-> source-owned reversible GAS grants`  
`-> stable ItemID/FastArray`  
`-> Loadout intent`  
`-> Pawn applied Equipment`  
`-> Controller/ViewModel UI projection`  
`-> CommonUI navigation layer`

同时它也证明了一个重要事实：即使整体架构不错，generic mutation RPC、handle registry 顺序、sync load、AI scaling、Save identity 仍可能是局部风险。

因此 SkillForge 后续面对优秀 GitHub 项目时继续坚持：**蒸馏机制，不崇拜项目；吸收边界，不复制工程债。**
