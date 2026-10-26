# SkillForge

面向游戏开发与创作工具的个人 Agent Skills 技能源。当前包含 10 个专业/方法技能，以及统一入口 `skillforge-orchestrator`，共 11 个；专业技能仍可独立或组合使用。正文以中文为主，API、节点名和技术关键词保留英文。

| 技能 | 使用时机 | 入口 |
|---|---|---|
| `skillforge-orchestrator` | 明确调用统一入口：提供A/B/C入口，承接个人习惯与项目依据，按任务性质推进 | [统一入口](skills/skillforge-orchestrator/SKILL.md) |
| `skillforge-engineering-preflight` | 高返工成本选型、性能敏感交互、大规模同步或重要UI的前置判断与最小验证 | [工程前置验证](skills/skillforge-engineering-preflight/SKILL.md) |
| `skillforge-experience-maintenance` | 个人习惯、验证经验及多Agent共享规则的记录、晋升、冲突与撤回 | [经验维护](skills/skillforge-experience-maintenance/SKILL.md) |
| `skillforge-debugging` | 已出现错误、崩溃、偶发失效或结果异常，需要排查与修复 | [排障](skills/skillforge-debugging/SKILL.md) |
| `skillforge-ue-cpp` | 当前任务确实涉及 UE C++、反射、生命周期、模块或蓝图暴露接口 | [UE C++](skills/skillforge-ue-cpp/SKILL.md) |
| `skillforge-ue-blueprint` | 创建、修改、解释或排查 UE 蓝图、Widget Blueprint 与节点图 | [蓝图](skills/skillforge-ue-blueprint/SKILL.md) |
| `skillforge-ui-design` | 设计或调整 HUD、工具窗口、配置面板的布局与交互 | [UI](skills/skillforge-ui-design/SKILL.md) |
| `skillforge-qt` | Qt C++ 桌面工具、Widgets/Quick、Model/View、线程/COM、DPI、部署及 MFC → Qt 迁移 | [Qt](skills/skillforge-qt/SKILL.md) |
| `skillforge-mfc` | 开发、审查或现代化 Windows MFC C++ 桌面程序、线程/COM、消息路由与窗口生命周期 | [MFC](skills/skillforge-mfc/SKILL.md) |
| `skillforge-archerage-addon` | 开发或排查 ArcheRage RU Lua 插件、Replicated Suite、API、HUD 与存档 | [ArcheRage RU 插件](skills/skillforge-archerage-addon/SKILL.md) |
| `skillforge-lgf` | 学习、接入、扩展或维护实际使用 LGameplayFramework 的工程与插件 | [LGF 接入与开发](skills/skillforge-lgf/SKILL.md) |

## 从统一入口开始（0.3.0）

新任务未指定入口，提供 A/B/C；已明确选择或同一任务继续不重复问。A 由 AI 在既定边界内自主推进；B 由人工指挥、AI 工作，方案、技术栈和未明确的功能细节先解释选项、利弊及推荐，等待确认后再实施相关部分；C 从用户需要的功能出发，每轮围绕一个核心问题给出选项、优缺点、适用情况和推荐，暂不实施，不先要求选择 A/B。C收敛后交付方案；明确要求实施时沿用已有 A/B，未选则仅补选一次。三种入口都按当前任务读取工程、习惯和必要技能，核对风险与证据。

等级不等于任务性质：只分析/只规划/只提示词不实施；明确实施后不再固定展示长提示词等待一次“开始”。旧版A“列计划”、B“参谋”已被替换，旧检查点必须核实含义，不能混用。

[使用说明](skills/skillforge-orchestrator/README.md)保留纯文本portable core。两个新增方法技能按需使用，专业技能保持独立；不自动安装、运行后台服务或修改宿主权限。

