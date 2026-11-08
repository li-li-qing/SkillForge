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


## 2026-11-07 更新器故障诊断补充

本节适用于当前 `scripts/apply_skillforge_update.py`，不改写上面的历史版本记录。更新器在尝试任何目标写入前，以及持锁后，检查旧事务；未完成记录会阻止新一次 apply，包括目标已等于新版的情形。

```text
python scripts/apply_skillforge_update.py --root "你的SkillForge总目录" --inspect-pending
```

此命令只读输出未完成事务、备份和状态文件路径、已记录完成项及当前文件哈希。发生目标写入或审计保存故障时，CLI 返回 exit 3 和 `status: incomplete`，分别报告 `mutation_attempted`、已读回验证项、尚不确定项及 `journal_persisted`。日志也无法持久化时应保存终端输出；不能把非零退出当作“未改任何文件”，也不能自动重试。

恢复仍是有证据的人工协调流程：停止同一更新目标的协作写入，保留备份与状态，核对计划内文件、退休目录及后来修改，选择完成剩余操作或按受保护逆向变更恢复。检查无法读取/缺失的状态文件时不得凭文件名猜测已完成。只有实际核验并处理所有项后，维护者才可在同一写锁协议保护下将该事务状态记为 `reconciled`，并用非空 `resolution` 记录处理理由与证据位置；该字段是维护者确认，不是程序证明。不要删除日志来绕过门禁。

此流程不提供多文件原子事务，也不承诺断电后目录元数据持久性。Windows 保留设备名和非法路径字符在跨平台预检中被拒绝；这属于路径静态检查，仍未进行 Windows 实机测试。


### v5 候选的锁清理状态补充

更新器已完成写入并持久保存applied后，若释放自己的write.lock失败，返回exit 3和cleanup_required / transaction_status=applied，保留原applied日志。此时处理的是锁清理，不是重跑更新或把已提交事务送入恢复。核实所有权及写入者状态后显式处理，不能自动偷锁。真正未完成写入仍返回incomplete并保留前述恢复门禁。两种失败同时发生时保留业务与清理错误。
