# GAS 文档事实修正（2026-11-07）

修正 UE-C++ gas-prediction-targetdata-patterns §4.1–4.2 和 LGF gas-combat-prediction §5：原文将客户端本地赋值 replicated CurrentTarget 后服务器旧值误归到顺序；标准属性 Server→Client，须先证明上传通道。两份引用各自包含官方版本来源、TargetData/activation-with-event-data 候选路径与本地事件边界。仅当真实通道存在，才讨论激活关联与到达先后。

同时修正 arpg-item-inventory-patterns §5、framework-composition-patterns §2 和 LGF external-project-patterns 的授予撤销概括：active GE handle 可指共享聚合实例，不自动证明装备独占；区分独立持续效果、聚合层贡献、Instant 执行，保留精确 AbilitySpec 撤销。贡献账本/重建是建议，非引擎现成保证。

官方依据（浏览时显示 UE5.8；不套用所有旧版本）：
- https://dev.epicgames.com/documentation/unreal-engine/replicate-actor-properties-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/GameplayAbilities/UAbilitySystemComponent
- https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/GameplayAbilities/FPredictionKey
- https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/GameplayAbilities/EGameplayEffectStackingType
- https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-effects-for-the-gameplay-ability-system-in-unreal-engine

独立改写，无复制外部实现或新增第三方代码许可要求。风险归类：技能建议的事实/前提缺陷；未宣称发现实际工程 bug。

新增 CPP-124/125、LGF-77/78 行为规格，全部 not_run。仅执行 JSON/引用/自包含结构检查；没有真实 UE、网络抓包、项目源码修改、安装或发布。StateTree 交由其他审查者处理，本轮未改该文件。

结构检查实际结果：`validate_skills.py --self-contained` 对 UE-C++、LGF 返回 `Validated 2 skill(s): 0 error(s); 2 standalone copies validated.`。尝试 git diff --stat 不适用：v5目录无git仓库，未产生diff统计；本轮修改清单为上述5个reference、2个behavior-cases.json和本报告，共8文件。
