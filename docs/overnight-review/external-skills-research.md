# SkillForge 外部 Skills 调研与吸收建议

核实日期：2026-11-07。只读研究，不安装、执行候选脚本，不修改 SkillForge 主树。

## 结论

不建议新增泛化的 debugging、skill-creator、MCP builder、UI testing 独立 Skill。现有 14 个 Skill 已覆盖其主要职责。优先给 experience-maintenance 增加**可选的技能行为对照评估参考页**，给 IDA MCP 增加**工具契约的失败路径验收**，给 engineering-preflight 增加**信任边界探针**。外部规则不是新的系统规则，也不能覆盖现有 A/B/C、授权或动态发现路由。

本轮读取现有 debugging、engineering-preflight、experience-maintenance、ui-design 的入口，检查 experience-maintenance 的触发与行为用例，以及 orchestrator 的维护/评测约定。现有技能已经有证据区分、回归、负例与并发保护，不能宣称这些是本轮新引入能力。

## 固定来源与维护证据

| 仓库 | 固定 commit | commit 日期 UTC | 许可证范围 |
|---|---|---|---|
| openai/skills | `49f948faa9258a0c61caceaf225e179651397431` | 2026-06-24 02:36:12 | 本轮检查的 skill-creator、security-threat-model、gh-fix-ci 各自 LICENSE.txt 为 Apache-2.0；仓库 API license=null，不能把局部授权推广整个仓库 |
| anthropics/skills | `2c5958ecac7cee2b583967a2c4981d0f4a75c579` | 2026-11-06 22:32:28 | 本轮检查的 skill-creator、mcp-builder、webapp-testing 各自 LICENSE.txt 为 Apache-2.0；仓库 API license=null |
| obra/superpowers | `22f0b463e7a5e579904dd6211a520321035526f7` | 2026-11-03 22:17:07 | 仓库 LICENSE：MIT，Copyright 2025 Jesse Vincent |

维护状态仅据 GitHub API 的固定 commit 与最近 push 判断，不代表审计过全部 issue/安全公告，不能以“官方/活跃”替代质量检查。上述 SHA 均由 GitHub API 实际返回；读取的是该 SHA 的 raw 文件，不以 main 链接代替固定证据。

## 1. Anthropic skill-creator：推荐吸收评测方法，不复制运行平台

源：
- https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator/SKILL.md
- https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator/agents/grader.md
- https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator/scripts/aggregate_benchmark.py
- 同目录 LICENSE.txt。

实际内容包括新旧技能对照、保存原版快照、每条断言引用输出证据、检验断言本身是否太弱、盲评、近邻负例、时间/token 与通过率分析。已阅读 SKILL 和 grader；已下载检查聚合脚本，未运行。

适配：扩展 `skillforge-experience-maintenance` 参考页，而非新增 skill-creator。适合重大触发边界/规则变更或宣称“新版更好”时启用：
1. 固定旧/新版本、相同任务/工具/模型条件；不让基线 Agent 继承新版规则。
2. 成对保存实际输出和证据路径；不能只检查包含了正确术语。
3. 新增近邻负例，例如“解释 MCP”不应自动安装连接器；“核对旧 UE 笔记”不应晋升成所有版本通用规则；“看一下按钮”不应触发全架构重构。
4. 评审同时找虚弱断言、未覆盖的失败路径、成本上升；只有真实运行才填 pass。
5. 不保证行为确定性，少量样本不宣称统计显著。

不可照搬：为提高 Claude 触发率而写“pushy description”；必须同时大量启动基线/新版；固定查看器/Claude CLI；每个小改动都强制完整模型评测。现有 orchestrator 已明确普通规则修订不机械增加多轮模型评测，应保留。

## 2. Anthropic mcp-builder：推荐吸收契约测试

源：https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/mcp-builder/SKILL.md
评测细节：同 commit `skills/mcp-builder/reference/evaluation.md`（已读取下载内容）；许可证同目录 LICENSE.txt。

值得借鉴：输入/输出 schema、分页、聚焦返回、可行动错误、readOnlyHint/destructiveHint/idempotentHint/openWorldHint 标注；独立、只读、有稳定答案的多工具场景评估。

适配 `skillforge-ida-pro` 的 MCP 参考/验收：
- 无连接、无 IDB、函数地址不合法、反编译器未授权、分页终止、超时/取消、写能力被拒等分开断言。
- 大 IDB 用固定夹具或固定文件 hash，分别记录工具发现、只读查询、写入拒绝、协议失败。
- 注解是提示，不是权限执行器；“只读”端点也要审查实际实现。
- 已有官方与社区适配器继续分离，评测不假定工具同名同 schema。

不可照搬：默认优先全面 API 覆盖会扩大 IDA Python 执行面；SDK v2/迁移建议属于该来源当前说明，不是本轮已核实的 MCP 官方稳定版本规则；不要直接运行 `npx ...@latest` 或自动迁移。版本须再以实际锁文件和 MCP 官方 SDK 核实。反向工程开放结论也不能强行改成字符串完全相等的“唯一答案”。

## 3. OpenAI security-threat-model：推荐吸收有证据的信任边界

