# XistGG/XistCommonGameSample 蒸馏报告

固定快照：`XistGG/XistCommonGameSample@7e01e1fed344a741f80fa82b7161c86c494a410b`  
仓库：MIT；默认分支 `main`；项目 `.uproject` 明确 `EngineAssociation: 5.7`。  
研究目标：CommonUI / CommonGame / Enhanced Input / GameplayTag input routing / GameplayMessageRouter / LocalPlayer UI lifecycle。

## 1. 技术时效性分级

### 对 LGF 当前 UE5.7 目标

**Current-to-target**。

理由：

- 项目本身固定 UE5.7；
- 最新提交 2025-12-02；
- README 明确从 Lyra 5.7 refactor/simplify；
- CommonUI、Enhanced Input、CommonGame、GameplayMessageRouter 都属于当前 UE5 生态仍在使用的方向。

### 对最新 UE5.8+

**Stable-but-old**。

必须重新核对：

- CommonUI / Enhanced Input integration 的当前成熟度；
- CommonGame/CommonUser/GameplayMessageRouter 是否仍使用同一复制版本；
- ActivatableWidget API、PlayerMappable/Input Config 配置；
- Lyra 5.8 是否修改 layer/input policy。

Epic 当前 5.8 CommonUI 文档仍维护 Input Routing 和 Activatable Widget；同时“CommonUI with Enhanced Input”页面仍带 Experimental/shipping caution，所以不能因为 Xcgs 能运行就宣称该组合在所有发行平台完全无风险。

## 2. 项目自述边界非常重要

README 明确：

- 单机 only；
- 无 Character；
- Pawn 直接持配置，而 Lyra 有 PawnData；
- 所有输入显式 C++ binding；
- **没有 Lyra 的 Tag-to-Ability mapping**；
- 没有 UIExtension；
- 主要目的是把 CommonUI + Enhanced Input 配置变得容易理解。

因此它非常适合 UI/Input 教学，却**不可以**作为：

- multiplayer Authority；
- GAS；
- JIP；
- feature hot-unload；
- PlayerState/Pawn readiness；
- 复杂 Experience/GameFeature

的生产证据。

## 3. InputAction -> GameplayTag DataAsset

`UXcgsInputActionMap` 将 `UInputAction*` 映射到 GameplayTag。C++ 代码用 tag 找 action，不依赖 `IA_*` 资产名。

值得吸收：

- 业务语义从资产命名剥离；
- InputAction 可换，InputTag 保持稳定；
- 可扩展到 native command / UI / GAS ability input 的统一语义层。

LGF 已有更完整 Input/Ability contracts，因此只吸收“稳定 tag 边界”，不照搬 Xcgs 的手工 bind 列表。

## 4. Possession 中 Push HUD + IMC：一半可学，一半拒绝

`AXcgsPlayerPawn::PossessedBy()`：

- 向 `UI.Layer.Game` push HUD；
- 获取 EnhancedInputLocalPlayerSubsystem；
- `ClearAllMappings()`；
- 添加 Pawn 配置的所有 IMC。

在单机教学项目中简单直接。

### Production 吸收

- IMC 有明确 owner 生命周期；
- HUD/IMC 的 add/remove 必须对称；
- Input Mapping Context priority 显式；
- input binding handle 保存并精确解绑。

### Production 拒绝

`ClearAllMappings()` 不适用于复杂共享 LocalPlayer，因为可能误删：

- UI context；
- accessibility；
- vehicle/form context；
- gameplay feature context；
- debug context；
- 其他模块 context。

复杂项目必须 source-owned add/remove。

同理，Root HUD 不应永久归 Pawn ownership。完整 UI root 更适合 LocalPlayer；Pawn 只控制 avatar-scoped projection/content。

## 5. CommonGame UI Policy：LocalPlayer root lifecycle

复制自 Lyra 5.7 的 `UGameUIPolicy` 展示了更成熟的 owner：

- 每 LocalPlayer 一份 Root Layout；
- PlayerController set 时 remove/readd；
- LocalPlayer removed/destroyed 时精确 teardown；
- split-screen 可有多个 Root Layout；
- Primary/Secondary local player 有独立控制策略。

这比 sample Pawn 自己 Push HUD 更适合作为架构证据。

LGF 已经有每 LocalPlayer `ULGameplayUINavigationSubsystem`，所以最终映射应是：

`LGF UINavigation truth -> CommonUI Presenter Root Layout -> GameplayTag Layer`

不是把 CommonGame 再变成第二套导航系统。

## 6. Activatable Widget Input Config

Xcgs 自定义 `UXcgsActivatableWidget` 默认：

- auto activate；
- active/inactive visibility；
- **默认 bSupportsActivationFocus=false**；
- InputMode=Default 时不返回 Input Config。

这是值得保留的原则：

> 大多数内容 Widget 不应该每次激活就改变整个玩家的 input mode。

只有真正定义交互域的 Game/Menu/Modal root 才需要声明 input policy。

## 7. UI Action lifecycle

`UXcgsHUDLayout` 在 Construct 注册 MainMenu UI Action，保存 `MenuActionHandle`，Destruct 明确 `Unregister()`。

这是标准副作用生命周期：

