# 窗口生命周期与资源所有权

## 1. 三层寿命

不要把以下三个对象等同：

1. C++ wrapper，例如 `CDialog` / `CWnd` 对象；
2. Win32 window，即 `HWND`；
3. 业务 receiver/model/token。

modeless 窗口最容易出现“HWND 已销毁但 C++ 指针还在”或相反的情况。

## 2. Modal 与 modeless

Modal：通常局部对象 `DoModal()`，返回后由正常 C++ 生命周期释放。

Modeless：先确定 owner pattern：

- parent/member owns object：窗口销毁不自删 C++ 对象；
- heap self-owned：结束时在正确的 `PostNcDestroy` 等路径释放；
- smart-owner：owner 持有对象并监听窗口结束，统一 reset。

不能同时 parent delete 和 `delete this`。

## 3. 销毁阶段

常见职责：

- `OnClose`：用户请求关闭，可做 dirty-check/取消；
- `OnDestroy`：HWND 销毁阶段，停止 timer、解绑依赖 HWND 的 callback；
- `PostNcDestroy`：非客户区销毁完成后，适合某些 self-owned MFC object 的最终对象处理；
- destructor：纯 C++ 成员资源最终释放，不能假设 HWND 仍可用。

具体类层级先看基类实现再 override。

## 4. Temporary MFC wrappers

`CWnd::FromHandle`、某些 GDI `FromHandle` API 可能产生 temporary wrapper。返回指针只适合当前受控调用，不要长期缓存到成员并假设永久有效。

若已有真实 MFC control member，优先保存该成员或其明确 owner，而不是再次从 HWND 制造 wrapper identity。

## 5. GDI 资源

每类资源写 acquisition/release table。例：

- `BeginPaint` ↔ `EndPaint`，在 MFC 中优先 `CPaintDC`；
- `GetDC` ↔ `ReleaseDC`；
- `CreateCompatibleDC` ↔ `DeleteDC`；
- `CreateFont/CreateBitmap/CreateBrush` ↔ `DeleteObject`；
- 从 `SelectObject` 换入自有 object 后，销毁 DC/object 前恢复原 object；
- stock/shared object 不按 owned object 删除。

优先让 `CFont/CBitmap/CBrush/CDC` 或自定义 unique handle 管理 owned resource，但要确认 wrapper 是否 attach 后取得所有权。

## 6. Menu/Icon/Cursor

Win32 不同加载 API 的 ownership 不同。不要根据类型名统一 `DestroyIcon/DestroyMenu`。记录：

- resource/shared handle；
- copied/created handle；
- attach 到哪个 MFC object；
- 谁最后销毁。

MFCMAPI 的 BaseDialog 代码会明确区分 `LoadIcon` 不需要后续销毁，同时对动态 menu 做 `DestroyMenu`，这种“逐 API 确认”比统一清理规则可靠。

## 7. COM interface 与 reference count

旧项目常用裸 interface + `AddRef/Release`；新代码可以用项目已采用的 COM smart pointer，但必须确认：

- 输入参数是 borrowed 还是 transferred；
- getter 是否 AddRef；
- cache 是否共享 ownership；
- callback sink 的 unadvise 是否先于 sink 释放；
- apartment shutdown 是否晚于 interface 释放。

MFCMAPI 当前 BaseDialog 既有 shared_ptr 管理的 cache 对象，也有显式 COM `AddRef/Release` 与 notification unadvise。蒸馏重点是“所有权写在边界上”，不是要求所有历史 COM 立即改成一种智能指针。

## 8. Async receiver teardown checklist

窗口关闭前检查：

- timer 已停；
- registered callback 已解绑；
- worker 不再接受新任务；
- generation 已失效；
- queue payload 能被 drain/释放；
- modeless self-delete 不会让 worker 留下裸 `this`；
- app exit 时 background thread 不再访问 MFC module state。
