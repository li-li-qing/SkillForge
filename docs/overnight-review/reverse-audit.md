# 三技能只读审查草案

范围：skillforge-ida-pro v3、skillforge-reverse-engineering、skillforge-cheat-engine。没有修改库，没有真实 IDA/CE/MCP 服务执行。

## 已复现问题

1. P1 地址类型静默转换：ida_evidence.ea(4096.9) 返回4096，ea(True)返回1；bounded(2.9)返回2。写计划经ea转换后可能落到另一有效函数起点。最小修复：地址/游标/limit入口拒绝bool和浮点，仅接受非负int及明确整数字符串。增加mutation入口测试，确认写API从未调用。
2. P2 JSON-RPC响应验证不完整：decode_response(b'{"jsonrpc":"1.0","id":true,"result":{"ok":true}}',1) 返回成功对象。未核协议版本、ID类型（Python True==1）及result/error互斥。最小修复：严格核jsonrpc=2.0、ID的类型和值、单一result/error、error结构；异常响应不得作为工具成功证据。

## 测试与可复现边界

执行 python -B .../scripts/test_examples.py：当前49测试，13 errors，原因是只读沙箱没有可写tempfile目录（No usable temporary directory），不是13项实现失败。不宣称全套通过。上述两项复现均仅内存操作，已执行成功。

CE案例明确标注历史试验与当前复查，保留collector/hash与局限，未把同值写入说成全部物品成功。CE行为eval覆盖未知写入效果、实例混用、引用释放、对象替换；缺可运行fixture是明确证据限制，不是运行通过证明。通用probe使用单文件描述符和前后size/mtime核验；这些是变化检测，不是不可变快照或抵御有意恢复时间戳的保证。

## 官方实践对照

来源：https://github.com/modelcontextprotocol/python-sdk
具体README中的Client上下文管理例程及docs_src/index/tutorial001.py链接；LICENSE：https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/LICENSE 。MIT，Copyright 2024 Anthropic PBC；采用代码应保留版权和许可。当前README已采用v2 MCPServer及Client接口，明确Python3.11+、提供迁移指南；仓库有活跃issues/PR和持续变更，不宜假定旧版导入稳定。未查明当前commit日期，不能据此承诺某个release可用。

建议采用：版本固定、协议模型校验、上下文管理会话释放、传输与业务查询分层。保持现有回环限制与显式只读审阅门槛。不采用：无版本锁定直接复制main新API、为轻量示例自动添加网络安装/启动服务器、把SDK工具存在当只读权限证明。原计划读取src/mcp/types.py返回404，说明路径已变化；未声称核对到该文件，不将猜测路径作为依据。

## 后续验证

对严格地址类型和RPC envelope各增离线反例；在可写临时目录重跑全套测试；真实IDA/CE验证仍需相应环境。现有GUI生命周期和fsync状态问题已修复，不重复计入本轮缺陷。

## 补充验证

获得指定审查所需临时文件写入权限后重跑同一命令：Ran 49 tests in 0.052s，OK，exit_code=0。此前13错误仅为只读沙箱限制，现已解除测试阻碍。以上是离线fake-module契约测试，不是IDA兼容验证。另已实际读取官方docs_src/index/tutorial001.py，确为MCPServer、类型标注工具与资源装饰器的15行示例。
