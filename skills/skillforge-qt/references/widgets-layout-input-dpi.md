# Widgets：布局、输入、主题与 DPI

## 先用标准机制

容器采用合适的 QBoxLayout/QGridLayout/QFormLayout、sizeHint、minimumSizeHint 与 QSizePolicy。明确哪些区域固定、伸缩、滚动、折叠；不要把一张截图的坐标逐个 setGeometry 到所有控件。

固定尺寸不是绝对禁令：工具栏图标、特定预览比例可有约束，但以逻辑尺寸和设计 tokens 表达，不能卡死翻译文字、输入法和字体缩放。只在确有定制排布需求时写 layout 子类，先给出标准 layout 无法满足的证据。

使用 .ui 时编辑源 .ui 或正确的自定义类，不手工修改自动生成的 ui_*.h。把控件放入 layout 后仍需明确 QWidget parent；删除 layout 不等于自动删除其中所有 widget，动态替换需按 QObject 拥有关系处理，避免隐藏旧控件叠在新控件下面。

## 编辑框分层/重影的检查顺序

1. 核对实际控件类型和父子树，确认是否真的只存在一个输入控件；检查重复创建、未移除 overlay 或占位控件。
2. 比较 focus 前后 palette、QSS、frame、textMargins、字体和 sizeHint；不要再加覆盖层来遮住差异。
3. 检查自绘是否与基类重复绘制 frame/background，paint 路径是否递归 update 或修改布局。
4. 检查屏幕缩放下逻辑 rect 与光栅像素是否被重复放大；核对 clip、contentsRect 和相邻容器边框。
5. 用最小页面保留同一主题复现，再修实际绘制/布局拥有方，并回归该公共控件的其他页面。

需要定制样式时先用 palette、有限 QSS 或 QStyle/QProxyStyle 的合适扩展点。不要为了外观丢掉标准编辑语义和 accessibility；自绘不等于重新实现输入法。

## 用户输入与后台刷新

必须区分：`committed value / edit draft / revision / editing state`。外部更新进入时先判断是否与草稿冲突；业务可以选择延迟投影、冲突提示或显式放弃草稿，不用 timer 强行 setText。

- QLineEdit::textEdited 适合用户编辑意图；textChanged 也会因程序 setText 触发。按实际语义连接，不能把所有 textChanged 都当用户提交。
- 程序投影确需屏蔽反馈时可局部 QSignalBlocker；其作用不是保证异步安全，也不替代正确的真值与 revision。
- editingFinished 不保证覆盖所有提交规则；validator 影响结束信号，中文输入法预编辑也不等于已提交业务值。
- 校验分输入级与业务级：空、负值、范围、单位、本地化小数、粘贴多字符都测试；不允许仅按钮禁用而 service 接受非法值。
- UI 更新保留 cursorPosition、selection、undo、焦点、Tab 顺序；恢复这些状态要基于同一编辑对象，不能把旧行的选择恢复到新行。

最小交互回归：未聚焦/聚焦外观，中文 IME 连续输入，Ctrl+A/C/V/Z，选区、拖选、右键菜单、Tab/Shift+Tab、Enter/Escape、只读/禁用、后台刷新发生在输入中。截图正常不证明这些行为正常。

## 主题、图像与刷新

tokens 集中定义间距、圆角、字号策略、图标逻辑尺寸；QSS 尽量作用域化。主题切换一次更新相关对象，不在 paint/resize/timer 中重复 setStyleSheet、重新解析 SVG 或扫描图标目录。缓存 key 包含真正影响结果的 DPR、主题、尺寸、状态；资源变化时明确失效。

QImage 用于可在后台处理的像素数据，QPixmap/Widget 相关操作遵守实际平台和 GUI 线程约束；不要把可重入的图像操作等同于可以在多个线程修改同一实例。

## DPI 与多显示器

Qt 6 Widgets 通常以设备无关坐标布局。不要把 widget 几何再统一乘 devicePixelRatio，造成二次缩放。QImage/QPixmap 的像素尺寸与 DPR 元数据是另一个层次，位图绘制和原生截图必须单独转换。

跨显示器时核对窗口所属 screen、availableGeometry、逻辑坐标、DPR 与外部 Win32/SDK 坐标来源。各 screen 的逻辑矩形不保证无缝连续；不要把所有屏幕包围矩形中的空洞当有效落点。

保存恢复窗口位置时处理：副屏拔掉、缩放变化、分辨率降低、任务栏、最小支持尺寸、主窗口和浮动 dock。标题栏与主要交互区应可达；恢复失败回到可见默认布局，提供“重置布局”，不要用不可见窗口的旧坐标覆盖最后可用配置。

100/125/150/200% 与多屏是建议测试矩阵，不是用户已承诺的最低配置。先读取当前产品支持尺寸，再补边界测试。

## 停靠与工作台

先判断 QMainWindow/QDockWidget 是否足够。需要更复杂的拖拽、tab、多工作区时才评估 ADS 等库；不为“好看”增加停靠框架。

dock 的 objectName 是稳定非本地化 ID，显示标题可以翻译；保存 geometry/state 记录布局 schema 版本。先创建所需 dock 再恢复 state，检查返回值、缺失面板、损坏数据和屏外窗口；恢复和正常交互路径避免互相回写。

关闭/移除/延迟删除分清：注销 manager 关系、断开订阅、释放 QObject 不能重复。ADS 的恢复代码注释展示了“旧 manager 反向指针 + deleteLater”造成双重移除的风险，不能只复制一个 deleteLater 修复所有寿命问题。

依据：[布局管理](https://doc.qt.io/qt-6/layout.html)、[QLineEdit](https://doc.qt.io/qt-6/qlineedit.html)、[High DPI](https://doc.qt.io/qt-6/highdpi.html)、[QMainWindow](https://doc.qt.io/qt-6/qmainwindow.html)、[来源案例](github-sources.md)。
