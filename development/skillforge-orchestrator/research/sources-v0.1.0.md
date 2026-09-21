# 来源与采纳边界

核对日期：2026-09-21。链接指向一手资料；在线文档会变，版本敏感内容使用前应复核。本包不复制第三方 Skill 正文或代码，索引脚本为本轮编写。

## 一手依据

| 来源 | 采纳内容 | 不推出的结论 |
|---|---|---|
| [Agent Skills Specification](https://agentskills.io/specification) | SKILL.md + frontmatter；元数据、正文、参考按需读取；可选目录 | 不意味着所有宿主都有相同调用方式或权限拦截 |
| [OpenAI：Build skills](https://developers.openai.com/codex/skills) | 明确触发边界、显式/隐式使用；可选 agents/openai.yaml | 不把某宿主预算比例、安装路径或自动匹配行为写成通用定律 |
| [OpenAI：Compaction](https://developers.openai.com/api/docs/guides/compaction) | 原生压缩属于 API/宿主能力，有实际配置与输出状态 | Skill 不能仅凭输出摘要获得这项工具能力；不抄模型/阈值常量 |
| [Anthropic：Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 高信号工作集、压缩、外部笔记、分层获取；警惕压缩丢失细节 | CHECKPOINT/COMPACT 的五选项为本包设计，不是该文定义的标准等级 |
| [Claude Code：Extend Claude with skills](https://code.claude.com/docs/en/skills) | 技能发现与作用域受宿主控制；上下文生命周期与命令调用有边界 | 用户能输入原生命令，不代表 Agent 能以 Skill tool 调用；语言规则不是安全沙箱 |

## 对上一轮讨论的修订

渐进加载本来就是原生 Skills 常见设计，本入口主要增加用户可见的路由与任务确认，不宣称“只有入口才能节省上下文”。索引大小随条目数增长，不承诺技能无限增长时固定 token 成本。

确认前可以读取必要专业 Skill 正文以核实硬约束；只禁止执行副作用，避免“尚未读规则就确定计划”的盲区。确认后沿用同一份任务，不按技能重复确认。

固定 token 百分比、指定模型窗口数、自动压缩、自动新会话、自动跨会话记忆均不作为能力承诺。新上下文恢复必须保留未验证项与授权来源。

## 本包自己的设计选择

“最小充分技能集”“原文+执行简报”“默认一次确认”“五种上下文动作”“只读索引检查”属于针对本用户需求的设计，不宣称经过第三方证明。其效果需要不同模型/宿主的真实试用对照；此次脚本与结构测试不能代替该证据。

前轮提及的第三方 Router/Prompt Optimizer 作为思路背景，不作为本版运行依赖，也不把其 README 的营销数值写成规范。
