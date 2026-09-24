# Model/View：身份、增量与性能

## 何时使用自定义 model

小型、静态选择框不必全改成复杂 model。持续增长的日志、任务树、会话状态、扫描结果等，优先 QAbstractListModel/QAbstractTableModel 加 view/delegate；树模型只有真实层次需要时才使用。

不要为几万行每格创建 QWidget。delegate 绘制与编辑器按可见/正在编辑范围工作；性能瓶颈通过采样、耗时、队列深度和内存实测定位，不以“Qt 理论很快”代替数据。

## 核心不变量

| 对象/动作 | 必须保证 |
|---|---|
| 行/列边界 | rowCount/columnCount/index/parent/data 在非法 index 下安全 |
| 插入、删除、移动 | begin... → 实际数据修改 → end...；范围与修改数量完全一致 |
| dataChanged | 只通知真实变化的范围和角色；不能代替结构变化通知 |
| reset | 仅整个投影确实替换时使用，知道索引/选择会失效 |
| QModelIndex | 是某 model 的短期索引，不是可存档业务主键 |
| QPersistentModelIndex | 遵守 model 变更后可保持部分身份；删除/reset 仍可能失效，不是永久 ID |
| 排序代理 | 先 mapToSource/mapFromSource，再获取稳定业务 ID；不能把 proxy.row 直接发引擎 |
| createIndex 指针 | 被引用存储必须稳定；vector 扩容可能使 element 地址失效 |

GUI 所使用的 model 不让 worker 直接 append/remove。worker 产生拥有关系明确的值批次，UI 线程串行提交 model 修改；不能因为 API 是 public 就从任意线程调用。

## 大量数据的数据流

```text
采集/计算线程 → 有界批次或有界队列 → UI 投影适配 → Model → View
                 配额/背压/代际检查       批量通知
```

先规定行数与字节数上限、最大单条长度、批次预算和队列满策略。日志采用有界保留和可查询的丢弃计数；进度可合并为最新值；错误、任务终态和清理失败不能当普通进度静默丢掉。关键事件需要容量保留、可靠交接或明确降级，不把无限队列伪装成可靠性。

重建、排序、过滤可能是 O(N)，不能承诺所有 model 操作只 O(visible)。将昂贵计算放到适当后台阶段，通过 generation/revision 判断结果是否仍适用；view 绘制和热读取尽量只接触当前数据。

data()、delegate paint、比较器和高频过滤回调不进行 I/O、COM、图片解码或反复编译复杂正则。昂贵预计算缓存按数据、筛选条件、主题和 DPR 变化失效。不得每次刷新整表 resizeColumnsToContents 扫所有历史记录。

增量更新保留：选中项的稳定 ID、展开集合、滚动位置、编辑草稿。日志自动滚动仅在用户处于跟随尾部状态时启用；用户向上阅读后不要强制拉回底部。

## 排序编辑错行：必测场景

有两条任务 ID A/B，代理顺序与 source 顺序不同。编辑代理第一行，只允许对应的业务 ID 改变；更新造成再次排序时，仍使用捕获的 ID 和预期 revision，不重新读取可能已改变含义的行号。删除选中项、过滤掉编辑项、异步旧结果返回都应有明确行为。

把该场景写成 model/service 测试，而不只 assert 表格行数。QAbstractItemModelTester 用于结构契约，业务身份映射仍需单独断言。

## 内存与数据结构

Qt 隐式共享值类型不等于共享可变对象线程安全。只读快照按值交接可减少拥有关系复杂度；写入仍需所属线程/同步。不要为避免一次拷贝而传悬空 buffer、指向 QVector 元素的临时指针或 UI 对象。

按测量结果处理 reserve、批次与缓存布局。频繁由多个线程写同一 cache line 才考虑拆分 hot state；不要普遍 alignas(64) 膨胀所有行对象。结构体天然对齐与 wire serialization 分开；不能用 packing 把整个内存布局直接发 IPC。

## 来源与验证

Wireshark 切片展示物理记录、可见投影和帧号映射；这不表示其所有通知顺序、全局对象或容量常量都适合新工程。新 model 以 Qt 正式契约为准，配合模型测试而非照抄现成代码。

依据：[QAbstractItemModel](https://doc.qt.io/qt-6/qabstractitemmodel.html)、[QSortFilterProxyModel](https://doc.qt.io/qt-6/qsortfilterproxymodel.html)、[QAbstractItemModelTester](https://doc.qt.io/qt-6/qabstractitemmodeltester.html)、[Wireshark 切片](github-sources.md)。
