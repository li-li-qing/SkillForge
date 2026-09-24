# 项目识别：事实先于方案

## 读取顺序

先读适用项目指令和用户给定的当前基线，再读构建入口、应用入口、任务相关模块与测试。使用 [事实表](../assets/project-profile.md)记录最少充分信息；已有可复查事实可复用，不每轮生成重复档案。

| 要核实的事实 | 优先证据 | 不允许的推断 |
|---|---|---|
| Qt 实际版本与最低支持版本 | kit、CMake 配置输出、锁定依赖、Qt 头文件、CI | 网页显示的最新 Qt 就是项目版本 |
| Widgets / Quick / 混合 | 依赖 target、入口、.ui/.qml、实际加载路径 | 因“现代界面”就默认 QML |
| 编译器与 C++ 标准 | CMakePresets、toolchain、项目属性、CI | 旧 MFC 曾用 C++17 所以新工程一定相同 |
| 进程位宽与 ABI | 构建架构、二进制检查、链接库/插件配置 | UI 是 x64，所以第三方 DLL 也一定是 x64 |
| COM/第三方宿主 | adapter/host 入口、创建线程、进程树、接口版本 | 出现大漠二字就新建 IPC，或默认 UI 可直接调用 |
| 当前可运行的验证 | 真实 test target、命令、日志与平台 | 有 tests 目录就等于已测试 |
| 持久化兼容 | 样本、schema/version、读写路径、迁移代码 | Qt 的 QSettings 可以直接替换任意旧数据格式 |

Windows 要同时确认 MSVC/MinGW、CRT、Debug/Release、插件与 Qt DLL 的配置一致性；相同位宽不代表不同 C++ ABI 可混用。工具链升级、位宽变更和 UI 框架迁移不要偷偷合并成一次任务。

## 结论分类

记录 `confirmed / user_constraint / assumption / unknown / conflict`，每条事实附路径/符号、日志或用户原话位置。源码描述现状，设计文档描述约定；矛盾需要列为偏差，而非擅自选择方便的一边。

缺少 Qt 工程时，可以完成通用设计、迁移风险表和待核项；不能声称已适配项目的实际类、位宽或构建命令。缺少某个 SDK 只阻断该集成分支，不妨碍独立模型测试与静态分析。

## 选择最小实现路径

- 已有 Widgets：标准 widget + layout + model/view，先复用已建立的控件/主题约定。
- 已有 Quick：沿用 QML 模块与 C++ 接口；只有涉及跨界集成才读 Widgets 规则。
- 尚无 UI 栈：根据数据编辑复杂度、动画、平台、团队和部署约束比较，不凭截图选型。
- 旧 MFC 迁移：读取旧 UI 的可观察行为和当前 Qt 的迁移阶段，保留已稳定业务核心。
- 仅日志排序/纯算法：不因仓库依赖 Qt 就动 UI、COM 或整个线程框架。

## 本用户的适配边界

LCot 已选择 Qt 是当前用户决定；历史 MFC/大漠讨论仅提供风险线索。具体版本、分层名称、会话槽位预算、文件位置都以当前工程为准。其他 Qt 项目不继承 LCot 的功能和进程拓扑。

Qt 的 QObject、QPointer、元对象、信号槽使用 Qt 契约；UE 的 UPROPERTY、TObjectPtr、OnRep、GetLifetimeReplicatedProps、FFastArraySerializer 只属于实际 Unreal target。保留“明确拥有者、少做热路径工作”的原则，不照搬不同运行时的 API。

来源入口：[Qt 官方文档](https://doc.qt.io/qt-6/)；版本敏感内容选择项目对应版本。资料检索本身不是部署认证。
