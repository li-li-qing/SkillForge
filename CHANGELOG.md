# 统一入口六步流程（2026-11-14）

入口升级为 0.4.0，保持 14 个技能和现有协作边界。大型改动复用澄清与清单，增加 spec、需求/验收到任务的对应、逐项执行与变更/恢复；普通小任务保持轻量。按当前缺口读取资料，核心保持宿主无关。

后续定向优化：合并重复入口索引和说明，入口正文 UTF-8/LF 从7645降至5837字节；明确规划草案与当前闭环可执行清单、待细化验收及完整任务依赖。专业技能和个人协作习惯保持原有范围，目标模型效果仍待实际验证。

设计与实施清单见 [整合设计](docs/large-change-workflow-design-2026-11-14.md)，WorkBuddy 排查说明在 [适配文档](adapters/workbuddy/README.md)。实际验证记录到 `evals/runs/2026-11-14/large-change/`；结构验证和本环境行为样本不代表 WorkBuddy、DeepSeek 或 GLM 实测。未自动安装、提交或推送。

# 简洁实现融合（2026-11-09）

以 main `12f82bb` 为基线，保留此前完整增强和后续两处测试修正。补充现有入口/预检/审查准则、6 个行为题并修正 DBG-03 备份评分；不新增技能、不改路由/协作习惯、不推送或安装。详细清单与实际验证见 [本轮报告](docs/simplicity-review/report.md)。

以下保留先前 v6 交付的 CHANGELOG 原文（main 曾缺此文件）：

# v6（2026-11-07）

拒绝评测JSON重复键，校正Qt题数及旧GAS评分边界。328个测试方法、8条skip记录，所有套件exit0；新增三个重复键负例先红后绿。旧v5证据保留为历史快照。

- README.md
- docs/eval-review-v6/independent-audit.md
- docs/eval-review-v6/report.md
- evals/runs/2026-11-07/eval-review-v6/final-addon.log
- evals/runs/2026-11-07/eval-review-v6/final-experience.log
- evals/runs/2026-11-07/eval-review-v6/final-ida.log
- evals/runs/2026-11-07/eval-review-v6/final-index.log
- evals/runs/2026-11-07/eval-review-v6/final-lgf.log
- evals/runs/2026-11-07/eval-review-v6/final-library.log
- evals/runs/2026-11-07/eval-review-v6/suite-results.json
- evals/runs/2026-11-07/eval-review-v6/validator-red.log
- scripts/validate_skills.py
- skills/skillforge-qt/evals/README.md
- skills/skillforge-ue-cpp/evals/behavior-cases.json
- tests/test_validate_skills.py
- CHANGELOG.md
- docs/eval-review-v6/change-manifest.json

# v5 完整快照（2026-11-07）

脚本事务/安全边界、GAS复制与生命周期、StateTree失败、Qt/MFC/Lua与请求所有权事实修订，以及七轮行为证据。327测试方法，8条skip记录，无失败；另40项脚本独立复验。评测数量防漂移检查已加入。新增规格not_run、原partial及平台限制如实保留。独立完整快照；Library回执另行保存。详见docs/transaction-review/report.md。

