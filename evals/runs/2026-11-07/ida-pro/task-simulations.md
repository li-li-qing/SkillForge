# 八项任务桌面推演记录
日期 2026-11-07；执行方式：维护者按实际技能文档手工走查。下面输入为合成场景，地址不是用户样本；没有真实 IDA、独立模型 A/B 行为实验或游戏运行。每项“符合”仅指此次桌面推演产出的决策符合约束，不是运行功能通过。

## 1 普通 Windows DLL
输入：只给 demo.dll，架构未知，当前环境没有 IDA。
实际推演：先复用通用逆向 probe_binary 计算文件 hash/解析 Machine；没有文件字节时 hash=unknown。不从 DLL 后缀猜 x64。待 IDA 时核 loader、自动分析、imports/exports/strings，然后只筛有限函数。输出“IDA 函数数/反编译=未执行”，不能编造。
结果：文档路径可定位，环境缺失分支符合；真实 DLL/IDA 待测。

## 2 字符串定位
合成输入：字符串 EA=0x140004100，数据 xref 到 0x140005000，代码 xref 从 0x140001020；包含函数 0x140001000，next_index=100。
实际输出：保留字符串→指针表→代码的两段证据，不将数据地址叫函数；读取函数 chunks/汇编并以 next_index 续页。只能写“已扫描页的候选函数”。
结果：符合；真实字符串编码/缓存状态待测。

## 3 调用链
合成输入：A 的 callsite 0x140001030 直接调用 B；B 在 0x140002040 为未解析 call；C 尾跳到 B。
实际输出：A→B 标 direct-call；B→unknown 标 unresolved；C→B 需另核 tail-call，不由 callers() 直接输出。双向追踪保存每条 callsite，环和范围设限。
结果：符合；不称完整动态调用图。

## 4 IDAPython 批量导出
输入：大型 IDB，要求导出函数/字符串/伪代码。
实际方案：functions_page 每100项及 next_ea；GUI 字符串用 timer iterator，后台单 iterator；反编译只收明确地址、每批最多20，记录每函数耗时和失败。JSON/CSV/Markdown 通过独占本地输出，报告覆盖和截断。
结果：脚本入口存在且离线调用白名单核验；IDA性能/UI实际待测。

## 5 简单 C++ 类
合成输入：本技能 class-recovery.md 中构造/读取/分配证据。
实际输出：vptr@0，32-bit value@8，unknown[4]@0x0c，pointer@0x10，总候选0x18。字段业务语义和类名为推测；验证 this 调整、分配契约与其他读写后才应用。
结果：候选布局自洽，仍非真实二进制恢复。

## 6 UE 类反射
输入：UE5 Shipping 无PDB，只有 ClassName 字符串，未知小版本。
实际输出：类归属=推测；补注册 owner/父类/UFunction 关联及匹配源码，记录具体地址。缺完整反射时转构造/虚表，不提供固定 UObject 偏移。
结果：符合；未取得目标源码、反射或布局证据。

## 7 RPC 相关函数
输入：名称 ServerMove_Implementation，无 flags 或网络轨迹。
实际输出：RPC 候选，置信度推测。下一步检查匹配版本 UFunction flags、注册 thunk、调用空间和网络分派；只见名称不能升“已验证”。属性复制需独立 lifetime/条件证据。
结果：符合；真实 RPC 未验证。

## 8 证据与置信度报告
合成条目：
- target：demo.dll（未提供）；SHA-256/架构/IDA版本：unknown；时间：2026-11-07 UTC；
- 函数：0x140001000（教学 IDB VA）；名称 CandidateInit（分析者命名）；
- xrefs：0x140002010（教学 call-site）；结构：CandidateObject；
- 证据：class-recovery.md 的合成 this+8 四字节写；
- 判断：可能含32-bit字段；置信度：推测；未决：真实样本、ABI、this起点、字段语义；
- 动态验证：未执行；IDB修改：无。
结果：模板能够表达缺失与证据范围；不把合成地址或空 hash 当真实验收证据。

## 后续真实验收
自编译小 DLL + PDB + 可控字符串/直接与间接调用/类；先只读逐项对照，再明确授权一项名称/类型/结构体操作，核日志与恢复副本。UE 用自有 fixture 的 Development/Shipping 配置对照。每个环境记录版本、样本 hash、命令、预期、实际与失败，不能用本报告替代。
