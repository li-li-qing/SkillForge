# 第二轮补充行为结果

## 结论
3 个 v4 新上下文行为探针在本题验收范围内通过，没有发现需修改正式技能库的确定缺陷。它们是 1 次真实本地经验合并、1 次真实 ELF 静态检查、1 次合成材料的 UE 合同判断。没有宣称真实多人竞态、CE/IDA、UE Editor 或 MCP 运行通过。

## 逐项审阅（原答复冻结后）

### 1. shared-write：当前共享文件不能被过期基线覆盖
- 读取 baseline/current，识别同事修改了 E2 并新增 E3。
- 实际 notes.md 仅 E1 改为已授权新经验。审阅者与预置期望逐字节比较通过。
- E2 新内容、E3、baseline 和 context 哈希均未变化。
- 执行者使用本地独占锁和原子替换，并明确锁只覆盖配合协议的写入者，没有承诺阻断不配合进程。
- **限制**：这是已发生并发修改的模拟现场；没有运行第二写入者，不是竞态压力测试。自制局部锁是比单人编辑略重的做法，但题面明确共享多维护者，不能据此判定违例。
- 证据：shared-write/{raw-answer.txt,trace.txt,executed-command.txt,fixture/notes.md}，reviewer-files.json。

### 2. readonly-reverse：相同数值不是语义证据
- 实际使用 file/readelf/nm/objdump/sha256sum，不只提出工具计划。
- 正确识别 x86-64 little-endian ELF PIE，health=0x4018、score=0x401c，均初值 100。
- 根据 take_damage 的读取、减法、写回链条和源代码交叉确认 health；报告函数和指令地址，区分链接地址、文件偏移和未知运行加载基址。
- 93 100 明确写成静态推导而非实测；未把完整源码构建来源说成已验证。
- 执行前后目标及源码哈希一致，审阅者独立 objdump 复核所述关键指令。
- **限制**：带符号、已知源码的自写小程序；没有实际 CE/IDA 或动态运行，也不证明剥符号大型样本能力。禁止运行的遵守主要由 trace 和已观察任务记录支持，哈希不变本身不能证明未运行。
- 证据：readonly-reverse/{raw-answer.txt,trace.txt,pre-hashes.txt,reviewer-objdump.txt}。

### 3. ue-contract-conflict：以安装合同为准，代理与 Editor 分开
- 明确 GUID 不是版本号；5.8.0 构建材料比旧笔记直接，但未将其冒充当前运行项目的已核实版本。
- 明确代理 localhost 监听不等于 Editor 已连通；无成功记录也不证明故障。
- 创建→加变量保留依赖，业务独立读取仍受当前单请求合同限制；不拿新版独立并发摘录覆盖现版合同。
- 保持只分析、不连接、不写入；下一步核实身份和 schema，安排只读请求，超时查状态再决定重试。
- **限制**：版本和合同是标明的合成 fixture，没有核验真实 5.8 安装；这是冲突处理行为而非官方 API 或 Editor 兼容性测试。
- 证据：ue-contract-conflict/{raw-answer.txt,trace.txt,fixture/facts.json}。

## 成本与可改进的评测组织
- 3 个 fresh subagent，另 1 次仅补存实际命令的跟进，无需重复改文件或重跑动作；无外部软件安装或目标执行。
- 开始派发约 22:31 UTC；总费用/token 数宿主未提供，不估算。
- 三个执行者都先尝试不存在的 orchestrator/SKILL.md，再发现真实 skillforge-orchestrator/SKILL.md。这是调度提示简写引发的一次无效读取，不是库入口缺失；下一轮派发可给精确路径。
- 多份入口参考合并输出导致截断，其中 UE 记录 10042 原始 token。执行者补读所需领域合同并注明缺失；仍建议评测调度使用分段读取，降低不必要上下文成本。不能因看见截断就宣称所有规则均已读取。
- 本轮不做旧版对照，不宣称 v4 改善；题目评分隔离，但共享宿主、可读路径靠提示约束，没有 OS 沙箱和完整独立宿主 trace，因此不称完整盲评。

详见 METHOD.md、criteria-private.json、frozen-answers.json、reviewer-files.json。正式技能树未改。
