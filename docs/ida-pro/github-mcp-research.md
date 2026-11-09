# IDA MCP 适配器调研与整合建议

核实日期：2026-11-07。方法：读取公共 GitHub 仓库，克隆固定提交并审阅源码、插件 manifest、参考资料及测试目录；没有安装插件，没有运行目标二进制，没有 IDA 真实运行验收。本文版本要求只对应下列提交，不等于历史版本或后续版本兼容承诺。

## 1. 可复核基线

| 仓库 | 本次固定提交 | 提交时间 | 本次读取的重点 |
|---|---|---|---|
| HexRaysSA/ida-mcp | 391c2f0606a773050fbafcd3ff62942688a0713b | 2026-10-28 16:59:38 UTC | README、pyproject、docs/ARCHITECTURE.md、ida_mcp/mcp.py、.codex-plugin manifest、LICENSE、tests 目录 |
| mrexodia/ida-pro-mcp | c133c3853faa111a9b00ee615c013b720d0c4acd | 2026-09-26 17:42:10 +02:00 | README、pyproject、skills/idapython/SKILL.md、类型参考、profiles/readonly.txt、api_core/api_python/sync/compat/http/rpc、LICENSE |
| Iamgublin/ida-codex-mcp | fe4a19bf64fcf4014032b6690e8adce77ee4e879 | 2026-06-12 22:32:55 +08:00 | README、ida_bridge.py、mcp_ida_server.py、仓库文件列表 |

提交永久链接：
- https://github.com/HexRaysSA/ida-mcp/tree/391c2f0606a773050fbafcd3ff62942688a0713b
- https://github.com/mrexodia/ida-pro-mcp/tree/c133c3853faa111a9b00ee615c013b720d0c4acd
- https://github.com/Iamgublin/ida-codex-mcp/tree/fe4a19bf64fcf4014032b6690e8adce77ee4e879

## 2. 官方 Hex-Rays IDA MCP

### 当前要求和真实工具模型

README 要求 IDA 9.4 或以上、idalib、Python 3.11+，PATH 中有 Git 和 uv。pyproject 将 Python 下限写为 3.11，依赖 ida-nexus >= 0.14.2、zeromcp >= 1.10.3 和 packaging。包版本为 20261028.0.3。不能将社区版的 IDA 8.3+ 要求套给官方版。

工具面是六个工具，不是旧社区 API 列表：open_database、execute_python、reference、list_databases、save_database、close_database。当前 open_database 还接受 load_options、gui；文档架构表中的简写不应替代运行时 tools/list schema。调用 reference 查询实际 ida-domain API，再用 execute_python 执行经过审阅的代码。上下文预置 db、ida_domain，变量在本代理的数据库租约内持续存在。

源码证据：
- https://github.com/HexRaysSA/ida-mcp/blob/391c2f0606a773050fbafcd3ff62942688a0713b/README.md
- https://github.com/HexRaysSA/ida-mcp/blob/391c2f0606a773050fbafcd3ff62942688a0713b/pyproject.toml
- https://github.com/HexRaysSA/ida-mcp/blob/391c2f0606a773050fbafcd3ff62942688a0713b/ida_mcp/mcp.py

### GUI、后台、并发和副作用

无 GUI 插件时可使用服务器 Python 环境中的 idalib worker；安装 GUI 插件后可使用 IDA 自带 Python 的 idat worker，并可按明确 GUI 请求打开界面。IDA_NEXUS_IDALIB_ONLY 可强制保留 idalib 路径。此区别影响可导入模块、插件和 Python 依赖，不可将三种运行方式当作完全等价。

架构在 ida-nexus 之上维护数据库句柄和租约，多 MCP 进程可各自持有租约。关闭本代理句柄不是任意关闭另一个客户端或 GUI 数据库。当前 execute_python 先固定目标实例，再等待初始自动分析；执行超时默认 360 秒，不包含独立的初始自动分析等待。取消使用 operation_id，失败的修改请求不应自动重试。

重要副作用：execute_python 调用传入 flush_database=True；架构说明最后一个托管租约释放时可能保存并结束 worker。不能把“不调用 save_database”当作绝对不保存。工作流要使用原件之外的工作副本，区分“不显式修改名称/类型/字节”与“底层分析缓存或数据库文件完全不变”。

### 安全与可借鉴部分

官方工具提供的是任意 Python 执行能力，不是只读沙箱。read_only 工具标注仅用于 reference 和 list_databases 等适用操作；不能用工具名或自然语言承诺替代权限隔离。默认推荐 stdio 或回环 HTTP。源码对非回环 HTTP 明确警告：传输没有内置认证，execute_python 可能被网络访问。Nexus 内部服务有认证，不代表外层 MCP HTTP 自动有认证。不得暴露未认证公网监听。