- CHANGELOG.md
- README.md
- development/skillforge-orchestrator/evals/collaboration-cases.json
- docs/orchestrator/v3-maintenance-guide.md
- docs/transaction-review/addon-file-safety.md
- docs/transaction-review/binary-input-review.md
- docs/transaction-review/desktop-request-clarifications.md
- docs/transaction-review/experience-review.md
- docs/transaction-review/fastarray-clarification.md
- docs/transaction-review/ida-boundaries.md
- docs/transaction-review/lgf-modules.md
- docs/transaction-review/persistence-clarification.md
- docs/transaction-review/platform-clarifications.md
- docs/transaction-review/replication-direction.md
- docs/transaction-review/report.md
- docs/transaction-review/statetree-failure-clarification.md
- docs/transaction-review/updater-review.md
- docs/transaction-review/validator-report.md
- evals/runs/2026-11-07/transaction-review/addon-count-red.log
- evals/runs/2026-11-07/transaction-review/closed-stdout-red.log
- evals/runs/2026-11-07/transaction-review/experience-v5-green.log
- evals/runs/2026-11-07/transaction-review/experience-v5-interop.log
- evals/runs/2026-11-07/transaction-review/experience-v5-red.log
- evals/runs/2026-11-07/transaction-review/final-addon.log
- evals/runs/2026-11-07/transaction-review/final-experience.log
- evals/runs/2026-11-07/transaction-review/final-ida.log
- evals/runs/2026-11-07/transaction-review/final-index.log
- evals/runs/2026-11-07/transaction-review/final-lgf.log
- evals/runs/2026-11-07/transaction-review/final-library.log
- evals/runs/2026-11-07/transaction-review/ida-authority/HARNESS.md
- evals/runs/2026-11-07/transaction-review/ida-authority/frozen-manifest.json
- evals/runs/2026-11-07/transaction-review/ida-authority/import-verification.json
- evals/runs/2026-11-07/transaction-review/ida-authority/integrity.json
- evals/runs/2026-11-07/transaction-review/ida-authority/mismatch-response.md
- evals/runs/2026-11-07/transaction-review/ida-authority/readonly-response.md
- evals/runs/2026-11-07/transaction-review/ida-authority/readonly.json
- evals/runs/2026-11-07/transaction-review/ida-authority/results.json
- evals/runs/2026-11-07/transaction-review/ida-authority/rubric.json
- evals/runs/2026-11-07/transaction-review/ida-authority/write_mismatch.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/REPORT.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/artifact-hashes.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/criteria-private.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/future-criteria-private.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/future-packet.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/METHOD.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/REPORT.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/criteria-private.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/frozen-answers.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/manifest-before.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/readonly-reverse/fixture/target
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/readonly-reverse/fixture/target.c
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/readonly-reverse/pre-hashes.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/readonly-reverse/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/readonly-reverse/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/readonly-reverse/reviewer-objdump.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/readonly-reverse/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/reviewer-files.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/shared-write/executed-command.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/shared-write/expected-after.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/shared-write/fixture/baseline.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/shared-write/fixture/context.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/shared-write/fixture/notes.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/shared-write/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/shared-write/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/shared-write/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/ue-contract-conflict/fixture/facts.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/ue-contract-conflict/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/ue-contract-conflict/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/ue-contract-conflict/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/METHOD.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/REPORT.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/criteria-private.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/experience-negative-evidence/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/experience-negative-evidence/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/experience-negative-evidence/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/frozen-answers.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/judgments.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/lgf-ui-state/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/lgf-ui-state/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/lgf-ui-state/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/lua-foreign-snippet/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/lua-foreign-snippet/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/lua-foreign-snippet/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/qt-selection-id/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/qt-selection-id/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/qt-selection-id/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/reviewer-integrity.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/skills-before.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/METHOD.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/REPORT.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/criteria-private.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/fixture/config.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/fixture/monitor.py
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/frozen-answer.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/pre-hashes.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/reviewer-runs.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/work/brief.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/work/diagnose.py
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/work/matched-error.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/work/matched-idle.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/work/matched-success.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/work/matched-topic.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/work/original-error.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/work/original-idle.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/work/original-success.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/METHOD.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/REPORT.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/criteria-private.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/frozen-answers.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/ida-unavailable/fixture/target
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/ida-unavailable/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/ida-unavailable/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/ida-unavailable/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/judgments.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/mcp-untrusted/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/mcp-untrusted/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/mcp-untrusted/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/pre-hashes.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/qt-shutdown/fixture/snippet.cpp
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/qt-shutdown/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/qt-shutdown/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/qt-shutdown/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/reviewer-objdump.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/METHOD.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/REPORT.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/client-property-rpc/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/client-property-rpc/raw-answer-candidate.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/client-property-rpc/raw-answer-v4.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/client-property-rpc/trace-candidate.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/client-property-rpc/trace-v4.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/criteria-private.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/frozen-evidence.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/gas-aggregate-removal/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/gas-aggregate-removal/raw-answer-candidate.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/gas-aggregate-removal/raw-answer-v4.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/gas-aggregate-removal/trace-candidate.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/gas-aggregate-removal/trace-v4.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/import-manifest.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/judgments.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/manifest-d57d1f45ea5e096aeda3d113b707e1ab76f415112674247ae10c148d084b19c4.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/results/22ce0635a922179ddddd6f13ac0d6b864477e9165e78cf6eddc27f8def219526/client-property-rpc/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/results/22ce0635a922179ddddd6f13ac0d6b864477e9165e78cf6eddc27f8def219526/client-property-rpc/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/results/22ce0635a922179ddddd6f13ac0d6b864477e9165e78cf6eddc27f8def219526/gas-aggregate-removal/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/results/22ce0635a922179ddddd6f13ac0d6b864477e9165e78cf6eddc27f8def219526/gas-aggregate-removal/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/results/d57d1f45ea5e096aeda3d113b707e1ab76f415112674247ae10c148d084b19c4/client-property-rpc/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/results/d57d1f45ea5e096aeda3d113b707e1ab76f415112674247ae10c148d084b19c4/client-property-rpc/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/results/d57d1f45ea5e096aeda3d113b707e1ab76f415112674247ae10c148d084b19c4/gas-aggregate-removal/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/results/d57d1f45ea5e096aeda3d113b707e1ab76f415112674247ae10c148d084b19c4/gas-aggregate-removal/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/snapshot-map.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/snapshots/22ce0635a922179ddddd6f13ac0d6b864477e9165e78cf6eddc27f8def219526/manifest.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/METHOD.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/REPORT.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/criteria-private.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/frozen-evidence.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/import-verification.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/judgments.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/same-route/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/same-route/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/same-route/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/shared-consumers/prompt.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/shared-consumers/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/shared-consumers/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/snapshot.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/snapshots/cb1479777885b2b075f5c0f412f247d3f543aa6ce9ae56817dd121f7b61ac73e/manifest.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/runtime-check.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/skill-input-hashes.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v3/project/README.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v3/project/fixture.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v3/project/report.py
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v3/project/test_report.py
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v3/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v3/reviewer-independent.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v3/reviewer-tests.log
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v3/trace.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v4/project/README.md
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v4/project/fixture.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v4/project/report.py
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v4/project/test_report.py
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v4/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v4/reviewer-independent.json
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v4/reviewer-tests.log
- evals/runs/2026-11-07/transaction-review/isolated-behavior/v4/trace.txt
- evals/runs/2026-11-07/transaction-review/lgf-dev-full.json
- evals/runs/2026-11-07/transaction-review/lgf-independent-final.json
- evals/runs/2026-11-07/transaction-review/lgf-runtime-probe-after.json
- evals/runs/2026-11-07/transaction-review/multiprocess/sf_v5_multiprocess_audit-rerun.json
- evals/runs/2026-11-07/transaction-review/multiprocess/sf_v5_multiprocess_audit-rerun.stderr
- evals/runs/2026-11-07/transaction-review/multiprocess/sf_v5_multiprocess_audit.json
- evals/runs/2026-11-07/transaction-review/multiprocess/sf_v5_multiprocess_audit.py
- evals/runs/2026-11-07/transaction-review/multiprocess/sf_v5_reverse_process-rerun.json
- evals/runs/2026-11-07/transaction-review/multiprocess/sf_v5_reverse_process-rerun.stderr
- evals/runs/2026-11-07/transaction-review/multiprocess/sf_v5_reverse_process.json
- evals/runs/2026-11-07/transaction-review/multiprocess/sf_v5_reverse_process.py
- evals/runs/2026-11-07/transaction-review/multiprocess/verification.json
- evals/runs/2026-11-07/transaction-review/observable-fixture/REPORT.md
- evals/runs/2026-11-07/transaction-review/observable-fixture/baseline/projection.py
- evals/runs/2026-11-07/transaction-review/observable-fixture/before.json
- evals/runs/2026-11-07/transaction-review/observable-fixture/criteria-private.json
- evals/runs/2026-11-07/transaction-review/observable-fixture/project/projection.py
- evals/runs/2026-11-07/transaction-review/observable-fixture/prompt.txt
- evals/runs/2026-11-07/transaction-review/observable-fixture/raw-answer.txt
- evals/runs/2026-11-07/transaction-review/observable-fixture/reviewer-independent.json
- evals/runs/2026-11-07/transaction-review/observable-fixture/trace.txt
- evals/runs/2026-11-07/transaction-review/persistence-scenarios/policy-under-test.md
- evals/runs/2026-11-07/transaction-review/persistence-scenarios/policy.diff
- evals/runs/2026-11-07/transaction-review/persistence-scenarios/report.md
- evals/runs/2026-11-07/transaction-review/script-safety/baseline.json
- evals/runs/2026-11-07/transaction-review/script-safety/current-hash-check.json
- evals/runs/2026-11-07/transaction-review/script-safety/report.md
- evals/runs/2026-11-07/transaction-review/script-safety/reproduce.py
- evals/runs/2026-11-07/transaction-review/script-safety/reverification.md
- evals/runs/2026-11-07/transaction-review/script-safety/reverify-extra-results.txt
- evals/runs/2026-11-07/transaction-review/script-safety/reverify-race-results.txt
- evals/runs/2026-11-07/transaction-review/script-safety/reverify-results.json
- evals/runs/2026-11-07/transaction-review/script-safety/reverify.py
- evals/runs/2026-11-07/transaction-review/script-safety/reverify_extra.py
- evals/runs/2026-11-07/transaction-review/script-safety/reverify_races.py
- evals/runs/2026-11-07/transaction-review/structure.log
- evals/runs/2026-11-07/transaction-review/suite-results.json
- scripts/apply_skillforge_update.py
- scripts/validate_skills.py
- skills/skillforge-archerage-addon/evals/README.md
- skills/skillforge-archerage-addon/evals/behavior-cases.json
- skills/skillforge-archerage-addon/references/callback-and-request-contracts.md
- skills/skillforge-archerage-addon/references/combat-and-price-contracts.md
- skills/skillforge-archerage-addon/references/runtime-and-api.md
- skills/skillforge-archerage-addon/references/verification-tools.md
- skills/skillforge-archerage-addon/scripts/verify_report.py
- skills/skillforge-archerage-addon/scripts/verify_skill.py
- skills/skillforge-archerage-addon/tests/test_file_safety.py
- skills/skillforge-archerage-addon/tests/test_tools.py
- skills/skillforge-experience-maintenance/references/skill-evaluation.md
- skills/skillforge-experience-maintenance/references/store-tool.md
- skills/skillforge-experience-maintenance/scripts/experience_store.py
- skills/skillforge-experience-maintenance/tests/test_experience_store.py
- skills/skillforge-ida-pro/references/idapython-api.md
- skills/skillforge-ida-pro/scripts/ida_evidence.py
- skills/skillforge-ida-pro/scripts/run_ida_batch.py
- skills/skillforge-ida-pro/scripts/test_revision_boundaries.py
- skills/skillforge-lgf/evals/behavior-cases.json
- skills/skillforge-lgf/references/ai-decision-orchestration.md
- skills/skillforge-lgf/references/external-project-patterns.md
- skills/skillforge-lgf/references/gas-combat-prediction.md
- skills/skillforge-lgf/references/migration-evidence.md
- skills/skillforge-lgf/scripts/inspect_workspace.py
- skills/skillforge-lgf/tests/test_inspect_workspace.py
- skills/skillforge-mfc/evals/behavior-cases.json
- skills/skillforge-mfc/references/dpi-layout-controls.md
- skills/skillforge-orchestrator/references/collaboration-policy.md
- skills/skillforge-qt/evals/behavior-cases.json
- skills/skillforge-qt/references/qobject-threading-shutdown.md
- skills/skillforge-qt/references/widgets-layout-input-dpi.md
- skills/skillforge-qt/references/windows-com-dmsoft.md
- skills/skillforge-reverse-engineering/references/tools-and-validation.md
- skills/skillforge-reverse-engineering/scripts/probe_binary.py
- skills/skillforge-ue-cpp/evals/behavior-cases.json
- skills/skillforge-ue-cpp/references/arpg-item-inventory-patterns.md
- skills/skillforge-ue-cpp/references/framework-composition-patterns.md
- skills/skillforge-ue-cpp/references/gas-prediction-targetdata-patterns.md
- skills/skillforge-ue-cpp/references/statetree-utility-ai-patterns.md
- tests/test_patch_installer.py
- tests/test_reverse_binary_probe.py
- tests/test_transaction_interop.py
- tests/test_validate_skills.py
- docs/transaction-review/change-manifest.json

