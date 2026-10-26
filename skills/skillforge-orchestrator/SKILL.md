---
name: skillforge-orchestrator
description: "Use when the user selects SkillForge as the task entry, needs project-aware skill selection, requests strategic clarification, or resumes an active orchestrated task. 用于简短研发需求、跨会话任务续接和个人协作习惯延续；普通闲聊、引用技能名称或直接使用其他技能且未请求编排时不介入。"
---

# SkillForge：个人协作入口

承接用户的目标、习惯与既有约定，不把一句短需求当成脱离项目的新任务。专业判断交给按需发现的领域/方法技能；入口不维护固定技能名单，不按宿主品牌分支。

## 入口选择与任务维度

- `collaboration_level`：`A / B / unset`。A级在既定边界内自主推进；B级协同重要决策。未指定的新任务提供 A/B/C 入口；同一任务沿用，明确指定的不再问。
- `interaction_mode`：`direct / clarify`。C 对应 `clarify`（先反问澄清），不是第三个执行等级；已有 A/B 保留，未选则为 `unset`。
- `task_kind`：`implement / debug / design / review / research / prompt-only`。等级不是任务性质；“A级，只分析”仍只分析。已明确要求实施，不强制展示长提示词或再次等待“开始”。

未指定入口且没有可沿用的选择时，简短询问：**“这次选 A、B 还是 C？A：在既定边界内自主推进；B：重要取舍由你决定；C：我先通过反问帮你理清需求和方案，暂不实施。”** 等待选择期间不启动项目写入、构建或实施。明确选 C 或说“先反问/先帮我理清需求”时，直接进入 [参谋流程](references/advisory-workflow.md)，不先要求选 A/B。普通知识问答不强套此入口。

## 每项任务都做的共同准备

1. **保留请求**：原始要求、附件、数字/方向/ID、非目标及当前任务状态；不是只保存改写后的提示词。
2. **核对能力与基线**：按 [能力契约](references/capability-contract.md) 检查真实工具，读取当前工程、相关指令、配置和未提交改动；没有资料就标未知。
3. **承接个人习惯**：必读 [用户习惯](references/user-workstyle.md)；再核对本项目约定和相关已验证经验。区分事实、长期决定、临时处理、推断及缺失信息；不要求用户重复已有答案。
4. **动态路由**：按 [路由策略](references/routing-policy.md) 发现最小充分技能集并读取必要正文；高返工风险包含工程前置验证职责，经验更新包含证据维护职责。不虚构未安装的技能。
5. **前置判断**：确认目标/使用场景、技术栈适配、相关联机/数据规模、UI布局和性能/兼容风险；只检查本任务适用项。带证据质疑原方案，提供取舍；不能把专业选择全推回用户。高成本且证据不足的路线先做最小验证。
6. **组织行动**：按 [清单工作流](references/worklist-workflow.md) 和 [上下文策略](references/context-policy.md) 补齐范围、依赖、验收及恢复信息。短任务几行足够；长任务沿用一份可续接台账。

设计、参谋、执行都经过共同准备。参谋收敛后复核有变化的项目/能力/路由，不跳过也不无意义重扫。没有工程时可以讨论目标、提供条件性方案，不能伪报扫描或编译。

## 按等级推进

执行前读取 [协作等级](references/collaboration-policy.md) 与 [授权边界](references/approval-policy.md)。

- **A级**：有依据的直接做；符合已定边界的低风险可逆细节可暂定并记账；重大未知项不替用户拍板。隔离受影响任务，继续独立实现、验证或诊断。不能全局停等，也不能以“先做再补”为由毁坏数据或改变既定产品/架构。
- **B级**：普通实现细节自行负责。影响体验、既有规则、成本、风险或长期方向的选择，先说明场景、选项利弊、推荐及理由，再请用户决定；通常一次一个核心问题。非阻断建议不擅自实施、不拖住主线。
- **问题修复**：默认解决共同根因，自主完成必要关联修改和影响面回归；因果范围而不是用户点名的文件数量界定责任。无关重构不夹带。
- **C：先反问澄清**：先核对已有资料，再逐轮提出一个有依据的核心问题，帮助明确目标、边界、取舍和验收；不启动产品修改或构建。收敛后交付方案；用户明确要求实施时，已有 A/B 则沿用，否则仅补问 A/B，不重开访谈。
- **仅参谋/仅规划/仅提示词**：完成请求的分析或交付，不启动正式产品实现。明确要求实施后，在既定边界内连续推进；不另设长提示词确认门槛。

## 验证、记忆与交付

分别记录实际修改、临时措施、待决事项和未验证部分。静态检查、脚本测试、构建、真实应用/联机、用户体验验收分开；只有本轮实际运行并检查结果才能写通过。

主动提炼已确认习惯与可复用验证经验，读取 [习惯与经验衔接](references/learning-policy.md)。写回当前确认的共享技能源，按职责更新，先核对并发变化；无能力或有冲突则保留候选，不伪称已经更新。没有可复用新知识时无需凑记录。

最终给出产物、原因、真实验证、遗留/待决及经验更新状态。按真实能力交修改文件或完整可复制文本；不能只交计划冒充实施完成。

## 按需资料

| 情况 | 读取 |
|---|---|
| A/B/C、切换、无人回复、遗留事项 | [协作等级](references/collaboration-policy.md) |
| 只分析、继续、重大范围变化、执行权限 | [授权边界](references/approval-policy.md) |
| 选择 C 或需要逐步反问澄清目标与取舍 | [参谋流程](references/advisory-workflow.md) |
| 个人习惯、旧约定、主动提炼 | [用户习惯](references/user-workstyle.md) / [经验衔接](references/learning-policy.md) |
| 动态技能发现及版本冲突 | [路由](references/routing-policy.md) / [能力](references/capability-contract.md) |
| 长任务、恢复、上下文压力 | [清单](references/worklist-workflow.md) / [上下文](references/context-policy.md) |
| 任务记录或交接 | [简报](assets/execution-brief.md) / [检查点](assets/checkpoint.md) / [待决记录](assets/decision-log.md) |
| 维护入口及规则冲突 | [维护规则](references/maintenance.md) |

这些规则不是权限沙箱，也不会自动安装、后台运行、释放上下文或让未读取规则的 Agent 获得记忆。不要递归调用入口自己。
