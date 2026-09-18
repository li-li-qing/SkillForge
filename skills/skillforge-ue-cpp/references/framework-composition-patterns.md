# UE Gameplay Framework 组合与生命周期模式

用于把 GAS、Inventory、Equipment、Enhanced Input、CommonUI、AI Director 等子系统组合成长期可维护的 Gameplay Framework。这里关注的是**数据所有权、可逆副作用、网络授权、重入边界和热路径**；具体项目仍以自己的源码和 UE 版本为准。

## 1. Persistent owner 与 replaceable avatar

玩家身份和当前世界 Avatar 不是同一个生命周期。

默认先按两层建模：

- **persistent owner**：PlayerState、Player Agent 或项目定义的稳定 Authority 对象。适合 ASC、长期 Attribute、Inventory、Loadout、Credits、Progression、stable ItemId、跨死亡/换 Pawn 仍存在的状态。
- **replaceable avatar**：Pawn/Character/Vehicle/Transform form。适合 Mover/CMC、碰撞、Mesh、AnimInstance、当前武器 Actor、Pawn Component、局部输入/镜头、当前 applied equipment/presentation。

换 Pawn、死亡重生、骑乘、吸收 NPC 或重 Possess 时，不要把长期状态复制到新 Pawn 形成第二份真值。推荐生命周期：

`Prepare old avatar -> revoke avatar-sourced grants -> unbind old dependencies -> detach/destroy presentation -> switch ActorInfo/avatar -> initialize new movement/animation -> compare-and-rebind -> re-apply compatible loadout/presentation`

关键点：

1. 在 `UnPossessed` 或 EndPlay 或等价切换点，**先**撤销旧 Pawn 来源的 GrantedHandles、Timer、Delegate、Input、装备 Actor，再让 PlayerState/ASC 链接失效。
2. 新 Pawn 只有在 `InitAbilityActorInfo`、核心组件和需要的资产都 ready 后才 reapply；不能因为 ASC UObject 仍存在就认为新 Avatar 已就绪。
3. 绑定使用 **compare-and-rebind**：解析到的 Inventory/ASC 与已绑定对象不同，就先从旧对象解绑再绑定新对象。一次绑定永久有效只适用于生命周期严格同构的对象。
4. Loadout assignment 与 applied equipment 分离。某 ItemId 在当前形态不兼容时可以继续保留 assignment，但不强行生成错误 Mesh/Ability；回到兼容形态再应用。
5. AI、无 PlayerState 的 Pawn、临时 Spectator/Vehicle 需要明确 fallback owner；不要把玩家路径硬编码成所有 Pawn 的唯一模型。

网络回归至少覆盖 Listen Host、Remote AutonomousProxy、SimulatedProxy、JIP、死亡重生、同 Pawn 换 Controller、不同 PlayerState 重 Possess、切换中途取消和旧异步回调晚到。

## 2. AbilitySet：grant source 必须拥有真实 revoke handles

AbilitySet/Equipment/Perk/Item 等动态来源授予 GAS 内容时，来源必须能精确撤销自己授予的 Ability、GameplayEffect、AttributeSet。

推荐：

```text
SourceEntry
  -> GrantedAbilitySpecHandles
  -> ActiveGameplayEffectHandles
  -> GrantedAttributeSets / other reversible handles
```

Authority 用这些精确 handle 撤销，不通过 AbilityClass 或 GameplayTag 全局扫描，因为同一能力可能同时来自职业、技能树、Buff 和多件装备。

### copy-empty-handle 反例

下面的顺序有逻辑缺陷：

```cpp
FGrantedHandles Handles;
Registry.Add(Handles);      // 复制的是空值
AbilitySet->Give(ASC, &Handles); // 填的是另一个局部对象
```

最终 Registry 可能仍保存空 handles。正确选择之一是：

- 先 `Give` 填完局部 handles，再 Move/Copy 到 registry；或
- 先取得一个**地址稳定、不会因容器扩容失效**的 registry entry，再直接填该 entry；或
- 把 handles 存在即将 publish 的业务 Entry 里，完整构建后一起提交。

