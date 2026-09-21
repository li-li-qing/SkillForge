# 架构、消息与命令

## 1. 先画出当前 MFC 对象图

最低限度确认：

`CWinApp` → Main Frame / Dialog → View / Child Dialog / Docking Pane → Control → service/model/adapter。

同时标出：

- 谁持有业务状态；
- 谁只有显示 snapshot；
- 谁可以发 mutation command；
- 哪些对象跟随窗口销毁，哪些跨窗口长期存在；
- 哪些消息是 Windows/MFC 原生消息，哪些是项目自己的异步协议。

大型 MFC 项目最常见的问题不是继承层级不够漂亮，而是 Frame、Dialog、Control、全局单例都能直接修改同一份业务状态。修复时优先收敛 writer，而不是先改类名。

## 2. Command routing 是 MFC 的优势，不要绕开

菜单、工具栏、快捷键若表达同一个动作，使用相同 command ID 和 command handler。可用性状态由同一处 `ON_UPDATE_COMMAND_UI` 计算，避免：

- 点击按钮能执行，但菜单灰掉；
- 快捷键绕过 validation；
- toolbar 自己缓存 checked state，菜单又缓存一份。

已有 Doc/View 工程中先检查 command target 链；不要在子控件里直接找全局 MainFrame 调函数，除非当前架构明确就是这样且迁移没有收益。

## 3. Doc/View 的边界

适合：

- 文档具有打开/保存、修改标记、多个 View、打印或 MDI 语义；
- View 是同一文档状态的不同投影。

不适合强行引入：

- 纯设置工具；
- 单窗口状态监视器；
- 后台引擎只是向多个 pane 推只读 snapshot 的工具。

已有 Doc/View 工程不要反向塞回巨型 Dialog；文档状态尽量不依赖具体控件 HWND。

## 4. Adapter / Model / Presentation

推荐依赖方向：

`MFC UI -> application service -> domain/model`

`MFC UI -> adapter interface <- COM/SDK adapter`

边界数据优先项目自有 value type。外部 COM 或 SDK 内部可以继续使用 HRESULT、BSTR、VARIANT、HANDLE，但跨出 adapter 后应转换为：

- UTF-16/string value；
- enum/status；
- POD/immutable result；
- RAII resource wrapper；
- 明确错误对象。

这样 UI 单测与 Model 测试不需要启动真实 COM 插件。

## 5. 多进程是架构手段

TortoiseGit 的成熟架构把 Explorer shell extension、主 GUI、后台 cache、diff/blame 等工具拆成不同 EXE/DLL，GUI 命令再调度它们。可迁移的不是它的具体进程名，而是：

- shell extension 保持轻量；
- 长时缓存与 Explorer 生命周期解耦；
- 重工具崩溃不拖垮所有交互；
- 进程间契约可单独诊断。

如果当前应用只是小型单 EXE，不为了模仿大项目强拆进程；只有隔离、生命周期或稳定性收益明确时采用。

## 6. 自定义消息协议

项目统一定义消息：

- message id；
- `WPARAM/LPARAM` 含义；
- payload 谁分配、谁释放；
- 允许在哪个线程发；
- receiver 销毁时如何处理；
- 是否带 request/generation id。

复杂 payload 不要把栈地址塞进 `PostMessage`。若 heap payload 由 receiver 释放，发送失败时 sender 必须回收。

在同进程内，私有异步协议通常集中使用 `WM_APP + offset`。跨 DLL/外部组件确需名称协调时再考虑 registered message。

## 7. 反模式

- `GetParent()->GetParent()->...` 穿层找主窗口执行业务；
- 多个 dialog 直接写全局 mutable singleton；
- 在 `WindowProc` 里堆所有业务逻辑；
- 资源 ID 同时充当持久化 schema、网络协议和业务 identity；
- 为了“解耦”增加字符串消息总线，却没有 typed contract 与 owner；
- 从 worker 持有裸 `CDialog*` 并持续调用成员更新 UI。
