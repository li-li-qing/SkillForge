# Desktop / addon 审查（2026-11-07）

范围：四个SKILL均已读取；深入读取ArcheRage四脚本和测试，MFC/UI references，Qt线程与发布和来源清单。其余Qt/addon主题未逐段穷尽，本轮不宣称全覆盖。未修改技能库、用户协作规则，未安装、推送或运行Windows/Qt/游戏。

## 结果

P1 AR-LUA-01 — scripts/check_lua51.py:52 仅拒绝首字节ESC，但Lua5.1 loadfile跳过以#开头的首行后接受字节码。输入 b"#!/usr/bin/lua\n\x1bLua..." 能通过Python文本门禁，接着进入loadfile二进制解析；这不是已证明目标chunk执行，仍违反text-only承诺。官方5.1.5源码 https://www.lua.org/source/5.1/lauxlib.c.html#luaL_loadfile （网页行562–576）直接支持。最小修复：按Lua首行规则定位有效首字节并拒绝ESC；用内存bytes断言，不运行未知字节码。补LF/CRLF shebang、普通文本、直接ESC四类测试。

P2 AR-LUA-02 — check_lua51.py:53 validated保存所有文件bytes。单文件4MiB、2000文件可积累约7.8GiB内存，缺总预算，正常大目录会OOM。最小修复增加MAX_TOTAL（如128MiB，按实际项目确认），读每个文件后、append前累加；用小预算模拟两个文件越界，禁止实际分配GiB。每文件5s超时也不限制全轮总耗时，建议整体deadline。

P2 UI-SNAPSHOT-01 — references/gameplay-ui-projection.md:43及commonui-input-routing-patterns.md:170先快照再订阅。单一游戏线程且无重入同步段通常安全；若跨异步边界/可重入回调，夹在两步间的一次变更永远丢失。规则缺适用前提。最小修复写明同线程无yield事务，或先订阅后取带revision快照并丢弃旧delta；添加snapshot与subscribe间mutation反例。现有compare-and-rebind段反而采用绑定后重新快照，可统一。

P2 EVAL-01 — MFC/UI/Qt现有题集与验证指南不等于运行记录；本轮未找到这些技能专属可执行桌面集成测试。无需强建框架：提供每类3个带输入证据与关键失败标准的真实Agent评测记录，再按环境补平台测试。ArcheRage测试中的R3RegressionLessonsTests只查关键词/案例ID，不能证明事件参数语义遵守；维持结构与行为证据分开。

Qt优点：明确wait与finished差别、deleteLater及COM清理时机、阻塞取消不可伪装成功；未发现足够证据支持新的Qt线程技术错误。MFC优点：payload所有权、generation、COM线程与DPI矩阵齐全；窗口关闭后已成功Post的payload回收仍宜用具体队列fixture验证，不能仅凭文字认为实现正确。

## 本轮测试

已审读脚本后运行：env -u RS_TEST_LUA51 PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s ida_delivery_work/Skills/skills/skillforge-archerage-addon/tests -q
只读初次：38 tests，19 errors（tempfile无可写目录）、2 skipped，非产品失败。获准提升运行范围后：38 tests in 0.357s，OK (skipped=2)，即36通过、2真实Lua测试未运行。无Lua目标chunk执行。未进行Windows/MFC、Qt、COM或游戏实机测试。

## 官方边界与外部Skill

Lua固定5.1.5官方源码见上链接。Qt官方 https://doc.qt.io/qt-6/qthread.html 当前网页标6.12.0，isCurrentThread/isMainThread为6.8、QoS为6.9；不能将浮动qt-6链接当最低Qt版本证明。现有技能要求按实际小版本核对是正确的，建议source manifest补文档读取日期与最低版本列。

外部项目：anthropics/skills，webapp-testing，固定目录最近提交 b9e19e6f44773509fbdd7001d77ff41a49a486c1，2026-04-20T21:38:16Z（GitHub commits API本轮查询）；目录许可证Apache-2.0。https://github.com/anthropics/skills/tree/b9e19e6f44773509fbdd7001d77ff41a49a486c1/skills/webapp-testing 。仓库仍公开且有活跃issue/PR入口；未将其等同维护响应承诺。源码审查读取的是main，固定SHA已解析但文件内容未再次逐字核对，采用前需固定提交复核。

