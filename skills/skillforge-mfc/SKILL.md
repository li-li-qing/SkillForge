---
name: skillforge-mfc
description: "设计、实现、审查和维护 Windows MFC C++ 桌面程序，涵盖 CWinApp/Frame/Dialog/Doc-View、消息与命令路由、窗口生命周期、工作线程与 UI 线程、COM/STA、资源所有权、DPI/布局、复杂控件、构建与测试。Use when work targets MFC, afxwin, CWnd, CDialog, CFrameWnd, CView, message maps, DDX/DDV, AfxBeginThread or MFC/ATL desktop integration. 普通 C++、Win32-only、Qt、.NET、UE 不因 C++ 字样触发。"
---

# MFC 桌面开发

以当前工程的 `.sln`、`.vcxproj`、入口类、资源文件和真实运行路径为依据。MFC 是稳定但成熟的 Windows 桌面框架：保留它擅长的窗口、命令、资源与平台集成，同时把业务逻辑、线程、COM 和资源所有权写得比传统示例更明确。

## 先定位工程

先确认以下事实，能从工程读取的不要反问用户：

- 应用类型：SDI、MDI、Dialog-based、Shell extension、辅助 EXE/DLL，是否使用 Doc/View。
- 字符集与平台：优先确认 Unicode、x86/x64/ARM64、静态或动态 MFC、目标 Windows SDK、实际 MSVC toolset。
- UI 主干：`CWinApp`、主 Frame/Dialog、View、主要自定义控件、资源 ID、消息映射与命令 ID。
- 外部边界：COM/ATL、Shell、Direct2D/GDI/GDI+、网络、数据库、第三方 SDK 或自动化插件。
- 异步入口：`AfxBeginThread`、`std::thread`、线程池、timer、异步 I/O、回调、进程/管道。
- 当前验证入口：实际解决方案配置、单元测试工程、打包/安装器、最低系统版本。

旧示例只用于解释 MFC 机制。遇到现代编译器、DPI、安全、线程、COM 或构建问题时，以当前工具链和当前 Windows 行为重新核对，不照搬 VC6/VS2010 写法。

## 架构与职责

- **UI 层拥有窗口，不拥有全部业务真值**。`CWnd/CDialog/CView` 负责消息、显示、输入和命令适配；复杂状态、算法、协议与持久化尽量放到普通 C++ service/model，使其可测试并减少 HWND 生命周期耦合。
- **命令与状态更新走 MFC 已有路由**。菜单、工具栏和快捷键优先使用 `ON_COMMAND` / `ON_UPDATE_COMMAND_UI` 与现有 command target 链；不要让多个控件各自维护一份 enabled/checked 真值。
- **Doc/View 只在它确实匹配数据模型时使用**。已有 Doc/View 工程沿用文档、视图、Frame 的职责；Dialog-based 工具不为了“更标准”强行迁移。
- **外部 SDK 做适配层**。COM、BSTR、VARIANT、原始句柄和第三方类型尽量封装在 adapter/host 边界，不向 Foundation/Model 扩散。MFC 类与资源 ID 也不要渗透到纯逻辑层。
- **进程边界优先于巨型 UI 进程**。Shell extension、后台缓存、长时间运行服务或高风险第三方组件，若现有工程已有独立进程职责，不为了少一个 EXE 合并回 GUI。

更细的路由与分层见 [架构、消息与命令](references/architecture-message-routing.md)。

## 窗口、对象与资源生命周期

先写清三种身份：C++ 对象、MFC wrapper、底层 `HWND/HGDIOBJ/COM interface`。它们的寿命不是一回事。

