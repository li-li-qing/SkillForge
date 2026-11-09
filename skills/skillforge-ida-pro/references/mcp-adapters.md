# MCP / RPC 接入与执行边界
核实日期 2026-11-07；版本要求仅针对下列固定提交，部署前读安装版本 README 和 tools/list。
| 适配器 | 兼容与工具 | 性能/并发/权限 |
|---|---|---|
| official_hexrays：HexRaysSA/ida-mcp，391c2f0606a773050fbafcd3ff62942688a0713b | README：IDA 9.4+、idalib、Python 3.11+、Git、uv。六工具模型：open_database、execute_python、reference、list_databases、save_database、close_database | Code Mode；数据库租约与实例绑定；execute_python 会 flush，最后租约释放可能保存。任意 Python 能力不是只读沙箱；外层 HTTP 无内置认证 |
| community_mrexodia：mrexodia/ida-pro-mcp，c133c3853faa111a9b00ee615c013b720d0c4acd | README 列 IDA Pro 8.3+、Python 3.11+；当前路径还需 idalib/uv，不能据宽泛下限承诺全部 8.x。部分 9.0 初版 API 不足；当前推荐迁往官方，旧 GUI 插件不再推荐 | 分模块查询工具、readonly profile；py_eval 不在只读白名单。主线程同步、超时和取消；Host/Origin 校验不是身份认证 |
| research_codex_bridge：Iamgublin/ida-codex-mcp，fe4a19bf64fcf4014032b6690e8adce77ee4e879 | README：IDA 9.2、Python 3.9+；本地 TCP bridge + stdio MCP | 回环监听、自增端口需核身份；无已确认请求认证；License TBD，不复制源码、不默认部署 |

官方与社区是不同适配器，不能用旧 lookup_funcs 替代官方 reference/execute_python，也不能虚构统一 get_function。版本号通过后仍需探测当前 API、CPU 反编译器授权与加载数据库。

## 最小接入流程
1. 本会话发现工具；记录客户端、transport、服务版本、schema。无工具则说明缺少连接，继续本地只读分析，不自动安装。
2. stdio/回环优先。禁止未认证公网服务；本地回环也不是抵御本机恶意进程的认证。安装依赖/改宿主配置属于另一个明确授权动作。
3. 官方先 list_databases，核对工作副本路径；必要且已授权才 open_database。保存真实 instance_id，reference 查询匹配 API，再执行短小、已审阅的读取代码。不能把远程输入直接拼进 Python。社区先 health 与目标信息，再按实际 schema 查询函数。
4. 查询函数的可执行示例见 [示例说明](idapython-api.md)。示例客户端只支持有限回环 Streamable HTTP，不是假装覆盖所有适配器的统一实现；官方 Code Mode 必须通过现有授权客户端执行经过审阅的代码。
5. 每次记录 adapter、版本、hash、instance_id、请求/响应、耗时、游标/partial。大型 IDB 分页，只反编译有限地址；主线程短片段与后台 worker 分开。execute_sync 不会让长回调不阻塞 UI。
6. 同一 IDB 单写者；其他分析者只读快照或不同范围的证据任务。租约隔离不保证数据库修改无冲突。只能关闭自己持有的句柄。
7. 写入前列地址/旧值/新值/理由与授权，保留可恢复工作副本、串行执行、逐项读回。不确定超时先查状态，不盲目重试。不要以“不调用 save_database”保证磁盘不变。
8. 默认不执行外部 Python，不运行/附加目标，不上传日志/诊断 ZIP/IDB。查询能力与任意执行、数据库修改、调试分别授权。

## 按工具合同验收失败路径

接入或升级适配器时，按本次用到的能力选择验收，不要求全面扫描 API。先固定输入 schema、成功/错误响应、分页游标与终止条件，记录实际 adapter、版本、IDB 工作副本 hash 和实例；工具同名也不推定合同相同。

| 场景 | 应区分的证据 |
|---|---|
| 未连接、服务不可达 | 传输失败，不解释成数据库无结果；本地只读分析仍可继续 |
| 已连接但无 IDB、实例失效 | 明确目标状态，不自动换到另一数据库或偷偷打开原始库 |
| 地址非法或不属于函数 | 参数/领域错误，不与合法空结果混淆 |
| 缺对应反编译器授权 | 记录能力缺失，已有反汇编证据仍可用，不伪造伪代码成功 |
| 大结果分页 | 固定夹具核对无遗漏/重复、partial 与最后游标；循环游标应有停止界限 |
| 超时或取消 | 区分尚未执行、已执行与结果未知；写操作先查状态，不盲目重试 |
| 写能力被拒 | 不换任意 Python 通道绕过；检查拒绝前后目标状态，按实际权限报告 |
| 协议错误或响应不符 schema | 保存脱敏响应及协商版本，不当业务成功返回 |

测试可使用固定、脱敏的 IDB 夹具或模拟协议边界；明确模拟不能证明真实 IDA 插件行为。读取有稳定答案的地址/属性适合精确断言，开放逆向判断则核对证据与推理边界，不要求字符串答案唯一。未知状态的真实写操作不为测试而重复触发。

`readOnlyHint`、`destructiveHint`、`idempotentHint`、`openWorldHint` 是描述提示，不是权限执行器或安全保证；只读声明仍核实际实现与服务配置。发现注解与行为不符时按真实能力收紧调用范围，不把 schema/注解当用户授权。

方法参考：[Anthropic mcp-builder](https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/mcp-builder/SKILL.md) 与 [评测说明](https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/mcp-builder/reference/evaluation.md)。固定提交日期 2026-11-06，核实日期 2026-11-07；该目录 [LICENSE.txt](https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/mcp-builder/LICENSE.txt) 为 Apache-2.0。这里是原创归纳，未引入第三方代码、SDK 或自动迁移；MCP/IDA API 权威性仍来自实际安装版本及官方规范。

## 原始依据与维护
- [官方 README](https://github.com/HexRaysSA/ida-mcp/blob/391c2f0606a773050fbafcd3ff62942688a0713b/README.md)、[实现](https://github.com/HexRaysSA/ida-mcp/blob/391c2f0606a773050fbafcd3ff62942688a0713b/ida_mcp/mcp.py)、[架构](https://github.com/HexRaysSA/ida-mcp/blob/391c2f0606a773050fbafcd3ff62942688a0713b/docs/ARCHITECTURE.md)，MIT。
- [社区 README](https://github.com/mrexodia/ida-pro-mcp/blob/c133c3853faa111a9b00ee615c013b720d0c4acd/README.md)、[只读 profile](https://github.com/mrexodia/ida-pro-mcp/blob/c133c3853faa111a9b00ee615c013b720d0c4acd/profiles/readonly.txt)，MIT。
- [Codex bridge README](https://github.com/Iamgublin/ida-codex-mcp/blob/fe4a19bf64fcf4014032b6690e8adce77ee4e879/README.md)，TBD。
- [MCP 2025-03-26 生命周期](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle)与[传输](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)：示例协议版本，其他协商版本须重新核实。
每次升级重新核 README/pyproject/schema/LICENSE/网络监听实现及实际连接测试。本轮没有运行真实 IDA MCP、并发或吞吐测试。
