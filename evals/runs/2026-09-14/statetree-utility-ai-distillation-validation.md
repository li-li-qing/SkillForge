# StateTree + Utility AI R12 蒸馏验证记录

日期：2026-09-14

## 范围

本轮基线：SkillForge Mass R11。

研究主证据：Epic UE5.8 StateTree 当前文档/API。

Utility AI 对照：`bohdon/UtilityAIPlugin@0f49e0c6d420497d3102c3975601360dc120bf15`（MIT，2025-04-06）。

R12 目标：将 StateTree、Utility scoring、GAS/Mover/SmartObject 执行、Mass 低保真决策和宠物/坐骑玩家命令分成明确所有权域；不把实验性 `FStateTreeConsiderationBase` 固化进 LGF Foundation public ABI。

## 时效性结论

- Epic UE5.8 StateTree core：Current。
- UE5.8 原生 Highest Utility / Weighted Utility selector：Current feature。
- UE5.8 `FStateTreeConsiderationBase`：官方 API 仍标 Experimental；采用 target-version adapter。
- `bohdon/UtilityAIPlugin`：Stable-but-old mechanism sample；没有 EngineVersion，不能作为 UE5.8 API 权威。
- UtilityAIPlugin 固定源码的 `CalculateDataScore()` 仍为 TODO；README 概念不得提升为已完成能力。
- UtilityAIPlugin 默认 0.025 秒 Tick、全 Action 重算只作为少量 Actor 样例，不作为大规模 NPC 默认调度模型。

## RED

在写正式 reference 前，R11 正式 Skill 参考对以下 12 个目标语义均未命中：

1. StateTree Utility Selector ownership；
2. utility consideration/scorer purity；
3. minimum dwell；
4. score breakdown；
5. DecisionGeneration；
6. Interrupt Policy；
7. active-path Task ANY/ALL completion；
8. PlayerCommand priority；
9. promotion DecisionState continuity；
10. Mass low-fidelity decision budget；
11. StateTree parameters promotion mapping；
12. single high-level Decision Owner。

新增行为样本：

- UE C++：CPP-68..CPP-75；
- LGF：LGF-45..LGF-48。

## GREEN

正式写回：

- `skills/skillforge-ue-cpp/references/statetree-utility-ai-patterns.md`
- `skills/skillforge-lgf/references/ai-decision-orchestration.md`

并接入两个 `SKILL.md`、LGF external project mapping、项目蒸馏索引、research 与 implementation progress。

使用与 RED 同一语义探针复测：**12/12 FOUND**。

核心合同：

- StateTree 默认是单一 high-level Decision Owner；
- Utility scorer 只读 DecisionContext，输出 normalized score/reason，不产生 Gameplay side effect；
- StateTree Task 列表不按 BehaviorTree Sequence 心智解释，明确 ANY/ALL completion；
- 决策切换使用 hysteresis / minimum dwell / cooldown / switch penalty；
- async execution 使用 DecisionGeneration/request identity 拒绝旧 completion；
- StateTree 选择 DecisionIntent，GAS/Mover/SmartObject 执行，Authority 决定 Cost/Damage/Loot/Inventory；
- Mass Agent 使用 event/signal/dirty-bucket/LOD budget，不为每实体固定 25ms 全量扫描；
- promotion/demotion 保存稳定 DecisionState，不序列化 StateTree 内部 frame；
- pet/mount PlayerCommand 优先于 autonomous utility；
- UE5.8 Experimental consideration API 只进入 adapter，不进入 Foundation public ABI。

## Fresh verification

### Self-contained validator

命令：

`python scripts/validate_skills.py --self-contained`

结果：

`Validated 6 skill(s): 0 error(s); 6 standalone copies validated.`

### Targeted validator unittest

执行 6 个当前仓库真实测试：

- portable package；
- self-contained relative resources；
- main file line budget；
- broken links；
- absolute local paths；
- eval JSON arrays。

结果：**6/6 PASS**，运行约 14.6 秒。

### LGF workspace inspector

命令：

`python -m unittest -v skills.skillforge-lgf.tests.test_inspect_workspace`

结果：**10/10 PASS**，约 0.015 秒。

### JSON

最终验证前共有 **42/42 JSON** 可解析。

### Behavior cases

实际扫描结果：

- UE C++：75，最后 CPP-75；
- LGF：48，最后 LGF-48；
- UI：8，最后 UI-09；
- Blueprint：4，最后 BP-04。

这里按 JSON 中实际唯一 ID 计数，不沿用历史人工汇总数字。

## Full validator suite

尝试：

`python -m unittest -v tests.test_validate_skills`

工具预算内未完整结束。

日志中前 **16 项均 `ok`**，预算耗尽时正在执行：

`test_name_constraints_and_directory_match`

随后单独执行该测试：

- R12：1/1 PASS，测试主体约 5.43 秒（进程总约 6.05 秒）；
- R11 baseline：1/1 PASS，测试主体约 5.61 秒（进程总约 6.21 秒）。

因此本轮状态是：**full suite 未完成；当前没有该慢测试由 R12 引入回归的证据。**

不得表述为“完整 suite 全绿”。

## 差异卫生

最终验证报告与 manifest 写入前：

- 新增：3；
- 修改：8；
- 删除：0。

新增为两份长期 reference + 项目蒸馏报告。

`skillforge-lgf/SKILL.md` 原 CRLF 保持 CRLF；未引入整文件换行噪声。

最终 changes 包还会包含本验证记录和 changed-files manifest。

## 未执行

本轮未执行：

- LGF UE5.7 UBT；
- UE5.8 UBT；
- StateTree Editor asset compile；
- PIE；
- Dedicated Server；
- StateTree + GAS cancel runtime；
- MassStateTree 1k/10k/50k benchmark；
- promotion/demotion runtime；
- pet/mount command runtime；
- UE5.7 与 UE5.8 Utility Consideration API compatibility build。

所以 R12 是 Skill/架构合同蒸馏，不是 LGF AI runtime 已完成实现。