因此规则不是“必须先 Add 还是先 Give”，而是：**registry 里持有的必须是被实际填充的那一份最终状态**。

撤销后清掉 registry/handle；重复 Clear 必须幂等。验证 partial grant failure、重复 Grant/Clear、Avatar 替换、装备 swap、Listen Host 本地刷新和 Remote proxy。

## 3. construct fully -> publish once

复杂 replicated entry 在创建时如果需要：

- 生成 stable identity；
- 解析 Definition；
- spawn SourceObject/presentation actor；
- grant AbilitySet；
- 填 GrantedHandles；
- 建反向索引；
- 初始化 condition/随机状态；

优先先在**局部未发布值**中完成，然后一次写入 canonical FastArray/容器并 Dirty/广播。

这样监听者不会先看到“装备已存在但 Ability 还没给”“Condition 默认 0 一帧后才补满”等半状态。

如果某一步必须异步，则不要把半成品直接当正常 entry 发布。使用 Pending/Loading transaction、稳定 request generation 和明确完成/失败状态。

## 4. Delegate / GameplayEvent / Asset load 都是可重入边界

调用以下任意内容后，都要假设当前 `TArray`、Map、Actor、Pawn 或业务状态可能已经改变：

- Dynamic/native delegate；
- GameplayEvent / GameplayMessage；
- Ability activate/apply effect；
- Blueprint event；
- `SpawnActor` 或 FinishSpawning；
- 同步或异步 Asset load；
- UI/外部 callback；
- 任意可扩展 virtual/interface call。

不要跨这些边界长期持有 `TArray` 元素引用、裸 pointer 或 SlotIndex 作为身份。

推荐：

1. 调用前复制后续必要字段或记录 stable ItemId / generation handle；
2. 执行可重入调用；
3. 返回后按稳定身份 **re-locate**；
4. 若对象已移除/版本变化，按 stale/conflict/idempotent contract 结束，不继续使用旧引用。

### 删除/卸装事件顺序

事件语义要写清楚是 pre-mutation 还是 post-mutation。

如果 `OnUnequipped` 的消费者需要在回调中读取仍存活的 SpawnedActor/Ability source，可采用：

`snapshot -> broadcast live-removal intent -> re-locate/remove canonical entry -> revoke handles -> destroy presentation`

如果消费者只需要最终结果，则可以先 commit 再广播 post-state。两种都成立，但 Host 和 Remote FastArray callback 必须语义一致。

## 5. 客户端 mutation RPC：operation-specific default-deny

`UFUNCTION(Server, Reliable)` 只决定调用在哪里执行，不证明调用者有权执行该业务。

高风险反模式：

```text
Server_AddItem(AnyDefinitionId, AnyCount)
Server_SetItemStat(ItemId, AnyItemStatTag, AnyValue)
Server_SetCredits(...)
```

即使函数内部有 `HasAuthority()`，一个拥有该 Actor/Component 的客户端仍可能提交任意候选参数。

生产接口拆成两层：

- **Authority internal mutation**：真正 `GrantItem`, `ApplyReward`, `SetProvenance`, `CommitCraft`, `RepairItem`，只允许服务器可信流程调用。
- **Client request**：表达具体意图，如 `RequestLoot(WorldItemId)`, `RequestBuy(ShopId, OfferId)`, `RequestRepair(ItemId, Points)`, `RequestCraft(RecipeId)`。Authority 从自己的数据解析结果，而不是让客户端直接指定最终奖励。

### Stat 写权限

对客户端 stat 更新采用默认拒绝：

- provenance：Grade/Rarity/Affix seed/ItemLevel；
- economy：Value/price/currency/repair cost inputs；
- durability/condition；
- binding/ownership；
- server combat roll；

都只能由对应 Authority operation 修改。

不要用“允许整个 `Item.Stat`，只黑名单 Grade”作为长期安全模型。新增一个叶节点时，黑名单很容易忘记更新。

如果确实有玩家可调 state（例如 cosmetic slider），建立明确 allowlist/capability，并限制范围、频率、payload size。

