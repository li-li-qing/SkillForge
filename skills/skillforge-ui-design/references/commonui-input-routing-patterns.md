# CommonUI / Enhanced Input：LocalPlayer、Layer 与输入所有权

用于 UE5.7+ CommonUI、CommonGame、Enhanced Input 与 GameplayMessageRouter 项目。重点不是复制某个样例的类名，而是明确 **LocalPlayer UI root、逻辑导航、输入上下文、UI Action、Gameplay Message** 的所有权与可逆生命周期。

## 1. 先做技术时效性判断

`XistGG/XistCommonGameSample@7e01e1fed344a741f80fa82b7161c86c494a410b` 明确绑定 UE5.7，并从 Lyra 5.7 提炼 CommonGame/CommonUI/EnhancedInput 组合。对目标 UE5.7，它可视为 Current-to-target；对 UE5.8+ 则属于 Stable-but-old，需要重新核对插件/API。

同时区分：

- CommonUI 核心 input routing / activatable widget / layer stack：当前 UE5.8 官方文档仍在维护，可作为 Current 机制；
- CommonUI 与 Enhanced Input 的直接集成：当前 UE5.8 官方文档仍保留 Experimental / shipping caution，采用前必须核对实际插件状态与目标平台；
- Xcgs 单机简化代码：只作为 UI/Input 机制证据，不是多人 Authority、GAS、JIP 证据；
- `ClearAllMappings()`、全局 `GetFirstPlayerController()`、blank blocker 等写法：按样例边界判断，不升级成通用生产模板。

## 2. Root Layout 属于 LocalPlayer，不属于 Pawn

完整 UI root 更接近：

`GameInstance UI Manager -> UI Policy -> LocalPlayer -> Root Layout -> GameplayTag Layers`

而不是：

`Pawn PossessedBy -> Create the whole HUD forever`

原因：

- Pawn 可以死亡、重生、骑乘、变形；LocalPlayer 仍是同一用户；
- Controller 可能替换或 Travel；Root Layout 需要可移出/重挂而不是把业务导航一起销毁；
- split-screen 下每个 LocalPlayer 必须有独立 root/context/focus；
- Dedicated Server 不应创建客户端 Root Layout。

如果项目已有独立 UINavigation（如 LGF），CommonUI Root Layout 只是 Presenter/Layer 容器；Route Stack、Back History 和 Instance identity 继续由 UINavigation 拥有。

## 3. Input Mode 只由真正的输入策略 owner 改

普通业务 Widget 默认不应在每次 Activate 时都：

- `SetInputMode`；
- 夺取全局 focus；
- 改鼠标 capture；
- 清空/重建全部 IMC。

更稳的规则：

- 普通内容页：默认不改变 input config；
- 顶层 Game/Menu/Modal route：声明 desired input policy；
- Router/Arbiter 根据当前最上层可交互 route 统一应用；
- 恢复时根据 stack identity 恢复前一个 policy，而不是 Widget 自己记一份“旧 input mode”。

CommonUI Activatable Widget 支持 optional input config；“支持”不等于“每个 Widget 必须使用”。

## 4. UI Action 与 binding 必须对称

UI Action / Enhanced Input binding 都是副作用：

`register -> save handle/source -> use -> unregister exact handle`

不要只按 Action 名称或 GameplayTag 猜应该移除哪一条 binding。

至少处理：

- Construct / Destruct；
- Activate / Deactivate；
- LocalPlayer / Controller teardown；
- async page load 后 owner 已变化；
- 同页面对象池复用/重复构造；
- modal 快速 push-pop。

如果 binding 只应在 Active 状态存在，优先把注册与 Active 生命周期对齐；如果用于全局 Back/MainMenu，则由更稳定的 HUD/root owner 持有。

## 5. Enhanced Input Mapping Context 是共享 LocalPlayer 资源

复杂项目不要复制教学样例中的 `ClearAllMappings()`。

一个 LocalPlayer 的 Mapping Context 可能同时来自：

- 基础 Gameplay；
- 当前 Avatar/载具；
- UI；
- accessibility；
- feature/plugin；
- debug/dev tools。

生产规则：

