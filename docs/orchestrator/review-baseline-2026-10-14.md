# SkillForge(5) 第一轮审查记录

日期：2026-10-14。范围：9 个 SKILL.md 入口、入口编排的主要规则与模板、相关评测定义、现有 Python 校验与工具测试。没有逐条重新核验全部领域 references 的技术结论，也未进行独立 Agent、UE、Qt/Windows、游戏客户端实测。

## 结论

保留现有领域划分与按需加载结构。优先修正编排入口的流程一致性、运行/开发资料分离及新增分支的行为验证。结构校验通过不等于 Agent 行为验证通过。

## 本轮实际验证

以下命令均在解包工作副本的 SkillForge 根目录运行。使用系统 Python 3.13 执行；两次先前使用默认解释器的完整根测试尝试被执行时限中断，以下只采用随后完整完成的运行结果。

| 检查 | 命令 | 实际结果 |
|---|---|---|
| 全库结构与独立复制 | `/usr/bin/python3 -B scripts/validate_skills.py --self-contained` | 9 个技能，0 error，9 份独立复制通过 |
| 根目录测试 | `/usr/bin/python3 -B -m unittest discover -s tests -v` | 43 项：40 通过、3 失败 |
| 开发版索引工具 | `/usr/bin/python3 -B -m unittest discover -s development/skillforge-orchestrator/tests -v` | 40 项通过 |
| 运行目录中的旧版索引工具 | `/usr/bin/python3 -B -m unittest discover -s skills/skillforge-orchestrator/tests -v` | 39 项通过 |
| ArcheRage 离线工具 | `/usr/bin/python3 -B -m unittest discover -s skills/skillforge-archerage-addon/tests -v` | 38 项：36 通过、2 跳过；未提供 RS_TEST_LUA51 |
| LGF 工作区检查工具 | `/usr/bin/python3 -B -m unittest discover -s skills/skillforge-lgf/tests -v` | 10 项通过 |

两套索引工具测试存在重复，不能把数量相加当作独立行为场景覆盖率。

根测试失败名称：

- `test_runtime_does_not_name_specific_hosts`
- `test_runtime_has_no_fixed_leaf_skill_catalog`
- `test_runtime_has_only_portable_surface`

这三项在包内 `evals/runs/2026-09-22/qt-initial-validation.md` 已有记录，本次仍可复现。

## F01：默认 A/B 流程与既有策略、评测没有同步

定位：

- `skills/skillforge-orchestrator/SKILL.md:26-35,55-64`
- `skills/skillforge-orchestrator/references/approval-policy.md:7-15`
- `skills/skillforge-orchestrator/references/user-workstyle.md:11-15`
- `development/skillforge-orchestrator/evals/approval-cases.json` 的 `SFO-A01`
- `development/skillforge-orchestrator/evals/behavior-cases.json` 的 `SFO-B27`

主入口对未指定模式的任务要求先选 A/B；授权策略仍规定新任务只读调查后返回执行简报，用户习惯则写需求明确时直接返回提示词等待一次确认。旧评测也直接期望简报 pending，没有模式选择阶段。

选择 A/B 是模式选择，不是执行授权，不能简单断言这就是“两次授权错误”。问题是多个文件没有表达同一套进入条件。应明确何时展示 A/B、何时直接进入准备、何时已有授权继续，并同步策略与案例。保留用户有意设计的 A/B 体验，不擅自删除。

## F02：参谋分支收敛后跳过共同准备阶段

定位：`skills/skillforge-orchestrator/SKILL.md:32-40`。

第 2 步写“收敛后转入步骤 7”；第 3—6 步分别为能力快照、项目识别、技能路由与上下文动作。这使按字面执行的 Agent 可以在未完成这些前置工作时直接写简报。

`references/advisory-workflow.md:10` 要求结合工程事实提问，但没有完整替代能力、路由、上下文检查；其第 62 行“切换回标准执行流程”也没有消除主入口明确跳转的歧义。