日志可记录代码、执行结果并关联代理会话；支持导出诊断 ZIP。不能擅自把日志、IDB、反编译结果上传给维护者。日志本地路径也不是任意读取代理历史的权限。

值得整合：小工具面 + 运行时 reference、目标实例绑定、请求所有权、取消和租约语义、明确 GUI/后台差异、按需批量执行、可追溯调用结果。不要整套复制其 Agent hooks/日志收集架构。不要承诺多 Agent 对同一 IDB 并发修改会无冲突；SkillForge 应给同一 IDB 单写者，其他代理只分析快照或分工只读。

MIT，版权 Hex-Rays SA 2026。可借鉴设计；若复制代码须保留许可，不继承其许可为 IDA 商业产品许可。当前存在测试目录，但本次未运行测试，未从目录存在推断全部通过。

架构及许可：
- https://github.com/HexRaysSA/ida-mcp/blob/391c2f0606a773050fbafcd3ff62942688a0713b/docs/ARCHITECTURE.md
- https://github.com/HexRaysSA/ida-mcp/blob/391c2f0606a773050fbafcd3ff62942688a0713b/LICENSE

## 3. 社区 mrexodia/ida-pro-mcp

README 当前推荐改用官方 Hex-Rays 项目；GUI 插件路径也注明不再推荐并将弃用，推荐 idalib-mcp。不能依据旧安装教程将旧 GUI HTTP 插件定义为长期默认。

README 写 Python 3.11+、IDA Pro 8.3+（推荐 9）、不支持 IDA Free；同文又要求新插件路径使用全局激活的 idalib 和 uv。该宽泛 IDA 下限不是新版 idalib 路径在所有 8.x 上可用的证据，必须按所选路径核实。compat.py 还会根据真实 API 探测拒绝部分缺少 func_t.get_name/get_prototype 或 tinfo_t.get_udm 的 IDA 9.0 初版，建议相应环境使用 SP1 或更高。版本号符合不等于构建兼容。

核心查询源码有 server_health、lookup_funcs、list_funcs、func_query、entity_query、imports、find_regex 等。分析、类型、内存、修改、调试分模块；py_eval 是标记 unsafe 的任意 Python 执行，局部变量默认跨调用保留。profiles/readonly.txt 是显式工具白名单，排除 py_eval、重命名、改类型、patch 和调试操作；它是值得借鉴的暴露面收缩，但不证明所有分析内核都绝无缓存副作用。

同步层包含 IDA 主线程执行、重入检查、取消及默认 60 秒工具超时。大型查询需要上限、分页、可重复游标和部分结果，不通过简单提高超时解决 UI 饥饿。HTTP 有 Host/Origin/CORS 相关防护；这些不是用户身份认证，不应据此开放到公网。

### Skills 组织借鉴与不能直接采纳的内容

skills/idapython/SKILL.md 用模块路由表引导读取 docs/<module>.md，且保留 RST 来源，适合借鉴“短入口 + API 分类 + 按需参考”。不要将第三方整理当成官方规范，也不要整体复制 50+ 模块参考而不标版本。

已发现实际质量风险：
1. SKILL 将 execute_sync 列作避免长操作阻塞主线程的替代方案。这不正确：它把工作送到 IDA 主线程，并不会使一个长回调变成后台任务。应该缩短主线程片段、分块调度或改用隔离后台 worker。
2. 该类型参考把 udm_t.offset/size 标为字节；官方 IDAPython 9.0 类文档至少明确 offset 是 bit。对应 SKILL 结构体示例 m.size=4 不可当作 32-bit 字段的正确通用范例。必须回到匹配版本官方文档核对单位与返回值。
3. “禁止任何 idc”过强；现代 ida_* 优先，但受支持的 idc 包装并非一概非法。应按具体 API 和版本说明。
4. “只能使用 int_convert MCP 做数制转换”耦合社区工具。Python int(value, 0)、hex、format 的确定性转换也可用，不能让官方适配器被不存在的 int_convert 阻断。

来源：
- https://github.com/mrexodia/ida-pro-mcp/blob/c133c3853faa111a9b00ee615c013b720d0c4acd/skills/idapython/SKILL.md
- https://github.com/mrexodia/ida-pro-mcp/blob/c133c3853faa111a9b00ee615c013b720d0c4acd/skills/idapython/docs/ida_typeinf.md
- https://python.docs.hex-rays.com/classida__typeinf_1_1udm__t.html （页面标注 IDAPython 9.0）
- https://github.com/mrexodia/ida-pro-mcp/blob/c133c3853faa111a9b00ee615c013b720d0c4acd/src/ida_pro_mcp/ida_mcp/compat.py
- https://github.com/mrexodia/ida-pro-mcp/blob/c133c3853faa111a9b00ee615c013b720d0c4acd/src/ida_pro_mcp/ida_mcp/sync.py
- https://github.com/mrexodia/ida-pro-mcp/blob/c133c3853faa111a9b00ee615c013b720d0c4acd/profiles/readonly.txt

