# skillforge-orchestrator v0.1.0 验证报告

日期：2026-09-21。用途：第一版外部试用，不是所有宿主行为已认证的发布。

## 基线与变更

基线为本会话 SkillForge-MFC-v1.zip，含 241 个文件、7 个专业/方法 Skill。新增 skillforge-orchestrator 后有 8 个入口。既有文件只修改 README.md；既有专业技能的 116 个文件逐字节不变，无删除。

新增内容：入口正文、7 份专题参考、3 份模板、独立说明、可选 Codex 显式调用元数据、只读优先的索引器及其单测、候选索引、触发/路由/上下文/确认/行为用例、设计与本验证记录。

本轮没有安装到你的 Agent，没有改项目工程，没有创建 Git 提交/推送，没有写宿主设置。索引快照来自出货库，不证明宿主的实际安装状态。

## 已完成的验证

| 检查 | 实际结果 | 证据/范围 |
|---|---|---|
| 索引工具首次测试 | 38 个预期失败 | [初始 RED](orchestrator-v1/index-initial-red.log)：实现尚不存在；不是 Agent 行为基线 |
| 中文输出路径旧式编码复现 | 1 个真实失败 | [编码 RED](orchestrator-v1/unicode-path-red.log)：文件写出后输出编码导致错误状态 |
| 索引工具最终回归 | 39/39 PASS | [最终日志](orchestrator-v1/index-final-green.log)，临时真实文件与子进程 |
| 既有 validator 完整测试套件 | 31/31 PASS | [完整日志](orchestrator-v1/legacy-validator-final-green.log)，无删改原测试 |
| 全库自包含校验 | 8 skills / 0 errors / 8 standalone copies | 运行 scripts/validate_skills.py --self-contained |
| 索引与当前出货专业技能一致 | CURRENT；7 条，入口自身未进入路由索引 | description、相对路径、入口字节 SHA-256 |
| Python 源码解析 | PASS | 新脚本与测试；并不表示已在所有 Python 版本运行 |
| 原有专业技能不变 | PASS，116 个原文件 SHA-256 一致 | 修改范围没有蔓延到 MFC/UE/LGF/ArcheRage 等 |
| 最终 ZIP 外校验 | 见发行清单的 package_checks 字段 | fresh extract、CRC、相对路径、JSON、自包含、增量重建一致性 |

执行环境：Linux，Python 3.13.5；名义最低 Python 3.10 的语法/API兼容经过代码检查，未在 Python 3.10 或 Windows 实机运行。中文编码测试是在子进程设置旧式编码的回归，不冒充 Windows 验证。

## 规则复核修正

1. 确认前允许只读必要专业技能正文，以免未读约束就承诺方案；不执行其中的副作用。
2. 一份原请求、一份修订简报、一次范围内确认；确认来自当前用户或可验证采用指令，不能由文档字段伪造。
3. KEEP/NARROW 不承诺回收 token；COMPACT 的推荐、请求与成功状态分开；不能从模型名称猜窗口。
4. 动态宿主清单优先，目录快照其次；索引不是已安装证据，新技能无需修改白名单。
5. 索引重复名、损坏头部、符号链接/边界、不可读源等 fail-closed；无自动脚本执行、安装或联网。
6. 原始需求中的数字、方向、ID、禁止项与讨论/实施模式保留，不允许“优化提示词”扩大任务。

这些是作者对规则的一致性检查，不是独立模型审阅通过的声明。

## 行为评测：未执行

已建立 12 个 trigger、16 个 routing、10 个 context、12 个 approval 场景；behavior-cases 汇总并补充为 41 例，彼此部分重叠，不能相加当独立通过数。

本会话没有可用的隔离模型/子 Agent 评测器。未执行无技能/有技能的独立对照；未证明路由正确率、token 节省量、确认门服从率或跨宿主改善。真实试用需保留实际回答与工具轨迹，不能靠命中关键词打 PASS。

## 第一版真实限制

Skill 是软规则而非权限沙箱；模型可能不遵守，硬只读依赖宿主权限。仅输出摘要不能真正压缩历史。缺少项目/技能读取工具时只能给条件性简报。索引支持本库受限 YAML，不是生态通用解析器；每次新增技能需要实时清单或重建快照，未内置后台自动更新。

未做：Codex/Claude Code 客户端安装与自动发现实测、原生压缩调用、Windows 脚本运行、真实 LCot 项目修改、独立 Agent 行为实验。

## 复核命令

在全库根：

```text
python -B -m unittest discover -s tests -v
python -B scripts/validate_skills.py --self-contained
python -B -m unittest discover -s skills/skillforge-orchestrator/tests -v
python -B skills/skillforge-orchestrator/scripts/build_skill_index.py --check skills/skillforge-orchestrator/generated/skill-index.json
```

独立包可以直接跑其 tests；没有安装其他七技能时，快照检查返回 stale 属实，不是自动安装失败。目录/链接结构检查与 Agent 行为检查分别进行。