建议：将共同准备放到分支前，或规定 B 收敛后回到第 3 步，已完成且证据仍有效的步骤允许复用。新增无工作区、仅文本能力、用户要求停止追问、B 转 A 的场景。

## F03：运行包仍混有开发资料和宿主适配文件

定位：`tests/test_orchestrator_portability.py:9-44`，以及 `skills/skillforge-orchestrator/`。

运行目录仍有 `agents/`、`generated/`、`evals/`、`scripts/`、`tests/`；同时仓库已经存在 `development/skillforge-orchestrator/`。`references/host-capabilities.md` 还保留具体宿主说明，`agents/openai.yaml` 存在产品适配元数据。

这是与本项目自己定义的 portable core 边界冲突，不代表 Agent Skills 标准禁止 scripts、assets 或扩展目录，也不能仅因出现某个 Agent 名称就断言实际路由错误。主入口和 routing-policy 本身采用动态发现，没有发现它们明确要求用旧索引代替真实技能清单。

建议明确交付物层次：运行核心、开发测试/快照、宿主适配。按边界移动并更新引用，保留历史和测试，不为得到全绿而删除断言。

## F04：两份索引实现分叉，现有快照过期

定位：

- `skills/skillforge-orchestrator/scripts/build_skill_index.py:22,218-224`：0.1.0；省略 --root 时默认读取兄弟技能。
- `development/skillforge-orchestrator/tools/build_skill_index.py:22,218-224`：0.2.0；--root 必填。
- `skills/skillforge-orchestrator/generated/skill-index.json`。

两个工具分别运行以下只读检查，都返回 STALE、退出码 1：

```text
/usr/bin/python3 -B skills/skillforge-orchestrator/scripts/build_skill_index.py --root skills=skills --check skills/skillforge-orchestrator/generated/skill-index.json
/usr/bin/python3 -B development/skillforge-orchestrator/tools/build_skill_index.py --root skills=skills --check skills/skillforge-orchestrator/generated/skill-index.json
```

用开发版工具生成临时结果进行逐字段比较，快照中的 LGF 入口 SHA-256 与当前文件不同；现有快照包含 Qt，并不是漏了 Qt。旧版工具还存在生成器版本差异。

快照明示不代表安装或授权，主流程也不依赖它，因此本轮只能认定维护状态漂移，不能宣称已经导致实际漏选技能。建议只保留一个权威工具实现，历史版本转为明确归档。

## F05：新增参谋分支缺专门行为题与实测证据

已查看入口开发题集的所有 prompt，未发现 A/B 选择、参谋收敛回流及相关中途切换的专门场景；旧规格仍以 v0.1 流程为主。开发版已有 41 个 behavior、12 个 approval、16 个 routing 等案例，但它们是案例定义，不是已经执行的结果。

Qt 第一轮验证报告明确列出独立 Agent 对照 not_run。现有 Python 测试证明结构和工具行为，不能证明模型会正确选技能、不会重复确认、会在 B 收敛后读齐专业规则。本轮也未执行此类模型行为试验。

建议补充新分支场景，并以相同工程片段、相同权限、可追踪原始输出进行真实 Agent 行为回归；不把答案 expectations 直接提供给执行 Agent。

## 可保留的设计

- 9 个技能分为入口、领域、项目与横切方法，Qt/MFC/UE/Lua 的边界已显式表达。
- 核对当前工程而不是继承旧版本、旧路径，Qt 不套用 UE 的 TObjectPtr/OnRep/FastArray。
- 主入口按可观察能力工作，区分可发现、可读取、已读取、原生调用与未知状态。
- 上下文策略区分检查点与真正压缩，不把摘要宣称为 token 已释放。
- 叶子技能按需读取 references，不要求每次加载全部领域知识。

## 未修改基线核对

逐文件与上传 ZIP 比对全部 757 个原文件的 SHA-256：内容变更 0，缺失 0；解包源码目录新增文件 0。本审查记录和测试日志位于源码副本之外。

原 ZIP SHA-256：`97943a45b4c6a3f912942dbc09daa99f91df32f2aef4d70cf6bb329de22f3aae`。