# 2026-11-07 全库增强版（基于IDA v3）

保留14技能与动态路由。修复更新器审计失败/未完成事务门禁、经验库恢复可观测性、验证器assets覆盖与symlink循环、IDA输入/RPC/备份/安全导出、Lua首行字节码与累计预算、LGF未知/冲突状态。补强UE MCP/Iris/Shipping边界、MFC资源与STA、UI订阅窗口、Qt可访问性及可选行为对照。全部来源和不采用内容见 docs/overnight-review；未复制第三方实现。

验证：277测试，269通过、8跳过；14技能及独立副本零错误；28Python语法检查。四题旧新版独立行为探针均符合，未证明提升。真实IDA/UE/Windows/Lua/游戏仍未执行。LGF null/status与CLI exit3是需注意的接口澄清；旧版ZIP保留。

## 本轮文件清单（相对v3，含证据）

- modify: `README.md`
- modify: `development/skillforge-orchestrator/snapshots/skill-index-current.json`
- modify: `docs/orchestrator/v3-maintenance-guide.md`
- add: `docs/overnight-review/desktop-audit.md`
- add: `docs/overnight-review/desktop-sources.json`
- add: `docs/overnight-review/external-skills-research.md`
- add: `docs/overnight-review/methods-audit.md`
- add: `docs/overnight-review/methods-sources.json`
- add: `docs/overnight-review/report.md`
- add: `docs/overnight-review/reverse-audit.md`
- add: `docs/overnight-review/ue-audit.md`
- add: `docs/overnight-review/ue-sources.json`
- add: `docs/overnight-review/worklog.md`
- add: `evals/runs/2026-11-07/overnight/baseline-addon.log`
- add: `evals/runs/2026-11-07/overnight/baseline-experience.log`
- add: `evals/runs/2026-11-07/overnight/baseline-ida.log`
- add: `evals/runs/2026-11-07/overnight/baseline-index.log`
- add: `evals/runs/2026-11-07/overnight/baseline-lgf.log`
- add: `evals/runs/2026-11-07/overnight/baseline-library.log`
- add: `evals/runs/2026-11-07/overnight/behavior-baseline.md`
- add: `evals/runs/2026-11-07/overnight/behavior-candidate.md`
- add: `evals/runs/2026-11-07/overnight/behavior-review.md`
- add: `evals/runs/2026-11-07/overnight/experience-recovery-green.log`
- add: `evals/runs/2026-11-07/overnight/experience-recovery-red.log`
- add: `evals/runs/2026-11-07/overnight/final-addon.log`
- add: `evals/runs/2026-11-07/overnight/final-experience.log`
- add: `evals/runs/2026-11-07/overnight/final-ida.log`
- add: `evals/runs/2026-11-07/overnight/final-index.log`
- add: `evals/runs/2026-11-07/overnight/final-lgf.log`
- add: `evals/runs/2026-11-07/overnight/final-library.log`
- add: `evals/runs/2026-11-07/overnight/final-structure.log`
- add: `evals/runs/2026-11-07/overnight/final-syntax.json`
- add: `evals/runs/2026-11-07/overnight/root-green.log`
- add: `evals/runs/2026-11-07/overnight/root-red.log`
- add: `evals/runs/2026-11-07/overnight/suite-results.json`
- modify: `scripts/apply_skillforge_update.py`
- modify: `scripts/validate_skills.py`
- modify: `skills/skillforge-archerage-addon/references/verification-tools.md`
- modify: `skills/skillforge-archerage-addon/scripts/check_lua51.py`
- modify: `skills/skillforge-archerage-addon/tests/test_tools.py`
- modify: `skills/skillforge-cheat-engine/evals/behavior-cases.json`
- modify: `skills/skillforge-cheat-engine/references/java-and-jni.md`
- modify: `skills/skillforge-debugging/SKILL.md`
- modify: `skills/skillforge-debugging/evals/behavior-cases.json`
- modify: `skills/skillforge-debugging/references/verified-cases.md`
- modify: `skills/skillforge-engineering-preflight/SKILL.md`
- modify: `skills/skillforge-engineering-preflight/evals/behavior-cases.json`
- modify: `skills/skillforge-engineering-preflight/references/risk-review.md`
- modify: `skills/skillforge-experience-maintenance/SKILL.md`
- add: `skills/skillforge-experience-maintenance/references/skill-evaluation.md`
- modify: `skills/skillforge-experience-maintenance/references/store-tool.md`
- modify: `skills/skillforge-experience-maintenance/scripts/experience_store.py`
- modify: `skills/skillforge-experience-maintenance/tests/test_experience_store.py`
- modify: `skills/skillforge-ida-pro/references/idapython-api.md`
- modify: `skills/skillforge-ida-pro/references/mcp-adapters.md`
- modify: `skills/skillforge-ida-pro/scripts/ida_evidence.py`
- modify: `skills/skillforge-ida-pro/scripts/ida_mutations.py`
- modify: `skills/skillforge-ida-pro/scripts/mcp_function_query.py`
- modify: `skills/skillforge-ida-pro/scripts/test_examples.py`
- add: `skills/skillforge-ida-pro/scripts/test_revision_boundaries.py`
- modify: `skills/skillforge-lgf/evals/behavior-cases.json`
- modify: `skills/skillforge-lgf/references/ai-decision-orchestration.md`
- modify: `skills/skillforge-lgf/references/gas-combat-prediction.md`
- modify: `skills/skillforge-lgf/references/mass-ai-scaling.md`
- modify: `skills/skillforge-lgf/references/migration-evidence.md`
- modify: `skills/skillforge-lgf/references/network-and-state.md`
- modify: `skills/skillforge-lgf/scripts/inspect_workspace.py`
- modify: `skills/skillforge-lgf/tests/test_inspect_workspace.py`
- modify: `skills/skillforge-mfc/evals/behavior-cases.json`
- modify: `skills/skillforge-mfc/references/threading-com-sta.md`
- modify: `skills/skillforge-qt/evals/behavior-cases.json`
- modify: `skills/skillforge-qt/references/widgets-layout-input-dpi.md`
- modify: `skills/skillforge-ue-blueprint/SKILL.md`
- modify: `skills/skillforge-ue-blueprint/evals/behavior-cases.json`
- modify: `skills/skillforge-ue-blueprint/evals/trigger-cases.json`
- modify: `skills/skillforge-ue-blueprint/references/unreal-mcp-editor-workflow.md`
- modify: `skills/skillforge-ue-cpp/SKILL.md`
- modify: `skills/skillforge-ue-cpp/evals/behavior-cases.json`
- modify: `skills/skillforge-ue-cpp/evals/trigger-cases.json`
- modify: `skills/skillforge-ue-cpp/references/container-transactions-and-subobjects.md`
- modify: `skills/skillforge-ue-cpp/references/editor-mcp-live-coding.md`
- modify: `skills/skillforge-ue-cpp/references/gas-prediction-targetdata-patterns.md`
- modify: `skills/skillforge-ue-cpp/references/mass-data-oriented-ai-patterns.md`
- modify: `skills/skillforge-ue-cpp/references/replication-review.md`
- modify: `skills/skillforge-ue-cpp/references/statetree-utility-ai-patterns.md`
- modify: `skills/skillforge-ui-design/evals/behavior-cases.json`
- modify: `skills/skillforge-ui-design/references/commonui-input-routing-patterns.md`
- modify: `skills/skillforge-ui-design/references/gameplay-ui-projection.md`
- modify: `skills/skillforge-ui-design/references/interaction-states.md`
- modify: `tests/test_patch_installer.py`
- modify: `tests/test_validate_skills.py`
- add: `docs/overnight-review/change-manifest.json`（本轮前后哈希；自身不递归入表）
- add: `docs/overnight-review/integrity.json`（保护文件与打包前核验）

