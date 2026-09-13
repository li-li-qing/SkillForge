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
