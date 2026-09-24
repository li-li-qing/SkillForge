# 架构与命令：UI 是投影和输入入口

## 用一条数据流解释功能

推荐从已有架构中识别四个职责，不为小功能强造四层类：

```text
Widget / QML View
    用户意图 → Presenter / Controller / Presentation Adapter
        类型明确的命令 → Application Service / Domain Model
            值类型请求 → Platform / SDK Adapter
        结果/状态快照 ← Service（含请求标识、错误和代际）
    UI 所在线程投影 ← Adapter（拒绝过期结果）
```

业务真值由 service/model 拥有；界面选择、滚动、展开和编辑草稿属于 presentation。不要让界面 enabled、运行状态标签或树行号反向成为执行引擎唯一事实。

Qt 工程可以合理使用 QString 等值类型；已经独立的纯 C++ Foundation/Model 不因换界面就全面改为 QObject。核心无需 Widgets/Gui 时不要链接这些模块。接口中避免 QWidget、QModelIndex、COM 接口指针与窗口句柄扩散；平台适配层负责转换。

## 命令统一

给可复用动作稳定的 command ID。菜单、工具栏、按钮和快捷键路由到同一 application command；共享 QAction 可用于呈现可用/选中状态，而不是复制四份判定。

命令检查分两层：UI 的 enabled 是交互提示，service 接收命令时仍验证真实状态。否则快捷键、测试或外部请求可绕过禁用按钮。必要时 command 结果分为 rejected/accepted/completed/failed；接受请求不表示执行成功。

项目未需要可扩展插件时，小型 action registry 或几项共享 QAction 已足够，不移植 Qt Creator 的完整插件/Context 引擎。快捷键上下文区分控件内、应用内与操作系统全局；后者需要平台服务，不能把 QShortcut 当全局热键。

## 状态契约

| 状态 | 可接受的操作 | UI 投影与证据 |
|---|---|---|
| Starting | 取消初始化或关闭；具体能力由服务定义 | 尚未 ready，不开放运行 |
| Ready | 提交新任务 | 记录 request ID 与目标版本 |
| Running | 取消、查看详情；是否允许并发按当前设计 | 展示进度，不宣称能强制中断 SDK |
| Stopping | 不再接受新任务，处理退出/清理结果 | 保持消息循环可响应 |
| Stopped / Failed | 恢复或重启由显式操作决定 | 输出终态、清理结果与失败原因 |

这是可裁剪的参考状态，不是强制替换项目现有枚举。已有状态机先映射同等语义；没有真实需求不增加十几个中间状态。

请求、取消、终态都记录 session/generation；重新绑定对象后，旧 service 结果不能继续改同一个视图。订阅返回可管理的 connection/token，窗口关闭、切换目标和重建页面都有一致的解绑路径。

## 依赖和代码审查

把跨模块接口与拥有关系画成文字表即可。检查：谁能写状态；谁发命令；线程在哪；谁释放资源；哪些错误上报 UI；哪些操作不可重试。新增全局单例前先确认生命周期/测试隔离是否真的需要。

CMake target 上明确 PUBLIC/PRIVATE 依赖。使用 Qt Core 并不意味着依赖 Qt Widgets；可测试服务不为方便直接 include 主窗口头文件。迁移只改 UI 时，避免顺手重写算法、会话预算、SDK 适配和存档协议。

## 外部案例与边界

[GitHub 来源](github-sources.md)中的 Qt Creator ActionBuilder 切片用于理解稳定命令、上下文和 QAction parent；OBS frontend CMake 用于理解界面与核心 target 分离。前者并不要求自建 IDE，后者也不表示应复制媒体依赖。机制采纳和第三方源码复制是两件事。

官方依据：[QAction](https://doc.qt.io/qt-6/qaction.html)、[QObject](https://doc.qt.io/qt-6/qobject.html)。
