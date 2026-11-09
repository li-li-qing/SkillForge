# IDAPython API 分类与来源

核实日期：2026-11-07。官方 Python 文档为滚动生成页，不能据此声称所有旧版可用。下面“已阅读”指本次实际打开核对的官方页；“索引”只提供官方入口，未声称逐 API 已验证。实际加载模块、签名、枚举和许可必须对照本机 IDA 文档。

## 已阅读的官方依据

| 官方来源 | 本次核对内容 | 本包使用/限制 |
|---|---|---|
| https://python.docs.hex-rays.com/ida_auto/index.html | auto_is_ok、get_auto_state、auto_wait | 队列空与当前 AU_NONE 不等价；auto_wait 可能处理并修改数据库 |
| https://python.docs.hex-rays.com/idautils/index.html | Functions、Chunks、FuncItems、XrefsTo/From、Strings | Strings(False) 复用当前列表；普通流引用不等于调用 |
| https://python.docs.hex-rays.com/ida_typeinf/index.html | parse_decl(tif,til,decl,flags)、tinfo_t.set_named_type、apply_tinfo | set_named_type 返回错误码，TERR_OK 为 0，不能直接当布尔成功；解析一条声明 |
| https://python.docs.hex-rays.com/ida_hexrays/index.html | init_hexrays_plugin、decompile、ctree/microcode 区别 | 获取伪代码不代表恢复源代码；每函数仍可能失败 |
| https://python.docs.hex-rays.com/ida_kernwin/index.html | execute_sync 的主线程调用与整数返回契约 | GUI 工作线程通过 bridge；timer 示例仍须真实 GUI 测试 |
| https://python.docs.hex-rays.com/ida_idp/index.html | is_call_insn(insn_t) | 先 decode_insn 再检查 call；不硬编码 x86 操作码 |
| https://python.docs.hex-rays.com/ida_ua/index.html | 指令解码相关接口 | insn_t 与 decode_insn；不虚构 CF_CALL 在该模块存在 |
| https://docs.hex-rays.com/developer/idapython/how-tos/idapython-porting-guide-ida-9 | IDA 9 迁移说明 | ida_struct/ida_enum 旧模块迁移至 ida_typeinf；不能盲目沿用旧教程 |

可信度：Hex-Rays 官方规范性来源，仍受版本适用范围限制。API 文档核对不是实际执行测试。

## 模块分类索引

以下 URL 均为官方 API 索引格式，未阅读的条目只作后续查阅入口。

