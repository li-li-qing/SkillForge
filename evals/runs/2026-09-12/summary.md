# SkillForge 第一版验证报告

日期：2026-09-12。交付范围为四个通用技能、按需参考、用例与使用说明；没有修改真实 UE/MFC 项目，也没有安装到其他 Agent。

## 结构与内容

四个入口分别为 37、38、38、39 行，共 11 份参考、24 个触发用例和 8 个独立技能行为用例。入口采用 Agent Skills 的 `name`/`description` 结构，资源通过包内相对路径读取。

实际使用 Python 3.12.14 执行：

```text
python -m unittest discover -s tests -v
Ran 28 tests in 13.339s
OK

python scripts/validate_skills.py --self-contained
Validated 4 skill(s): 0 error(s); 4 standalone copies validated.
```

复制检查在临时目录验证完整包，不借用仓库其他技能或本机历史资料。校验器只支持本库明确声明的 YAML 子集和可识别的 Markdown/路径语法，不能证明所有自然语言指令可移植。

内容审查核对了 UE 5.7.4 源码中的可见性、Canvas 布局、WidgetTree 遍历和 Actor 构造路径。审查发现的 YAML 名称类型歧义、单段绝对 POSIX 路径漏检均已补回归并修复；后者另有独立修复复核，见 [内容审查](final-content-review.md)。

## 独立技能行为比较

每个技能 2 例，每例 4 个期望。下表按与回答者分开的 Agent 审阅计数，**仅衡量这次文本方案的覆盖**，不是工程成功率。每项 pass 需要回答给出具体步骤、条件或验证依据；题目只要求方案，未运行项目不自动判失败。

| 技能 | 无新技能 Baseline | 首次 With-skill | 可观察结果 |
|---|---|---|---|
| 排障 | 8 pass | 8 pass | 保持正确；没有证明期望级改善 |
| UE C++ | 6 pass、2 partial | 7 pass、1 partial | CPP-02 补足 `.generated.h` 顺序与跨模块导出检查；CPP-01 的构建目标发现仍欠具体 |
| UE 蓝图 | 8 pass | 8 pass | 两臂都能给出初始化和版本核验方案；引用已核验记录不等于现场核验或效果提升 |
| UI | 7 pass、1 partial | 8 pass | UI-02 对加载记录和定位处理中状态的方案覆盖更完整 |

首次比较共 32 项：Baseline 29 pass、3 partial；With-skill 31 pass、1 partial，没有 fail。根据 CPP-01 缺项，随后在 C++ 入口补充“目标来源、目标/平台/配置、执行状态”的交付要求，再做一次新上下文的 [CPP-01 定向复查](ue-cpp-forward-recheck.md)，4 项文本要求均满足。此结果单独记录，不覆盖首次回答，也不作为新增独立样本并入首次比较。

原始回答先保存，再揭示用例期望并追加回答者自查。作者自查和独立审阅有不同口径的地方，以独立审阅的同口径比较为上表依据，详见 [排障与 C++ 审阅](independent-assessment.md) 和 [蓝图、UI 与定向复查审阅](remaining-behavior-assessment.md)。

| 技能 | 原始记录 |
|---|---|
| 排障 | [Baseline](debugging-baseline.md) · [With-skill](debugging-forward.md) |
| UE C++ | [Baseline](ue-cpp-baseline.md) · [首次 With-skill](ue-cpp-forward.md) |
| UE 蓝图 | [Baseline](ue-blueprint-baseline.md) · [With-skill](ue-blueprint-forward.md) |
| UI | [Baseline](ui-design-baseline.md) · [With-skill](ui-design-forward.md) |

## 触发与组合

[元数据匹配检查](trigger-composition.md)只读取四个技能的名称和描述，再对输入作判断：24/24 个触发标签、5/5 个组合技能集合与期望一致。覆盖应触发、不应触发、需上下文判断，以及蓝图背包、C++ 控件点击、MFC 布局/故障和普通 C++ 命令行任务。这没有调用宿主自动发现机制，不能写成自动激活实测通过。

元数据阶段的简短分工只覆盖 7 项、部分覆盖 5 项、未证明 2 项组合行为要求，因此未将选对技能等同于正文协作通过。随后另做 [读取正文后的组合检查](composition-behavior.md)：同一上下文已经看过期望，是非盲的协作方案检查，具体答案与结果单独保存，不回写元数据阶段的冻结答案。

正文阶段 5 个方案在作者自查中覆盖 14/14 项文字要求，未观察到共享所有权、证据链或框架边界的冲突。因为该阶段已知期望且回答更完整，不能把它与元数据短分工的计数相减来宣称技能收益，也不能当作宿主自动组合实测。

## 条件、版本与限制

- 各独立技能条件使用新 Agent 上下文、继承同一主任务模型设置、相同提示和工具权限；仅允许读取评测/技能材料并保存文本报告，没有真实工程工具执行。精确后端 model ID 和推理参数未暴露，不能声称已独立核验其固定值。
- 基线仍带有宿主系统/开发者规则和已安装技能目录。排障基线还实际读取了宿主排障与 UE UI 技能，蓝图基线额外读取了宿主排障、UE UI 和 Actor/组件技能；对应新技能条件没有读取这些背景正文，是明确的背景混杂。其他加载差异见各报告，不能将既有能力归功于新技能。
- 每题每条件一次冒烟；同一技能的两题在该条件中共用上下文。独立评审可见作者自查，非盲审；冻结顺序依据保存记录，并未独立审计全部执行轨迹。因此观察到的两项覆盖增加不证明稳定的因果收益。
- C++ 首次前向回答先于入口交付要求调整；排障前向评测后修正了官方页面版本的来源说明，指导语义未变。最终技能与用例的 SHA-256 见 [输入快照](input-manifest.json)，快照不冒充历史版本存档。
- 技术核验、编译与运行分别记录：本次已读官方资料/本机源码；**未执行 UHT、项目编译、蓝图资产读写/保存/重载、PIE、打包、UI 输入/视觉或性能验收**。行为回答中的操作均为方案。
- 其他 Agent 尚未实测；当前只声明格式与文件组织可移植。具体 Agent 安装适配、发现行为和真实项目试用留待后续。

GitHub 固定提交、许可检查、原资料指纹及项目案例的候选/核验状态见 [研究记录](../../../docs/research.md)。更新规则见 [经验收录流程](../../../docs/experience-workflow.md)。