日常协作约定：注释使用自然中文，说明用途、原因和易错点；已有 Git/P4 的工程不反复复制备份；个人 Git 项目优先 main，P4 按可运行的完整功能段组织 Pending CL。验证按改动选择必要检查，B 模式下的画面、动画和交互表现交用户实际验收。UE 5.8 及以后优先发现当前可用的 MCP 与热更新入口。详见 [个人习惯](skills/skillforge-orchestrator/references/user-workstyle.md)、[版本控制与阶段交付](skills/skillforge-orchestrator/references/version-control-workflow.md)；[本轮记录](evals/runs/2026-10-26/personal-workflow-validation.md)区分静态检查与尚未运行的行为评测。

本轮设计、依据及任务清单见 [编写设计](docs/orchestrator/v3-design-and-plan.md)，实际结果见 [0.3.0验证](evals/runs/2026-10-15/skillforge-v0.3.0-validation.md)。此前报告是历史证据，不代表本版本结果。

## 目录说明

日常使用从 `skills/` 开始；其余目录服务于技能库的维护。

| 目录 | 内容 |
|---|---|
| `skills/` | 正式技能及各自的参考、用例 |
| `docs/` | 编写维护说明、来源研究与实施记录 |
| `evals/` | 跨技能组合用例、行为对比与评测报告 |
| `scripts/` | 技能包校验工具 |
| `development/` | 入口开发工具、现行评测、历史归档与索引快照 |
| `adapters/` | 可选宿主metadata，不自动安装 |
| `tests/` | 校验工具自身的回归测试 |

## 使用方式

本仓库保存源码；仅把文件放在这个目录，不代表任意 Agent 都会自动发现它们。

1. 原生支持 Skill 目录的工具：将选中的完整运行时技能目录放入该工具文档指定的位置。保留 `SKILL.md`、`references/` 与该 Skill 自带的运行时资源；不要假定开发 `evals/tests` 也是安装必需。
2. 能读取文件但没有技能发现机制的工具：在任务里明确提供该技能的实际路径，请它先读 `SKILL.md`，再按其中条件读取参考资料。例如：`先读取 <技能实际位置>/skillforge-ue-blueprint/SKILL.md，再分析背包 Widget 的初始化。`
3. 只能粘贴文本的工具：提供技能正文，以及当前任务需要的参考资料。没有读取工具时，提到文件名不会自动加载文件。

宿主是否自动匹配、何时加载以及支持哪些工具，取决于宿主实现。本版验证的是包结构与所记录的行为样本，未宣称所有 Agent 已实测兼容。首版没有安装器、宿主专属配置、自动后台同步或插件依赖。

## 组合与项目边界

| 当前任务 | 组合 | 各自负责 |
|---|---|---|
| 用蓝图做背包界面 | 蓝图 + UI | 数据与节点流；布局、输入和状态 |
| C++ 控件点不到 | C++ + 排障；涉及层级时加 UI | 接口与生命周期；定位证据；输入层级 |
| Qt 工具增加任务/日志面板 | Qt；涉及交互时加 UI | Qt 模型/线程/拥有关系；布局与输入 |
| Qt 页面偶发卡死或输入被覆盖 | Qt + 排障；按需加 UI | Qt 契约；故障链；交互验收 |
| 已决定从 MFC 迁到 Qt | Qt；读取旧代码时按需 MFC | 行为迁移与 Qt 目标架构；旧实现解释 |
| MFC 工具增加日志面板 | MFC + UI | MFC 窗口/命令/生命周期；布局、焦点与状态 |
| MFC 日志面板偶发失效 | MFC + UI + 排障 | MFC 消息/线程/窗口；界面状态；故障链 |
| ArcheRage RU 插件统计异常 | ArcheRage RU + 排障 | 宿主 API 与数据契约；证据和故障链 |
| Replicated Suite HUD 布局与点击 | ArcheRage RU + UI；有故障时加排障 | 当前框架、生命周期与输入；布局和状态 |
| 用 LGF 做蓝图交互门 | LGF + 蓝图 | 现有交互扩展、拥有者与复制；资产和节点接线 |
| LGF 换 Pawn 后能力或背包界面失效 | LGF + C++/蓝图 + 排障；涉及布局时加 UI | 长期状态与 Avatar、请求和刷新链；具体实现与回归 |

