# 线程、异步与 COM/STA

## 1. UI thread ownership

MFC 窗口默认由创建它的 GUI thread 拥有。worker 负责耗时任务，不应直接调用控件更新方法。

推荐流程：

1. UI 建立 `RequestId` / generation，采集不可变输入；
2. worker 执行计算、I/O、SDK 调用；
3. worker 产出独立 result；
4. result 进入线程安全队列或作为有明确所有权的 message payload；
5. `PostMessage` 唤醒 UI；
6. UI 比较 request/generation，应用仍然有效的结果；
7. UI 更新控件。

这样可以区分“任务还在跑”和“这个窗口实例是否还需要结果”。

## 2. 为什么 `IsWindow` 不够

`IsWindow(hwnd)` 只能说明该时刻这个 HWND 存在。窗口销毁后句柄值未来可能被系统复用；旧 worker 可能把结果送给新的窗口实例。

因此异步协议至少再带一个业务 identity：

- generation counter；
- request id；
- shared state token；
- receiver-owned cancel token。

UI teardown 时增加 generation 或关闭 token，让迟到结果自然失效。

## 3. `PostMessage` payload 所有权

常见安全模式：

- sender `new Result`；
- `PostMessage` 成功后 ownership 转给 receiver；
- `PostMessage` 失败时 sender delete；
- receiver handler 立即包装 `std::unique_ptr<Result>`，保证早退也释放。

高吞吐不要每条记录一个 heap + 一个消息。改为 worker 批量放入 queue，UI 只收到一次“有新数据”通知，再 drain 一个有限 batch。

## 4. Cancellation 与 shutdown

取消是协议，不只是一个 bool：

- stop accepting new work；
- set stop/cancel flag；
- 阻塞 API 若可取消则触发其取消；
- worker 定期观察 stop token；
- UI 禁止再次触发同类任务；
- join 或等待 owned worker 完成；
- 再销毁 worker 会触碰的 state。

如果使用 `CWinThread*`，明确 `m_bAutoDelete` 与谁等待线程对象。不要保存一个已经 auto-delete 的 `CWinThread*` 后继续访问。

## 5. `SendMessage` 死锁边界

worker 同步 `SendMessage` 给 UI 会等待 UI handler 返回。若 UI 此时在等待该 worker 完成，就形成经典循环等待。

普通进度与结果通知默认用 `PostMessage`。只有协议确实需要同步且确认不存在等待环时才使用跨线程 `SendMessage`。

## 6. COM apartment

每个调用 COM 的线程独立初始化：

- UI/OLE 场景通常是 STA；
- worker 是否 MTA/STA 取决于 SDK；
- `CoInitializeEx` 成功的线程需匹配 `CoUninitialize`；
- `RPC_E_CHANGED_MODE` 不是“忽略继续”的普通成功。

不要把 STA interface pointer 当普通 C++ 指针跨线程传。选择之一：

- 所有调用留在创建它的 STA host thread；
- 使用 COM marshaling；
- SDK 明确支持 agile/free-threaded 后按其契约使用。

## 7. 专用 STA host

第三方自动化/识图插件很适合：

`UI -> command queue -> STA host -> COM object`

`STA host -> result queue/PostMessage -> UI`

host thread 唯一拥有：

- COM 初始化；
- COM object 创建/释放；
- SDK 原始句柄；
- BSTR/VARIANT 转换；
- SDK-specific retry/error mapping。

Pimpl 可以进一步让公开头文件完全看不到 COM 类型。

## 8. 外部项目证据

WinMerge 当前源码能看到 `AfxBeginThread`、异步 task、atomic cancel/shared state 和 `PostMessage(WM_APP+...)` 结果投递。它证明成熟 MFC 项目仍会使用 MFC worker thread 与消息回 UI，但它的具体 heap payload 写法不是唯一正确实现。

TortoiseGit 多个 dialog 使用 `AfxBeginThread` 避免阻塞窗口，并维护 running/cancel 状态。部分旧代码仍会在 worker 路径触碰 dialog/control，因此蒸馏时只采纳“异步、取消、状态可见性”的机制，不把每个历史线程访问模式当作新项目模板。
