# SkillForge 0.3.0 使用与维护

## 安装本轮修改包

本轮基于 SkillForge(5).zip，不是从用户实时共享目录读取。先暂停对该总目录的所有Agent写入，避免更新与开发经验回填同时发生；不要关闭用户产品或删除工程。

将变更ZIP解压到共享总目录之外。包内payload是保持原相对路径的新增/修改文件，manifest.json记录每个路径的原始/新版哈希，REMOVED_PATHS.txt列旧运行目录需移除文件。

优先在解压目录运行包内apply_update.py：

```text
python apply_update.py --root "你的SkillForge总目录"
python apply_update.py --root "你的SkillForge总目录" --apply
```

第一条只读检查，不写目标目录。确认无冲突后第二条备份受影响文件到目标目录的 .skillforge-backups，再应用并核对。需要Python3.10+；本轮实际测试是本地Linux，不宣称Windows实测通过。

如果报告CONFLICT，说明本地文件已不同于上传基线；不要强行覆盖。把差异交给当前维护Agent三方合并。若旧运行目录多出清单以外文件/缓存，工具也会停止，不能自动删除未知内容。无Python环境时由有文件工具的Agent按manifest进行同样的基线核对、备份、应用和验证，不仅直接覆盖payload。

工具只锁住遵守协议的写入者，不能防止任意编辑器或非协作Agent修改。中途失败保留备份/state.json，不盲目整库回滚；核对已完成路径及后来改动，再决定重试或受保护撤回。

## 日常使用

调用统一入口并发送任务。未选等级先问A/B；同一任务继承已确认等级。已有任务已选级且明确让其实施，不能再次发长提示词等用户说开始。

A自主不是无限权限，B协同不是普通实现逐步审批。仅分析、仅规划、仅提示词与正式实施分开。共享总目录不会自动让所有宿主加载技能，需确认实际入口读取和新增方法技能可发现。

## 经验怎样延续

个人习惯在入口user-workstyle.md；工程前置验证管风险/探针；经验维护管来源/归属/晋升/冲突。领域技术回领域，项目事实回项目。没有新知识不凑新条目。

实际共享更新先候选后核对：已确认偏好或证据充分技术内容无冲突可晋升；有争议保留依据继续独立工作。可选experience_store.py在共享根创建 .skillforge-memory，记录前后哈希、变更和受保护撤回；不能自动判断语义正确。

技能入口被宿主缓存时，按宿主实际重载方式使后续任务读取新版，不能假定改了文件就已更新当前Agent上下文。跨会话的检查点保留等级来源、任务性质、习惯版本、临时/待决及经验更新状态。

## 可复现检查

在总目录执行：

```text
python -B -m unittest discover -s tests -v
python -B scripts/validate_skills.py --self-contained
python -B -m unittest discover -s development/skillforge-orchestrator/tests -v
python -B -m unittest discover -s skills/skillforge-experience-maintenance/tests -v
python -B -m unittest discover -s skills/skillforge-archerage-addon/tests -v
python -B -m unittest discover -s skills/skillforge-lgf/tests -v
python -B development/skillforge-orchestrator/tools/build_skill_index.py --root skills=skills --check development/skillforge-orchestrator/snapshots/skill-index-current.json
```

索引排除编排器自身，因此11个技能对应10个候选条目。历史快照本来描述旧版本，不要求历史文件匹配当前内容。两个Lua5.1实机编译相关测试需要实际解释器配置，缺失时跳过不是通过。

行为题位于development/skillforge-orchestrator/evals/collaboration-cases.json，执行者只读取prompt/context，评审者才读取expectations；所有新增题本轮仍是not_run。原始输出与真实工具轨迹应随实际运行保存，不拿关键词检查当模型实测。