以上是专业技能的组合说明，可由统一入口使用，也可直接选择；不是要求每次加载全部技能。每个专业技能可以单独使用；组合不会使未安装的技能成为硬依赖。跨技能重叠时用一份任务说明、一份证据清单和一份验证结果，不重复启动流程。

UE 技能面向 UE5，执行时从当前工程确定小版本、目标、插件与工具能力。当前项目的源码和配置描述实际状态，项目文档描述约定；有冲突时核对差异，不把 LGame/LGF 的构建路径或 Listen Server 约束套用到普通项目。

## 添加经过验证的经验

技能库以帮助解决实际问题的准确性为首要标准，不设置资料总量目标。用户做过的项目用于理解开发背景和验证适配；社区项目按具体机制、实现证据和回归结果取长补短，不因作者身份、星数或体量直接判定优劣。

需要解释清楚的契约、失败路径、诊断步骤和案例可以持续扩充。通过主题索引和按需读取控制单次加载范围；重复或过时内容原位整理，不能为了精简删掉解决问题所需的细节。

讨论确认、探针或修复产生可复用内容时，主动按 [经验收录流程](docs/experience-workflow.md) 提炼并及时记录。技术规则应能说明条件、证据和验证结果；未验证的解释留在候选记录。项目专属路径、资产、服务名与当前进度仍留在项目自身资料中。

外部 UE/UE4 GitHub 项目按固定提交逐个做源码蒸馏，完整项目级分析收在 [项目蒸馏索引](docs/project-distillations/README.md)，可复用结论再写回对应技能；不会为了项目数量把所有源码笔记塞进 `SKILL.md`。
从第八轮起，所有外部项目还必须先经过技术时效性分级（Current / Stable-but-old / Historical / Reject），并用目标 UE 版本源码、当前官方文档和实际工程交叉核对；旧项目只迁移仍成立的机制。

ArcheRage 插件可直接提供故障反馈文档，按 [插件反馈与蒸馏](skills/skillforge-archerage-addon/references/feedback.md) 逐次完善。[首批来源](skills/skillforge-archerage-addon/references/sources.md) 区分了社区候选、RU 官方变更和当前项目代码，未把本地模拟说成游戏实测。

Replicated Suite 连续开发经验已补入同一个 ArcheRage 技能：[维护案例索引](skills/skillforge-archerage-addon/references/maintenance-lessons-2026-09.md)涵盖分页报告、旧档与长ID保存、输入草稿、事件签名、持续留存、询价和日账本。它区分用户现场、源码核对和既有模拟记录；新增评测题不冒充已运行的行为实验。[本轮技能检查](evals/runs/2026-09-12/replicated-suite-lessons.md)记录实际结构检查与未执行部分。

LGF 使用单独的项目技能，按主题指向现有源码和文档，保留接入契约与已核实的易错点；没有把 53 个模块分别拆成技能。取材版本、范围和限制见 [LGF 取材依据](skills/skillforge-lgf/references/sources.md)，后续开发反馈按 [LGF 验证与演进](skills/skillforge-lgf/references/validation-and-evolution.md) 更新。

LGF、Replicated Suite、Advanced UI 的旧资料目录已在完成取材后按用户要求删除。采纳结论保存在正式技能中，来源名称与取材时的指纹保存在研究记录中，不保留重复目录或空的资料归档目录。新技能随库自带所需说明。

## 校验与评测

需要 Python 3.10 或更高版本；校验脚本只使用标准库。在仓库根执行：

```text
python -m unittest discover -s tests -v
python scripts/validate_skills.py --self-contained
```

