# Gameplay UI：Layer、Controller/ViewModel 与 Domain Command

用于 UE Gameplay UI 使用 CommonUI/UMG、GAS、FastArray、PlayerState/Pawn 等状态时的职责划分。目标是让导航、数据投影、输入和 Authority 结果各有唯一边界。

## 1. Layer stack 只管理导航与焦点

CommonUI 或项目自己的主布局可以用 `GameplayTag -> ActivatableWidgetContainer` 注册层，例如 HUD/Menu/Modal/Overlay。

Layer 负责：

- Push/Pop/transition；
- focus/return path；
- gamepad/keyboard navigation；
- input suspension token；
- modal stacking/z-order。

业务 Widget 不直接维护第二份“当前菜单栈”。多个 async transition 同时存在时，Suspend/Resume token 或引用计数必须成对，不能一个完成就错误恢复所有输入。

某项目为了规避 gamepad focus 把 transition duration 设成 0，只是该项目策略；不要把它写成 CommonUI 普遍要求。

## 2. WidgetController / ViewModel 是只读 projection

FastArray、ASC、PlayerState、EquipmentComponent 等是 canonical gameplay truth。UI 层可以构建 disposable projection：

`canonical state -> controller/view-model -> widget`

ViewModel 可以保存：

- DisplayName/Icon；
- stack count；
- condition fraction/band；
- selected/equipped flags；
- 已格式化显示值。

但不能成为 Authority state。它被销毁、换 Pawn 或重开菜单后，应该能只靠 canonical snapshot 重建。

旧 Blueprint 依赖 UObject item view-model 时，可以临时从 FastArray entry 按需创建 transient UObject 兼容，不要因此把 gameplay inventory 重新改回每件物品 UObject。

## 3. Initial snapshot + delta event

UI 绑定通常分两步：

1. 读取一次 initial snapshot；
2. 订阅 Add/Change/Remove、Attribute delegate、LoadoutChanged 等事件。

不要只等 future event，否则打开界面时已有数据为空；也不要只轮询 snapshot，否则高频 Tick 浪费并增加焦点/排序抖动。

FastArray callback 到达时如果关联 UObject/Actor 引用还未解析，允许暂缺并在后续 related delta/changed event 重新解析，而不是把 null 永久缓存。

Listen Host 的 Authority local mutation要主动触发与 Remote callback 等价的 UI projection；同时防止 Host 双播。

## 4. Pawn / PlayerState 替换：compare-and-rebind

HUD、Hotbar、Equipment panel 可能同时依赖：

- PlayerState 上的 Inventory/ASC/Loadout；
- 当前 Pawn 上的 Equipment/Avatar 状态。

当死亡、重生、车辆、spectate、变形导致对象替换时，UI 要：

1. 解析当前 dependency；
2. 与 Bound object 比较；
3. 若不同，从旧对象解除 delegate；
4. 绑定新对象；
5. 重新读完整 snapshot；
6. 恢复当前用户选择/焦点中仍有效的部分。

优先使用 possess/player-state-ready 等明确事件。若框架缺少可靠通知，可用低频 resolver 做兼容兜底；它只检测“对象是否换了”，不是业务刷新频率。不要因为某示例 0.25 秒 resolver 就让所有 UI 每 0.25 秒重建业务内容，更不能每帧扫描。

## 5. same domain command：鼠标和按键共享业务决策

快捷栏常见错误是：

- GameplayAbility 判断某 slot 是 Consumable 就 Use；
- Widget click 另写一份判断并直接 Equip；
- 两条路径半年后规则漂移。

将决定放在 domain command，例如：

`ActivateItemSlot(Pawn, SlotTag)`

内部统一读取 Loadout assignment 和 Item Definition，再决定 Use/Equip/Toggle。Keyboard/Gamepad Input Ability 和 Widget click 都调用 **same domain command**。

Widget 只负责“用户点击 Slot 2”，不负责定义最终 gameplay side effect。

## 6. optimistic request 与 UI feedback

客户端 `RequestEquip()`/`UseItem()` 调 Server RPC 后立即返回 true，通常只是提交成功，不是业务成功。

UI 区分：

- submitted/pending；
- Authority accepted；
- rejected（slot invalid、item no longer held、cost insufficient、asset not ready）；
- replicated final state。

永久勾选、扣钱动画、成功音效以 result/replicated truth 为准。可以立即做短暂 input feedback，但要能 rollback/reconcile。

## 7. 事件顺序与 live resources

如果 `OnUnequipped` UI 需要读取即将销毁的 SpawnedActor/图标来源，事件合同可定义为 pre-teardown；消费者不能假定所有“Removed”事件都是 post-state。

UI 设计/接口文档要说明：

- 事件触发时 canonical entry 是否仍存在；
- presentation Actor 是否仍有效；
- 下一帧是否保证销毁；
- consumer 是否应重新 query canonical state。

最安全的 UI 通常把 event 当“需要刷新”的 signal，再从 canonical state 重读，而不是把 event payload 长期保存成 truth。

## 8. UI 热路径与资源

禁止在 Tick、FastArray callback、每个 hotbar refresh 中 `LoadSynchronous` 图标/WidgetClass/音效。使用：

- Asset bundle/preload；
- async image/resource；
- ViewModel cache with explicit invalidation；
- placeholder + loading state。

如果每次 entry change 都“全量重建 4 个 hotbar slot”，规模小是合理的。是否改成单 slot delta 要按实际 slot 数和 profiling，而不是为了理论 O(1) 复杂化 UI。

## 9. 验证矩阵

至少覆盖：

- 初次打开已有数据；
- Add/Change/Remove；
- Host 本地 mutation 与 Remote replication；
- JIP；
- Pawn death/respawn/repossess；
- PlayerState 替换；
- mouse + keyboard + gamepad；
- modal push/pop/focus restore；
- Authority reject；
- asset not ready；
- 快速连续点击/重复 request；
- UI close/destruct 后旧 delegate 不再触发。
