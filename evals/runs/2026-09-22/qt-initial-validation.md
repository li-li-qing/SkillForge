# Qt Skill 第一轮实际验证

日期：2026-09-22。输入：SkillForge(4).zip。输入 SHA-256：`300e676f5c23a9a9e5f77c9b7dfc5f96edd45b6fd396831a282d30f1c000bd60`。

## 结论

新增 `skillforge-qt` 的结构、资源与独立复制校验通过；根完整测试仍有原包已存在的三项 orchestrator 便携性失败，不能称为“全部测试通过”。本轮没有增加新的根测试失败。

这是技能文档/包验证，不是 LCot 产品构建或 Qt/Windows/COM 运行验证。

## 实际命令与结果

以下命令以 SkillForge 根目录为工作目录，均只在本轮工作副本运行，没有安装到用户宿主。

| 检查 | 命令 | 实际结果 | 证据 |
|---|---|---|---|
| 原包完整根测试 | `python -m unittest discover -s tests -v` | 37 项：34 通过、3 失败；退出码 1 | [原包日志](qt-logs/baseline-tests.txt) |
| Qt 包契约 RED | `python -m unittest discover -s tests -p test_qt_package.py -v` | 未创建 Qt 资源时 6 个测试方法产生 16 个失败断言/子测试；属于预期缺资源失败 | [RED](qt-logs/qt-contract-red.txt) |
| Qt 包契约 GREEN | 同上 | 6 项通过 | [GREEN](qt-logs/qt-contract-green.txt) |
| 新包完整根测试 | `python -m unittest discover -s tests -v` | 43 项：40 通过、3 失败；退出码 1；失败名称与原包完全相同 | [完整回归](qt-logs/final-tests.txt) |
| 所有 Skill 独立复制校验 | `python scripts/validate_skills.py --self-contained` | 9 个 Skill，0 error，9 份 standalone copy 验证通过 | [包校验](qt-logs/final-validator.txt) |
| 开发版元数据索引工具测试 | `python -m unittest discover -s development/skillforge-orchestrator/tests -v` | 40 项通过；退出码 0 | [索引工具测试](qt-logs/dev-index-tests.txt) |
| 新元数据快照 | `python development/skillforge-orchestrator/tools/build_skill_index.py --root library=skills --check development/skillforge-orchestrator/snapshots/skill-index-2026-09-22-with-qt.json` | CURRENT；8 个叶子 Skill 包含 Qt，按工具规则排除 orchestrator 自身 | [快照](../../../development/skillforge-orchestrator/snapshots/skill-index-2026-09-22-with-qt.json) |

snapshot 只是元数据，不证明某个 Agent 已原生安装或正确路由。

第一次整体检查遇到工具单次执行上限，之后在当前任务内重新运行并读取完整退出码；开发索引测试也在一次限额中断后完整重跑。表中只计完整运行，不将中断输出算 PASS。

## 原包已有的三个失败

`test_orchestrator_portability.OrchestratorPortabilityTests`：

- `test_runtime_does_not_name_specific_hosts`
- `test_runtime_has_no_fixed_leaf_skill_catalog`
- `test_runtime_has_only_portable_surface`

原上传包的 orchestrator 目录残留 `agents`、`generated`、`evals`、`scripts`、`tests` 等历史资料；其内容与当前 portable core 测试约定冲突。本轮没有改变这些文件、删测试或调整断言来掩盖失败。新增 Qt 可独立使用，不依赖此旧目录清理。

## 新增六项包契约的范围

主入口名称与规模、十个主题及模板存在、六个来源的提交/blob/范围格式、18 个触发题和24个行为题的唯一 ID 与评分槽位、未知工程字段不预填、运行时参考不逃出自身目录。

RED/GREEN 仅证明这些结构断言具有缺失检测能力；不能证明模型经过训练，也不能冒充独立 Agent 行为对照。技术内容另做人工式静态复核，核心 API 用 Qt/Microsoft 一手资料校准。

## 未运行的项目

| 项目 | 状态与原因 |
|---|---|
| 独立 Agent 基线/加载 Skill 后对照 | not_run；当前没有独立 Agent 评测运行器 |
| LCot Qt 编译与测试 | not_run；本次附件为技能库，不是新 Qt 工程 |
| Windows Widgets/Quick/IME/DPI/多显示器 | not_run；没有相应 Windows 运行环境 |
| 真实大漠/COM/IPC与目标窗口 | not_run；没有当前 SDK/宿主工程和实测目标 |
| 六个外部 GitHub 项目构建或整仓审计 | not_run；本轮仅固定提交的定向文件切片 |
| 完整依赖与发布许可审计 | not_run；来源文件头不等于交付许可结论 |

## 变更与交付边界

原有文件只修改根 README 的 Qt 导航、数量和本轮说明。八个原 Skill 的文件内容均与输入 ZIP 一致；新增 Qt 目录、包契约测试、设计/交接文档、开发快照和证据记录。实际哈希比对见 [文件变化清单](qt-file-audit.json)。

完整合并 ZIP 只省略 `.git` 和 Python 缓存/临时缓存，不清理原来的技能或历史文档；它不是 Git 历史备份。独立 ZIP 根目录为 `skillforge-qt/`，包含正文、参考、模板和可选评测题集。都没有自动写入用户 Library、工程或 Agent 配置。
