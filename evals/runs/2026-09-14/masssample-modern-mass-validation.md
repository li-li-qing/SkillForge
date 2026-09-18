# MassSample + Epic UE5.8 Mass 蒸馏验证记录

日期：2026-09-14

## 固定来源

- Current upstream：`Megafunk/MassSample@ca9825861f35ab4f8e152351de2adb893b51ca70`，MIT；提交日期 2026-06-27，提交信息包含 `(5.8)`。
- Historical comparison：`getnamo/MassCommunitySample@1487f0208873acda6fedcfe58a4b1a2f3268192a`，MIT；其 README 主体仍保留 UE5.1-era 说明，因此仅作为 API 演化证据。
- Modernity calibration：Epic UE5.8 当前 MassEntity / MassGameplay / MassAI / MassCrowd / ZoneGraph / StateTree / SmartObject 文档与发布说明。

## RED → GREEN

R10 正式参考在写回前缺少以下合同：

1. UE5.8 Mass architecture overhaul / off-thread entity creation；
2. QueryExecutor 与旧 Processor/Query API 的版本边界；
3. Signal 只作为 wakeup，不承载 canonical payload；
4. representation Actor 为 transient projection；
5. Simulation / Representation / Replication 三轴 LOD；
6. ZoneGraph / SmartObject / StateTree 职责分离；
7. Mass Debugger / Insights 先测后迁；
8. StableAgentId + Mass↔Actor promotion/demotion；
9. pet/mount hybrid promotion contract；
10. CombatOwner authority fence；
11. Experimental MassGameplay/MassAI/MassCrowd/ZoneGraph feature gate。

写回后同一 semantic probe：`11/11 PASS`。

## 行为样本

- UE C++：67 个，末项 `CPP-67`；本轮新增 `CPP-60..67`。
- LGF：44 个，末项 `LGF-44`；本轮新增 `LGF-41..44`。
- UE Blueprint：5 个，末项 `BP-04`。
- UI Design：9 个，末项 `UI-09`。

## Fresh verification

### Self-contained validator

`python scripts/validate_skills.py --self-contained`

结果：`Validated 6 skill(s): 0 error(s); 6 standalone copies validated.`

### Targeted validator unittest

执行当前仓库真实 `ValidateSkillsTests` 的 6 项：

- self-contained relative resources；
- main file line budget；
- broken links；
- repository escape；
- absolute local path；
- eval JSON。

结果：`Ran 6 tests ... OK`。

### LGF Inspector

`python -m unittest skills.skillforge-lgf.tests.test_inspect_workspace`

结果：`Ran 10 tests ... OK`。

### JSON

创建本验证文件之前，41 份 JSON 全部解析成功；最终 changed-files manifest 创建后需要包外再次解析，不用本条提前声称最终数字。

### Full validator suite

尝试：`python -m unittest -v tests.test_validate_skills`，工具预算 220 秒。

- 超时前前 12 项均显示 `ok`；
- 当时正在执行 `test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names`；
- 因超时，**不宣称完整 suite 通过**。

阻塞点单独对照：

- R11：1/1 PASS，约 8.995s unittest runtime；
- R10 baseline：1/1 PASS，约 9.265s unittest runtime。

因此当前没有证据显示该慢测由 R11 引入回归，但完整 suite 状态仍为“未在工具时限内完成”。

## 源码/运行验证边界

本轮没有执行：

- UE5.7/5.8 UBT build；
- Editor/PIE；
- Listen Server / Dedicated Server；
- MassReplication JIP / reconnect / packet loss；
- StateTree/ZoneGraph/SmartObject runtime integration；
- Mass Debugger 实际 trace；
- 1k / 10k / 50k entity benchmark；
- LGF Mass adapter 实装。

所以 R11 是 current-source / current-doc / Skill-contract 层验证，不是 LGF Mass production certification。