- `CWnd*` 有效不等于 HWND 仍有效；HWND 有效也不等于原业务对象仍是当前实例。异步回调需要实例代际或 request token，不能只靠 `IsWindow`。
- 不长期保存 `CWnd::FromHandle` 可能返回的临时 wrapper 指针。需要长期引用时保存明确拥有关系、控件成员或安全的窗口标识，并在使用点重新验证。
- modeless dialog 必须明确谁 `new`、谁 `DestroyWindow`、谁最终释放 C++ 对象；只有采用 self-owned heap 模式时才在匹配的结束路径 `delete this`，不能套到栈对象或成员对象。
- GDI/DC/菜单/图标/COM 等资源逐类确认获取与释放契约。RAII 优先，但不要给 borrowed/shared 句柄套错误 deleter。
- `OnDestroy`、`PostNcDestroy`、析构函数承担不同阶段；取消订阅、停止 timer、拒绝迟到消息与释放 C++ 对象要放在正确阶段。

细则见 [窗口生命周期与资源所有权](references/window-lifetime-resources.md)。

## 工作线程与 UI 线程

默认规则：工作线程做阻塞和计算，UI 线程拥有窗口状态。

1. worker 不直接改 MFC 控件，也不依赖 UI 对象在任务期间一直存活。
2. 结果打包成拥有关系明确的数据，通过自定义 `WM_APP + n`、线程安全队列后 `PostMessage`，或项目已有 dispatcher 回到 UI 线程。
3. payload 的释放方必须唯一且写清楚；Post 失败、窗口销毁、任务取消都不能泄漏。
4. UI 对结果做 generation/request-id 检查，旧请求不能覆盖新状态。
5. teardown 先禁止新任务，再发取消，最后 join/等待或让 receiver 安全丢弃迟到结果。不要靠固定 `Sleep` 猜线程已结束。
6. 谨慎从 worker `SendMessage` 到 UI：如果 UI 同时等待 worker，容易形成死锁。普通结果通知优先异步投递。
7. timer 负责节流、合并或触发，不在高频 `WM_TIMER` 中执行磁盘扫描、COM 枚举、图像识别或其他重任务。

COM apartment、MFC worker thread 与异步取消见 [线程、异步与 COM/STA](references/threading-com-sta.md)。

## COM / STA / 第三方自动化

MFC 工具常与 COM、Office、Shell 或自动化插件共存，线程模型必须成为显式契约。

- 每个使用 COM 的线程独立初始化 apartment；不要假设主线程初始化会自动覆盖 worker。
- STA 对象默认只在创建它的 apartment 使用。跨线程需要合法 marshaling、代理或把调用投递回拥有线程；不能把裸 COM interface 指针直接交给任意 worker。
- 对必须固定在 STA 的第三方对象，优先单独的 STA host thread + command queue；UI 只发请求，host 拥有 COM 对象和其销毁。
- Pimpl/adapter 边界应阻止 `IUnknown*`、`VARIANT`、`BSTR`、SDK HRESULT 细节进入 Model；外层转为项目自己的值类型、错误码和结果对象。
- shutdown 顺序必须保证：停止新请求 → 完成/取消队列 → 释放 COM 对象 → 对应线程 `CoUninitialize` → 线程退出。

## DPI、布局与控件

- 新代码优先按目标系统采用 Per-Monitor DPI-aware 设计；历史 `SetProcessDPIAware` 只视为旧工程兼容手段，不作为新工程首选。
- 不把 96-DPI 像素常量散落到绘制、字体、图标和最小尺寸逻辑。集中缩放，处理 `WM_DPICHANGED`，必要时重建 DPI 相关资源。
- 持久化窗口位置时考虑显示器变化、DPI 变化和屏外恢复；不要把旧像素坐标无条件恢复到新环境。
- resize 中避免同步触发再次 resize 的递归链。需要重排但会引发新消息时，可使用 posted message 或显式 reentrancy guard 合并。
- 大列表优先虚拟/owner-data、批量更新、`SetRedraw(FALSE/TRUE)` 或项目现有增量模型；不要在每次滚动/paint 中重新做昂贵 I/O、COM、正则或复杂格式化。
- 自绘控件明确 background erase、double buffering、主题/Dark Mode、字体/brush/bitmap 生命周期与 accessibility，不只追求“看起来正常”。

见 [DPI、布局与复杂控件](references/dpi-layout-controls.md)。

## DDX、消息和输入边界

