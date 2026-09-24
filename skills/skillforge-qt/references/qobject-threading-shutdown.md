# QObject、异步与关闭：拥有者、线程和请求身份

## 三个维度不要混为一谈

C++ 对象是否存活、QObject 属于哪个线程、业务请求是否仍是当前请求，是三项独立条件。QPointer 非空只帮助判断被观察 QObject 尚未销毁，不意味着正在正确线程、不意味着会话没有重置。

parent 托管、RAII 独占、非拥有观察分别标明。QObject 通常由 parent 释放；没有 parent 的普通资源可用 unique_ptr。不要给 parent-owned QObject 再配置独立释放的 shared_ptr/unique_ptr。外部 C API 句柄根据实际 deleter 管理，不机械套 delete。

## 信号槽与捕获

优先类型安全 connect；带 lambda 时提供生命周期 context，避免无上下文捕获 this。捕获能独立存活的值、request ID、session generation；临时引用、栈变量和裸 UI 指针不要跨异步边界。

自动断连防止向已经销毁的 receiver 调用，但 disconnect 不撤回已投递的全部业务事件，也不使已完成但过期的结果重新有效。接收端仍检查身份/状态。窗口切换目标、任务重启、host 重连都更新代际；必要时先撤销当前请求再解绑。

AutoConnection 的判断涉及发射时所在执行线程和 receiver affinity，不是看 sender 对象最初在哪里创建。跨线程排队参数需要可复制、可存活，使用目标 Qt 版本所需的元类型声明/注册；“编译成功”不证明运行时 queued invocation 没有类型错误。

## QThread 的两种合法用途

- 事件驱动服务：worker QObject 无 parent 地迁移到线程，在线程中的初始化步骤创建需要该线程事件循环的资源。
- 受控 run 实现：QThread 子类可封装自足任务或 STA run 生命周期；构造与 run 所在线程不同，普通槽不会因写在该子类上自动进入 run 线程。

不能 move 一个有 parent 的对象到另一线程。QObject 的成员变量不自动等于子对象；构造函数在 UI 线程创建的 timer/socket 若未正确归属，迁移外层对象不自动修复它们。核对创建、parent、moveToThread、启动/停止和销毁的位置。

Qt 线程池适合可并行且没有固定 apartment/事件循环依赖的工作，不是任意 COM 对象的执行容器。QThread 的事件循环也不等于已经调用 CoInitializeEx。

## 取消协议

quit 让事件循环退出，不强制打断正在执行的长槽。requestInterruption 是协作信号，工作代码必须检查。若一个槽持续阻塞，排到同一线程的 cancel 槽不能及时运行。

对可分割工作使用有界片段和线程安全取消 token；对 SDK 支持的取消调用核实线程和重入约束；对无法中断的调用记录 deadline 和“取消已请求、正在等待调用返回”，不能立即向 UI 谎报 Stopped。具有强隔离需求时单独设计宿主进程，不对每个普通任务强制 IPC。

BlockingQueuedConnection 需要证明无互等、receiver 事件循环可运行且生命周期覆盖调用；本技能不把它作为通用同步桥。UI 正在 join worker 时，worker 同步等待 UI 是典型死锁，不能靠延长超时处理根因。

## 关闭顺序与异常路径

| 阶段 | 必要动作 | 验证点 |
|---|---|---|
| 拒收 | 标记 stopping，关闭新任务入口 | 菜单/热键/外部入口一致拒绝 |
| 请求取消 | 取消待处理命令，向运行任务发协作取消 | 重复取消幂等，未开始任务不再启动 |
| 拥有线程清理 | 停 timer、解绑回调、释放 SDK/COM 资源 | 失败也有终态，释放线程正确 |
| 线程收尾 | 资源清理后退出事件循环/run；按契约等待同步完成 | 不销毁普通运行中的 QThread，不假 join |
| 展示终态并退出 | 丢弃旧结果、完成日志与状态保存，再结束主循环 | 不依赖已停止事件循环处理关键清理 |

窗口 closeEvent 可先进入 stopping 并暂缓真正销毁，保持 UI 消息循环响应；结束后重新完成关闭。不要在主循环仍承担 worker 回调时阻塞等待 worker。最终 wait 若确需使用，要在无反向依赖的路径执行并检查返回值；timeout 不是已完成。

QObject::deleteLater 依赖事件循环/线程收尾的具体时机；QThread::finished 连接 worker::deleteLater 是 Qt 的常用收尾方式，但 COM 资源若需要在 CoUninitialize 前销毁，应先显式在拥有线程释放，不能寄希望于之后的 deferred deletion。

finished 已发出与所有线程局部析构完成不完全等价；需要与全部线程后效应同步时使用成功返回的 wait。特殊 API（如不同 Qt 版本的 QThread::create 析构行为）按版本核查，不泛化到所有 QThread。

## 调试记录与测试

日志至少按需含 request ID、generation、状态变迁、发出/处理线程标识、取消与完成原因；敏感数据脱敏，不把图像识别原始内容或凭据塞入普通日志。

测试：启动即关闭、初始化失败、快速启动/取消、取消晚于完成、重复取消、receiver 销毁、对象未销毁但代际变化、阻塞 SDK、清理失败、反向 UI 调用、重复打开窗口。用可控假 service 触发时序，不靠固定 sleep“恰好没崩”。

案例：QHotkey 在检查的版本里跨线程注册会同步等主线程，主事件循环先停后销毁 worker 热键会卡死。可选择主线程热键服务、异步分发任务意图，而不是搬来该阻塞桥。详见 [来源](github-sources.md)。

依据：[QObject](https://doc.qt.io/qt-6/qobject.html)、[QThread](https://doc.qt.io/qt-6/qthread.html)、[QPointer](https://doc.qt.io/qt-6/qpointer.html)、[Threads and QObjects](https://doc.qt.io/qt-6/threads-qobject.html)。
