---
name: skillforge-ui-design
description: "设计、调整或检查游戏 HUD、工具窗口、配置面板的信息结构、布局、交互状态、缩放、焦点与输入层级。Use for UI layout, interaction states, responsive tool panels and HUD design across existing frameworks. 纯业务算法、无界面任务和仅制作图片不触发；已有界面故障可与排障技能组合。"
---

# UI 设计与布局

从用户当前任务、真实内容与现有框架出发，给出可实现、可验证的布局和交互方案。

## 确认界面条件

- 确定是战斗 HUD、编辑工作台还是配置流程，用户最常执行的动作、必须随时可见的信息、允许打断的时机。
- 读取已有控件树、布局代码、截图或设计资料，确认框架、父容器、窗口客户区、缩放策略、输入设备与组件职责。没有材料时标明假设，不把通用草图写成项目实测结论。
- 沿用现有 MFC、UMG、Slate、游戏插件 UI 或其他框架。新面板复用已有样式和组件；只有当前框架确实无法满足已确认需求时，才讨论替代方案。

## 设计步骤

1. 按任务优先级分区，列出默认位置、可调整范围和空间不足时的处理。HUD 保护角色、目标和预警视野；工作台保留对象选择、内容预览、属性修改与诊断之间的联系。
2. 给出最小尺寸、文本溢出、滚动、折叠和缩放规则。以真实内容上限检查布局，不用固定像素截图代替窗口与 DPI 适配。
3. 划分职责：业务/数据层拥有状态，呈现层解释并显示，布局层安排空间。控件发出用户意图，再通过项目已有入口改变业务状态；不复制第二套游戏状态或后台任务。
4. 高频数据变化时保持行高、数值区域、用户选择与滚动位置稳定。排序和布局更新应有明确触发条件，不能每次数据变化都使控件移动或抢焦点。
5. 为相关操作列出正常、空、加载中、处理中、错误和不可用状态及可执行动作。区分尚未获取、过期、能力未知与真实零值；状态复杂度与任务规模一致。
6. 明确键盘顺序、默认操作、取消/返回、焦点恢复，以及鼠标命中和遮挡关系。只在支持拖动时增加编辑模式、拖动取消和屏外恢复；不强制所有面板都浮动、吸附或支持复杂窗口管理。

## 按需参考

- HUD 分区、工作台、窄窗口和实时数据：读 [布局模式](references/layout-patterns.md)。
- 加载、错误定位、键盘、拖动和输入层级：读 [交互与状态](references/interaction-states.md)。
- UE Gameplay UI 使用 CommonUI/GAS/FastArray、需要 ViewModel/WidgetController、Pawn 重绑定或快捷栏输入统一时：读 [Gameplay UI 投影与 Domain Command](references/gameplay-ui-projection.md)。
- 核对旧 UMG 笔记或提炼项目经验：读 [案例与核验](references/cases.md)。具体 API 仍核对项目版本。

蓝图节点或 C++ 实现可组合相应技能；遇到异常时加入证据排查。MFC 等非 UE 任务不会因“控件”“HUD”“UI”字样引入 UE 生命周期或 API。

## 验证与交付

交付信息分区、尺寸与收缩规则、交互状态、组件职责和验证结果。文本方案说明控件关系和行为即可；用户只需小改动时，不先要求建立完整设计系统。

按影响范围检查最小客户区、常用和极端内容、目标 DPI/分辨率、键盘路径、错误恢复与高频更新；记录使用的实际尺寸和状态。验证拖动或滚动时，还需检查取消、关闭重开和布局恢复。性能结论依据测量，不凭“事件驱动”或“减少 Tick”直接宣称流畅。

能操作实际界面时，检查布局并执行关键输入路径；截图只能证明可见外观，不能证明点击、焦点或性能。仅给出方案、未运行应用或未取得截图时，明确标记相应验证待执行。

## CommonUI / Enhanced Input 专项

当任务涉及 CommonUI root layout、Activatable Widget input config、GameplayTag layer、Enhanced Input Mapping Context 生命周期、UI Action binding、GameplayMessageRouter 或 LocalPlayer/Controller/Pawn UI ownership 时，读取 [CommonUI / Enhanced Input：LocalPlayer、Layer 与输入所有权](references/commonui-input-routing-patterns.md)。不要把单机样例中的 ClearAllMappings、GetFirstPlayerController 或 blank blocker 直接外推到多人/复杂项目。