源：https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/security-threat-model/SKILL.md
许可证：同目录 LICENSE.txt。

适配 `skillforge-engineering-preflight` 的高风险接口/自动化探针：分开运行时、CI/dev、示例；列资产→入口→信任边界→攻击者能力与非能力→现有控制证据→建议控制；优先级附现实前提而不是泛化“高危”。例如本地 MCP 的公网暴露、任意 Python、IDB 写权限，必须分别有可观察配置依据。

不可照搬：完整威胁建模本来仅在用户明确要求时触发；不能扩大成每次普通 UI 任务都做 AppSec。其第 6 步要求暂停等用户回答，不能覆盖当前用户睡眠期间自主推进或 A/B/C 的既定约定。缺少事实可以做条件性结果而不伪造确认。该项目不提供 IDA/UE API 权威性。

## 4. OpenAI skill-creator：复用分层组织，不直接采用简版验证器

源：https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.system/skill-creator/SKILL.md
脚本：https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.system/skill-creator/scripts/quick_validate.py
许可证：同目录 LICENSE.txt。

值得借鉴：短入口、按需 references、可复用 scripts/assets，明确触发语义。SkillForge 已实现该模式，维持即可。

实际脚本是 minimal validator，仅检查 YAML、有限前置字段、名称格式与长度等。代码用 `if name:` 与 `if description:` 包围内容验证，因此空字符串不会被此处拒绝；不检查断链、路由误触发、脚本真实性、API 版本、实际能力。不能把其 `Skill is valid!` 当验收通过。SkillForge 应继续本身较强的结构/引用/语法/行为分层检查。

## 5. obra/superpowers：方法参考，拒绝整包路由接管

源：https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7/skills
本轮读取 writing-skills、systematic-debugging、verification-before-completion；根 LICENSE 为 MIT。

可复用：用无技能基线暴露真实失败；对纪律类技能设计时间压力/沉没成本场景；分析最终输出中的隐含完成声称；独立复核 Agent 的变更而非相信“完成”。现有 debugging 和 experience-maintenance 已有主要方法，不新增同义技能。

不直接采纳：整套 MUST 入口、跨技能强依赖、每个修订都必须先失败、机械强制同一消息运行验证命令、没有完整验证就称“partial proves nothing”。实际应精确表述局部证据能证明的局部范围；有效历史验证也应可追溯保存，而不是因消息边界失效。保留 SkillForge 风险自适应流程和自包含技能。

## 6. 不建议直接加入的候选

### Anthropic webapp-testing
固定源：同 Anthropic SHA 的 `skills/webapp-testing/SKILL.md` 与 `scripts/with_server.py`，许可证 Apache-2.0。

已检查实际 helper：以 socket 连接端口判断 ready；`Popen(shell=True, stdout=PIPE, stderr=PIPE)` 启动但运行中不消费输出；最后 terminate/kill 该 Popen，不保证清理所有 shell 子孙进程。可能误把同端口旧服务当新服务、长输出堵塞、子进程残留。入口还要求先执行黑盒 `--help` 再看源码，并将 networkidle 当动态 JS 已完成的重要条件。均不适合直接输入 SkillForge 的未知脚本安全和工程验证规则。

只吸收“先观察真实 UI 状态再动作、截图与交互验证分开、拥有的资源 finally 清理”。不要把 Web Playwright 工具引入 Qt/MFC/UE 的原生测试；不要把网络静默当页面业务准备完成证据。没有新增 Web 项目需求，暂不加入独立技能。

### OpenAI gh-fix-ci
固定源：同 OpenAI SHA 的 `skills/.curated/gh-fix-ci/SKILL.md`，Apache-2.0。

值得参考：记录 run URL/head SHA、日志缺失状态、CLI 字段漂移降级、区分第三方 CI。但其固定“显式批准之后实施”、登录假设和只支持 GitHub Actions 不宜覆盖当前工作流；已有 debugging 可以按需增加 CI 证据条目，不新增整包。

## 推荐整合包（给主集成人）

1. `experience-maintenance/references/skill-evaluation.md`：自拟中文规则，记录基线、公平条件、近邻负例、实际证据、成本、盲评可选、not_run 与 pass 分离。入口加按需链接，别改变主路由。
2. 对现有 trigger-cases 增加每技能一两个真正近邻负例，替换只有“你好”类弱负例；不把 JSON 用例存在称 Agent 实测。
3. IDA MCP 现有测试/说明补入上述失败路径清单（如已覆盖则仅引用，不再复制）。
4. 只做来源归纳优先。若复制/改编 Apache 或 MIT 代码、文字，保留相应 LICENSE、原版权/NOTICE（若上游有），标明修改与原 SHA；不要把“链接引用”误写成“已引入第三方代码”。
5. 本轮不建议新增 Skill，不引入新框架、后台服务、自动插件安装或新授权层。

## 验证状态

完成：GitHub 仓库 metadata/commit/tree 读取，固定版本源文件和相关许可证读取，现有技能职责比对，候选脚本静态审阅。
未执行：第三方技能安装、脚本运行、模型 A/B 评测、浏览器实测、IDA/MCP 实机验证。以上建议是有源材料的适配分析，不是宣称现有技能已获得运行能力。