### Delta 胜过客户端 absolute

计数型并发状态如果客户端意图是“增加 1”或“消耗 N”，请求发送 delta/operation，服务器对自己的最新值 read-modify-write。不要让客户端基于可能过期的 Proxy 值算出 absolute 再提交，避免 lost update。

### optimistic return 不是业务结果

客户端函数在发出 Server RPC 后立即返回 `true`，只能解释为“本地接受了提交”。最终成功来自：

- replicated authoritative state；
- transaction/result RPC；
- request id 对应的明确确认。

UI 不能因为 optimistic `true` 就扣钱、播放永久装备成功或关闭失败提示。

## 6. FastArray canonical data + disposable accelerator

大量 replicated entry 可以只复制 canonical 数据；查询加速结构保持 NotReplicated/Transient 并可随时重建。

例如：

```text
replicated: TArray<Tag, Count>
local cache: TMap<Tag, Count>
```

合同：

- Authority mutation 同步维护 cache；
- save load、RPC copy、FastArray Add/Change 后 rebuild；
- cache miss/stale 最多导致慢路径扫描，不能改变正确答案；
- JIP 只靠 canonical snapshot 可重建；
- 不复制 cache 来制造第二份一致性问题。

这适合 per-item stats、ItemId->index、slot lookup、InputTag index 等。

## 7. InputAction -> InputTag -> AbilitySpec

Enhanced Input 与 GAS 的数据驱动链可以是：

`InputAction -> InputConfig/DataAsset -> GameplayTag -> AbilitySpec DynamicSourceTag -> GAS activation`

优点是 Character/PlayerController 不需要一个按 AbilityClass 分支的巨型 switch；输入重绑和不同 PawnData 也更容易替换。

### 热路径规模化

几十个 Spec 时遍历 `GetActivatableAbilities()` 可能足够简单。不要无基准优化。

当 Pressed/Held/Released 高频发生且 Spec 达到数百，维护本地查询缓存：

`InputTag -> AbilitySpecHandle(s)`

缓存必须：

- 在 grant/remove/clear 后更新；
- DynamicSpecSourceTags 改变时更新；
- handle 失效后清理；
- 多 Ability 共用 Tag 时定义顺序/优先级/阻断语义；
- 可从 ASC canonical spec list 重建。

缓存只缩小候选集合；`AbilitySpecInputPressed/Released`、PredictionKey、CanActivate、cost/cooldown 等仍由 GAS 真值处理。

## 8. Loadout intent 与 applied equipment

Loadout 是“玩家希望这个 slot 指向哪个 stable ItemId”，Applied Equipment 是“当前 Avatar 真正应用了什么”。两者不应合并。

这样可以支持：

- 玩家死亡时 Loadout 留在 PlayerState；
- 新 Pawn Possess 后重建装备；
- 消耗品 hotbar 只有 assignment，不需要常驻 equipment entry；
- 变成不兼容形态时 assignment 保留但 applied state 暂停；
- Item 被丢弃/消耗后 Authority 清理引用它的 assignment；
- Save 保存 stable assignment，不保存 transient SpawnedActor/AbilitySpecHandle。

OnRep 若无法可靠给出“具体哪个 slot 变了”，参数为空的 `OnLoadoutChanged` + 消费者重读 canonical state 比构造不一致的伪 delta 更安全。大型 loadout 可以进一步用 FastArray/版本化 diff，但仍保持事件语义一致。

## 9. UI：canonical gameplay state 之外只做 projection

Gameplay Framework 中的 WidgetController/ViewModel 是**一次性可重建的表现投影**：

- FastArray、ASC、PlayerState 等是 canonical truth；
- Controller 绑定 canonical delegate，生成 UMG 需要的轻量 snapshot；
- Widget 不写第二份 Inventory/Equipment/Condition 真值；
- ViewModel 丢失时可由当前 canonical state 重建；
- Server/Host 本地 mutation 与 Remote replication 都驱动同一种 presentation event。

