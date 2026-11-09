# v2 反向审查变更

原发布保留。修复无法续页、重放前缀成本低报和审计fsync失败状态。

- CHANGELOG.md
- evals/runs/2026-11-07/ida-pro/examples-tests.log
- evals/runs/2026-11-07/ida-pro/index-tests.log
- evals/runs/2026-11-07/ida-pro/library-tests.log
- evals/runs/2026-11-07/ida-pro/pagination-red.log
- evals/runs/2026-11-07/ida-pro/report.md
- skills/skillforge-ida-pro/references/idapython-api.md
- skills/skillforge-ida-pro/scripts/ida_evidence.py
- skills/skillforge-ida-pro/scripts/ida_mutations.py
- skills/skillforge-ida-pro/scripts/test_examples.py

测试：37项离线测试通过，真实IDA未执行。分页RED复现8项错误已由新实现修复。
