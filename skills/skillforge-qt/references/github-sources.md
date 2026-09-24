# GitHub 第一轮：六个项目的定向切片蒸馏

核对日期：2026-09-22。先从 GitHub 检索工具型 Qt 工程，再以 commits API 截止时间选择固定 revision，通过连接器读取具体文件。没有以 stars 排名替代架构检查，也没有克隆、构建或完整通读六个仓库。

本轮材料的作用是给规则提供可复查的机制证据，不是推荐全部项目成为 LCot 依赖。仅给出独立整理的说明，不打包上游源码、图标、字体或 SDK。

机器可读证据见 [source-manifest.json](source-manifest.json)。read_ranges 只记录已读范围的保守子集；不表示整个文件其余部分也已审查。参考链接可能包含最新文档，实际 API 仍以目标 Qt 小版本为准。

## 选择逻辑

| 项目 | 选择原因 | 最重要的限制 |
|---|---|---|
| Qt Creator | 与桌面工具的命令、上下文、对象管理相关 | 不搬完整 IDE 框架 |
| OBS Studio | C++ 核心与 Qt 前端的构建边界可直接观察 | 只读构建切片，不评判整套 UI |
| Wireshark | 持续数据、物理记录和可见列表的投影问题 | 通知顺序和新模型契约需独立验证 |
| CopyQ | 平台行为、故障隔离和进程集成测试 | 不将测试中的阻塞等待移入生产 GUI |
| Qt Advanced Docking System | 窗口恢复、稳定 ID、注销与延迟销毁 | 标准 dock 足够时不引入 |
| QHotkey | Windows 原生热键及跨线程退出风险 | 较旧快照，仅采纳经核对机制 |

分类 Current / Stable-but-old 是资料时效性标签，不是项目质量排名或维护承诺。

## 1. qt-creator/qt-creator

提交 `bfb91a9719a0d690471e16435a447ca509662e71`；提交者日期 `2026-09-18T07:19:16Z`；Current。

主题：命令、上下文与 QAction 生命周期。

