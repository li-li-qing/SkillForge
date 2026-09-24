# Windows / COM / 大漠：仅在实际使用时加载

## 先确认集成事实

读取当前 SDK 版本、接口说明、可用二进制位宽、注册/免注册方式、adapter/host 源码与进程拓扑。用户决定用 Qt，不表示 UI 已是 x64、SDK 已升级或 COM 已允许任意线程访问。本包没有大漠具体函数表；没有接口证据就不编造函数、参数和返回值。

Qt Widgets 可调用平台适配服务；ActiveQt 是否使用取决于实际依赖和目标工具链，不强行把已有可靠的 COM Pimpl 改为 QAxObject，也不在每个按钮里创建 COM 对象。

## 平台隔离

业务侧暴露值类型命令/结果、应用错误码、会话身份，不暴露 IDispatch/IUnknown、BSTR、VARIANT、QAxObject、原始 HWND 或 COM apartment 操作。转换和资源管理放在 adapter/host，必要句柄只以明确平台协议封装，不伪称普通业务数值。

C++ 对象、窗口句柄、COM 对象和目标进程均有不同寿命；IsWindow 或句柄非零不证明目标仍是原实例。任务包含受控的目标身份/会话代际，重绑定后旧请求被拒绝。

## STA 所有权

每个实际使用 COM 的线程分别调用正确的初始化流程。CoInitializeEx 成功（包括 S_FALSE）与 CoUninitialize 配对；失败特别是 RPC_E_CHANGED_MODE 不得当成“已经可用”。在同一 apartment 创建、调用并释放对象，除非有明确、合法且经过验证的跨 apartment marshaling 契约。

STA 需要消息分发以支持 COM 调用；不要把整个线程永久塞进不泵消息的自制 wait 循环。Qt 的 event loop 可以成为线程执行结构的一部分，但要核对实际 Windows dispatcher 和 SDK 重入行为；同时避免重入时状态机重复执行命令。

关闭：拒绝新任务 → 清理/取消队列 → 在拥有线程释放接口及相关 wrapper → CoUninitialize → 线程退出。SDK 对象不能在 UI 析构或线程池任意节点释放；QThread::quit 也不代替 COM 清理。

## 位宽和进程选择

先核对相同进程加载的 EXE/DLL 位宽与 ABI。64 位进程不能直接加载 32 位 DLL；但这不等于 Qt 框架一律不能服务于 32 位场景。实际 Qt release 的支持矩阵、可得构建与 SDK 兼容需要单独验证。

| 已核实条件 | 处理 |
|---|---|
| UI 与 SDK 的进程内集成符合位宽/ABI及线程契约 | 沿用适配层与拥有线程，不为迁移强加进程 |
| 现有架构已采用独立 DmHost | 保留协议边界，Qt 只替换界面或 client 适配 |
| 必须 x64 UI + 仅有 x86 in-process SDK | 评估独立 x86 host 与有版本协议，不把 DLL 塞进 x64 UI |
| 位宽/SDK 能力未知 | 暂不改变二进制拓扑，继续独立 UI/模型设计与测试 |

进程隔离是需要明确授权的架构变更，不是所有 Qt 桌面工具的默认模板。仅窗口皮肤任务不涉及 COM/IPC 重构。

## 已采用 IPC 时的最低协议

请求包描述 protocol_version、session_id、generation、request_id、command、长度和 deadline/超时策略；字段按项目实际语义裁剪，不能缺少区分重连会话与重复请求的机制。

不要跨进程传指针、QObject、COM 接口裸值、原始 QModelIndex 或直接 memcpy 本地 C++ struct。wire 格式声明固定宽度、字节序、字符串编码、范围、最大消息长度和未知字段策略；内存对齐不等于序列化协议。跨进程时钟不应假定同一 epoch，deadline 用双方明确约定的时间基准或接收端预算。

本地通信也校验访问权限、对端身份、协议协商、消息长度和状态，不因“只在本机”就接收任意命令。有限队列、心跳和超时只发现故障，不证明 SDK 调用已取消或输入已回滚。

按键/鼠标等副作用命令区分 accepted、started、completed。连接断开后执行状态不确定，不自动重发非幂等命令。输入账本在拥有执行状态的一侧记录按下/释放；host 崩溃后清理能力取决于实际输入后端，不能承诺始终恢复。隔离、重试、补偿和人工恢复都要写明。

## 验证边界

纯测试替身覆盖命令排序、代际、超时、退出和失败语义。Windows 实测才覆盖 COM 注册、STA、真实 SDK、目标窗口、全局热键和跨位宽进程。替身通过不证明真实大漠已可用。

要测试初始化失败、不兼容 DLL、目标退出、连续重连、非幂等命令中途断线、host 启动失败与关闭清理失败。错误必须回到可诊断终态，不能一直显示“正在连接”。

依据：[Microsoft STA](https://learn.microsoft.com/en-us/windows/win32/com/single-threaded-apartments)、[CoInitializeEx](https://learn.microsoft.com/en-us/windows/win32/api/combaseapi/nf-combaseapi-coinitializeex)、[32/64 位互操作](https://learn.microsoft.com/en-us/windows/win32/winprog64/process-interoperability)、[Qt Windows 支持](https://doc.qt.io/qt-6/windows.html)、[来源中的 CopyQ/QHotkey](github-sources.md)。
