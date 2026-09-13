# 案例与核验

## UI-K01：隐藏、命中和子控件边界

- **状态/适用版本**：机制已核验；本机 UE 5.7.4，Changelist 51494982。具体项目点击问题未复现。
- **症状**：旧 UMG 笔记声称“Hidden 仍可点击”，或父容器不可命中时尝试只把按钮设为 Visible。
- **触发条件**：使用 UMG/Slate 可见性；必须先确认实际父子层级及枚举值。
- **证据**：`Engine/Source/Runtime/UMG/Public/Components/SlateWrapperTypes.h` 的 `ESlateVisibility`；[Epic API 当前页](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/UMG/ESlateVisibility) 读取时显示 5.8，不能代替 5.7 源码证据。
- **原因**：混淆占用布局空间与鼠标命中。`Hidden` 不显示、占位、不可命中；`Collapsed` 不显示也不占位；`HitTestInvisible` 连同子控件均不参与命中；`SelfHitTestInvisible` 仅自身不可命中。
- **修复**：按设计目的选择可见性，检查祖先链和遮挡。需要装饰父容器透传而保留按钮交互时核对 `SelfHitTestInvisible` 是否符合实际树结构；不能盲目修改所有父控件。
- **验证结果**：枚举语义已核验；目标 UI 鼠标、键盘和业务事件链未运行，不能宣称问题已修复。

## UI-K02：Canvas 尺寸变化与拉伸锚点

- **状态/适用版本**：布局机制已核验；UE 5.7.4，同上构建。实际布局异常为待复现场景。
- **症状**：照“Offsets 总是位置与宽高”笔记设置后，视口变大时尺寸或边距不符合预期。
- **触发条件**：UMG Canvas Slot，轴上锚点可能重合或分离，可能启用 AutoSize。
- **证据**：`Engine/Source/Runtime/Slate/Private/Widgets/Layout/SConstraintCanvas.cpp` 的锚点拉伸、AutoSize 与布局分支；`Engine/Source/Runtime/UMG/Private/Components/CanvasPanelSlot.cpp` 的 `SetSize` 对 Right/Bottom 赋值。
- **原因**：同一 Offsets 字段在不同轴/布局条件下不总表达尺寸。非拉伸轴尺寸由 SlotSize 或 AutoSize 的 DesiredSize 决定；拉伸轴的远侧 Offset 参与边距计算，不能仅凭 `SetSize` 名称推断最终像素尺寸。
- **修复**：先读取锚点、Alignment、Offsets、AutoSize、父级可用空间和缩放，再按当前容器语义调整。不要把一组固定偏移用于所有分辨率。
- **验证结果**：源码路径已检查；尚未创建控件或比较实际分辨率下的布局。

## UI-K03：实时更新引起跳行和视野变化

- **状态/适用版本**：设计候选；来自既有 Advanced UI HUD/工作台/实时布局资料与 Replicated Suite 刷新约束，未绑定经复现的单个故障或框架版本。
- **症状**：更新后数值挤动、排序跳行、日志回到底部或焦点改变。
- **触发条件**：高频数据更新与自动尺寸、排序或滚动联动；是否存在该联动需查实际实现。
- **证据**：当前仅有历史设计约束，无该案例的事件日志、截图对比或性能测量。
- **原因**：更新逻辑同时修改布局或选择状态是候选解释，不是确定根因。
- **修复候选**：检查稳定 ID、数值宽度、行高、跟随末尾状态和焦点拥有者；按证据分开数据刷新与用户工作状态。
- **验证结果**：待在最大内容量、筛选/排序、回看日志及键盘操作下复现并回归。只有经过项目验证的结论才升级为案例；业务服务名与项目限制留在项目资料中。

UMG 更新成本可参考 [Epic UMG Optimization，UE 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/optimization-guidelines-for-umg-in-unreal-engine?application_version=5.7)。这是 UE 专属资料，只有任务使用 UMG 时读取；它不证明其他框架或当前项目的性能。
