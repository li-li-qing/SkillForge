# Desktop请求边界澄清

2026-11-07；v5文档/未运行行为题的小范围修订，未修改脚本、未发布。

MFC依据微软官方 https://learn.microsoft.com/en-us/windows/win32/controls/list-view-controls-overview ：LVM_SETITEMCOUNT范围内任意条目应可供数；LVN_ODCACHEHINT只是缓存建议，LVN_ODFINDITEM支持快速键/查找。替换“只请求可见项”，补非可见与缓存未命中反例。

Addon完整阅读callback-and-request-contracts与combat-and-price-contracts后，确认前文虽已明确generation不是无ID响应证明，冷却段和AR-55仍可被读成只凭路线/代次接收。改为响应归属证据，加入R1(A)超时→R2(A)→R1无ID迟到的具体反例；串行和超时本身不能排除旧响应。样本缓存更新与新请求完成分开。

共享询价原“关闭Feature/取消清排队请求”缺owner边界，补consumer lease释放及其他消费者仍可正常收到结果的正例。这是文档合同歧义审查，不是确认RU游戏存在运行故障。没有读取真实Native请求实现或实机复现，因此不推定任何具体服务端取消、延迟上界或事件字段存在。

新增MFC-OWNERDATA-RANGE-01、Addon两题，修AR-55评分条目，均not_run。验证仅JSON、引用与包结构；没有Windows列表/游戏实测。

## Qt布局与输入会话追加核验

Qt当前官方6.12.0布局管理的Tips明确已安装layout自动reparent，QLayout说明parentWidget未安装时可为空，removeWidget保持widget所有权，replaceWidget不改旧widget parent。已修原“仍需明确parent”的歧义，不再暗示每个构造必须手动传parent；仍保留独立layout安装与动态替换生命周期检查。来源：https://doc.qt.io/qt-6/layout.html 、https://doc.qt.io/qt-6/qlayout.html 。

输入ledger增加owner/session和执行不确定状态。取消不能释放他人/物理按键，是否安全配对取决于后端真实隔离与仲裁合同。微软SendInput只证明插入计数及现有键状态可干扰，不证明大漠实现或会话独占。来源：https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput 。无实际大漠后端证据，全部按条件性合同表达。新增两条QT题均not_run；未运行Qt/Windows输入或改脚本。
