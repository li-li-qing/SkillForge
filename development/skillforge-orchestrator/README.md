# 入口开发资料

本目录承载工具、测试、现行行为规格、研究与历史，不进入运行核心。

- tools/build_skill_index.py 是唯一活动索引实现，显式提供--root；不隐式扫描兄弟目录。
- snapshots/skill-index-current.json 是本轮诊断快照，内容变化后需重新生成；路由仍依赖当前元数据，不依赖快照。
- evals/ 是0.3.0现行规格，包含协作与经验案例；历史题集和旧工具在history/归档。
- 宿主metadata在仓库adapters/，没有自动安装。

结构和脚本结果见根evals/runs/2026-10-15/；没有独立模型运行记录时不宣称行为通过。
