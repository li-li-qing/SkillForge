# skillforge-orchestrator v0.2.0 portability redesign

目标：让运行时核心对未来未知 Agent 也成立。核心不识别产品名，只识别能力；不维护当前 SkillForge 的固定叶子 Skill 列表；不携带开发 eval、索引脚本或宿主专用 metadata。

## Runtime

`skills/skillforge-orchestrator/` 只包含 `SKILL.md`、README、references 与 assets。frontmatter 仅 `name + description`。

## Development

`development/skillforge-orchestrator/` 保存 eval、索引工具、测试、历史快照和研究。索引工具根目录必须显式传入，避免假定任意宿主的安装布局。

## Capability-first

核心路由只消费 capability snapshot：skill discovery/loading、context meter/compaction、file read/write、command execution、artifact delivery 等。宿主专有格式只在外部 adapter 映射成这些能力。

## Dynamic routing

routing policy 按 Project / Domain / Method / Surface 职责槽位从实时元数据选择最小充分集合，不再写死任何叶子 Skill 名称。具体组合只保留在开发 eval 中作为当前 SkillForge 的回归案例。