许可 MIT，版权 Duncan Ogilvie 2025；仍需保留引用代码许可。截止所查提交推荐迁移，不可据此断言项目已归档或停止所有维护。

## 4. ida-codex-mcp 的明确身份

本次搜索识别为 Iamgublin/ida-codex-mcp，不是 Hex-Rays 官方，也不是 Codex 官方组件。README 写 IDA Pro 9.2、Python 3.9+、Windows/Linux/macOS；Hex-Rays 为伪代码功能前提。是 IDA 插件本地 TCP JSON bridge 加 stdio MCP server。

源码固定监听 127.0.0.1:31337，端口占用时递增。请求处理以 execute_sync 送到主线程，存在 ida_py_exec/exec 及修改名称、类型等操作。所查 bridge 没有发现请求身份验证；回环地址仅减少远程暴露，不阻止本机恶意进程。连接读取未显示明确总请求大小上限或读超时，应作为采用前审查项。不要把它当作成熟的隔离边界。

值得借鉴：多目标别名/发现、伪代码和汇编分页、显式功能工具。不要采用：缺少清晰授权边界的广泛 Python 执行、未经证据的自动命名/类型推断、生产依赖未核实的自增端口发现。源码有将常见返回类型补成通用参数表的签名归一化逻辑，不应当作真实函数签名恢复证据。

许可证：README 写 TBD，本次根目录未见 LICENSE。未建立允许复制再分发的许可基础，因此仅记录功能思想和原始地址，不将其源码带入 SkillForge。此判断是本次版本审查，不是法律意见。

- https://github.com/Iamgublin/ida-codex-mcp/blob/fe4a19bf64fcf4014032b6690e8adce77ee4e879/README.md
- https://github.com/Iamgublin/ida-codex-mcp/blob/fe4a19bf64fcf4014032b6690e8adce77ee4e879/ida_bridge.py
- https://github.com/Iamgublin/ida-codex-mcp/blob/fe4a19bf64fcf4014032b6690e8adce77ee4e879/mcp_ida_server.py

## 5. SkillForge 的适配器选择与验收规则

1. 先发现本会话真实工具列表、协议、版本、进程/数据库实例、输入文件 hash 和架构。不按包名猜工具存在。
2. 满足官方 9.4+/idalib/Python 条件且已授权安装时优先官方；旧版 IDA 或既有社区部署单独评估社区路径。找不到能力就列缺失，不自动安装另一个适配器。
3. 两套适配器分别命名 official_hexrays / community_mrexodia；第三方 codex bridge 仅可选研究适配，不默认启用。避免两个相似工具面同时暴露导致误路由。
4. 官方：list_databases → open_database(确认路径) → 保存返回 instance_id → reference(任务/API) → execute_python(显式 instance_id，小批只读代码)。不要编造 get_function 工具；在 reference 取得当前 API 形状后才构造读取脚本。
5. 社区：tools/list/health → 核目标 → 查询实际可用的 lookup/list/decompile/xrefs 工具，参数以运行时 schema 为准；read-only profile 优先，但不得擅改用户配置。
6. 每次调用记录适配器、版本、目标 hash、数据库实例、请求摘要、超时、耗时、结果/错误、截断与游标。查询返回不完整需明确 partial，不可把第一页当全集。
7. 纯查询与 IDB 写入分离。写入必须先提供候选名称/旧值/新值/理由/地址列表、授权范围和副本恢复点；单写者串行执行，每项读回验证，局部失败保留记录。
8. 超时不是未执行证明。修改、启动/附加调试、保存等发生不确定结果时，先查实际状态，禁止盲目重放。
9. 静态分析和读取已打开 IDB 不授权运行未知程序。动态验证另核目标、隔离、断点、进程和副作用。
10. 连接成功仅证明 transport；须分别检查反编译器授权、CPU 支持、模块/API、自动分析、目标一致性、读写权限、分页与取消。不能以模拟 tools/list 或 Python 语法通过声称真 IDA 通过。

## 6. 验收限制与长期维护

本次仅源代码/文档审查。未测试任何真实 MCP 请求、IDA 版本、Hex-Rays 授权、并发吞吐或大型 IDB 性能。定期更新时重新核 README、pyproject、manifest、tool schema、LICENSE 和安全实现；固定版本及 commit 后再安装，不自动跟随 main。GitHub stars/commit 数不作为稳定性证据。本文不授权安装、监听端口、执行外部脚本或上传分析结果。