## 既有IDA版本记录（保留）

# CHANGELOG

## 2026-11-07 v3 — GUI导出生命周期修订

- 写入、关闭、注册失败均清理任务状态，回调停止，不锁死后续任务。
- 输出先写.partial，成功关闭后无覆盖发布最终文件；失败/取消不冒充完整导出。
- 补GUI生命周期故障注入和真实临时文件发布测试，示例总49项通过。
- 保留v1/v2发布文件，新完整包独立保存。

## 2026-11-07 v2 — 反向审查修订

- 补齐xrefs_to/assembly/callers/callees/pseudocode可续页offset及嵌套查询完整性。
- 说明原生枚举排序、冻结IDB的一致性前提、深分页重放成本和100000 offset上限。
- 审计日志fsync失败保留已尝试/已验证/不确定状态，禁止自动重试。
- 新增分页RED复现及故障注入/成本测试，总37项示例离线测试。
- 独立v2 ZIP和Library文件保留v1发布，不覆盖。

## 2026-11-07 v1 — IDA Pro 专业领域整合

在原13技能库上新增一个skillforge-ida-pro，现14技能。保留总入口动态路由、个人协作规则与全部原技能。未安装宿主技能或修改远程仓库。

### 能力与设计

- 一个总入口按任务分配静态/Hex-Rays/IDAPython/类恢复/UE/调试/MCP参考，不拆成十二技能。
- 复用通用逆向与UE源码技能的职责；增加可选名称组合，不产生兄弟目录硬依赖。
- 六个Python文件含采集、修改、GUI分片、批处理、MCP客户端及测试；十五项示例具版本、环境、依赖、修改与失败边界。
- 官方/社区/研究适配器分离，任意Python执行不当只读沙箱。
- UE主次版本、构建/符号/LTO、反射/RPC/复制/Blueprint证据分层。
- 写操作增加IDB身份绑定、hash、旧值复查、部分成功审计及类型读回。

