# LGF UI 平台

## 唯一逻辑路由与可替换表现

当前 `ULGameplayUINavigationSubsystem` 属于每个 LocalPlayer，拥有 Route Stack、Back History、Presentation 选择与 Input Arbiter。UMG 和 CommonUI 是 Presenter Provider；不能在两者内部再各造一套页面/返回真值。

| 模块/职责 | 不能混淆的边界 |
|---|---|
| UIContracts | 中立的数据合同，不承载具体客户端 Widget 真值 |
| UINavigation | 每 LocalPlayer 的逻辑路由、实例和唯一输入仲裁 |
| UMG/CommonUI Presenter | 实际呈现与完成回报，不另立导航所有者 |
| UIExtension | 非页面 HUD 内容，按扩展点挂载，不冒充页面栈 |
| WorldUIRuntime | 服务器可用的 World Source/Registry |
| WorldUI | 客户端摄像机、LOD、遮挡、预算和 Widget 表现 |
| FoundationUIInput | 本地输入适配；当前为 ClientOnly |

检查 `.uplugin` Module Type 和真实 Build.cs，不能在 Runtime 玩法模块 Public 引入 ClientOnly UI 来绕过分层。描述符启用 CommonUI 插件依赖，不等于 Dedicated Server 应执行客户端表现逻辑。WorldUI 处理世界空间 UI，并不是 WorldMap 系统。

## 打开、关闭与替换的结果

从当前头文件查真实公开入口。取材版本有 RequestOpenRoute、RequestCloseRoute、RequestBack、RequestPopToRoute、RequestReplaceRoute、RequestClearRoutes 及更新 Payload/InputPolicy 的 Request。

- 打开返回 Receipt，不保证 Presenter 已完成加载。按 RequestId 关联 `OnNavigationRequestCompleted` 与最终结果。
- Close 使用精确 InstanceId；过期 ID 不能后退去关闭另一个页面。
- Replace 在新 Presenter 就绪前保留旧表现；不能在请求刚提交时销毁旧页，留下空白或幽灵输入锁。
- 输入策略声明经 UINavigation 仲裁应用。不要让每个 Widget 自行 SetInputMode/抢焦点并各自记录旧状态。
- Route/Presentation Provider 的生产注册入口当前有仅 C++ 的部分；不能把公开 C++ 函数都描述为现成蓝图节点。

## UI 不更新时的检查顺序

确认当前 LocalPlayer/Controller → Route 注册与标签/Payload → Request Receipt → 选中的 Provider/Presentation → Ready/Failed 回报 → 精确 Route Instance → Widget 绑定和刷新。记录 RequestId/InstanceId、页面状态和拥有者，区分未注册、加载中、失败、旧实例和输入仲裁问题。

异步资源完成、PlayerController 替换和 Travel 后，旧 Provider 或 Widget 的结果不能污染新代次。按项目实际 Provider Handle、实例身份和注销合同处理，不只看 UObject 指针仍有效。

验证 UMG/CommonUI 所选路线、Back/Close/Replace、加载失败、过期 InstanceId、多 LocalPlayer、Controller 替换、Travel、HUD 与菜单共存、焦点与游戏输入恢复。Runtime/ClientOnly 依赖变化还需真实 Server 构建；学习阶段只记录待验证项。

当前 UIEditor 提供 `LGameplayUIMigration` Commandlet；它的用途、报告和局限见[验证与演进](validation-and-evolution.md)。扫描通过不能代替实际页面和网络运行。

## XistCommonGameSample / CommonGame 对照补充

UE5.7 `XistCommonGameSample` 提供了一个有价值的 CommonUI/Input 参照，但 README 明确是单机简化 Lyra。LGF 只吸收其可复用 UI 生命周期语义，不复制其简化 ownership。

- **Root UI owner**：完整 Root Layout 应跟随 LocalPlayer/Controller UI 生命周期；Pawn 只提供 Avatar-scoped HUD projection。当前 `ULGameplayUINavigationSubsystem` 仍是每 LocalPlayer 的唯一逻辑 route/back/input arbiter，CommonUI `PrimaryGameLayout` 只能作为 Presenter root/layer 实现。
- **IMC owner**：禁止在 LGF 复杂消费工程中用 `ClearAllMappings()` 作为 Pawn Possess/UnPossess 清理。FoundationUIInput、Gameplay、Avatar/Vehicle、Feature、Accessibility 等 context 必须 source-owned add/remove，teardown 只撤本 source。
- **Input policy**：普通页面默认不抢 input mode；只有顶层 route/modal 声明 Game/Menu/All policy，由 UINavigation/Input Arbiter 统一应用。Widget 自己不保存第二份“旧 input mode”。
- **UI action**：注册 Back/MainMenu 等 action 时保存 exact handle/source，Destruct/Deactivate/LocalPlayer teardown 对称注销，避免复用 Widget 后 ghost binding。
- **Layer transition**：并发 transition 使用 suspend token/refcount 成对恢复；不要用单 bool。
- **GameplayMessage**：只作为 typed presentation signal；不是 RPC、复制、JIP snapshot 或业务 truth。UI 仍需 initial snapshot + delta/message。
- **Modal**：不默认用 blank widget 遮低层；优先走现有 layer/input arbiter。若特定 Presenter 需要 blocker，必须保存 exact instance 并处理 nested modal。
- **多人边界**：样例中的 `GetFirstPlayerController()`、Pawn-owned HUD 与单机 pause 逻辑不作为 LGF 网络证据。

升级 UE5.8+ 时重新核对 CommonGame/CommonUser/GameplayMessageRouter 的来源与 CommonUI+Enhanced Input 插件成熟度；复制自 Lyra 5.7 的插件源码不能自动视为永远 Current。

## 抑制条件里的隐含假设会被批次推进模式推翻

制作台领取提示曾按“队列里还有 Pending/InProgress 条目 ⇒ 没有可领取产物”来抑制世界提示。这个蕴含只在**整批完成**语义下成立。

配方字段 `BatchProgressMode`（`ULCraftingRecipeDefinition`，默认 `WholeBatch`）改为 `SequentialPerUnit` 后，批次仍在推进与已有可领取产物**同时成立**：`GetAvailableCraftCount() = CompletedCraftCount - ClaimedCraftCount` 中途就大于 0，于是提示被一直压到整批结束才出现，表现为“做 5 个时前 4 个做完了却不提示领取”。

排查方法：把 UI 的抑制/显示条件与队列真值定义逐条对照，找出其中隐含的“状态 A ⇒ 数量 B”推断，再核对当前推进模式下该推断是否仍成立。同类风险适用于任何按“阶段”而非“数量”判定的提示。

另记：`SequentialPerUnit` 下批次总耗时为 `N × CraftDuration`（整批模式是共用一次计时），调整表现时长时不要把它当成不变量。
