# Lyra R8 Skill TDD / Validation Record

## Baseline

基线：`SkillForge_GAS_R7.zip`。

新增测试前，正式 UE C++ / LGF reference 对以下合同做定向文本断言：

- Current / Stable-but-old / Historical / Reject 技术时效性分级；
- Lyra 5.1+ Init State；
- Experience readiness barrier；
- GameFeatures Beta 风险；
- Inventory Item / Equipment Instance 生命周期拆分；
- PawnData / InputConfig / TagRelationshipMapping 组合。

结果：6/6 均缺失，RED 成立。

## New Behavior Cases

UE C++：CPP-43..49。

LGF：LGF-32..35。

## GREEN

写入：

- `skillforge-ue-cpp/references/external-project-freshness-and-lyra.md`
- `skillforge-lgf/references/lyra-modern-framework-mapping.md`
- LGF external project / validation reference 摘要与时效性门。

同一组语义断言：6/6 PASS。

## Structural / Regression

- `python scripts/validate_skills.py --self-contained`: 6 skills, 0 errors, 6 standalone copies validated.
- LGF workspace inspector: 10/10 PASS.
- JSON parse: 39/39 PASS.
- validator targeted tests: 6/6 PASS.

完整 root unittest 在 210 秒工具预算内未跑完；超时前 12 项全部 `ok`，正在运行 `test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names`。该单测在 R8 当前工作区和 R7 基线分别独立执行均为 1/1 PASS（约 8.9 秒）。因此不宣称完整 suite 通过。

## Evidence Scope

Epic 当前 Lyra 官方文档在读取时显示 UE5.8；当前 GitHub connector 无法访问 Epic 私有 UnrealEngine/Lyra 源码，因此没有把公开 mirror 当官方源码。

GitHub 次级对照固定：`XistGG/XistCommonGameSample@7e01e1fed344a741f80fa82b7161c86c494a410b`，README 明确为 UE5.7 Lyra-like HUD & Input 单机简化项目。它只作为 CommonUI / Enhanced Input 分层证据，不用于多人 Authority/GAS 结论。

## Runtime Limits

本轮未：

- 在 LGF UE5.7 实现 InitState adapter；
- 编译/运行 Lyra；
- 执行 GameFeatures packaged build；
- 执行 feature unload/reload；
- 执行 Listen/Remote/JIP；
- 执行 Avatar race injection。

因此本轮交付是研究、Skill 合同与静态验证，不是 LGF runtime 功能完成声明。
