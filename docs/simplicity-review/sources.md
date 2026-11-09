# 来源与取舍

核实日期：2026-11-09。仅原创归纳方法，不复制第三方代码、插件或其权限。没有引入新依赖。

- [Anthropic code-simplifier](https://github.com/anthropics/claude-plugins-official/blob/0412be76f50ab4f4f8abff3753efa9269fbbca5b/plugins/code-simplifier/agents/code-simplifier.md)：官方仓库实际 Agent 文件。采纳保持行为、可读性优先和避免过度简化；不采纳其前端专属风格和自主修改权限声明。
- [Karpathy-inspired 社区规则](https://github.com/multica-ai/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/skills/karpathy-guidelines/SKILL.md)：非 Karpathy 本人官方；frontmatter 标注 MIT。采纳以当前需求和验证目标约束改动；不采纳单用途绝不抽象、遇未知一律停止等绝对化措辞。未复制原文实现。
- [Google 工程审查](https://github.com/google/eng-practices/blob/3bb3ec25b3b0199f4940b1aa75f0ac5c5753301c/review/reviewer/looking-for.md)：Google 仓库稳定原则（已归档）。采纳阅读/修改成本衡量复杂度，仍检查合理并发和失败路径；不替换用户中文注释、工作流或语言规范。

这些是方法依据，不是证明本轮 Agent 表现改善的实验证据。