### 修改文件（原有）

- README.md
- development/skillforge-orchestrator/snapshots/skill-index-current.json
- docs/research.md
- skills/skillforge-reverse-engineering/SKILL.md

### 新增文件

- docs/ida-pro/design-and-integration.md
- docs/ida-pro/github-mcp-research.md
- docs/ida-pro/github-ue-research.md
- docs/ida-pro/skill-inventory.json
- evals/runs/2026-11-07/ida-pro/examples-tests.log
- evals/runs/2026-11-07/ida-pro/index-tests.log
- evals/runs/2026-11-07/ida-pro/library-tests.log
- evals/runs/2026-11-07/ida-pro/report.md
- evals/runs/2026-11-07/ida-pro/review-notes.md
- evals/runs/2026-11-07/ida-pro/structure.log
- evals/runs/2026-11-07/ida-pro/syntax.log
- evals/runs/2026-11-07/ida-pro/task-simulations.md
- skills/skillforge-ida-pro/SKILL.md
- skills/skillforge-ida-pro/assets/analysis-report.md
- skills/skillforge-ida-pro/assets/change-log.json
- skills/skillforge-ida-pro/evals/behavior-cases.json
- skills/skillforge-ida-pro/evals/trigger-cases.json
- skills/skillforge-ida-pro/references/class-recovery.md
- skills/skillforge-ida-pro/references/dynamic-debugging.md
- skills/skillforge-ida-pro/references/idapython-api.md
- skills/skillforge-ida-pro/references/idapython-sources.md
- skills/skillforge-ida-pro/references/mcp-adapters.md
- skills/skillforge-ida-pro/references/sources.md
- skills/skillforge-ida-pro/references/static-and-decompiler.md
- skills/skillforge-ida-pro/references/unreal-engine.md
- skills/skillforge-ida-pro/references/workflows.md
- skills/skillforge-ida-pro/scripts/gui_strings_export.py
- skills/skillforge-ida-pro/scripts/ida_evidence.py
- skills/skillforge-ida-pro/scripts/ida_mutations.py
- skills/skillforge-ida-pro/scripts/job.example.json
- skills/skillforge-ida-pro/scripts/mcp_function_query.py
- skills/skillforge-ida-pro/scripts/run_ida_batch.py
- skills/skillforge-ida-pro/scripts/test_examples.py
- CHANGELOG.md
- docs/ida-pro/change-manifest.json
- docs/ida-pro/packaging-exclusions.json
- evals/runs/2026-11-07/ida-pro/final-integrity.json

