# GASDocumentation + GASShooter 蒸馏验证记录

日期：2026-09-14

## 基线

本轮以用户最新上传的 `SkillForge(1).zip` 为唯一基线，而不是上一轮 R6 输出。基线包含 Codex 根据实际 LGF 工程新增的：

- `skills/skillforge-lgf/references/multi-blade-combo-validation.md`
- LGF-25..27 行为样本
- `equipment-ability-lifecycle.md` 的手持/收纳分路规则
- `evals/runs/2026-09-14/twin-blade-handoff.md`

这些内容在 R7 中保留并继续扩展。

基线验证：

- `python scripts/validate_skills.py --self-contained`：6 skill，0 error，6 standalone copies valid。
- `python -m unittest discover -s skills/skillforge-lgf/tests -v`：10/10。
- 39 份 JSON 可解析。

## 固定外部来源

- `tranek/GASDocumentation@8f76c5780bdea69e0ea2cc161ab2f435f04182eb`，MIT，社区文档目标 UE5.3。
- `tranek/GASShooter@26295c548a19f221917e4a7232c12e763db64cb1`，MIT，UE4-era advanced shooter sample。

旧 API 仅作为机制证据；具体 UE5.7/5.8 实现必须再查当前 Engine source。

## RED

先新增行为样本：

- CPP-36..42
- LGF-28..31

随后只扫描正式 Skill/Reference Markdown，不读取新 eval expectations，检查六个目标合同：

1. prediction window across latent callbacks；
2. TargetData consume-once / data-before-listener；
3. Ability RPC batching = transport only；
4. dynamic AttributeSet removal replication race；
5. SourceObject + exact spec handle；
6. predicted multi-mesh/layer reject rollback。

R7 写回前六项均为 FAIL，确认新行为不是旧参考已经覆盖的同义重复。

## GREEN

新增正式参考：

- `skills/skillforge-ue-cpp/references/gas-prediction-targetdata-patterns.md`
- `skills/skillforge-lgf/references/gas-combat-prediction.md`

并更新：

- UE C++ / LGF `SKILL.md` 路由；
- LGF `external-project-patterns.md`；
- `equipment-ability-lifecycle.md`；
- `multi-blade-combo-validation.md`；
- 项目蒸馏索引、研究记录和实施进度。

同一六项语义断言重跑后 6/6 PASS。

## 回归

已执行：

- `python scripts/validate_skills.py --self-contained`：6 skills / 0 error / 6 standalone copies。
- validator 定向 unittest：self-contained、主文件行数、链接、链接逃逸、绝对路径、eval schema，6/6。
- `python -m unittest discover -s skills/skillforge-lgf/tests -v`：10/10。
- 39 份 JSON 全部解析。
- 行为样本总数：UE C++ 42、LGF 31、UE Blueprint 5、UI 4。

完整 `python -m unittest discover -s tests -v` 在工具 210 秒预算内未完成：前 12 项为 `ok`，执行到 `test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names` 时超时。因此不宣称全量 suite 通过。

该 quoted-name 测试已在 R7 当前工作区与用户最新基线分别单独执行，均 1/1 PASS，约 8.7～9.0 秒。说明本轮没有观察到该测试的回归，但完整 suite 的总体耗时问题仍存在。

## 生成文件清理

用户最新 ZIP 中存在 `__pycache__/*.pyc`。本轮完整 R7 包会删除这些生成缓存；它们不是 Skill 内容。运行验证产生的新 `__pycache__` 也会在打包前再次清理。

## 未执行

- 未构建 GASShooter 于 UE5.7/5.8；
- 未在 LGF 实际项目执行 PIE/Dedicated/高延迟 GAS 网络回归；
- 未宣称旧 GASShooter TargetActor / RPC batching API 可直接用于当前引擎；
- 未修改用户实际 LGF 生产源码，本轮只更新 SkillForge。
