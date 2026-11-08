# IDAPython API 与可执行示例
核实日期：2026-11-07。目标 API 基线为官方 IDAPython 9.0 文档；例程目标 IDA 9.x/Python 3，靠模块/能力探测拒绝不支持项。**没有任何 IDA 版本在本轮实际运行通过**。8.x 需要移植而不是无条件支持；IDA 9.x 的版本范围也不是兼容保证。

## 分类索引
| 模块 | 常用入口/用途 | 版本或语义注意 |
|---|---|---|
| idaapi | 兼容聚合命名空间 | 新代码优先显式 ida_*，避免把聚合别名当长期规范 |
| idautils | Functions、FuncItems、Chunks、Strings、XrefsTo/From | Functions 可能重复跨段 chunks；Strings(False) 只读现有列表 |
| idc | ARGV、get_type | 受支持包装可用，不一概禁用；核返回 None |
| ida_funcs | get_func、get_func_name、get_func_qty | 返回 None 表示未识别函数，不证明没有代码 |
| ida_bytes | get_bytes、get_full_flags、is_code | 数据可能不可读；不把 IDB bytes 当原文件 hash |
| ida_name | get_name、get_name_ea、set_name、SN_CHECK | set_name 修改 IDB，核冲突与返回值 |
| ida_xref | fl_CN、fl_CF 与引用种类 | code xref 包含跳转，不都是 call |
| ida_typeinf | tinfo_t、parse_decl、apply_tinfo、set_named_type | 类型恢复与写入分离；TERR_OK=0，不能 bool 化 |
| ida_struct | 8.x 历史结构体接口 | 9.0 移除，改用 ida_typeinf；不要直接 import 后假定存在 |
| ida_segment | get_first_seg/get_next_seg、get_segm_name | IDA segment 与文件 section 不完全等价 |
| ida_entry | get_entry_qty/get_entry_ordinal/get_entry/get_entry_name | ordinal 与序号不同；entry 不等于唯一执行入口 |
| ida_nalt | get_input_file_path/get_imagebase、get_tinfo | 读回类型在 ida_nalt，不是 ida_typeinf.get_tinfo |
| ida_hexrays | init_hexrays_plugin、decompile、cfunc.get_pseudocode | 安装/授权/CPU/单函数均可能失败 |
| ida_kernwin | get_kernel_version、execute_sync、register_timer | execute_sync 送主线程，不是后台计算 |
| ida_auto | auto_is_ok、get_auto_state、auto_wait | auto_wait 会推进分析及更改数据库；空队列非分析完美 |
| ida_dbg | debugger 事件、断点、寄存器/内存 API | 后端/状态不同，查当前文档再执行；请求异步 |
| ida_gdl | FlowChart | 基本块与 CFG；不推断完备动态调用图 |
| ida_ida/ida_idaapi | inf_get_procname/位宽/端序、BADADDR | 9.x 使用新 accessor，不复活旧 get_inf_structure 假设 |
| ida_ua/ida_idp/ida_lines | decode_insn/is_call_insn/generate_disasm_line/tag_remove | 真实指令检查、显示标记清理 |
| ida_loader | get_path(PATH_TYPE_IDB) | 当前数据库路径；backup 不能等于该文件 |