### 验证与限制

- 原库87项（85通过、2跳过）；索引40项；示例27项；14技能自包含0错误。
- 八项任务桌面推演及独立代码审查；没有真实IDA/Hex-Rays/MCP/UE或动态运行测试。
- 8.x不承诺兼容，9.x为目标API范围而非全版本认证。
- 当前元数据索引13条专业技能，有意排除orchestrator；历史快照保留。
- 完整ZIP保留Skills/相对结构；排除.git/.worktrees/缓存，见排除清单。没有删除原技能或源文件。
- 输入中的既有未来日期保留；本轮核实时间2026-11-07。

新增v2记录：docs/ida-pro/v2-reverse-review.md、evals/runs/2026-11-07/ida-pro/pagination-red.log。


# 原 README 资料与历史导航（移存于 2026-11-14）

以下保留迁移前的经验说明、来源和历次交付链接；其中数量、版本与验证结论对应各自原日期，不是当前使用规则或本轮验证结果。链接仍以仓库根为基准。

原入口 0.3.0 的 [编写设计](docs/orchestrator/v3-design-and-plan.md) 与 [对应验证](evals/runs/2026-10-15/skillforge-v0.3.0-validation.md) 同样保留；它们描述当时的设计和实际结果。

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

逆向与 CE 首轮补充见 [设计与范围](docs/reverse-engineering-design-2026-11-08.md) 和 [实际验证](evals/runs/2026-11-08/reverse-engineering/report.md)。包括只读 PE 地址核验工具、固定提交来源、独立触发/行为题，以及有条件的 CE/JNI 历史案例；没有自动安装宿主技能或修改游戏。

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

