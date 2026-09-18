# Obsidian 蒸馏 R2 验证记录

日期：2026-09-14

## RED / 基线缺口

在 Obsidian 写回前，对 `skillforge-ue-cpp/references/runtime-gameplay-patterns.md` 与 `skillforge-lgf/references/external-project-patterns.md` 做定向术语扫描，以下主题均未形成专门规则：

- Definition / Instance / Fragment ARPG 物品分层；
- per-equipment `GrantedHandles` 精确 GAS 撤销；
- Master / Hero / Shared Stash save domains；
- GPL-3.0 外部项目复制边界；
- ItemInstance 静态展示数据过度复制；
- Affix/equip loop 中同步资源加载的专门反例。

这不表示旧技能完全无法回答相关问题，只表示没有足够明确、可检索、可评测的 Obsidian/ARPG 专项合同。

## GREEN / 写回内容

新增：

- `skills/skillforge-ue-cpp/references/arpg-item-inventory-patterns.md`
- `docs/project-distillations/obsidian.md`

更新：

- `skills/skillforge-ue-cpp/SKILL.md` 增加 ARPG 物品/容器参考入口；
- `skills/skillforge-lgf/references/external-project-patterns.md` 增加 Obsidian -> LGF 二次映射；
- UE C++ behavior cases 增加 CPP-08..11；
- LGF behavior cases 增加 LGF-17；
- 项目蒸馏索引、research、implementation progress 同步记录。

行为 case 本轮是**评测规格新增**，没有冒充已由多个外部 Agent 执行通过。

## 实际验证

- `python scripts/validate_skills.py --self-contained`：6 skill，0 error；6 standalone copies validated。
- 定向内容断言：Definition/Instance/Fragment、GrantedHandles、LoadSynchronous、GPL-3.0、Obsidian、CPP-11、LGF-17 均存在。
- UE C++ behavior JSON：11 cases，ID 唯一。
- LGF behavior JSON：17 cases，ID 唯一。
- `test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names`：当前单测通过，8.700s。
- `test_self_contained_copy_keeps_all_relative_resources_valid`：通过，0.559s。
- `skills/skillforge-lgf/tests` workspace inspector：10/10 tests passed。
- 全仓 JSON 解析：34 files parsed。

## 限制

一次 `python -m unittest -v tests.test_validate_skills` 全套运行在工具 120 秒时限内未完成；它停在 quoted-name 测试附近。该测试在修改前快照单独执行通过（8.626s），当前版本单独执行也通过（8.700s），因此本记录不声称“全套 unittest 已完整跑完”，只报告实际完成的单测、Skill validator 和 Inspector 结果。

未运行 UE 编译、Obsidian PIE、Dedicated Server、JIP、断线重连、复制带宽或大型库存性能基准。
