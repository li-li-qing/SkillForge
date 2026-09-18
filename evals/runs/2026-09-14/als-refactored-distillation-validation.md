# ALS-Refactored 第六轮蒸馏验证

日期：2026-09-14

固定外部源码：`Sixze/ALS-Refactored@b754d6f0f2bb03741d301f8fb88077ebfe561e17`。

## TDD 语义基线

在 R5 基线快照上检查 6 个新增正式合同，全部缺失，得到预期 RED：

1. `FCharacterNetworkMoveData` / CMC SavedMove 语义迁移到 Mover；
2. Push Model `MARK_PROPERTY_DIRTY` + Iris custom struct 完整合同；
3. `view network smoothing` 与 actor/visual smoothing 分离；
4. animation field `write phase`；
5. 固定 ALS-Refactored snapshot 的 LGF selective migration；
6. Blueprint Linked Layer Property Access `write phase`。

写回正式参考后用同一组断言重跑，6/6 命中。

## Skill 自包含校验

命令：

```text
python scripts/validate_skills.py --self-contained
```

结果：

```text
Validated 6 skill(s): 0 error(s); 6 standalone copies validated.
```

## Validator 定向回归

执行 6 个与本轮修改最相关的测试：

- self-contained copy；
- broken links；
- repository escape；
- absolute local path；
- eval JSON array；
- behavior expectation / fixture path。

结果：6/6 `OK`。

## LGF Inspector

命令：

```text
python -m unittest discover -s skills/skillforge-lgf/tests -v
```

结果：10 tests，10 `OK`。

## JSON

新增变更清单 JSON 后重新解析仓库所有 JSON；最终结果记录在交付前验证中。行为样本本轮增加：

- UE C++：CPP-30..35；
- LGF：LGF-23..24；
- Blueprint：BP-04。

## 全量 validator unittest 限制

尝试：

```text
python -m unittest discover -s tests -v
```

180 秒执行预算内前 12 项均为 `ok`，随后工具在 `test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names` 执行期间超时，因此**不宣称全量 suite 完成**。

该测试单独在：

- R6 当前工作区；
- R5 修改前基线

均为 1/1 `OK`，耗时约 8.8~9.0 秒。说明目前没有证据表明本轮修改破坏该测试，但也不能用单测替代全量 suite 完成声明。

## 未做的运行验证

本轮没有：

- 构建 ALS-Refactored UE5.8；
- 在 LGF UE5.7 实际移植；
- PIE Listen/Dedicated/Iris；
- URO/foot-lock 性能测量；
- moving/rotating base 实机多人验证。

因此当前通过范围是 SkillForge 结构、文本合同、行为样本和现有 inspector；不是 UE 工程运行验收。