| 模块 | 职责与常用入口 | 来源与状态 |
|---|---|---|
| idaapi | 历史聚合入口；新脚本优先明确模块导入 | https://python.docs.hex-rays.com/idaapi/index.html （索引） |
| idautils | Functions、Chunks、FuncItems、Strings、XrefsTo/From | https://python.docs.hex-rays.com/idautils/index.html （已阅读） |
| idc | 高层兼容包装，get_type；批处理 ARGV | https://python.docs.hex-rays.com/idc/index.html （索引） |
| ida_funcs | get_func、get_func_qty；函数边界和属性 | https://python.docs.hex-rays.com/ida_funcs/index.html （索引） |
| ida_bytes | get_bytes、get_flags 等字节与 item 状态；写/patch API 另授权 | https://python.docs.hex-rays.com/ida_bytes/index.html （索引） |
| ida_name | get_name、get_name_ea、set_name；重命名是 IDB 修改 | https://python.docs.hex-rays.com/ida_name/index.html （索引） |
| ida_xref | fl_CN/fl_CF 等引用分类；代码引用不是都属于 call | https://python.docs.hex-rays.com/ida_xref/index.html （索引） |
| ida_typeinf | tinfo_t、parse_decl、apply_tinfo、Local Types、UDT | https://python.docs.hex-rays.com/ida_typeinf/index.html （已阅读） |
| ida_struct | 旧版结构体模块；9.0 迁移后不得直接导入照用 | https://docs.hex-rays.com/developer/idapython/how-tos/idapython-porting-guide-ida-9 （已阅读） |
| ida_segment | Segment 查询和权限，区分磁盘 Section 与加载后 Segment | https://python.docs.hex-rays.com/ida_segment/index.html （索引） |
| ida_entry | 入口/导出序号与地址 | https://python.docs.hex-rays.com/ida_entry/index.html （索引） |
| ida_nalt | get_input_file_path、get_imagebase、导入表辅助 | https://python.docs.hex-rays.com/ida_nalt/index.html （索引） |
| ida_hexrays | 初始化、反编译、ctree/microcode；需相应许可 | https://python.docs.hex-rays.com/ida_hexrays/index.html （已阅读） |
| ida_kernwin | execute_sync、GUI timer、UI；不用于无 GUI 假设 | https://python.docs.hex-rays.com/ida_kernwin/index.html （已阅读部分） |
| ida_auto | 队列状态、auto_wait | https://python.docs.hex-rays.com/ida_auto/index.html （已阅读） |
| ida_dbg | 调试状态、断点、寄存器、请求队列；运行目标另授权 | https://python.docs.hex-rays.com/ida_dbg/index.html （索引，未接触进程） |
| ida_gdl | FlowChart、基本块 CFG；不是过程间完整调用图 | https://python.docs.hex-rays.com/ida_gdl/index.html （索引） |
| ida_ida | inf_get_procname、inf_is_64bit/inf_is_32bit_exactly、inf_is_be | https://python.docs.hex-rays.com/ida_ida/index.html （索引） |
| ida_idaapi | BADADDR 无效地址哨兵；0 可能有效 | https://python.docs.hex-rays.com/ida_idaapi/index.html （索引） |
| ida_lines | generate_disasm_line、tag_remove | https://python.docs.hex-rays.com/ida_lines/index.html （索引） |
| ida_ua / ida_idp | insn_t、decode_insn、is_call_insn | 上表两条已阅读来源 |
| ida_loader | get_path(PATH_TYPE_IDB)；当前数据库路径 | https://python.docs.hex-rays.com/ida_loader/index.html （索引） |

## 兼容策略

1. 不通过 `try import ida_struct` 后静默回退为另一种布局。8.x/9.x 类型系统迁移需要明确适配和实测。
2. 采集器动态导入并报告缺失模块/API；不会把缺失反编译器解释成空函数。
3. 类型写入示例只接受 9.x，保守限制声明长度和预处理器。不能解析用户提供的任意头文件，也不会自动下载/运行外部脚本。
4. UDT offset API 常以 bit 为单位，报告内偏移应明确 byte/bit；本包优先 C 声明解析而不是混淆单位手工写偏移。
5. ABI 由加载目标决定。`__fastcall` 示例不是跨 Windows/System V/ARM 通用声明；使用前检查真实架构和调用点。
6. 能导入 API ≠ API 行为已验证；能初始化插件 ≠ 当前目标可反编译；存在备份 ≠ 已验证恢复。

## MCP 示例来源与界限

- 协议权威入口：https://modelcontextprotocol.io/specification （索引；部署前固定协议版本）。
- Python SDK：https://github.com/modelcontextprotocol/python-sdk （本次阅读；当前主分支的客户端 API 与旧教程有差异，因此未硬写未经验证的 SDK 导入）。
- 社区适配器：https://github.com/mrexodia/ida-pro-mcp 。`lookup_funcs` 等名称仅作为受限候选，**必须以当前服务 tools/list 为准**；不假定不同 release 同 schema。
- 官方适配器：https://github.com/HexRaysSA/ida-mcp 。不能用社区工具名冒充官方工具，也不能对只提供 Code Mode 的服务自动发送任意 Python。

本客户端只演示发现与查询的受控闭环，不能替代真实适配器的安装说明、权限控制、版本兼容检查和认证客户端。
