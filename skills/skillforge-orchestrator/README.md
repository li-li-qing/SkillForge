# skillforge-orchestrator v0.2.0 portable

这是 SkillForge 的通用入口层。目标是让同一套编排逻辑在不同 Agent、IDE、模型和未来未知宿主中复用，而不是针对某几个产品写死。

## 使用原则

1. 用当前宿主**实际支持的方式**显式选择/读取 `skillforge-orchestrator`。
2. 把原始需求直接跟在入口之后；不要为了适配入口先人工改写需求。
3. 入口先返回项目识别、能力快照、Skill 路由、上下文建议和执行简报。
4. 默认等待一次确认；回复“开始”即可继续当前唯一简报。若本次明确写“直接执行，无需确认”，可跳过普通确认。
5. 只要宿主可以读取 `SKILL.md`，即使没有原生 Skill 调用机制，也可以按文件规则使用；此时必须诚实标记为“read-file/inline-text”，不能宣称原生调用。

## 不依赖的东西

portable core 不包含：

- 特定 Agent 的 metadata；
- 专用 `/`、`$` 等调用命令；
- 固定技能安装路径；
- 当前七个/八个 Skill 的静态索引；
- Python 或其他脚本运行时；
- eval/test 开发资料。

因此未来出现新的 Agent 时，优先做 capability mapping，而不是修改 Orchestrator 核心。

## 常用使用方式

### 1. 交互式分流（日常最推荐）

只需直接附上任务意图，AI 会主动给出 A/B 选择，不急于出方案：

```text
用户：
使用 skillforge-orchestrator。我想做一个瞬移技能。

AI：
收到需求：【制作瞬移技能】。请选择接下来的推进方式：
- 【A. 列计划推进】需求已明确，直接核对工程、匹配技能并出具执行简报与实施清单。
- 【B. 打磨需求（战略参谋）】需求还在构思中，身份对调，由我作为战略参谋向你抛出关键问题摸清底牌，理顺逻辑后再落地方案。
回复 A 或 B 即可开始。
```

- 若回复 **A**：走标准执行流，只读检查、技能路由、出具清单与简报，等待一次确认后实施。
- 若回复 **B**：进入参谋打磨流，身份对调，AI 每轮抛出 1~3 个关键问题摸清底牌与边界，理顺逻辑后平滑收敛为执行简报。

### 2. 快速直达模式（若一开始意图明确）

```text
【直达 A：直接列计划】
使用 skillforge-orchestrator。直接列计划：
<原始需求>
```

```text
【直达 B：直接做战略参谋打磨】
使用 skillforge-orchestrator。作为战略参谋帮我打磨需求：
<初步想法 / 困惑>
```

```text
【直接执行，跳过普通确认】
使用 skillforge-orchestrator。本次直接执行，无需普通确认：
<原始需求>
```

```text
【只优化提示词】
使用 skillforge-orchestrator。只优化提示词，不执行：
<原始需求>
```

这些是自然语言工作约定，不要求宿主支持固定命令语法。

## Portable Runtime 内容

```text
skillforge-orchestrator/
├─ SKILL.md
├─ README.md
├─ references/
│  ├─ advisory-workflow.md
│  ├─ capability-contract.md
│  ├─ routing-policy.md
│  ├─ context-policy.md
│  ├─ approval-policy.md
│  ├─ user-workstyle.md
│  └─ maintenance.md
└─ assets/
   ├─ execution-brief.md
   ├─ checkpoint.md
   └─ feedback-template.md
```
