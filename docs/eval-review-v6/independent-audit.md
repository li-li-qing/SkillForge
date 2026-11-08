# v5 Eval 专项审查

范围：`transaction_review_v5/Skills`，正式树只读；2026-11-07 UTC。

## 发现

### 中：全库 eval JSON 重复键不被拒绝

`scripts/validate_skills.py:218` 使用默认 `json.loads(text)`。若同一 case 中有 `"expected":"no_trigger","expected":"trigger"`，前者被静默覆盖，结构门禁仍通过。重复 prompt/expectations/id 键同理。这不是当前题库已含重复键的证据，而是可复现维护门禁缺口：合并错误可能改变判分语义且无诊断。Addon 的独立 `verify_skill.py` 已实现 `unique_object`，两级门禁不一致。建议全库使用拒绝重复键的 object_pairs_hook，添加真实负例回归，勿把此修复称 Agent 行为提升。

复现：临时 package evals 中建立三例，分别覆盖三类别，每例放两个 expected 键。调用 validate_evals 得 errors=[]。未写入正式树。

### 低：Qt 评测 README 题数和 expectation 数失真

`skills/skillforge-qt/evals/README.md:7` 声称 24 题，每题至少四项验收。实际 28 题，末尾 QT-ACCESS-01/QT-WAIT-PLATFORM-01/QT-LAYOUT-PARENT-01/QT-INPUT-OWNER-01 各三项。这不是案例质量不够，不应为凑数添加第四项；应更新说明或由 JSON 自动核对统计。

### 低至中：旧 GE rubric 与新边界存在歧义，非已证明评分失败

`skills/skillforge-ue-cpp/evals/behavior-cases.json:105` CPP-10，`:193` CPP-18，泛化表述 Effect 持有精确 handle 并撤销。新 CPP-125 明确共享聚合 active effect 和 Instant 无法如此等同；refs/arpg-item-inventory-patterns.md:97-99 同样正确。旧期待并未明说“删除整个共享实例”，所以不能宣布硬性逻辑矛盾；但评分者容易把只保存 FActiveGameplayEffectHandle 的回答判为完整通过。建议旧 rubric 同步限定独立持续实例、共享贡献和 Instant 反向结算，勿只靠新增题补足旧题判分。

## 已执行验证

- `PYTHONDONTWRITEBYTECODE=1 python scripts/validate_skills.py --self-contained`：14 skills、14 standalone，0 errors。
- `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_validate_skills tests.test_qt_package -q`：44 tests，OK，无 skip。
- 全部现有 skill eval JSON 可解析；case prompt 精确重复扫描未发现同一文件重复。
- 13 个专业技能拥有 trigger/behavior JSON；orchestrator 由根 composition cases 和专用合同测试覆盖，不将“无独立题库”误报缺失。
- 当前根工具明确仅验证结构；evals/README 明确静态探针不等于行为结果、冻结后评分、原始输入/输出及工具轨迹要求，没有把静态通过冒充 Agent 通过。
- 有 execution_status 的 92 个案例均为 not_run；缺该可选字段不等于已通过。应以实际 run evidence 而非题库状态推断执行。
- 平台 skip 包括 Windows junction、大小写文件系统、Lua 5.1 parser；当前 44-test 子集没有这些 skip，不能替代其他套件或真实平台测试。

## 范围限制

没有实际运行所有题库 Agent 回答或逐项判分，没有 UE/IDA/Qt/Windows/Lua 实机环境；技术 rubric 的其他领域尚不能宣称全部正确。上面的 GE 项是可维护性歧义，不伪造 fail→pass。