`register -> handle -> unregister exact handle`

适合映射 LGF route/input arbiter。

## 8. Layer + Transition input suspension

Lyra/CommonGame `UPrimaryGameLayout`：

- GameplayTag -> ActivatableWidgetContainer；
- layer transition begin 时 `SuspendInputForPlayer()`；
- 保存 token；
- transition end 只 resume 对应 token。

值得吸收：**并发 transition 用 token/refcount，不用单 bool**。

源码把 transition duration 固定为 0 来规避 gamepad focus，是具体 workaround，不是通用规则。

## 9. Main Menu 的 blank blocker

Xcgs Menu 激活时，会往低层 Game / GameMenu 各 push 空白 Widget；关闭时 pop，用于“有效禁用”低层 UI。

评价：**Sample-specific workaround**。

它能演示 stack priority，但不适合作为所有 modal 的默认实现，因为：

- visual blocking 与 input blocking 混合；
- nested modal 需要额外 identity；
- accessibility / hit test 容易变隐式；
- 项目已有 UINavigation/Input Arbiter 时更应直接仲裁 lower layer。

LGF 应拒绝照搬空白 blocker，除非特定 Presenter 层确实需要它。

## 10. GameplayMessageRouter

`AXcgsGameState` pause/unpause 后广播 typed `FXcgsTimeMessage`。

值得吸收：

`canonical state changed -> typed message -> UI optional listener`

但 GameplayMessageRouter 是本地解耦，不是网络真值。Xcgs 本身是单机，还直接 `GetFirstPlayerController()`；这些都不能用于多人推论。

生产 UI 继续要求：

- initial snapshot；
- typed delta/message；
- listener unregister；
- Remote/JIP 由 replicated canonical state 收敛。

## 11. CommonGame Root Layout soft class load

`UGameUIPolicy::GetLayoutWidgetClass()` 使用 `LoadSynchronous()`。

这个调用位于 LocalPlayer root creation 的冷路径，风险低于 Tick/列表逐项加载，但仍应：

- 确认 Root Layout 是否已 startup/preload；
- profile 首次打开 hitch；
- 不把同步加载扩散到 hotbar/hover/list callback。

Xcgs HUD 打开 MainMenu 则使用 streamed push，这是更适合可选页面的路径。

## 12. CommonUI + Enhanced Input 的当前官方风险

Epic UE5.8 当前文档：

- CommonUI input routing 仍是当前体系；
- Activatable Widget input config 是 optional；
- CommonUI + Enhanced Input 页面仍标 Experimental / shipping caution；
- UI IMC 可以按 activatable widget 激活/停用，但官方也建议 generic UI IMC 与其他 top-level contexts 一起组织。

所以 SkillForge 不能写：

“CommonUI + Enhanced Input 已经无条件 production safe”。

正确写法：

“当前 UE5 中仍受支持并被持续文档化，但目标发行项目需核对当前版本、平台和插件成熟度。”

## 13. 对 LGF 的实际映射

| Xcgs / CommonGame | LGF |
|---|---|
| LocalPlayer Root Layout | CommonUI Presenter root；逻辑 Route 仍归 UINavigation |
| GameplayTag UI Layer | Presenter layer / route presentation mapping |
| UI Action handle | FoundationUIInput/UINavigation action source + exact teardown |
| InputAction -> InputTag | 保留稳定语义；Ability path 走现有 GAS input contract |
| Pawn IMC | 仅 Avatar-scoped contexts；不 ClearAllMappings |
| GameplayMessage | UI projection signal；不替代 Request/Authority/replication |
| Blank blocker | 默认拒绝；用现有 input/layer arbiter |
| CommonGame policy | 借鉴 LocalPlayer/Controller lifecycle，不复制第二套 route truth |

## 14. 最终采纳清单

### Current-to-target

- LocalPlayer root UI ownership；
- CommonUI GameplayTag layer；
- ActivatableWidget top-level input policy；
- UI Action exact handle lifecycle；
- source-owned Enhanced Input contexts；
- InputAction -> GameplayTag；
- typed GameplayMessage projection；
- async/streamed optional page push。

### Stable-but-old / verify on upgrade

- copied Lyra 5.7 CommonGame/CommonUser/GameplayMessageRouter exact API；
- CommonUI + Enhanced Input exact configuration；
- PlayerMappable/InputData details。

### Reject as general production template

- `ClearAllMappings()` for shared player subsystem；
- global `GetFirstPlayerController()` multiplayer ownership；
- whole Root HUD owned by Pawn lifetime；
- blank Widget as universal modal policy；
- future-message-only UI without initial snapshot；
- gameplay message as replication replacement。

## 15. 验证建议

LGF 实施时至少测试：

- UMG Presenter / CommonUI Presenter 切换；
- Controller replacement；
- Pawn death/repossess/vehicle/form swap；
- split-screen；
- menu + nested modal；
- rapid push/pop；
- feature-scoped IMC enable/disable；
- keyboard/gamepad focus restore；
- message listener teardown；
- Travel；
- Dedicated Server target；
- packaged build。

本轮只完成外部源码/文档蒸馏与 Skill 合同，不代表已在 LGF UE5.7 项目中完成上述运行验收。
