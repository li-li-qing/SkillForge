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

## 三种常用模式

```text
【默认】
使用 skillforge-orchestrator 处理下面的原始需求：
<原始需求>
```

```text
【本次直接执行】
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