脚本检查本库的受限头部格式（name/description，可选字符串 compatibility/license/allowed-tools 与字符串映射 metadata）、链接、路径、用例结构以及复制后的包完整性。它不是通用 YAML 解析器，也不能证明技术结论正确或模型行为改善。

行为评测方法见 [评测约定](evals/README.md)，真实结果见 [第一版验证报告](evals/runs/2026-09-12/summary.md)。来源、采纳理由和技术核验见 [研究记录](docs/research.md)。

ArcheRage RU 领域技能的首轮触发检查与行为结果见 [插件技能评测](evals/runs/2026-09-12/archerage-assessment.md)，后续回调、请求确认和统计口径的定向验证见 [社区机制深化评测](evals/runs/2026-09-12/archerage-community.md)。原报告保留当时的输入版本与结果。

LGF 的触发与六个接入/排障方案案例见 [LGF 技能评测](evals/runs/2026-09-12/lgf.md)。文字方案评测与真实插件构建、资产和联机验证分开记录。

MFC 首轮 GitHub 蒸馏、结构验证与未验证边界见 [MFC 首轮验证](evals/runs/2026-09-21/mfc-initial-validation.md)。

后续在实际使用中继续蒸馏 MFC，并扩展其他 Lua 宿主、Maya、Photoshop 专属技能；每个新技能仍先明确触发边界和真实验收案例。

## 2026-09-14 旧库迁移与实战经验

维持六个技能入口，通过按需参考增加内容，不创建第二个 LGF 大总管：

- LGF：[GASP/Mover 接入](skills/skillforge-lgf/references/gasp-mover-integration.md)、[武器动画诊断](skills/skillforge-lgf/references/weapon-animation-diagnostics.md)、[装备/能力生命周期](skills/skillforge-lgf/references/equipment-ability-lifecycle.md)。
- 蓝图：[官方资产流程、Socket 预览与 UMG 几何](skills/skillforge-ue-blueprint/references/official-asset-workflows.md)。
- 排障：[多轮审查、版本证据与防假绿](skills/skillforge-debugging/references/review-and-validation.md)。
- UE C++：[复制与生命周期审查](skills/skillforge-ue-cpp/references/replication-review.md)。
- ArcheRage：[迁移、回滚、容量和发布补充](skills/skillforge-archerage-addon/references/migration-release-boundaries.md)；保留其原有工具和测试。

迁移覆盖、备份/恢复位置、实际测试和限制见 [本轮报告](evals/runs/2026-09-14/migration-report.md)。这些技能没有自动安装到任何 Agent 宿主，本次也没有修改 LGame 工程。历史运行记录用于提炼方法，不当作本轮 UE/游戏运行通过。

动画经验已进一步补充：[新武器动画实施与交付顺序](skills/skillforge-lgf/references/animation-delivery-workflow.md)，包括素材覆盖表、真实播放验证、生成器门禁与人工交接。单一源 Socket 变换和覆盖曲线钩子也已细化；[补充记录](evals/runs/2026-09-14/animation-supplement/report.md)注明证据与未完成的旧目录删除。


## 2026-09-22 Qt 工程 Skill

新增 [skillforge-qt](skills/skillforge-qt/README.md)：短入口、10 个按需主题、两份事实/交接模板、六个固定提交的源码切片来源，以及待运行的触发/行为题集。Qt 版本、位宽、编译器与 UI 栈从当前工程读取，不继承历史 MFC 配置。

本次保留所有原专业 Skill 与 orchestrator 核心，未改 LCot 产品源码、未安装 SDK。动态入口发现新 Skill 不需要硬编码目录白名单。

[设计与研究范围](docs/qt-skill-design-2026-09-22.md)说明取材和裁剪；[实际验证报告](evals/runs/2026-09-22/qt-initial-validation.md)区分结构通过、原包已有失败及未运行的 Qt/Windows/Agent 验证。历史说明：2026-09-22当时未清理的入口便携性问题，已在0.3.0中统一处理，见上方本轮报告。
