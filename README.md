# SkillForge

面向游戏开发与创作工具的个人 Agent Skills 技能源。当前包含 13 个专业/方法技能，以及统一入口 `skillforge-orchestrator`，共 14 个；专业技能仍可独立或组合使用。正文以中文为主，API、节点名和技术关键词保留英文。

| 技能 | 使用时机 | 入口 |
|---|---|---|
| `skillforge-orchestrator` | 明确调用统一入口：提供A/B/C入口，承接个人习惯与项目依据，按任务性质推进 | [统一入口](skills/skillforge-orchestrator/SKILL.md) |
| `skillforge-engineering-preflight` | 高返工成本选型、性能敏感交互、大规模同步或重要UI的前置判断与最小验证 | [工程前置验证](skills/skillforge-engineering-preflight/SKILL.md) |
| `skillforge-experience-maintenance` | 个人习惯、验证经验及多Agent共享规则的记录、晋升、冲突与撤回 | [经验维护](skills/skillforge-experience-maintenance/SKILL.md) |
| `skillforge-debugging` | 已出现错误、崩溃、偶发失效或结果异常，需要排查与修复 | [排障](skills/skillforge-debugging/SKILL.md) |
| `skillforge-reverse-engineering` | 二进制、反汇编/伪代码、ABI、布局、运行时与未文档化协议分析 | [逆向分析](skills/skillforge-reverse-engineering/SKILL.md) |
| `skillforge-ida-pro` | IDA Pro、Hex-Rays、IDAPython、MCP 与 UE 二进制取证 | [IDA 专业分析](skills/skillforge-ida-pro/SKILL.md) |
| `skillforge-cheat-engine` | CE 扫描、地址重新定位、Lua、MCP、Java collector 与崩溃排障 | [CE 实战](skills/skillforge-cheat-engine/SKILL.md) |
| `skillforge-ue-cpp` | 当前任务确实涉及 UE C++、反射、生命周期、模块或蓝图暴露接口 | [UE C++](skills/skillforge-ue-cpp/SKILL.md) |
| `skillforge-ue-blueprint` | 创建、修改、解释或排查 UE 蓝图、Widget Blueprint 与节点图 | [蓝图](skills/skillforge-ue-blueprint/SKILL.md) |
| `skillforge-ui-design` | 设计或调整 HUD、工具窗口、配置面板的布局与交互 | [UI](skills/skillforge-ui-design/SKILL.md) |
| `skillforge-qt` | Qt C++ 桌面工具、Widgets/Quick、Model/View、线程/COM、DPI、部署及 MFC → Qt 迁移 | [Qt](skills/skillforge-qt/SKILL.md) |
| `skillforge-mfc` | 开发、审查或现代化 Windows MFC C++ 桌面程序、线程/COM、消息路由与窗口生命周期 | [MFC](skills/skillforge-mfc/SKILL.md) |
| `skillforge-archerage-addon` | 开发或排查 ArcheRage RU Lua 插件、Replicated Suite、API、HUD 与存档 | [ArcheRage RU 插件](skills/skillforge-archerage-addon/SKILL.md) |
| `skillforge-lgf` | 学习、接入、扩展或维护实际使用 LGameplayFramework 的工程与插件 | [LGF 接入与开发](skills/skillforge-lgf/SKILL.md) |

## 从统一入口开始（0.4.0）

新任务未指定入口，提供 A/B/C；已明确选择或同一任务继续不重复问。A 由 AI 在既定边界内自主推进；B 由人工指挥、AI 工作，方案、技术栈和未明确的功能细节先解释选项、利弊及推荐，等待确认后再实施相关部分；C 从用户需要的功能出发，每轮围绕一个核心问题给出选项、优缺点、适用情况和推荐，暂不实施，不先要求选择 A/B。C收敛后交付方案；明确要求实施时沿用已有 A/B，未选则仅补选一次。三种入口都按当前任务读取工程、习惯和必要技能，核对风险与证据。

