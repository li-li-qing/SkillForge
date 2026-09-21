# DPI、布局与复杂控件

## 1. DPI 设计原则

对现代 Windows，新工程优先使用 manifest/应用配置声明合适的 Per-Monitor DPI awareness，并为 DPI 变化设计资源重建。历史工程若只能先用 System DPI awareness，也应把它标成迁移阶段，不把限制固化到新控件。

把以下尺寸集中到可缩放来源：

- margin/padding；
- row/header height；
- icon/bitmap；
- font；
- splitter width；
- min/max window size；
- custom hit-test rectangle。

不要只缩文字不缩 hit box，也不要只缩控件不重建 bitmap/font。

## 2. `WM_DPICHANGED`

典型处理：

- 接收新 DPI；
- 应用系统建议 window rect；
- 更新 DPI cache；
- 重建 DPI-dependent font/icon/bitmap；
- 重新 layout；
- invalidate 必要区域。

不要把同一 resize 链同步递归触发多次。若 layout setter 会再次造成 `WM_SIZE`，使用 reentrancy guard 或 posted layout request 合并。

Microsoft Comic Chat 的 2026 现代化记录就专门修复了 resize/reflow 重入：面板列数重算改为 posted message，避免 `SetPanelsWide -> WM_SIZE` 的递归崩溃。这个机制值得保留，但其 `SetProcessDPIAware` 属于旧工程兼容方案，不推广成新工程首选。

## 3. 位置持久化

保存窗口位置时同时考虑：

- 当前 monitor work area；
- DPI；
- maximized/minimized state；
- 多显示器减少或顺序变化；
- 最小可见区域。

启动恢复后做 clamp/repair，保证 title bar 或可拖动区域可见。

## 4. Resizable dialog

不要用硬编码像素在 `OnSize` 里逐个 `MoveWindow` 叠补丁。可采用：

- MFC Dynamic Layout；
- 项目已有 anchor/resizable library；
- 明确的自定义 layout manager。

选哪一个取决于当前工程，不因为新 Skill 强制迁移。

## 5. CListCtrl / Tree / 大数据

数据量大或高频刷新时：

- owner-data/virtual list 让 UI 只请求可见项；
- stable row/item identity 与 visual index 分离；
- 排序/过滤先在 model 中完成，再一次发布 snapshot；
- 批量更新时冻结重绘并恢复 selection/scroll anchor；
- 高频更新合并到固定帧/节流窗口，不一条业务事件就全表刷新；
- custom draw 只读已经准备好的轻量 view data。

如果用户正在滚动或编辑，自动“跟随最新”必须暂停，不能每次 append 把滚动条拉回底部。

## 6. 自绘与 flicker

先区分：

- background erase 闪烁；
- 每项 invalidation 过多；
- 控件主题反复切换；
- parent/child 同时 paint；
- GDI object 每帧创建销毁。

double buffering 只解决其中一部分。不要看到闪烁就无条件加 `WS_EX_COMPOSITED`，它可能改变子窗口绘制与性能。

## 7. 输入与可访问性

- tab order 与 `WS_TABSTOP` 保持逻辑顺序；
- default/cancel button 与 Enter/Esc 行为明确；
- `PreTranslateMessage` 不吞掉 IME、标准编辑快捷键和 accessibility 所需事件；
- owner-draw 控件仍要提供文字、焦点和状态反馈。
