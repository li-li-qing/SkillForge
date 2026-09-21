# Orchestrator 维护规则

## 核心必须保持宿主无关

运行时目录只承载编排语义和模板。不要把以下内容写进核心：

- 某个 Agent/IDE/模型的名字作为条件分支；
- 某个产品的专用命令或固定安装目录；
- 某个宿主的专用 frontmatter/metadata；
- 当前 SkillForge 的固定叶子 Skill 列表；
- 需要特定语言运行时才能完成路由的必需脚本。

如果某个宿主必须额外 metadata 或包装格式，应在运行时核心之外生成 overlay/adapter；核心只读取映射后的 capability snapshot。

## 新增 Skill 时

不改 Orchestrator 的固定路由表。保证新 Skill 的 `name` 和 `description` 能清楚描述触发、排除和职责；真实宿主能发现它时，它自然参与动态路由。

只有跨项目的编排错误进入本入口。项目 API、框架约束、业务知识继续进入对应叶子 Skill。

## 回归分类

- 选错/多选/漏选 Skill → routing case
- 假压缩/错误 handoff → context case
- 重复确认/未确认写入 → approval case
- 提示词丢数字、方向、非目标 → prompt/behavior case
- 依赖某一宿主才能工作 → portability case

行为评测、索引工具和发布脚本属于开发资料，不应放进 portable runtime 包。