1. 每个 source 记录自己添加的 IMC；
2. teardown 只移除自己的 IMC；
3. priority 只表示同存 contexts 的解析优先级，不表示 ownership；
4. Avatar 切换只替换 Avatar-scoped context；
5. UI 顶层 generic IMC 与 Gameplay IMC 分域；
6. 明确 `bIgnoreAllPressedKeysUntilRelease` 等切换策略，避免切菜单时旧按键穿透。

## 6. InputAction -> GameplayTag 是稳定边界

DataAsset 将 InputAction 映射到 GameplayTag 的优点：

- C++ 不依赖资产名字；
- 输入资产可替换而业务语义 tag 保持稳定；
- UI、native command、GAS ability input 可以共享统一语义命名，但不能共享一个“业务 owner”。

要求：

- 一个 InputAction 的主语义映射唯一或冲突可诊断；
- tag 查找失败有明确日志；
- 高规模热路径按需要建立索引；
- feature/avatar 重绑时重建 source-owned binding；
- 不退化成 PlayerController 巨型 AbilityClass switch。

## 7. GameplayTag Layer 负责展示层级，不成为业务真值

推荐把 `UI.Layer.Game / GameMenu / Menu / Modal` 等 tag 映射到 ActivatableWidgetContainer。

Layer 处理：

- z-order / stack；
- focus path；
- input routing；
- transition；
- modal priority。

业务状态仍来自 canonical gameplay model。

### Transition input suspension

多 transition 并发时：

- `SuspendInput` 返回 token；
- 每次 completion 只 resume 自己的 token；
- teardown 要能清理遗留 token；
- 不用一个 bool 表示“全局是否 suspended”。

将 transition duration 固定为 0 是某些项目为了 gamepad focus 的 workaround，不是通用要求。

## 8. Modal 不默认靠“空白 Widget 遮层”实现

往低层 push blank widget 可以快速实现视觉/命中阻挡，但它只是简化样例策略。

生产优先级：

1. 统一 route/layer input policy；
2. modal priority / lower-layer suspension；
3. 精确 visibility / interaction state；
4. 最后才使用 blocker widget。

如果必须用 blocker：

- 保存 exact instance；
- nested modal 使用 stack/refcount；
- visual blocking 和 input blocking 分别定义；
- 关闭时恢复正确的前一层状态；
- 检查 screen reader/accessibility 与 hit-test 行为。

## 9. GameplayMessageRouter 是本地事件总线，不是网络层

Gameplay Message 适合：

`canonical gameplay state change -> typed message -> optional UI listener`

它不替代：

- replicated property / FastArray；
- Server RPC / Authority result；
- SaveGame；
- JIP snapshot；
- 业务事务日志。

UI 模式仍应：

1. 读取 initial snapshot；
2. 注册 typed message listener；
3. 收到 signal 后更新 projection 或重读 canonical state；
4. Destruct/owner change 时注销 listener。

只依赖 future message 会导致晚打开 UI 和 JIP 缺数据。

## 10. Soft UI class：冷路径与热路径分开

Root Layout 在 LocalPlayer 创建阶段一次性 `LoadSynchronous()` 与每次 hover/hotbar update 同步加载不是同一个风险等级。

生产判断：

- startup/cold path、已预加载且只发生一次：可以接受同步解析，但要测量；
- menu push 使用 streamed/async class：更适合可选页面；
- Tick、FastArray callback、列表逐项构建：禁止同步加载资产。

## 11. LocalPlayer / Controller / Pawn 三层 teardown

建议分层：

### LocalPlayer lifetime
- root layout；
- UI navigation/router；
- global UI input/action routing；
- player-specific accessibility/settings。

### Controller lifetime
- viewport/controller context；
- controller-specific focus/input device state；
- reconnect/travel reattach。

### Pawn/Avatar lifetime
- HUD projection source；
- avatar-scoped IMC；
- Pawn ability/equipment state；
- target/reticle/avatar-specific widgets。

Avatar teardown 不应清空整个 LocalPlayer UI/input 系统。

## 12. 验证矩阵

至少覆盖：

- keyboard / mouse / gamepad；
- controller replacement；
- death/repossess；
- travel；
- split-screen 2 LocalPlayers；
- nested modal；
- rapid push/pop；
- async page load owner 已变化；
- IMC feature enable/disable 顺序变化；
- UI close 后旧 action/message callback 不触发；
- late-open UI 有 initial state；
- Dedicated Server target 不引用 ClientOnly UI；
- UMG/CommonUI Presenter 切换时逻辑 Route identity 不变。
