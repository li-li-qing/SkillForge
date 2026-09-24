---
name: skillforge-qt
description: "Use when designing, implementing, reviewing, migrating or debugging C++ Qt desktop applications: Qt Widgets, QML/Qt Quick, QObject, signals/slots, QThread, Model/View, Qt CMake, DPI, Qt with Windows COM or MFC-to-Qt migration. 用于 Qt 工具软件、编辑框/布局异常、跨线程回调、关闭卡死、模型刷新与部署；纯 MFC、UE、普通 C++ 不因同为 C++ 自动触发，QuickTime 的 QT 缩写也不触发。"
---

# Qt 桌面工程

以当前工程为事实来源。先采用 Qt 已有控件、布局、命令、模型与生命周期机制，再为真实缺口添加薄适配；不把迁移做成另一套自研 UI 引擎。主场景是 C++ 桌面工具；Widgets 与 Quick 由项目证据决定，不互相强制替换。

## 首次接入

读取当前项目指令、构建配置、入口、任务相关 UI/模型/线程及测试，填 [项目事实表](assets/project-profile.md)。能读到的不要反问；未知项标 `unknown`，不沿用别的工程或旧 MFC 的版本、位宽与路径。只有未知项阻断当前操作时才停止该操作，其他只读分析继续。

采用项目现有命名、格式化和 C++ 标准。跨平台 Qt 不套用 Unreal 的反射、TObjectPtr、OnRep 或 FastArray；QSortFilterProxyModel 也不是网络 Proxy。实际 Qt/UE 混合工程按编译目标隔离。

## 执行契约

1. **定位真值**：指出业务状态、编辑草稿、显示投影分别由谁拥有；窗口不是整个程序的业务状态容器。
2. **锁定范围**：保留当前用户已批准的任务；设计/只审查时不改产品代码，已批准实施不因进入本 Skill 再问一次。
3. **选择主题**：只读下表中当前任务所需的参考，不先全量加载案例库。重要 API 用实际 Qt 小版本的文档或头文件核实。
4. **先验失败路径**：建立最小复现或失败测试；明确正常、取消、失败、过期结果和退出行为，然后做最小兼容改动。
5. **核对影响面**：改公共控件/dispatcher/model/协议时列出调用方并回归；修改处解释原因、拥有者、线程/数据流、兼容边界和剩余风险。
6. **按证据交付**：使用 [审查与交接模板](assets/review-handoff.md)，区分静态检查、真实构建、UI 实测和第三方接口实测。提供本次文件，不用“建议可行”冒充修复成功。

## 必守边界

- **单一拥有关系**：QObject parent 托管与智能指针独占托管不要同时成立。QPointer 只是非拥有观察，不延长寿命，也不使跨线程访问安全。
- **线程职责清楚**：GUI 和与视图连接的 model 在其拥有线程修改。QThread 对象本身不自动住在它管理的线程中；worker 初始化、事件循环和资源销毁必须有实据。
- **异步身份清楚**：跨线程传值或明确的不可变快照；回到 UI 后校验 request ID、会话代际与当前状态。对象还活着不代表旧结果仍有效。
- **取消不造假**：quit/requestInterruption 不等于中断正在阻塞的 SDK 调用。不能用 UI 线程等待、BlockingQueuedConnection 对等互等、terminate 或 sleep 冒充安全退出。
- **模型契约正确**：begin/end 包围实际结构修改；代理行号不是业务 ID。高吞吐数据有批次、内存上限、背压和过期处理，不逐条刷新整页。
- **输入不被刷新破坏**：区分编辑草稿与已提交值，后台状态不能覆盖正在输入的文字；保留 IME、撤销、焦点、选择与键盘导航。
- **热路径不做重活**：paint/data/resize/高频 timer 不反复加载图片、DLL、创建 COM、扫描磁盘或执行复杂匹配；缓存必须定义失效条件。
- **平台边界显式**：COM/STA、句柄、位宽、IPC 只在真实用到时启用相应规则；换成 Qt 不代表 Windows 自动化本身跨平台。

## 按需读取

| 当前问题 | 参考 |
|---|---|
| Qt 版本、工具链、事实/假设、接入范围不清楚 | [项目识别](references/project-profile.md) |
| 分层、菜单/工具栏/快捷键、业务真值 | [架构与命令](references/architecture-commands.md) |
| 编辑框分层、输入丢失、布局、DPI、停靠恢复 | [Widgets、输入与 DPI](references/widgets-layout-input-dpi.md) |
| 大列表、排序编辑错行、刷屏、内存增长 | [Model/View 与性能](references/model-view-performance.md) |
| QObject、连接、线程、取消、迟到回调、关闭卡死 | [生命周期与退出](references/qobject-threading-shutdown.md) |
| 大漠、COM/STA、Win32、位宽与进程通信 | [Windows 与 COM](references/windows-com-dmsoft.md) |
| 正在把旧 MFC 界面迁到 Qt | [迁移切片与回滚](references/mfc-migration.md) |
| 测试、持久化、构建、部署与许可核查 | [验证与发布](references/testing-build-deployment.md) |
| 工程确实含 QML/Quick，或用户明确评估该路线 | [Quick 边界](references/qml-quick-boundary.md) |
| 需要外部案例、来源、版本和不采纳理由 | [GitHub 来源](references/github-sources.md) |

## 与已有 Skill 协作

本 Skill 自包含，不要求安装某个 Agent 或兄弟 Skill。可发现时，`skillforge-ui-design` 负责交互与视觉验收，`skillforge-debugging` 负责故障证据；涉及旧 MFC 源码才按需读 `skillforge-mfc`。统一入口 `skillforge-orchestrator` 通过元数据发现本 Skill，不需要新增硬编码路由。

跨技能保持同一任务、同一状态/拥有关系和同一验证报告；没有宿主原生调用能力时，明确是读取文件使用。Skill 不自动安装依赖、启动后台任务、压缩上下文或授权外部写入。