等级不等于任务性质：只分析/只规划/只提示词不实施；明确实施后不再固定展示长提示词等待一次“开始”。旧版A“列计划”、B“参谋”已被替换，旧检查点必须核实含义，不能混用。

[使用说明](skills/skillforge-orchestrator/README.md)提供两种流程：明确的小改动用短清单直接推进；大型改动用“需求生成 → 分析 → 澄清 → spec → todo → 逐任务开发”。大型流程复用原有澄清与任务清单，不新增技能，仍共 14 个。已有规格、清单和选择直接接续。

大型任务通常只维护 spec 与 todo 两份主文件，任务对应具体需求/验收编号，逐项实现、验证、回填。仅规划不进入产品开发。详见 [大型改动六步流程](skills/skillforge-orchestrator/references/large-change-workflow.md)；参考资料按当前任务和阶段读取，普通小修改不展开全套流程。

日常协作约定：注释使用自然中文，说明用途、原因和易错点；已有 Git/P4 的工程不反复复制备份；个人 Git 项目优先 main，P4 按可运行的完整功能段组织 Pending CL。验证按改动选择必要检查，B 模式下的画面、动画和交互表现交用户实际验收。UE 5.8 及以后优先发现当前可用的 MCP 与热更新入口。详见 [个人习惯](skills/skillforge-orchestrator/references/user-workstyle.md)、[版本控制与阶段交付](skills/skillforge-orchestrator/references/version-control-workflow.md)；[本轮记录](evals/runs/2026-10-26/personal-workflow-validation.md)区分静态检查与尚未运行的行为评测。

本轮整合依据与任务清单见 [设计与实施](docs/large-change-workflow-design-2026-11-14.md)，实际检查与行为样本限制见 [验证记录](evals/runs/2026-11-14/large-change/report.md)。版本历史和旧验收入口见 [CHANGELOG](CHANGELOG.md)，旧报告不代表本轮结果。

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

宿主是否自动匹配、何时加载以及支持哪些工具，取决于宿主实现。源码更新不代表宿主已安装或已重新读取。不同模型的结果要结合实际读取、工具轨迹和任务产物检查；[WorkBuddy 检查方法](adapters/workbuddy/README.md)提供只读排查步骤，本轮不自动修改宿主配置或安装技能。

## 组合与项目边界

| 当前任务 | 组合 | 各自负责 |
|---|---|---|
| 用蓝图做背包界面 | 蓝图 + UI | 数据与节点流；布局、输入和状态 |
| C++ 控件点不到 | C++ + 排障；涉及层级时加 UI | 接口与生命周期；定位证据；输入层级 |
| 无符号 DLL 的行为或结构恢复 | 逆向；存在故障时加排障 | 指令/地址/ABI 证据；最小复现 |
| 自有离线 Java 游戏 CE 地址失效或 collector 崩溃 | CE；按需加逆向与排障 | 实例/对象/扫描；JNI 与故障证据 |
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

## 维护与验证

个人习惯、通用方法、领域知识和项目事实各有归属。已有内容优先原位维护；只有职责独立且触发明确时才新增技能。通过主题索引和按需读取控制本次加载范围，保留解决问题所需的契约、异常路径与证据。

经验收录见 [维护流程](docs/experience-workflow.md)，外部项目分析见 [项目蒸馏索引](docs/project-distillations/README.md)。旧版本交付、来源及验收入口保存在 [CHANGELOG](CHANGELOG.md)，不应作为每次任务的必读材料。

校验工具需要 Python 3.10+，只使用标准库。在仓库根执行：

```text
python -B -m unittest discover -s tests -v
python -B scripts/validate_skills.py --self-contained
python -B -m unittest discover -s development/skillforge-orchestrator/tests -v
python -B development/skillforge-orchestrator/tools/build_skill_index.py --root skills=skills --check development/skillforge-orchestrator/snapshots/skill-index-current.json
```

检查覆盖包结构、引用、用例格式和工具回归，不能证明模型行为改善。行为用例与实际结果分开保存，方法见 [评测约定](evals/README.md)；目标宿主或模型未运行时明确标记未验证。
