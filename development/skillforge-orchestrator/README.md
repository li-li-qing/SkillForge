# skillforge-orchestrator development

本目录存放 portable runtime 之外的评测、工具、历史快照和研究材料。`skills/skillforge-orchestrator/` 才是可直接分发的通用核心。

原则：
- 开发工具可以依赖 Python，但运行时核心不能依赖它。
- 行为 eval 可以引用当前 SkillForge 的具体 Skill 名称，但运行时 routing-policy 不可以维护固定组合表。
- 宿主专用 metadata 应作为外部 overlay 维护，不得写进 portable `SKILL.md`。
- 新宿主优先映射到 capability contract；只有格式发布确实要求时才做 adapter。

工具：`tools/build_skill_index.py` 只用于开发/诊断，必须显式提供一个或多个 `--root label=directory`，不再假定“兄弟 skills 目录”。