已读：[`src/plugins/coreplugin/actionmanager/actionmanager.cpp`](https://github.com/qt-creator/qt-creator/blob/bfb91a9719a0d690471e16435a447ca509662e71/src/plugins/coreplugin/actionmanager/actionmanager.cpp)，行 1–215；blob `34f646b23ff7ff8a396857826c80c9110bcdeab6`。

**采纳**：稳定 command ID 与 action 上下文；界面入口共享命令语义；QObject parent 和带 context 的回调连接。

**不采纳/不外推**：完整 IDE 插件系统与 private Core API；照抄 QTC 宏和全部 builder 层级；根据 IDE 当前版本强行升级 LCot 工具链。

**许可边界**：所读 actionmanager.cpp 文件头：LicenseRef-Qt-Commercial OR GPL-3.0-only WITH Qt-GPL-exception-1.0；未据此完成全仓库许可审计。

## 2. obsproject/obs-studio

提交 `ea7536c49cb84420296d3831cda526c232fed3bc`；提交者日期 `2026-09-21T23:13:24Z`；Current。

主题：UI/核心的 target 分离。

已读：[`frontend/CMakeLists.txt`](https://github.com/obsproject/obs-studio/blob/ea7536c49cb84420296d3831cda526c232fed3bc/frontend/CMakeLists.txt)，行 1–100；blob `98daf7bb0bde81835298b55b175005b2703ddcc8`。

**采纳**：frontend 与 libobs/frontend-api 的构建依赖边界；按 UI 组件与平台组织构建职责。

**不采纳/不外推**：FFmpeg/流媒体依赖集；把大项目的所有分层移入小工具；推断未读的全部 UI 线程实现已正确。

**许可边界**：本轮 frontend/CMakeLists.txt 切片没有完整许可说明；复制源码或引入依赖前另核对根许可与目标文件。

## 3. wireshark/wireshark

提交 `996389fe368e79f0c5aa6513c310ea9f37479078`；提交者日期 `2026-09-21T23:56:13Z`；Current。

主题：物理记录、可见投影与稳定身份。

已读：[`ui/qt/models/packet_list_model.cpp`](https://github.com/wireshark/wireshark/blob/996389fe368e79f0c5aa6513c310ea9f37479078/ui/qt/models/packet_list_model.cpp)，行 1–210；blob `7ac054e049b7599f20820182fef3998bceab0c25`。

**采纳**：physical_rows 与 visible_rows 分离；稳定帧号到投影行的映射；边界验证与容量规划意识。

**不采纳/不外推**：全局唯一 model；无条件 reserve 100000；照抄所有 begin/end 通知顺序或历史 Qt 写法；新实现以官方模型契约和测试为准。

**许可边界**：packet_list_model.cpp 文件头：GPL-2.0-or-later；仅蒸馏机制，无源码复制。

## 4. hluk/CopyQ

提交 `76fe2d8f23996e4bae61c970a6ee924ce71a528e`；提交者日期 `2026-09-20T14:20:51Z`；Current。

主题：平台接口、进程隔离与集成测试。

已读：[`docs/source-code-overview.rst`](https://github.com/hluk/CopyQ/blob/76fe2d8f23996e4bae61c970a6ee924ce71a528e/docs/source-code-overview.rst)，行 1–180；blob `4d2dc79846be7231c41363bc4f2053061426f0f0`。

已读：[`src/tests/tests.cpp`](https://github.com/hluk/CopyQ/blob/76fe2d8f23996e4bae61c970a6ee924ce71a528e/src/tests/tests.cpp)，行 1–180；blob `9c7c0ce6969bc3a7e9ae19650cdad721fd3d0afe`。

**采纳**：平台相关逻辑隔离；特定故障域的独立进程与存活检查；进程启动/关闭、环境与错误日志的真实测试入口。

**不采纳/不外推**：将文档中的阻塞 ScriptableProxy 当通用 UI 桥；把测试 waitForFinished/terminate/kill 直接放入生产 closeEvent；断言架构文档与所有当前实现完全一致。

**许可边界**：src/tests/tests.cpp 文件头：GPL-3.0-or-later；文档和其他文件许可另核对。

## 5. githubuser0xFFFF/Qt-Advanced-Docking-System

提交 `4f4f602c3f7b02ee041793e9bc5833bab1bdb4ab`；提交者日期 `2026-09-10T10:33:11Z`；Current。

主题：停靠状态恢复与延迟销毁。

已读：[`src/DockManager.cpp`](https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System/blob/4f4f602c3f7b02ee041793e9bc5833bab1bdb4ab/src/DockManager.cpp)，行 1–150、260–440；blob `55e3d4cc6b05b65bc142babdaf6f7d915a2ab740`。

**采纳**：版本化状态与测试式解析；稳定 objectName 校验；浮动窗口弱观察与恢复状态控制；移除 manager 关系再延迟销毁的生命周期意识。

**不采纳/不外推**：默认安装 ADS；所有项目都需要高级停靠；只调用 deleteLater 就一定不会双重移除。

**许可边界**：DockManager.cpp 文件头：LGPL-2.1-or-later；实际引入版本/修改/分发义务另评审。

## 6. Skycoder42/QHotkey

提交 `4e3a244d87f1f7e741e1395f2ffe825f3a8ada45`；提交者日期 `2025-09-30T22:28:08Z`；Stable-but-old。

主题：原生全局热键与退出互等风险。

已读：[`README.md`](https://github.com/Skycoder42/QHotkey/blob/4e3a244d87f1f7e741e1395f2ffe825f3a8ada45/README.md)，行 78–119；blob `c61a6f4d6dccea00a034078df8152b631e0948fe`。

已读：[`QHotkey/qhotkey_win.cpp`](https://github.com/Skycoder42/QHotkey/blob/4e3a244d87f1f7e741e1395f2ffe825f3a8ada45/QHotkey/qhotkey_win.cpp)，行 1–215；blob `949d87a6f82cb836aa407e0fbab0ceee38a8e250`。

**采纳**：全局热键需要原生事件适配；Qt 对象线程亲和性与原生处理职责分开；退出前注销与主线程事件循环依赖必须明确。

**不采纳/不外推**：跨线程 BlockingQueuedConnection 作为通用默认；旧 qpm 安装路径或历史平台能力直接当当前能力；将库较久未更新推断为必然失效或安全。

**许可边界**：本轮重点文件切片未完成许可核对；引入时核对该提交 LICENSE 及依赖，不把可参考等同可任意复制。

## 机制到 Skill 的落点

命令/action 进入 [架构](architecture-commands.md)；投影/身份进入 [模型与性能](model-view-performance.md)；恢复/输入进入 [Widgets](widgets-layout-input-dpi.md)；平台与热键进入 [Windows/COM](windows-com-dmsoft.md) 和 [线程](qobject-threading-shutdown.md)；进程测试进入 [验证与部署](testing-build-deployment.md)。

大漠、LCot 的具体接口没有从上述项目推导。STA、位宽和运行时语义由官方文档与当前项目校验，真实 SDK 能力由用户提供的版本文档和 Windows 实测确认。

## 官方校准点

以下是一手 API/机制依据，不把外部项目特有写法覆盖框架契约：

| 问题 | 依据 |
|---|---|
| 对象所属线程、连接与销毁 | [QObject](https://doc.qt.io/qt-6/qobject.html)、[QThread](https://doc.qt.io/qt-6/qthread.html)、[QPointer](https://doc.qt.io/qt-6/qpointer.html) |
| model 通知与验证 | [QAbstractItemModel](https://doc.qt.io/qt-6/qabstractitemmodel.html)、[Model Tester](https://doc.qt.io/qt-6/qabstractitemmodeltester.html) |
| 输入与屏幕坐标 | [QLineEdit](https://doc.qt.io/qt-6/qlineedit.html)、[High DPI](https://doc.qt.io/qt-6/highdpi.html) |
| Qt 测试与文件提交 | [QSignalSpy](https://doc.qt.io/qt-6/qsignalspy.html)、[QSaveFile](https://doc.qt.io/qt-6/qsavefile.html) |
| SDK 线程约束 | [Microsoft STA](https://learn.microsoft.com/en-us/windows/win32/com/single-threaded-apartments) |
| 交付与许可核查 | [Windows deployment](https://doc.qt.io/qt-6/windows-deployment.html)、[Qt LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations) |
| Quick 的补充分支 | [Qt Quick performance](https://doc.qt.io/qt-6/qtquick-performance.html) |

## 下一轮研究方法

优先由实际 Qt 项目故障或新功能触发：确定问题 → 选一个相关文件/测试 → 固定提交 → 阅读调用方与失败路径 → 提取可迁移规则 → 当前工程复现/验证 → 更新评测题与结果。不要按项目数量扩大入口，也不要把未读目录写成已掌握。

本轮尚未做：外部项目构建、完整依赖/许可审计、LCot Qt 实际代码接入、Windows UI/COM 实测、独立 Agent 无 Skill/有 Skill 行为对照。结构验证结果只见对应交付报告，不能从此来源表推出运行通过。
