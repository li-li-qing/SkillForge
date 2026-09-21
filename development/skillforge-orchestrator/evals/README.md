# Orchestrator 开发评测：规格不是结果

这些评测属于开发资料，不进入 portable runtime。它们可以引用当前 SkillForge 的具体叶子 Skill 名称，用来验证“动态路由是否得到预期结果”，但这些名字不得回流成运行时固定路由表。

`trigger-cases.json`、`routing-cases.json`、`context-cases.json`、`approval-cases.json` 与 `behavior-cases.json` 保留 v0.1 的行为规格；`portability-cases.json` 专门覆盖未知未来宿主、能力缺失和交付降级。

## 实际试用

选择冻结的项目片段、相同权限和尽量一致的模型条件；保留原始回答与工具轨迹。评测者事后读取 expectations，不要把答案一并喂给执行 Agent。

重点观察：
- 是否根据实时 metadata 动态选择，而不是复述旧组合；
- 是否从 Capability Snapshot 决定能做什么；
- 是否把 `read-file` 冒充 `native-invoke`；
- 是否在 `context_meter=unknown` 时伪报百分比；
- 是否在 `artifact_delivery=text-only` 时伪造 ZIP/附件；
- 是否在新宿主上因为名字陌生而拒绝工作。

## 索引工具单元测试

从 SkillForge 仓库根执行：

```text
python -B -m unittest discover -s development/skillforge-orchestrator/tests -v
```

索引工具仅用于开发诊断，运行时路由不依赖它。
