# 方法组最终报告
修改仅在 overnight_review_20261107/Skills 独立副本。未改原库、orchestrator权威文件、experience_store或根工具。

## 修复
- engineering-preflight/SKILL.md 步骤7：单维护者Git/P4差异审阅；实际并发才强制锁/条件写入。与共享协议一致。
- debugging/SKILL.md 增加诊断正控，先确认探针启用、类别与输出；沉默不能推出正常。
- debugging/references/verified-cases.md K03–K05明确历史报告、本轮未独立复核，列出缺原始任务ID/日志差异/日期。不补造来源或抹去历史经验。K04保留可关闭限量诊断，明确每局开关启用与已知事件正控。
- 两技能behavior-cases共新增3题，全部not_run。锁单维护者/并发各一题，诊断观测失效一题。

## 验证
此前原库经验工具29 tests OK（4 skipped），索引40 tests OK；索引CURRENT。本轮副本结构输出见structure.log。文档测试不证明模型行为改善；没有UE现场验证。未运行下载的外部脚本。

## 外部研究
官方规范 https://agentskills.io/specification 已读取：name/description必需、其他元数据可选，短入口与按需引用符合渐进披露。
下列具体源文件及LICENSE.txt均按固定SHA下载在本目录，未执行。两个skill-creator子目录许可证均Apache-2.0；不能据此推断仓库其他技能许可。

- anthropics/skills commit 2c5958ecac7cee2b583967a2c4981d0f4a75c579，提交时间 2026-11-06T22:32:28Z。这是可观察维护时间，不保证未来维护。

- openai/skills commit 49f948faa9258a0c61caceaf225e179651397431，提交时间 2026-06-24T02:36:12Z。这是可观察维护时间，不保证未来维护。

Anthropic具体文件 skills/skill-creator/SKILL.md 与 agents/grader.md：可迁移“检查断言是否区分真正成功与假绿、逐条证据支持评分、反馈改进评测”；本库已经有冻结答案与隔离expectations协议，保留并补充正控题。不采用自动反复优化description的整套宿主专用流水线，不以触发率代替完成质量。
OpenAI具体文件 skills/.system/skill-creator/SKILL.md 与 scripts/quick_validate.py：可迁移短入口、明确何时读引用、描述触发边界、格式检查与行为验证分层。quick_validate只做基础结构/字段验证，不能证明语义。未引入外部脚本/PyYAML依赖或agents/openai.yaml宿主专属结构。
未复制上述源文件到技能库；仅机制对照、用自己的中文修订。保留A/B/C、长期习惯与动态metadata路由。

## 剩余
三项新增行为题待独立上下文运行；K03–K05缺历史工件不能伪补；Windows/断电持久性不在本轮验证内。

## 后续：事务部分成功的CLI可观测性修复
仅独立副本的experience_store.py、test_experience_store.py及store-tool.md变更。
先注入promote与rollback最终journal写失败：目标分别已为new/old，但CLI退出2仅REFUSED。recovery-red.log记录两个子场景均因2!=3失败；故障后显式recover完成状态协调，使子场景独立。
修复为RecoveryRequired异常携带status=recovery_required、事务ID、target、当前观察hash（无法读unknown；缺失null）、retry_safe=false、禁止自动重试提示；CLI stdout JSON、退出3。prepared写入后的目标操作/最终journal异常都保守要求恢复，未改pending/recover协议。
修复后30 tests OK，4平台相关skip，详见recovery-green.log。故障注入检验目标内容、JSON、退出码、无REFUSED误报以及recover状态和rule_modified=false。未测试真实断电或日志介质物理损坏。