鼠标点击和键盘/手柄 Ability 应调用 **same domain command**，例如同一个 `ActivateQuickSlot(SlotTag)` 决定 Use/Equip/Toggle，而不是 Widget 和 GameplayAbility 各自实现一套规则。

CommonUI 的 layer stack、焦点和 input suspension 属于导航/布局职责，不混入 Inventory/GAS 业务状态。

更详细 UI 合同见 `skillforge-ui-design` 的 Gameplay UI 投影参考。

## 10. Authority Spawn Director：预算、选择、空间、实现分层

大规模 AI/拾取物生成不要把“每 N 秒扫全世界 + 均匀随机 DataTable + Spawn”当最终 Director。

推荐四层：

1. **population/budget**：Authority 维护当前活体、区域上限、点数/波次预算。优先由 spawn/death/register 事件更新 registry；规模大时避免周期性 `TActorRange` 全世界计数。
2. **selection**：轻量 metadata 保存 Weight、SpawnCost、Level、Category、PrimaryAssetId。按预算/权重选 ID；高频选择预计算候选/累计权重或按 profile 缓存。
3. **spatial query**：EQS/ZoneGraph/Nav 只决定候选位置与空间约束，不同时承担经济预算真值。
4. **realization**：AssetManager async load -> Authority callback revalidate -> Spawn -> register。

异步前 reserve budget；回调带 wave/request generation，重验 World、Director、capacity、location 和当前 phase。Load/Spawn 失败 refund。并发多个 EQS/load 请求不能各自看到同一个旧空位后一起超出上限。

Trace 建议记录：alive count、reserved budget、EQS duration/results、asset wait、spawn batch、reject/refund reason。

## 11. 资源加载仍是 transaction dependency

Definition 很小也不代表 gameplay hot path 可以随意 `TryLoad()`/`LoadSynchronous()`。Inventory Add/Use/Drop、Equipment equip、hotbar click、FastArray callback、AI 高频选择都应优先消费 resident data。

依赖未就绪时：

- 预热 PrimaryAsset bundle/registry；或
- 返回 AssetNotReady/Pending；或
- 启动带 Owner/Item/Avatar/Request generation 的 async transaction。

同步加载可能 pump/tick 引发可重入，所以即使暂时保留 legacy sync fallback，也必须按第 4 节在返回后重新解析稳定身份，不能继续信任旧数组引用。

## 12. 迁移评审清单

从一个完整 Gameplay Framework 学习时至少回答：

- 哪些数据跨 Pawn/死亡长期存在？谁拥有？
- 哪些状态只是当前 Avatar 的 applied projection？
- Ability/Effect/Attribute 谁授予、谁保存 revoke handles？
- Client RPC 是 request 还是最终 mutation API？默认 allow 还是 default-deny？
- delegate/Blueprint/asset load 后是否继续持有数组引用？
- Input 规模是否需要 tag->spec cache？
- UI 是否读 canonical state，而不是自建 truth？
- AI Director 是否分离预算、selection、spatial query、realization？
- Save 是否保存稳定 identity，而不是 transient handle/Actor pointer？
- Host/Remote/JIP/Respawn/Repossess 是否共享同一业务语义？

## 13. LocalPlayer UI 与 Enhanced Input 的 source ownership

复杂 UE 项目中，完整 UI root 和共享 input context 都不应默认归 Pawn 生命周期。

- Root Layout / UI Policy 以 LocalPlayer 为主身份；Controller replacement/Travel 做 reattach，Pawn replacement 只更新 Avatar projection。
- Enhanced Input Mapping Context 是 LocalPlayer 共享资源；模块/feature/avatar/UI 各自保存自己添加的 source/handle，teardown 只移除自己。`ClearAllMappings()` 仅适合高度受控样例，不是通用生产清理。
- Mapping Context priority 只是解析优先级，不是 ownership 或回滚机制。
- UI Action/EnhancedInput binding 和 delegate 一样遵守 register -> handle -> unregister exact handle。
- GameplayMessageRouter 适合作为 typed local event bus；Remote/JIP 仍依赖 canonical replicated state。
