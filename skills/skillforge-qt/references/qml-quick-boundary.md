# Qt Quick / QML：证据驱动的分支

只有当前项目确实采用 Quick/QML、用户明确要求该路线或需要评估混合边界时加载本文件。普通 Widgets 控件修复不额外引入 QML 引擎。

## 适用与责任

Quick 适合声明式布局、动画和动态视觉需求，但没有“所有现代 UI 都必须 QML”的规则。复杂桌面编辑工具的键盘、表格、焦点与原生窗口集成需实际比较；已有 Quick 工程也不因用户懂 C++ 就退回 Widgets。

业务真值与耗时算法仍放在可测试 C++ service/model；向 QML 暴露有类型、范围和错误语义的属性、方法、信号或模型角色。UI property binding 表达投影，不能使多个绑定路径都成为同一业务状态的写入方。

## 生命周期与线程

确认 QQmlEngine、root object、context property、singleton 和 C++ 实例的拥有关系。QObject 的 parent 与 QML engine ownership 不是任意可互换的托管方式；不得让 engine 删除仍被 C++ 独占托管的实例，也不得让 QML 持有已经销毁的外部实例。

C++ 回调、模型更新回正确的 UI 所在线程；Quick scene graph 可能在渲染线程工作，render 回调不直接随意触碰 GUI 对象。仅熟悉 Widgets 主线程规则还不够，遵守所用图形 API 和渲染阶段契约。

## 模型、绑定和输入

大列表通过 C++ model 和角色暴露数据，不每帧把全部记录重新复制为 JS 数组。delegate 可被销毁/复用，选择、编辑和异步身份必须使用业务 ID，不依赖 delegate 实例或 index 永久不变。

复杂 binding、JS 循环、图片解码与频繁创建组件可能阻塞 UI。图片按展示需求设置合理 sourceSize 和异步策略，测量缓存与内存；不在动画期间反复生成巨大图像或展开完整数据模型。

输入回归仍包含 IME、Tab、键盘快捷键、焦点区域、选择和滚动。带动画的漂亮截图不证明编辑框输入行为与桌面软件一致。

## 混合工程

QQuickWidget、QQuickView、原生子窗口或 Widgets/Quick 嵌入都有渲染、焦点、堆叠和资源代价，按实际选择做小型验证。混合不是默认升级步骤；确认现有版本支持与性能测量再决定。

QML 模块、资源与插件需要进入构建/部署；开发环境 import 成功不证明发布包成功。工具例如 qmllint 或 QML Profiler 仅在当前工具链实际可用时使用，不虚构运行结果。

依据：[Qt Quick 性能](https://doc.qt.io/qt-6/qtquick-performance.html)、[QML 与 C++ 集成](https://doc.qt.io/qt-6/qtqml-cppintegration-overview.html)、[QQmlEngine](https://doc.qt.io/qt-6/qqmlengine.html)、[QQuickWidget](https://doc.qt.io/qt-6/qquickwidget.html)。本轮六个案例主要覆盖 Widgets/原生工程，未进行额外 Quick 应用源码审计。
