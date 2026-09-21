# 构建、测试与现代化

## 1. 先固定构建矩阵

从 `.sln/.vcxproj` 读取而不是猜：

- Toolset；
- Windows SDK；
- Use of MFC / ATL；
- Unicode/ANSI；
- Runtime Library；
- x86/x64/ARM64；
- Debug/Release；
- manifest / DPI / Common Controls；
- delay-load、COM registration、post-build steps。

用户只发布 x64 时不强制维护无价值的 x86；但工程若同时提供多位数 build，修复必须考虑 ABI、注册和第三方 DLL 位数。

## 2. 抽纯逻辑再测试

MFC UI 本身难做细粒度单测，所以把这些从窗口类抽出：

- parser / serializer；
- state machine；
- command validation；
- list sort/filter；
- path/registry mapping；
- SDK result conversion；
- retry/backoff policy。

让测试不需要 HWND、消息泵或真实 COM server。

## 3. UI 回归

窗口类至少覆盖：

- create/destroy/reopen；
- focus/tab/default button；
- command route/menu enable；
- async close/cancel；
- DPI/resizing；
- large list scroll/selection；
- dark/light theme 若产品支持；
- explorer/shell host 若属于 shell extension。

## 4. MFCMAPI 的工程化经验

当前 MFCMAPI 同一 solution 中有主 MFC 程序、console tool 和 UnitTest 项目；构建脚本覆盖 Debug/Release、Unicode/ANSI、x86/x64/ARM64/ARM64EC，还提供 PREfast/Code Analysis、format check 与 fuzz 配置。

不要求普通项目复制整个矩阵。可迁移原则：

- build/test 命令可脚本化；
- 静态分析与格式检查进入可重复流程；
- parser/低层库比窗口更适合 fuzz；
- 多架构支持用真实 CI/build 验证而不是宏推断。

## 5. 旧工程现代化顺序

建议拆四个阶段：

### A. Build compatibility

只解决：旧语法、SDK 冲突、废弃库名、manifest、第三方缺失依赖、资源编译与链接。

### B. Behavior compatibility

验证旧功能能启动、打开、保存、通信；先不做 UI 全面改版。

### C. Modern Windows compatibility

处理 DPI、Common Controls、Unicode、长路径/权限、TLS/系统 API 变化等。

### D. Internal modernization

再引入 RAII、Pimpl、service/model extraction、thread protocol、测试和更严格 warnings。

Microsoft Comic Chat 的 2026 现代化就是很好的“先把历史 MFC 程序在当前工具链跑起来，再修 DPI/重入/现代网络”的 worked example；其仓库自己也明确它是历史教学样例而不是 production-hardened 产品。

## 6. 不要盲目 modernize

- 不因为能换 `CString` 就一次改完所有字符串；
- 不把 MFC message map 全改成 lambda/callback；
- 不为了 `std::thread` 替换所有 `AfxBeginThread`；
- 不把资源编辑器生成的稳定代码机械“现代 C++ 化”；
- 不在同一个 patch 同时迁 build system、DPI、线程和业务模型。

现代化目标是明确 ownership、testability 和 correctness，而不是减少 MFC 关键字数量。