- DDX/DDV 用于明确的数据交换，不把 `UpdateData(TRUE/FALSE)` 当成任意时刻的全窗口刷新器。编辑中的草稿值与已提交模型值需要区分，避免 timer/异步刷新把用户输入覆盖回去。
- `PreTranslateMessage` 只处理确实属于窗口层的快捷键/导航；业务命令仍汇入统一 command handler，避免键盘和按钮走两套逻辑。
- 自定义消息使用项目集中定义的 ID 区间与 typed payload 约定，避免不同窗口随手复用 `WM_USER + 1` 导致协议碰撞。
- registered message 适合跨模块或外部组件需要名称协调的场景；进程内私有协议通常使用集中管理的 `WM_APP` 范围即可。

## 构建、测试与现代化

- 优先 Unicode；仅在真实兼容需求存在时保留 ANSI 配置，不让新代码继续扩散窄字符转换。
- 通过 `.vcxproj` 确认 MFC/ATL 设置、Runtime Library、Windows SDK、编译器警告与预处理宏。不要用新增全局宏掩盖单个头文件或 ABI 问题。
- 把可测试逻辑从窗口类抽出；单元测试覆盖 parser/model/adapter，UI 通过小范围窗口生命周期、命令路由、DPI、焦点和异步 teardown 验证补齐。
- 至少验证实际目标平台；x86/x64 同时发布时分别构建运行，不能把一边通过外推到另一边。涉及 COM/Shell 时额外确认位数匹配和注册边界。
- 旧 MFC 工程现代化按“先构建兼容 → 再行为兼容 → 再 DPI/UX → 再内部重构”的顺序，避免一次把编译器迁移、UI 改版和线程重写混在一起。

工程化与迁移案例见 [构建、测试与现代化](references/build-testing-modernization.md)。首轮 GitHub 来源、固定提交与采纳边界见 [GitHub 第一轮蒸馏](references/github-sources.md)。

## 性能检查

MFC GUI 的性能问题通常来自工作放错线程、刷新过密或对象/资源抖动，而不是消息映射本身。

- paint/scroll/timer/鼠标移动等高频路径只做必要的 O(visible) 工作；缓存昂贵的解析、图像、字体和布局结果，并定义失效条件。
- 不在 UI 热路径反复 `LoadLibrary`、打开注册表、创建 COM 对象、扫描磁盘或解析完整数据集。
- 大量跨线程结果做批次或 coalescing；一条数据一条 `PostMessage` 在高吞吐下会淹没消息队列。
- 避免多个线程频繁写共享状态；UI snapshot 与 worker-owned state 尽量单向交接，降低锁竞争和 cache-line 抖动。
- 优化前用 ETW/WPA、VS Profiler、采样器或至少可控计时证据定位；不要凭“窗口卡”就直接重写控件。

## 与其他 Skill 组合

- **MFC + debugging**：崩溃、死锁、偶发失效、线程竞态、控件状态错乱。
- **MFC + UI design**：布局、控件层级、键盘导航、实时列表、缩放与工作台设计。
- **MFC 单独使用**：新增窗口/命令、线程/COM 架构、生命周期审查、工程现代化。
- 普通 C++ 算法、Windows API-only、Qt/.NET/UE 不因同在 Windows 或使用 C++ 自动触发本技能。

跨技能只维护一份失败路径、一个所有权模型和一套验证结果。

## 验证与交付

按任务给出实际证据：改了哪些类/资源/消息协议，线程和对象由谁拥有，已运行哪些 build/test/manual checks。典型回归至少从相关项选择：

- 创建/关闭/重复打开、modeless 关闭后迟到消息；
- 快速连续触发异步请求、取消、窗口销毁、应用退出；
- x86/x64、Unicode、Debug/Release；
- 100%、150%、200% DPI、跨显示器、窗口缩到最小支持尺寸；
- 键盘/鼠标、菜单/工具栏/快捷键走同一命令；
- COM 初始化失败、第三方调用失败、host thread 退出；
- 大列表持续更新时滚动、选择、焦点和 CPU 占用。

没有实际构建或运行时明确写成“静态审查/待运行验证”，不要把建议写成已通过。
