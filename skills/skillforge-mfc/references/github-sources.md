# GitHub 第一轮蒸馏（2026-09-21）

首轮只选择能代表不同 MFC 问题域的项目。星数不是采纳依据；以源码机制、维护状态、目标问题和可迁移性为准。

## 1. microsoft/mfcmapi

- 固定提交：`c8379e0f2673227cf0b429ba8ab31d7f7ba093bb`（2026-09-16）。
- 分类：**Current / production-grade MFC reference**。
- 仓库：https://github.com/microsoft/mfcmapi
- 重点证据：`UI/Dialogs/BaseDialog.cpp`、`UI/Controls`、`core`、`UnitTest`、`package.json`。

采纳：

- MFC UI 与 core 分目录；
- 共享 cache/model 用现代 C++ ownership，同时保留明确的 COM AddRef/Release 边界；
- menu/notification/message map 集中到基础 dialog；
- solution 有 UnitTest，脚本化多配置 build/test、静态分析、format、fuzz。

限定：

- MAPI 自身的 reference-count、notification 与错误宏不是通用 MFC API；
- 不能因为该项目保留某些裸 COM 指针，就否定其他项目使用 smart COM pointer；
- 它的 UI 架构服务于诊断工具，不等于所有工具都需要同样复杂的 base dialog。

## 2. WinMerge/winmerge

- 固定提交：`63deba2519c0ce81b1cf459c1659ad443b9e18ea`（2026-09-21）。
- 分类：**Current / large desktop MFC application**。
- 仓库：https://github.com/WinMerge/winmerge
- 重点证据：`Src/OpenView.cpp`、`Src/Common/MessageBoxDialog.cpp`、主 frame/view 与 compare UI。

采纳：

- 大型传统 MFC 应用可以逐步引入 `std::shared_ptr`、atomic state，而不需要先重写框架；
- worker + async notification 适合把阻塞工作移出 UI；
- 窗口尺寸/位置持久化和复杂对话框需要显式 layout policy；
- VS2022+、x86/x64/ARM64 构建仍能与 MFC 共存。

限定：

- 单个源码文件里存在的历史 ownership 写法不自动成为最佳实践；
- heap payload + message 只是一个实现，新的高吞吐模块优先 queue + coalesced wakeup。

## 3. TortoiseGit/TortoiseGit

- 固定提交：`acc10fc20afe36aabc4afbc5f1af33f31acae32e`（2026-06-27）。
- 分类：**Current / mature MFC + shell integration architecture**。
- 仓库：https://github.com/TortoiseGit/TortoiseGit
- 重点证据：`architecture.txt`、`src/TortoiseProc`、`src/TGitCache`、大型 list/dialog 代码。

采纳：

- Shell extension、GUI、background cache、diff/blame 等进程职责分离；
- handler/dialog 按命令域组织，而不是所有 Explorer 功能塞进一个窗口类；
- 多处使用 background thread 避免阻塞 dialog，并显式记录 running/cancel 状态；
- reusable status list/control 承担大量复杂列表场景。

限定：

- 项目历史很长，某些 worker 对 UI/control 的直接调用不应复制到新代码；
- 多进程拆分只在隔离和生命周期收益成立时采用。

## 4. microsoft/comic-chat

- 固定提交：`48a162249484ab8d116c243e8203b0956d350c09`（2026-07-22，仓库已归档）。
- 分类：**Historical application + Current modernization worked example**。
- 仓库：https://github.com/microsoft/comic-chat
- 重点证据：`docs/MODERNIZATION.md`、`v1.0-pre-modern`、`v2.5-beta-1-modern`。

采纳：

- 把编译迁移、DPI、UX 与网络现代化分阶段记录；
- 96-DPI 像素常量集中缩放；
- 根据真实 DC/extent 修复 GDI surface；
- resize/reflow 使用 posted message 规避同步 `WM_SIZE` 重入崩溃；
- Common Controls manifest、旧宏冲突、link library 都属于真实迁移风险。

限定：

- 仓库明确是历史 worked example，不是 production hardening 指南；
- `SetProcessDPIAware` 只是其历史程序的阶段性方案，新工程优先 Per-Monitor DPI；
- 旧 VC4/VC5 工程结构不作为现代 solution 模板。

## 5. Microsoft/VCSamples

- 固定提交：`9e1d4475555b76a17a3568369867f1d7b6cc6126`（2019-11-24；仓库 2021-02-09 归档）。
- 分类：**Historical canonical MFC mechanism samples**。
- 仓库：https://github.com/microsoft/VCSamples
- 重点样例：VisualStudioDemo、Ribbon/Feature Pack、WordPad、MFCIE。

只采纳仍稳定的 MFC 概念：

- Doc/View；
- Frame/MDI；
- message map；
- command/update UI routing；
- docking/ribbon/control 使用方式。

不采纳为现代默认：

- 编译器/SDK 配置；
- 安全策略；
- Unicode/ANSI 取舍；
- 线程、DPI、COM lifetime；
- 原始 new/delete 或旧 CRT/WinInet 用法。

## 6. 时效性校准

Microsoft C++ 文档当前仍说明 MFC 继续受支持，但框架本身已经成熟，官方不再持续增加新功能或更新所有 MFC 文档。因此本 Skill 采取：

- MFC 核心语义可参考官方历史样例；
- 现代 Windows 行为优先当前 SDK/Visual Studio 与活跃 MFC 工程；
- 每次遇到 DPI、manifest、Shell、COM、security/toolset 相关问题都重新核对目标环境。

## 7. 后续建议研究轮次

后续正式开发中优先按遇到的问题增量蒸馏，不为了数量一次塞满：

- MPC-HC / MPC-BE：高频绘制、媒体线程、自绘主题与 DPI；
- 具体 Shell extension/COM server：registration、bitness、Explorer isolation；
- 大型 owner-data list/tree：百万项数据、selection identity、增量刷新；
- Accessibility/IME/Dark Mode：现代 Windows UX；
- Installer/update/crash dump/ETW：MFC 工具发行与现场诊断。