## 2026-11-07 IDA 专业能力

新增一个可独立使用的 IDA 技能，保留动态路由与既有协作规则。IDA 任务按需组合通用逆向；UE 二进制分析由 IDA 执行、源码契约可组合 UE C++；CE 扫描仍由 CE 技能负责。

[架构与路由](docs/ida-pro/design-and-integration.md)、[GitHub MCP 调研](docs/ida-pro/github-mcp-research.md)、[UE 与知识库调研](docs/ida-pro/github-ue-research.md)、[知识索引](skills/skillforge-ida-pro/references/sources.md)、[验证报告](evals/runs/2026-11-07/ida-pro/report.md)、[详细变更](CHANGELOG.md)。本次未安装到宿主，未执行真实 IDA/UE。

## 2026-11-07 全库定向审查

保持14个技能与原动态入口，补强脚本故障处理、UE/桌面生命周期和可选行为评测。完整范围、来源、兼容变化及未验证项见[本轮交付报告](docs/overnight-review/report.md)，逐文件记录见[CHANGELOG](CHANGELOG.md)。这是独立完整副本，尚未安装到用户环境。

## v5 候选复审

[事务与返回状态复审](docs/transaction-review/report.md)记录v4之后的定向修复、实际回归和未验证项；当前为独立候选，尚未发布或安装。

当前v6评测门禁修订与验收：[报告](docs/eval-review-v6/report.md)。此前v5报告与清单为历史快照。

## 2026-11-09 简洁实现准则融合

保持 14 个技能、原路由与协作规则，在现有入口/预检/审查中澄清复杂度取舍、校验失效边界、行为保持和有限反查，并补充配对评测。完整范围、验证与历史包保留情况见 [本轮报告](docs/simplicity-review/report.md)。
