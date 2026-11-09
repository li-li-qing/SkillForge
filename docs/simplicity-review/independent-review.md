# SkillForge 简化准则：独立反向审查

审查日期：2026-11-09。审查者：独立子任务 `independent_review`，不是实现作者。输入：`simplicity_upgrade_20261109` 中相对 main `12f82bb9b8c80ac42ad992d1efdc9721fc1a989b` 的本轮工作树差异。

## 结论

在本次阅读的 7 个已跟踪变更文件中，未发现阻断交付的问题。修改与已批准的小范围融合相符，未新增 Skill。

- `routing-policy.md`、`user-workstyle.md`、`collaboration-policy.md`、`approval-policy.md` 与 HEAD 逐字节相同；未改变 A/B/C、授权或路由。入口新增的是短实施准则，不强制普通任务触发高风险预检。
- 抽象判断以当前需求、职责、命名和阅读/测试成本为依据，没有把一次性 helper 一律禁止，也没有把最少行数当目标。
- 入口校验原则明确条件是“保证未失效”，保留异步、对象生命周期、跨边界和可变状态后的必要重查；没有要求编造异常概率。
- 纯简化要求保持行为，故障修复允许明确的预期行为变化；不会因保持行为而阻止根因修复。
- 反查仅针对本次改动与必要调用方；没有新问题即停止，不要求为了反查制造修改或启动全库重构。
- DBG-03 的备份期望已改为先核实版本控制、既有本地修改和恢复能力，正常可恢复的已纳管修改不机械复制备份；与既有用户习惯一致，未变成一律不保护资产。
- 新增 6 题分别覆盖避免投机框架、允许合理拆分、复用有效保证、保留失效后检查、保持错误/资源行为和停止无意义清理。评分关注行为和理由，不按代码行数、函数数评优；所有新增题仍标 `not_run`，没有以题目存在冒充模型行为通过。

## 独立执行的检查

- `python scripts/validate_skills.py --self-contained`：14 个技能、14 个独立副本，0 错误。
- `python development/skillforge-orchestrator/tools/build_skill_index.py --root skills=skills --check development/skillforge-orchestrator/snapshots/skill-index-current.json`：CURRENT。
- `git diff --check`：无输出，退出码 0。
- 两个修改的题库 JSON 均能解析，ID 在各自题库内唯一；debugging 10 题，preflight 13 题。

## 范围与限制

这是文件/规则一致性和结构检查，不是完整行为效果评测，也不是 UE、Qt、IDA 或游戏实机测试。未评审实现作者之后可能新增的报告、完整 ZIP 和上传产物，打包前仍需由交付者核对。未替代具体模型在同条件下的多次对照测试；不能据此声称新规则必然提高生成质量。