可采用：先读取已渲染状态再动作、截图与交互分离、server生命周期try/finally模式；这些机制可用于桌面测试夹具思想而非直接引入Playwright控制原生Qt。不可原样采用：SKILL要求先运行再读黑箱脚本，不符合本次未知脚本审计；with_server.py以端口可连当就绪、shell=True、stdout/stderr PIPE未持续排空，不能当可靠桌面host启动器。不要把所有动态页面等待networkidle当普遍必需。只建议蒸馏方法，不安装/复制。

外部证据：https://raw.githubusercontent.com/anthropics/skills/main/skills/webapp-testing/SKILL.md 、scripts/with_server.py 、LICENSE.txt（同目录）。

## 最小修复草案（未实施）

优先AR-LUA-01首行探测加4个纯bytes测试；再AR-LUA-02总字节预算与轻量边界测试；最后UI-SNAPSHOT-01补适用前提和变更夹缝案例。维持所有协作级别/授权规则不变。全库发布前，明确本轮离线工具通过不能替代Agent行为或实机验收。

## 父线程交叉复核补充

P1 MFC-POST-01 — skillforge-mfc/references/threading-com-sta.md:34–39 将new Result、Post成功转移receiver、handler unique_ptr称为常见安全模式，漏掉Post成功后窗口关闭而handler未消费的释放路径。后文queue仅作为高吞吐优化，不足以约束此路径。最小修复：标明原模式仅在保证消费/显式排空协议时成立；默认owning mailbox持unique_ptr，消息只作wake token；close关闭入口、同步停止producer并discard/drain mailbox，最后销毁窗口。行为案例：成功Post后handler前close，payload恰好析构一次；Post失败、重复close、HWND复用也不泄漏/双释。微软PostMessageW说明投递是排队：https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-postmessagew （官方链接由父线程核对，本子线程未重新浏览）。

## 收尾实施（独立副本）

目标 overnight_review_20261107/Skills。Lua总预算已用两个8字节fixture、模拟MAX_TOTAL=15重现：40 tests，1 failure、2 skip；修复后MAX_TOTAL=128MiB，累计后append前拒绝，16字节边界仍允许，40 tests / 38通过 / 2 skip。所有Lua subprocess均mock，未执行字节码；真实Lua未配置。

MFC补STA消息分发与重入（Microsoft官方已本轮打开核对），UI/Qt补图标按钮辅助名称角色值状态、系统字体与DPI分别检查及目标辅助工具验证。非颜色表达原有layout-patterns已覆盖，新增段只串联到局部验收而非重造规范。各增加一条behavior case，execution_status=not_run。未修改协作等级或增加强制全量审查。

官方：https://learn.microsoft.com/en-us/windows/win32/com/single-threaded-apartments 、https://doc.qt.io/qt-6/accessible.html 。之前外部Skill固定SHA缺口已经external-source.json三个固定提交文件抓取与哈希补齐。

## 本轮最终状态（覆盖开头只读阶段的时态）

原库始终未改；独立副本 overnight_review_20261107/Skills 已实施以下修复：Lua shebang字节码门禁与128MiB总预算、对应mock RED/GREEN回归（40项38通过2 skip）；MFC Post成功未消费的owning mailbox与关闭协议、STA消息泵/重入；Qt/UI辅助语义与字体放大验收；UI两处快照后订阅规则补同线程无yield/无重入前提及revision方案，新增UI-SNAPSHOT-GAP-01未运行行为题。

随后按父线程授权集成外部方法：experience-maintenance新增自包含references/skill-evaluation.md及SKILL按需链接；IDA mcp-adapters补失败路径合同表和注解非权限；preflight risk-review只在实际跨信任边界时补条件性证据。引用固定Anthropic 2c5958ecac7cee2b583967a2c4981d0f4a75c579、OpenAI 49f948faa9258a0c61caceaf225e179651397431；Apache-2.0仅对应所读技能目录，中文原创归纳，无代码复制/安装/新流程强制。未触碰experience_store及其测试。

最终静态检查：上述6个文档UTF-8及全部本地链接通过；UI behavior JSON可解析、11个案例ID唯一且具prompt/expectations。新增行为题均not_run，未运行模型A/B或真实Windows/Qt/COM/IDA/游戏。
