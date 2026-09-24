# 测试、持久化、构建与部署

## 分清证据层级

| 层级 | 可以证明 | 不能外推 |
|---|---|---|
| 文档/包结构检查 | frontmatter、路径、资源、题集格式有效 | 技术规则正确或 Agent 会遵守 |
| 静态源码审查 | 指定版本/文件内观察到的机制与风险 | 真实构建、DPI 和 SDK 可用 |
| 单元与契约测试 | 覆盖到的模型、命令、状态机与错误路径 | 全部 UI/平台行为 |
| Qt 集成/交互测试 | 测试平台与环境里的连接、输入、控件行为 | 没运行过的 Windows IME/多屏 |
| 真实 SDK/进程测试 | 实测位宽、COM、宿主与目标环境行为 | 其他 SDK 或插件版本 |
| 干净环境部署 | 已测试机器/镜像上的打包依赖与启动 | 所有系统版本兼容 |

每条验证记录 command/scenario、平台、配置、版本、结果与日志位置；失败不能被“本次没改这里”隐去。既有失败与新增回归分开记录。测试没运行写 not_run，缺 SDK 写 blocked，不写推测 PASS。

## Qt Test 与异步

小型测试可覆盖纯 service/model，UI 测试使用当前工程已有 Qt Test target。QSignalSpy 先检查 isValid，断言参数、顺序和次数；不能只看“发过一次信号”而忽略对象、状态和错误。

异步等待使用可判定状态和有界 timeout，如实际版本支持的 QTRY_*；不要依赖固定 qWait/sleep 偶然碰到结果。嵌套 processEvents 可以产生重入，不作为生产阻塞代码的常规补丁。

自定义 model 配 QAbstractItemModelTester，选择能使测试失败的报告模式；不要只输出 warning 后在报告写通过。额外断言业务 ID 映射、编辑 commit、过滤/排序后的选择与数据持久化。

必须优先覆盖当前变更的失败路径，再执行可用的项目整体测试。没有独立 Agent 运行器时，可以提供 Skill 评测题和评分标准，但不能编造未加载/加载 Skill 后的行为差异。

## 最小风险矩阵

| 变更 | 至少增加的场景 |
|---|---|
| 编辑/布局 | 输入中后台更新、IME、复制撤销、最小尺寸、缩放与焦点 |
| 异步/线程 | 初始化失败、关闭时忙碌、取消晚到、同窗口旧代际结果 |
| model | insert/remove/reset 契约、代理排序后编辑正确 ID、容量上限 |
| 平台/SDK | host 启动失败、错误位宽/注册、重连、清理失败、真实调用 |
| 持久化 | 旧档、损坏/截断、写入失败、版本不支持、回滚 |
| 部署 | 不带开发 PATH 的环境启动，Qt 平台插件与第三方 DLL 完整 |

截图用于补充视觉证据，不替代输入与线程验证。性能报告包含数据规模、机器/配置、基线和指标，不将某 GitHub 项目性能外推成 LCot 性能。

## 持久化

QSettings 适合应用设置，但业务数据格式、版本和迁移仍由项目设计。不要为了减少代码把既有事务/完整性保护替换成无版本键值写入。

文件整体替换可评估 QSaveFile：检查 open、实际写入长度/错误、commit 返回值；失败不更新 UI 的“已保存”状态。直接写入 fallback 是否启用会影响保护语义，不能忽略。原子替换不自动解决跨文件事务、跨进程冲突、断电持久性或 schema 兼容。

序列化声明版本、编码、字段范围和未知字段政策；不要把 GUI model index、QObject 指针或内存布局当存档。使用真实旧样本，验证读写往返和失败后原文件保持。

## 构建

从真实构建入口使用已有 CMake/.pro/项目配置，不在 UI bug 修复中顺手重建整个 build system。CMake 链接明确 Qt targets，moc/uic/rcc 的启用方式与项目版本一致；.ui/.qrc/.qml 必须进入对应目标/模块。

Qt 提供的部分 CMake helper、QThread helper 和 QML API 有小版本门槛，依据实际最低版本决定是否可用。不要把“网上最新示例能编译”当兼容证明。

Windows 核对 Qt kit、编译器、MSVC/MinGW、架构、CRT、插件与 Debug/Release。平台宏/头文件污染在 adapter 边界解决，不把全局禁用警告当修复。产品代码和测试命令按实际发现的 target 给出，不发虚构 build 路径。

## 部署与许可检查

使用匹配 kit 的 windeployqt 或现有部署流程，检查 Qt 平台插件、资源、翻译、QML 模块及第三方动态库。windeployqt 不替你收集所有外部 SDK DLL，也不解决 COM 注册/授权条件。

在干净目标环境运行，不依赖 Qt Creator、开发 PATH 或本地插件目录。测试缺依赖、无写权限、配置迁移失败时能产生可复制诊断，不只验证开发机双击启动。

第三方库按实际文件和版本核对许可：参考思路不等于可以复制 GPL 源码；LGPL/商业选择、修改、链接和再分发义务应结合发布方案评审。本 Skill 不提供“只要用 DLL 就自动合规”的保证，也不把闭源一概说成必须购买所有 Qt 商业许可。

依据：[Qt Test](https://doc.qt.io/qt-6/qttest-index.html)、[QSignalSpy](https://doc.qt.io/qt-6/qsignalspy.html)、[Model Tester](https://doc.qt.io/qt-6/qabstractitemmodeltester.html)、[QSaveFile](https://doc.qt.io/qt-6/qsavefile.html)、[Windows Deployment](https://doc.qt.io/qt-6/windows-deployment.html)、[Qt LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations)。