上述 API 按 [官方 9.0 索引](https://python.docs.hex-rays.com/9.0/index.html)查对应模块。[8.x→9.0移植](https://docs.hex-rays.com/9.0/developer-guide/idapython/idapython-porting-guide-ida-9)明确移除项。[类型 API](https://python.docs.hex-rays.com/namespaceida__typeinf.html)、[tinfo_t](https://python.docs.hex-rays.com/classida__typeinf_1_1tinfo__t.html)、[ida_nalt](https://python.docs.hex-rays.com/namespaceida__nalt.html)用于写入及读回。udm_t 的 offset/size 涉及 bit 单位，不能把 4 字节直接写成 size=4；示例采用解析声明，仍须检查目标 ABI 的最终布局。

## 运行环境
脚本在 [scripts](../scripts/ida_evidence.py)，不是普通 Python 内可执行的 IDA 替代品。普通 Python 只运行离线测试和 MCP 客户端。
- GUI：在 IDA Python console 将该技能 scripts 的真实绝对路径加入 sys.path，再 import；使用 File → Script file 或 console。API 在 IDA 主线程调用。
- GUI RPC worker：短调用使用 on_main_thread；不能持有 UI 所需锁，不用一个长 execute_sync 回调做整库反编译。
- GUI 全字符串导出：gui_strings_export 使用定时器短片段；单次约 25ms 预算不能保证某次内核 API 本身不耗时。可取消，必须确认最终文件已发布且 status().published 为真才算全量。
- 批处理：核实际 IDA 可执行文件与 -A/-S/-L 选项；在工作 IDB 上运行 run_ida_batch.py。脚本不隐式 qexit 或保存，调用者负责生命周期；不要把没有退出当成功。
- idalib 后台：由已安装版本提供的打开/关闭 API 建立工作数据库后，在 owner thread 调用 run(config)；GUI timer 不适用。MCP 官方 worker 生命周期见适配器说明。

示例 console 准备：先将 SKILLFORGE_IDA_SCRIPTS 环境变量设置为当前技能 scripts 的真实绝对目录；输出示例相对于当前工作目录。
```python
import os, sys
sys.path.insert(0, os.environ["SKILLFORGE_IDA_SCRIPTS"])
import ida_evidence as e
print(e.analysis_state())
# 仅在允许自动分析修改的工作副本上明确调用：
# e.wait_for_analysis()
```
地址必须换成当前 IDB 中核实的函数地址。报告输出路径父目录必须存在，文件不得已存在；独占写入避免覆盖。分析未完成、函数不存在、API缺失会抛 AnalysisError 或返回 ok=false，不吞异常冒充空结果。

## 十五项示例映射
下表 1–14 目标均为 IDA 9.x，依赖已加载工作 IDB、匹配 API，除另注外为 GUI 主线程/后台 owner thread；未作真实 IDA 验证。读操作可能生成分析器缓存，不能承诺数据库文件字节不变。
| # | 调用 | 是否显式修改 IDB | 预期/错误处理 |
|---|---|---|---|
| 1 统计函数 | e.count_functions() | 否 | 返回 recognized_function_count；分析未完成拒绝 |
| 2 全字符串 | gui_strings_export.start(path) | 否 | GUI JSONL，成功关闭后发布；cancel 保留.partial |
| 3 字符串 xrefs | e.string_xrefs("Save failed", limit=100) | 否 | 地址与引用、next_index；逐页继续 |
| 4 函数汇编 | e.assembly(address, limit=500) | 否 | 含 EA/chunks，truncated 不代表完整 |
| 5 伪代码 | e.pseudocode(address) | 不显式写 | 初始化失败/函数失败给原因 |
| 6 调用者 | e.callers(address) | 否 | 直接 call xrefs；间接/尾调用不保证 |
| 7 被调用者 | e.callees(address) | 否 | 指令+call xrefs；未解析调用点保留 |
| 8 批量重命名 | m.run_plan(plan) | dry-run 否；commit 是 | hash/旧值/重名检查；日志与读回 |
| 9 函数类型 | function_type 计划 | 同上 | parse_decl/tif.is_func；读回比较 |
| 10 创建结构体 | structure 计划 | 同上 | 本地类型不得已存在；解析布局/读回 |
| 11 调用图 | e.callgraph_page(limit=25) | 否 | next_ea、incomplete_functions；不是完备动态图 |
| 12 JSON 报告 | e.export(e.report(...), path) | 仅本地导出 | context/hash/版本/耗时；文件已存在拒绝 |
| 13 分析状态 | e.analysis_state() | 否 | 队列/状态；wait_for_analysis 为显式可修改操作 |
| 14 Hex-Rays 检查 | e.hexrays_status() | 初始化插件 | available 不能保证每个函数可反编译 |
| 15 MCP 查函数 | mcp_function_query.py | 仅经审阅查询 | 普通 Python 3；回环 HTTP、协议/schema核对；不支持官方代码执行 |

函数/字符串/调用图完整导出示例（后台或小 IDB；GUI 用 timer 分片）：
```python
identity = e.context()  # 本次分页任务复用身份，避免每页重哈希大文件。
cursor = 0
page = 0
while True:
    result = e.report("functions", start=cursor, limit=100, context_snapshot=identity)
    e.export(result, f"output/functions-{page:04d}.json")
    if not result["ok"]:
        raise RuntimeError(result["error"])
    cursor = result["data"]["next_ea"]
    if cursor is None:
        break
    page += 1
```
字符串普通批处理替换为 operation="strings" 与 start_index，使用 next_index 续页，保持 string list 不变。不存在字符串时仍按扫描条数限制；翻页重新遍历的成本适用于中小导出，大量 GUI 字符串优先单 iterator timer。

批量反编译：e.decompile_batch([address1,address2])，最多20个明确地址；逐函数错误和耗时保留。不设“全程序”默认。导出 CSV/Markdown：e.export(result,path,"csv") 或 "markdown"；CSV 保留完整 provenance envelope，二进制内容不成为表格公式。

## 修改示例（默认 dry-run）
```python
import ida_mutations as m
identity = e.context()
plan = {
  "expected_idb_path": identity["idb_path"],
  "expected_image_base": identity["image_base"],
  "expected_input_sha256": e.context()["input_sha256"],
  "reason": "已授权的候选布局标注，依据当前函数读写指令",
  "operations": [
    {"kind":"rename","ea":"0x140001000",
     "expected_old":"sub_140001000","new":"candidate_init"},
    {"kind":"function_type","ea":"0x140001000",
     "expected_old":None,"declaration":"int candidate_init(void *self, int value);"},
    {"kind":"structure","name":"CandidateRecord",
     "declaration":"struct CandidateRecord { unsigned int value; unsigned char unknown[4]; void *link; };"}
  ]
}
preview = m.run_plan(plan)  # 不提交；必须换成实际地址/旧值/hash并核对 ABI。
print(preview)
# 完成授权与工作 IDB 恢复副本验证后，明确执行：
# result = m.run_plan(plan, commit=True, audit_path="output/change.jsonl",
#                     backup_path="backups/verified-work.i64")
```
这不是原子事务。部分修改失败/不确定时先核日志与 IDB，不自动重试。backup 仅检查存在、不同路径及 hash，不自动证明可恢复。IDB 是否可写由实际操作返回和读回确认，不存在跨版本通用的“只读保证”旗标。结构体字段需进一步按 ABI 核对偏移，无法以成功 parse 证明恢复正确。

## 批处理作业
编辑 [job.example.json](../scripts/job.example.json) 的输出路径，使用真实工作 IDB：
```text
idat -A -Lrun.log -S"../scripts/run_ida_batch.py ../scripts/job.example.json" work.i64
```
这是 IDA 支持该命令参数时的调用形状，不保证本机可执行文件叫 idat。run(config) 可在 GUI/idalib 调用；配置只接受白名单 operation，不执行配置提供的 Python。

## MCP 查询
以下命令在技能的 references 目录运行。先用已安装适配器真实 URL（不是固定端口保证）：
```text
python ../scripts/mcp_function_query.py http://127.0.0.1:13337/mcp
```
查看 initialize 与 tools/list；核目标、schema、权限后，社区版本若确实暴露 lookup_funcs 且 schema 接受 queries：
```text
python ../scripts/mcp_function_query.py http://127.0.0.1:13337/mcp --tool lookup_funcs --arguments '{"queries":["0x140001000"]}' --read-only-reviewed
```
地址/参数从真实 schema 构造。客户端拒绝非回环、重定向、任意执行及未发现工具；有更多工具页则停止查询，使用完整客户端。它不是安全沙箱，不会证明服务的函数查询绝无副作用。只支持 MCP 2025-03-26，服务协商其他版本时拒绝；有限 SSE、8MiB、30s 限制，不支持认证/stdio/无限事件流。
官方 six-tool Code Mode 不适用上述函数查询命令；用已授权客户端 reference 得到当前 API，再 execute_python 读取绑定实例的函数。这一分支本轮只提供接入流程，没有伪造通用可执行 get_function 工具。

逐模块来源核对层级见 [API 来源台账](idapython-sources.md)。

提交还会核对 IDB 存储的输入 SHA-256 与磁盘文件一致，并绑定已审阅 IDB 路径和 image_base；缺失或不一致拒绝修改。原始输入 hash 不证明 IDB 未被修改，工作库的身份和旧值仍需核对。

只读分页可复用 context_snapshot；期间不切库/改库/替换文件，任务结束重新调用 e.context() 核对 hash、IDB路径及基址，变化则废弃该批缓存并重新取证。修改计划始终重新读取身份，不使用该缓存。

## v2 反向审查：分页、成本与审计契约
本次修订纠正 v1 只有 truncated 无续页参数的缺口；v1 ZIP保留，使用最新修订版进行新分析。
### 查询分页
xrefs_to(address, limit, offset=0)、assembly(address, limit, offset=0)、callers(address, limit, offset=0)、callees(address, max_items, offset=0)、pseudocode(address, max_lines, offset=0) 均返回 next_offset、complete、truncated、scanned 和 iterator_items_visited。
- offset 是零基序号，下一页原样使用 next_offset；None表示该枚举到尾。空rows不代表到尾，过滤后的空页仍需续页。
- xrefs_to 与 callers 顺序为当前 IDAPython XrefsTo 原生枚举顺序；callers分页计原始引用，之后过滤call。不是按函数排序或去重。
- assembly 顺序为 FuncItems 原生顺序（包含 chunks）；不承诺全局地址升序。
- callees 顺序为 FuncItems，再逐项 XrefsFrom 的原生顺序。分页单位是事件：非调用item、每条outgoing xref、无call目标时的unresolved标记。max_items现在限制事件数，避免一个call大量xref突破返回上限；同一call的多个目标可分布在不同页。不要将事件offset当指令地址或函数offset。
- pseudocode offset为伪代码行序号。每次仍请求decompile，Hex-Rays是否复用缓存由真实环境决定；长函数导出优先在同一受控会话保留cfunc并一次迭代。行上限不是反编译执行超时。
- string_xrefs 的每条字符串有独立xrefs.next_offset，续读调用xrefs_to(字符串EA,offset=...)；strings_complete只表示字符串页到尾，complete同时考虑该页子查询。先续完该页所有子引用，再沿next_index处理下一字符串页。
- callgraph_page 的next_ea仅续函数页；每个incomplete_functions[].details.next_offset通过callees(该函数EA,offset=...)续读。functions_complete不等于调用图complete；fully_resolved为false还可能是未解析间接调用。
- functions_page按地址next_ea续页；strings_page继续兼容start_index/next_index，同时返回统一offset字段。

```python
offset = 0
identity = e.context()
while True:
    r = e.report("xrefs_to", address, limit=100, offset=offset, context_snapshot=identity)
    if not r["ok"]:
        raise RuntimeError(r["error"])
    e.export(r, f"output/xrefs-{offset}.json")
    offset = r["data"]["next_offset"]
    if offset is None:
        break
```

### 顺序与一致性边界
这些offset不是服务器快照或可跨会话令牌。必须在同一数据库、同一分析完成状态、同一目标地址和过滤条件下读取。期间禁止重新分析、重命名、设置类型、增删引用、改变函数/chunks、重建Strings、rebase、切库或重新打开数据库；任何变化后丢弃全部旧游标并重新取证。单写者/任务冻结由宿主协调，脚本没有事务锁，hash与基址不检测每一种IDB内部修改。不能用它们保证并发一致性。
顺序不跨IDA版本或进程保证；把游标和本次IDB/session/参数/修订记录一起保存，只能在确认未变化的原会话续用。不能在变化后拼接结果并称无遗漏。

### 深分页成本
通用offset实现每次重放前缀并最多额外读1项判断是否还有页。scanned仅为本页处理事件数；iterator_items_visited才包含跳过前缀与lookahead的真实Python枚举取项数（不是底层IDA CPU成本）。
1000条字符串每页100的十页总取项为5509，不能声称O(n)全量分页。offset/start_index限制0..100000，更深查询拒绝，改用已有gui_strings_export持久iterator或后台单iterator全量导出。GUI持久iterator仍必须冻结IDB，取消/关闭前处理结束状态。functions_page地址寻址不受该offset上限。
所有大文件任务记录实际耗时；单个IDA内核调用仍可能阻塞。无界全程序反编译没有默认入口。

### 审计写盘失败
mutation_attempted说明是否调用过写API；verified_results/applied只包含读回一致的操作；uncertain_operation_indices表示尝试过但未能完成读回验证的项。all_mutations_verified与audit_complete独立，ok只有全部操作验证且审计持久化成功才为true。
partial只表示已尝试但尚未全部验证，不能单独判断“未修改”；始终读取mutation_attempted与verified_results。applied或completed日志fsync失败后保留已验证结果，返回ok=false/audit_complete=false及失败阶段，禁止自动重试。持久日志可能只有部分内容甚至不可用：返回值中的内存证据只能由调用者立即保存，不能伪称日志已可靠落盘；进程同时崩溃时需直接检查IDB和恢复副本。

## v3 GUI生命周期修订
start(path)先独占创建同目录path.partial。写入/flush/fsync/close均成功后，使用无覆盖硬链接发布path，再移除partial。文件系统不支持该发布方式、目标冲突或任一前置步骤失败时不发布，保留partial与status()错误，不能自动重试覆盖。发布成功但partial清理失败，最终文件仍完整，status中cleanup_error单独说明重复残留。
定时器回调失败返回-1停止，finally清空_JOB；关闭失败也不会锁死新任务。注册异常/None、首写失败均清理并抛启动错误；读取status()获取本次内存状态。cancel只请求取消，下一回调关闭部分文件；关闭IDB前需等待状态结束。取消与失败的partial中即使出现complete文本也不是成功凭证；只认成功发布的最终文件及status().published。
status()不是持久化日志或进程崩溃恢复机制；硬链接发布和GUI timer仍需目标平台/IDA实测。数据fsync不等于目录变更在断电后必然持久，本文不作该承诺。

## 严格边界与导出发布修订
地址、offset和limit拒绝bool/float（包括整数值浮点数）；接受非负Python int及十进制或0x/0b/0o整数字符串，防止写目标被静默截断。
MCP响应必须具有jsonrpc=2.0、类型和值均匹配的ID、互斥result/error；error需整数code和字符串message。无ID通知单独检查，不充当响应。
修改前os.path.samefile核对备份与当前库，硬链接同文件也拒绝；无法stat确认时拒绝提交。该检查不证明备份可恢复，也不能抵御检查后外部替换，操作期间须冻结工作库/备份路径。
普通export先独占创建path.partial，写入、flush、fsync及close成功后才以同目录硬链接无覆盖发布path。任何发布前失败保留partial，正式路径不代表部分输出；不要自动覆盖或重试partial。发布后清理partial失败，正式文件仍已发布；不使用warnings或stderr报告，以免输出失败或warnings=error掩盖已发布状态。默认export仍返回路径字符串，兼容既有调用；需检查清理结果时使用export(result,path,return_status=True)，返回path、published=true、partial_path、cleanup_error（成功清理为null）。发布前失败仍抛原异常，不返回成功状态。批入口run(config)在返回的分析结果中增加export_status，保留ok/error等分析字段的原语义；该附加状态不写回已发布的分析文件。批入口诊断输出遇OSError时将diagnostic_error记入export_status，调用者应保存返回值，不以终端是否打印成功判断发布。依赖文件系统硬链接支持，不支持时失败关闭；目录元数据未fsync，不能承诺断电恢复。Windows/网络文件系统和真实IDA未在本轮测试。
回归：[边界回归测试](../scripts/test_revision_boundaries.py)；原有离线fixture补充实际独立工作库文件和合法JSON-RPC信封。这些不是IDA恢复或运行验证。

字符串分页的行index与offset使用同一已验证整数，支持无符号十进制及0x/0o/0b字符串；bool、float和非法字符串仍拒绝。

关闭stdout可能抛ValueError；batch诊断输出仅捕获OSError与ValueError，并将错误放入export_status.diagnostic_error。KeyboardInterrupt等BaseException不捕获。日志失败不等于导出未发布；该行为已由关闭StringIO离线回归核实，非真实IDA测试。

### 哈希输入边界
sha256_file只接受常规文件；合法symlink跟随至常规文件，特殊文件目标拒绝。先stat，使用只读及可用O_NONBLOCK/O_BINARY标志打开，再fstat复查实际描述符；拒绝FIFO/socket/device并关闭失败路径的fd。按初始大小分块读取，不限制合法大文件的总大小；短读、额外增长字节或末尾size/mtime变化返回错误。小写SHA-256合同保持不变，context仍将OSError记入hash_error；备份hash失败阻止提交。
该实现不跨技能import。非阻塞标志的平台支持不同，不能承诺Windows命名管道/网络文件系统行为、对任意并发替换的防护或原子快照；恶意恢复mtime可能绕过变化检测，仍应使用稳定副本。本轮只有离线文件测试，无真实IDA。
