# 第一版取材与技术核验

检查日期：2026-09-12。正文为本项目重新组织的中文指导；本版没有复制第三方技能文件、脚本或大段原文。下表区分方法借鉴、候选材料与已核验机制，不以星数作为正确性证据。

## GitHub 来源快照

| 来源与固定版本 | 本次采纳 | 本次舍弃或限定 | 许可核查 |
|---|---|---|---|
| [OpenAI skill-creator](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.system/skill-creator/SKILL.md) | 短入口、条件引用、按任务补充资源 | 宿主 UI 元数据与专属安装命令不进入通用正文 | 对应目录 `LICENSE.txt`：Apache-2.0 |
| [Anthropic skill-creator](https://github.com/anthropics/skills/blob/34040c9c568585f6929bedeaad110ad08f079624/skills/skill-creator/SKILL.md) | 同输入有/无新技能对比，检查实际输出 | 不强制依赖其评测工具链；单次冒烟不写成统计改善 | 对应目录 `LICENSE.txt`：Apache-2.0 |
| [Superpowers systematic-debugging](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/systematic-debugging/SKILL.md) | 复现、证据链、对照正常路径、最小假设实验 | 排障深度按问题调整；不采用固定补丁次数作为通用停工或重构阈值 | 仓库：MIT |
| [游戏开发蓝图候选技能](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/b105e1cf617adf0b68ed98790a716bbb60993179/skills/unreal/unreal-blueprints/SKILL.md) | 按图表类型、通信方式和数据职责组织 | 其 UE 5.8 目标不能代替项目版本；“Construction Script 不在游戏中运行”的绝对说法不采用 | 仓库：Apache-2.0 |
| [Anthropic frontend-design](https://github.com/anthropics/skills/blob/34040c9c568585f6929bedeaad110ad08f079624/skills/frontend-design/SKILL.md) | 根据任务、受众和真实内容确定设计方向 | 网站首屏、特定审美偏好不推广到 HUD 或 MFC 工作台 | 对应目录 `LICENSE.txt`：Apache-2.0 |

上述提交通过公开 GitHub API 获取。许可信息按目录文件或仓库元数据核对；未来若直接复制、改编并分发具体文件，需同时保留其适用许可与声明。本库没有替原始本机资料重新授权。

## 标准与可移植性

采用 [Agent Skills 规范](https://agentskills.io/specification) 的目录和 `name`/`description` 头部。名称前缀减少与既有技能撞名；相关内容在需要时读取。宿主的自动发现不属于本库实现，单独复制测试也不等于多个 Agent 的实测认证。

本库 v1 选择只含 `name` 与 `description` 的最小头部；描述是一行 JSON 风格双引号字符串，也是有效的 YAML 字符串。名称使用无歧义 plain 标量或 JSON 风格双引号字符串；数字开头及 YAML 保留标量必须加引号，避免名称被宿主解释成数值、布尔或空值。校验器明确只支持这个写作子集，不冒充通用 YAML 解析器。

## 本机项目资料的取舍

本次读取了原有 LGF 的 UMG/构建笔记、Replicated Suite 的 API 能力与刷新链约束，以及 Advanced UI 的 HUD/工作台/实时布局规则。这些目录在取材时由本机 Git exclude 排除，未作为新技能依赖；完成第一版后已按用户要求删除，并移除相应的本机排除条目。

| 原始记录 | 核验和收录结果 |
|---|---|
| LGF：“Hidden 仍可点击” | 错误；本机 UE 5.7.4 的枚举注释明确不可命中。新参考记录修正后的条件 |
| LGF：“BindWidget 只找直接子控件” | 对同一 WidgetTree 的普通 Panel 嵌套不成立；初始化遍历 WidgetTree。独立嵌套 UserWidget 的内部树是另一边界，不能混为一谈 |
| LGF：“Canvas Offsets 总是位置与宽高” | 已核对布局源码：不作为通用规则；拉伸轴的 Right/Bottom 作为远侧边距，非拉伸轴才按尺寸参与布局，还需考虑 AutoSize |
| LGF：固定构建路径、DebugGame、Listen Server 约束 | 留作项目背景，不搬入 UE 通用正文 |
| Replicated Suite：未知 API 与真实空数据应分开 | 收录为诊断/显示方法；当前 RU 客户端可用 API、具体服务名和性能没有运行验证 |
| Advanced UI：实时数值不应打乱布局与用户选择 | 收录为目标和检查方法；具体布局效果尚需目标 UI 的实际验证 |

原始材料没有作为本仓库的已跟踪版本分发，以下用取材时的 SHA-256 记录内容指纹。表中的历史相对路径仅用于溯源，原文件现已删除，不是可访问链接或新技能运行时依赖；指纹本身不能恢复原文件。

| 材料路径 | SHA-256 | 主要使用位置 |
|---|---|---|
| `lgf-ue5-devkit/SKILL.md` | `C54E5E1CB9941CF4C6C2CA2370979AAA0118176CCC810790E7BFD1F9A80E5188` | C++ 所有权/生命周期与项目边界 |
| `lgf-ue5-devkit/references/project/umg-pitfalls.md` | `4A427789C0AE9FA203970D8F38562D66CF6DC4E2A5D726EF0AD2979FE8E13002` | 排障、蓝图、UI 的旧规则反例 |
| `lgf-ue5-devkit/references/project/build-debug.md` | `7446B1A248DA46DF9E0B1A5BB022831823EAA1B6398AD82875F803CD041B9BF5` | 固定构建配置不得泛化的案例 |
| `replicated-suite-maintenance/SKILL.md` | `73655E8E8548824DBAA1CB80C5AD4E9FB2B42FB3102DF5DB52A61F77E97DE111` | 排障证据链、能力未知与空数据、UI 职责 |
| `Advanced_UI_Layout_Skill_v4/advanced-ui-layout/SKILL.md` | `D160DAA41DAB75F70DB42622CEE7F70AC107B34B57D0940CA9B55CD272EAEC05` | HUD/工作台分区、实时几何稳定 |
| `Advanced_UI_Layout_Skill_v4/advanced-ui-layout/PRO_TOOL_PATTERNS.md` | `0D4B66F18CBBE97E758E20B00E419B4467C3A661456F3B93ADEACA0BE30DF234` | 布局职责、错误定位链；去除强制完整停靠系统 |

## UE 证据账本

本机 `Engine/Build/Build.version`：UE **5.7.4**，Changelist **51494982**，分支 `++UE5+Release-5.7`。以下路径均相对引擎根目录，没有把引擎源码复制到仓库。

| 结论 | 已检查证据 | 检查层级 |
|---|---|---|
| Hidden 占位但不可命中；两种 HitTestInvisible 对子控件影响不同 | `Engine/Source/Runtime/UMG/Public/Components/SlateWrapperTypes.h`，`ESlateVisibility`；[Epic API 当前页](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/UMG/ESlateVisibility) | 本机 5.7.4 源码与读取时显示 5.8 的 API 页；未跑输入回归 |
| 普通容器嵌套不等于超出 WidgetTree | `Engine/Source/Runtime/UMG/Private/WidgetTree.cpp` 的 `ForEachWidget` / `ForWidgetAndChildren`，`WidgetBlueprintGeneratedClass.cpp` 的 `InitializeWidgetStatic` 遍历与属性赋值 | 本机源码；未创建示例资产 |
| Canvas Offsets 解释取决于轴上锚点和布局模式 | `Engine/Source/Runtime/Slate/Private/Widgets/Layout/SConstraintCanvas.cpp` 的水平/垂直拉伸分支，结合 `UMG/Private/Components/CanvasPanelSlot.cpp` 的 SetSize | 本机源码；未执行布局视觉检查 |
| 运行期生成 Actor 的构造路径不能等同“只在编辑器” | `Engine/Source/Runtime/Engine/Private/Actor.cpp` 的 `FinishSpawning` 调用 `ExecuteConstruction`；`ActorConstruction.cpp` 的用户构造逻辑 | 本机源码；未运行 PIE 或打包 |
| UObject 指针类型分别处理保活、观察、资源路径 | [Object Pointers，UE 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/object-pointers-in-unreal-engine?application_version=5.7) | 版本匹配官方资料；没有编译修复示例 |
| UMG 刷新方式应根据更新频率和实际成本选择 | [UMG Optimization，UE 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/optimization-guidelines-for-umg-in-unreal-engine?application_version=5.7) | 官方资料；没有性能测量 |

源码复核指纹（SHA-256）：

- `SlateWrapperTypes.h`：`AB4C66FA84A4C96C644ECF1ACCCBBA1CFD396053899153D58D61B20B83860BDA`
- `WidgetTree.cpp`：`1C9A3214CE84D0ADCF8EA7BDAF173B43A9FDA2D1668B5BCFED991F5B534D3200`

UE5 通用入口不宣称全部小版本一致；调用时仍检查目标版本、源码分支和任务条件。规范或来源更新后，先验证受影响的结论，再修改技能。

资料读取限制：本次网络工具未能打开带 5.7 参数的 `ESlateVisibility` 和 Actor Lifecycle 页面；相关 5.7 行为以实际读取的本机 5.7.4 源码为证据。Object Pointers 和 UMG Optimization 的 5.7 页面已读取。不要把链接中的版本参数当成已成功核验该版本的证明。

## 2026-09-14 增补说明

前述 v1 的两字段头部限定已扩展为受限可选元数据格式，以兼容库内现有 ArcheRage 包；不删除它的 compatibility/revision，不宣称支持任意 YAML。头部、文件名误报和原包全部负测已纳入当前校验。

本轮再收到位于库外的旧技能副本，因此前文“旧资料已删除”仅指当时工作区，并不证明新提供目录没有增量。本轮重新按文件哈希登记，共 91 文件、25 个内容相同的后续副本；具体取舍见迁移清单。新增 GASP/Mover/战斗生命周期主题取自旧库、当前项目源码及历史运行报告，强度分开记录。没有将早期“Stretch=None”“owner已正常”“Cancel返回成功即动画停止”等已推翻推断再作为规则。

迁移、校验和文字行为样本详见 [本轮报告](../evals/runs/2026-09-14/migration-report.md)。本轮未重新运行 UE 或联网，未重新验证旧社区推荐列表，未把仓库知名度当作证据。


## 2026-09-14 GitHub 项目蒸馏：ActionRoguelike

第一项外部 UE 工程采用 `tomlooman/ActionRoguelike@a3f9a182c985b1732d9f72ae8b92e4845babfa3f`。README 将 master 标为 UE 5.6，并明确说明 Actor Pooling、aggregate/deferred ticking、data-oriented projectile 等属于实验/WIP；因此没有把这些功能的存在等同生产成熟度。仓库元数据没有声明可直接依赖的 License，本轮没有复制第三方代码或资产，只记录机制和风险。

已读取的重点源码范围：ActionSystem 的 Component/Action/AttributeSet；AIController 与 BT Service；StateTree task；GameMode 的 DataTable/EQS/PrimaryAsset 异步生成；InteractionComponent；SaveGameSubsystem；ActorPoolingSubsystem；ProjectilesSubsystem 与 Projectile FastArray；EffectSlotWidget；Build.cs 与实验功能开关。

本轮采纳：replicated UObject subobject 完整生命周期、OnRep 与 Listen Host 本地刷新分离、local candidate 与 Authority revalidation、轻量选择数据到 PrimaryAsset async load、Save participant + post-load rebuild、FastArray hot/cold 数据分层、pool reset contract、延迟任务生命周期、Insights/feature gate。明确拒绝直接迁移：客户端修改 authoritative FastArray、Remote client 通过 GameState 发 Server RPC、客户端 Focus 直接授权交互、Actor FName 作为长期存档 ID、未验证 reset 的网络对象池、用该项目自制 Action 替换 LGF GAS。

完整模块分析见 [ActionRoguelike 蒸馏](project-distillations/actionroguelike.md)。通用规则写入 `skillforge-ue-cpp/references/runtime-gameplay-patterns.md`；LGF 二次映射写入 `skillforge-lgf/references/external-project-patterns.md`。新增 CPP-03..07 和 LGF-16 行为样本用于防止照搬样例。

## 2026-09-14 GitHub 项目蒸馏：Obsidian

第二项外部 UE 工程固定为 `intrxx/Obsidian@bbe55b5b4c0ae4761ab57868398aca1c3b6b8c0b`。仓库许可证为 GPL-3.0；README 同时说明公开代码引用了未提交资产，不能把源码存在性写成“仓库可直接构建”。本轮没有复制第三方实现，只提炼数据所有权、复制、资源生命周期和可迁移模式。

重点源码：InventoryGridItemList/InventoryComponent、ItemDefinition/ItemInstance/Fragments、EquipmentList/EquipmentComponent、AffixAbilitySet、PlayerStash/StashItemList、ItemDataLoaderSubsystem、ItemDropComponent、PlayerController 与 Master/Hero/SharedStash Save。

本轮采纳：Definition/Instance/Fragment 分层、FastArray Authority entries + derived local indexes、replicated Item UObject 的 ReadyForReplication/Add/Remove subobject、装备 GAS exact GrantedHandles、Inventory/Equipment/Stash 共用稳定 Item identity、GameplayMessage 投影 UI、Master/Hero/SharedStash 按生命周期分域。明确收紧：静态展示数据不按实例重复复制；Affix/equip/drop 热路径禁止 `LoadSynchronous`；掉落 roll 必须 Authority；Controller Server RPC 仍需参数重授权；跨容器替换按事务处理。

完整分析见 [Obsidian 蒸馏](project-distillations/obsidian.md)。通用 ARPG 规则进入 `skillforge-ue-cpp/references/arpg-item-inventory-patterns.md`；LGF 二次映射进入 `skillforge-lgf/references/external-project-patterns.md`。新增 CPP-08..11 与 LGF-17 行为样本。

## 2026-09-14 GitHub 项目蒸馏：Sixze/ALS-Refactored

第六项外部 UE 工程固定为 `Sixze/ALS-Refactored@b754d6f0f2bb03741d301f8fb88077ebfe561e17`。仓库许可证 MIT。固定提交的 README 发布表仍写 4.17 / UE5.7，但同提交 `ALS.uplugin` 已是 VersionName 4.18、EngineVersion 5.8.0，因此本轮以固定源码和 `.uplugin` 作为 current-main 版本证据，不用 README 版本表替代源码。

重点源码：custom CharacterMovement SavedMove/NetworkMoveData、AAlsCharacter Push Model 与 SimulatedProxy/view smoothing、UAlsAnimationInstance GT/worker/post-update 分层、UAlsLinkedAnimationInstance Property Access 线程注释、GameplayTag Blend AnimNode、Mantling RootMotionSource、moving-base relative transform、Engine.ini Push Model/Iris/URO 配置、ALS Camera component、Movement Settings DataAsset。

本轮采纳的是网络与动画工程语义：prediction state 必须进入历史 move/resim；Push Model 需要配置/声明/dirty 三段闭环；Legacy NetSerialize 不自动证明 Iris custom struct 支持；Actor transform/view/visual mesh 是不同 smoothing channel；URO/AlwaysTickPose/absolute mesh rotation 按 network role 和 movement base 条件启用；Property Access 必须有 field write phase；moving-base traversal 是带 stable identity 的 movement transaction。明确拒绝迁入 LGF：ACharacter/CMC 主链、复制 PhysWalking、CMC RootMotionSource 类、ALS Camera 与 GameplayCamera 双 owner、客户端 Roll/Mantle 参数的轻量服务器校验边界。

完整分析见 [ALS-Refactored 蒸馏](project-distillations/als-refactored.md)。规则写回既有 Mover/动画网络、LGF GASP/Mover 和 Linked Animation Layer 参考，没有建立第二套 ALS Skill。新增 CPP-30..35、LGF-23..24、BP-04 行为样本。

## 2026-09-14 GitHub 项目蒸馏：GASDocumentation + GASShooter

第七轮固定 `tranek/GASDocumentation@8f76c5780bdea69e0ea2cc161ab2f435f04182eb`（MIT，文档目标 UE5.3）与 `tranek/GASShooter@26295c548a19f221917e4a7232c12e763db64cb1`（MIT，UE4-era advanced sample）。两者都不作为 LGF UE5.7 的现行 API authority；本轮只迁移 Prediction、TargetData、AbilityTask、Owner/Avatar、SourceObject/SpecHandle、RPC batching、item-local state 和多表现层 prediction rollback 的机制。

重点源码/文档：GASDocumentation 的 ASC、PredictionKey/Scoped Prediction Window、TargetData、NetSecurityPolicy、AbilityTask、AttributeSet runtime add/remove、EffectContext、GameplayCue batching；GASShooter 的 PlayerState ASC、Hero possession ActorInfo、Weapon SourceObject/SpecHandle、reusable TargetActor AbilityTask、Ability RPC batching、multi-mesh montage prediction/rejection 与 owner-only ammo state。

本轮收紧：PredictionKey 不跨 latent callback 自动延续；client natural ability end 不直接决定 Authority end；TargetData NetSerialize 不等于授权，需 consume-once、处理 data-before-listener race 并 Authority sanitize/retrace；Ability RPC batching 只是 transport optimization；item-local ammo/durability 不必 AttributeSet-per-item；dynamic AttributeSet removal 有 replication teardown race；GameplayEffectContext 只承载一次执行 provenance；GameplayCue 不承载业务真值。

完整分析见 [GASDocumentation + GASShooter 蒸馏](project-distillations/gasdocumentation-gasshooter.md)。通用规则进入 `skillforge-ue-cpp/references/gas-prediction-targetdata-patterns.md`；LGF 映射进入 `skillforge-lgf/references/gas-combat-prediction.md` 并补充 Codex 最新的多刀刃与装备生命周期规则。新增 CPP-36..42、LGF-28..31。


## 2026-09-14 GitHub/官方样例蒸馏：Lyra 现代框架与技术时效性门

第八轮不再把“项目存在于 GitHub”视为足够证据，正式引入 `Current / Stable-but-old / Historical / Reject` 四级时效性分类。任何外部 UE 项目在进入 Skills 前，都要记录固定版本、维护时间、license、目标 UE 版本，并与当前目标引擎源码/官方文档/用户真实工程交叉检查；stars、forks 和旧 README 不能替代版本证据。

Lyra 主证据使用读取时 Epic Developer Community 的 UE5.8 当前文档。官方升级页明确：Lyra 5.1 将 5.0 的 Pawn 初始化改写为 `IGameFrameworkInitStateInterface` + `GameFrameworkComponentManager` Init State，用于修复 network replication race 并提升 feature component 扩展性；所以 5.0 固定初始化顺序降级为 Historical。当前 5.8 文档仍保留 PawnExtension readiness、PlayerState ASC、AbilitySet/PawnData、Experience/GameFeature、Inventory/Equipment 生命周期和 Enhanced Input/CommonUI 组合思想。

GitHub 次级证据固定 `XistGG/XistCommonGameSample@7e01e1fed344a741f80fa82b7161c86c494a410b`，README 明确是 UE5.7 Lyra-like HUD & Input 单机简化样例；只用于交叉验证 CommonUI/EnhancedInput/InputAction→GameplayTag 分层，不用于多人 Authority/GAS 证据。由于当前 connector 无法访问 Epic 私有 UnrealEngine/Lyra 源码，本轮没有把公开 mirror 冒充官方源码，也没有复制 Epic Sample 实现。

本轮采纳：模块化 Pawn readiness state、stable PlayerState ASC + replaceable Avatar、PawnData 式静态组合配方、Experience 异步 readiness barrier、feature activation/deactivation 对称性、Inventory item 与 Equipment generation 生命周期拆分、feature-scoped input registration、CommonUI input router 与 gameplay input 分层。明确收紧：GameFeatures 当前官方 5.8 API 仍标 Beta，Production 是否采用必须独立评估；Lyra Inventory 不作为复杂 ARPG 容器能力上限；LGF 不引入第二套 Lyra Foundation/Inventory/Mover/GameplayCamera。

完整分析见 [Lyra 现代框架蒸馏](project-distillations/lyra-modern-framework.md)。通用规则进入 `skillforge-ue-cpp/references/external-project-freshness-and-lyra.md`；LGF 映射进入 `skillforge-lgf/references/lyra-modern-framework-mapping.md`，并新增 CPP-43..49、LGF-32..35 行为样本。

## 2026-09-14 GitHub 项目蒸馏：XistCommonGameSample

第九轮固定 `XistGG/XistCommonGameSample@7e01e1fed344a741f80fa82b7161c86c494a410b`（MIT，`.uproject` EngineAssociation 5.7）。项目 README 明确它是从 Lyra 5.7 简化出的单机 CommonUI + Enhanced Input 教学工程，因此对 LGF UE5.7 的 UI/Input 机制属于 Current-to-target，但不能外推为多人 Authority/GAS/JIP 证据。

重点源码：`AXcgsPlayerPawn` 的 HUD/IMC/binding 生命周期、`UXcgsInputActionMap` 的 InputAction->GameplayTag、`UXcgsActivatableWidget` 的 optional input config、HUD/MainMenu UI Action、CommonGame `UGameUIPolicy` per-LocalPlayer root、`UPrimaryGameLayout` GameplayTag layer + suspend token、GameplayMessageRouter pause message。

本轮采纳：LocalPlayer root ownership、source-owned IMC、top-level input policy、UI Action exact handle、transition suspend token、typed gameplay message projection、streamed optional page。明确拒绝推广：`ClearAllMappings()`、全局 FirstPlayerController、Pawn-owned whole HUD、blank widget universal modal blocker、GameplayMessage 替代复制。Epic 当前 UE5.8 CommonUI 文档仍维护 input routing；CommonUI+EnhancedInput 当前官方页仍带 Experimental/shipping caution，因此升级或发行前必须重新核对插件成熟度。

完整分析见 [XistCommonGameSample 蒸馏](project-distillations/xist-common-game-sample.md)。通用 UI 规则进入 `skillforge-ui-design/references/commonui-input-routing-patterns.md`；LGF 映射补入 `ui-platform.md` 与外部项目迁移参考。新增 UI-05..09、CPP-50..51、LGF-36 行为样本。


## 2026-09-14 GitHub 项目蒸馏：unreal-combee

第十轮固定 `nulla-sutra/unreal-combee@971fa227179a99d308956b7031d5422634cefbfd`（MPL-2.0，2026-06-30）。仓库维护时间属于 Current，但 `Combee.uplugin` 明确 `IsExperimentalVersion=true` 且未固定 EngineVersion，因此分类为 `Current source / Experimental adoption`，不把“项目新”直接等价成“目标 UE5.7/5.8 production-ready”。

重点源码：Container/FastArray、Item/Fragment、Unique/Shared/Link presets、registered subobject helper、Transaction/Bridge、Move/Swap/Assign/Eject、Snapshot。新增 active-code evidence 检查后发现多个 README 宣称不能直接晋级：Hive 的 `FIrisFastArraySerializer` 路径被 `#if 0` 关闭；rollback 代码被注释；FRWLock 只有 writer lock 证据；subobject remove helper 没找到 active caller；Snapshot active apply 不能重建清空后的 item graph。

本轮采纳：stable ItemId 与 runtime cell/version 分离、Link slot 按 stable identity 重解、FastArray canonical commit + frame-coalesced UI projection、registered subobject 对称 transfer、server-owned operation registry、container capability、transaction before-image/write-set、child mutation result gate、GameThread UObject truth、versioned snapshot graph。明确拒绝：client-selected TransactionClass/RemoteClass+FuncName server dispatch、failure bubble 代替 rollback、global current play world、writer-only lock 代替 thread safety、class path + JSON 代替完整 Save identity。

完整分析见 [unreal-combee 蒸馏](project-distillations/unreal-combee.md)。通用规则进入 `skillforge-ue-cpp/references/container-transactions-and-subobjects.md`；LGF 映射进入 `skillforge-lgf/references/container-transaction-contracts.md` 并补 `external-project-patterns.md`。新增 CPP-52..59 与 LGF-37..40 行为样本。


## 2026-09-14 GitHub/官方项目蒸馏：MassSample + Epic UE5.8 Mass

第十一轮首先纠正来源：`getnamo/MassCommunitySample@1487f0208873acda6fedcfe58a4b1a2f3268192a` 是脱离 upstream 的历史快照，README 主体仍带 UE5.1-era API；当前主样本改为 `Megafunk/MassSample@ca9825861f35ab4f8e152351de2adb893b51ca70`，该 upstream 于 2026-06-27 明确更新到 UE5.8。旧 fork 只保留为 API 演化证据。

当前 Epic UE5.8 资料显示 MassEntity 在 5.8 有明显架构演化：Signals 进入核心、支持 off-thread entity creation、processor scheduling/dependency resolution 重构，并出现简化 QueryExecutor 方向；因此旧 `ConfigureQueries()/ForEachEntityChunk` 教程只能作为语义参考，具体调用必须以目标引擎源码为准。与此同时 MassGameplay、MassAI、MassCrowd、ZoneGraph 仍需按 Experimental feature 逐项 gate，不能因为属于 Epic 插件就默认生产可用。

本轮采纳：archetype/chunk 数据布局、fragment 热冷分层、query access 作为并发合同、Signal 只做 wakeup、Simulation/Representation/Replication 三轴 LOD、StableAgentId 与 transient Mass handle 分离、Mass↔Actor promotion/demotion transaction、server-to-client MassReplication projection、ZoneGraph/SmartObject/StateTree 职责分离、Mass Debugger/Insights 先测后迁。LGF 映射明确：Mass 是低成本模拟层，不替代 Foundation/GAS/Mover/GASP；近战/高交互实体 promotion 为完整 LGF Avatar，CombatOwner 保持 Authority damage truth；宠物/坐骑在骑乘前 promotion，卸载后可 demote。

完整分析见 [MassSample + Epic UE5.8 Mass 蒸馏](project-distillations/masssample-modern-mass.md)。通用规则进入 `skillforge-ue-cpp/references/mass-data-oriented-ai-patterns.md`；LGF 映射进入 `skillforge-lgf/references/mass-ai-scaling.md`。新增 CPP-60..67、LGF-41..44 行为样本。未执行真实 UE5.7/5.8 UBT、PIE、Dedicated Server、MassReplication/JIP 或大规模性能基准。

## 2026-09-14 第十二轮：StateTree + Utility AI

研究主证据改为 Epic UE5.8 StateTree 当前文档/API；`bohdon/UtilityAIPlugin@0f49e0c6d420497d3102c3975601360dc120bf15` 只作为 Utility scoring、hysteresis、tag filter、debugger 的机制对照。StateTree 当前已支持 Highest Utility / Weighted Utility child selector，但 `FStateTreeConsiderationBase` API 仍标 Experimental，因此 SkillForge 要求 game-owned pure scorer + target-version StateTree adapter，不把实验节点类型固化到 Foundation public ABI。

关键收敛：一个 Agent/Avatar 同时只有一个 high-level Decision Owner；默认 StateTree 负责状态、transition 和 utility sibling selection，scorer 只读 `DecisionContext` 并返回 score/reason；GAS/Mover/SmartObject 负责执行；Authority 决定 Cost、Cooldown、Damage、Loot 与 Inventory。StateTree active path 的 Tasks 不是 BehaviorTree Sequence，必须显式定义 ANY/ALL completion、cancel/exit cleanup 与 `DecisionGeneration` 迟到回调拒绝。

大规模 Agent 不采用每个 AI 固定 0.025 秒全 Action 扫描。Mass Agent 走 signal/event/dirty bucket + LOD decision budget；promotion 到完整 LGF Avatar 时保存 Stable DecisionState/intent/target/cooldown/player command，重建 StateTree runtime，不序列化内部 execution frame。宠物/坐骑由 PlayerCommand 层覆盖 autonomous utility，避免自动 AI 与骑乘输入抢 Mover。

完整证据与迁移结论见 `docs/project-distillations/statetree-utility-ai.md`、`skills/skillforge-ue-cpp/references/statetree-utility-ai-patterns.md`、`skills/skillforge-lgf/references/ai-decision-orchestration.md`。


## 2026-09-14 第十三轮：MothCocoon/FlowGraph

第十三轮固定最新设计 `MothCocoon/FlowGraph@c616a5d2afa8124cb7c1d66b1071fd499f2be7db`（MIT，2026-08-31），同时识别出当前 `5.x` 已处在 Flow 2.4 / UE5.9 方向，因此为 LGF UE5.7 额外固定 `v2.3-5.7@8211b25999068407cb7b40b8c97e18b52d4832ca` 作为 target-compatible anchor。以后维护活跃的 UE 插件也要同时核对 latest branch 与目标引擎 release/tag，不能把 `5.x` 当作同一 API。

本轮重点源码：`UFlowAsset` template/runtime instance、`UFlowNode` lifecycle/NodeGuid/SaveGame state、`UFlowSubsystem` root/subflow registry 与 deferred trigger flush、`UFlowNode_SubGraph` ownership/preload/load、`UFlowComponent` IdentityTag/Notify replication/RootFlow、FlowSave structs、SignalMode patch compatibility、2.3/2.4 release migration notes。最新源码的 SubGraph 仍存在 active `LoadSynchronous()` 路径，证明 soft reference/preload framework 存在不等于 runtime async 已完成。

采纳机制：template/runtime split、latent node source-owned lifecycle、Keep/Abort finish policy、deferred transition/execution gate、parent-owned SubGraph、NodeStableId Save ABI、PassThrough/tombstone patch、分层 Save hooks、runtime debugger/editor validation。LGF 强化：StableOwnerId/QuestInstanceId、SchemaVersion/GraphDefinitionVersion、typed domain command、reward idempotency ledger、Authority durable snapshot + event delta/JIP、active-world staging restore、historical save fixtures、Mass/StateTree/Flow/GAS ownership separation。

完整分析见 [FlowGraph 蒸馏](project-distillations/flowgraph.md)。通用规则进入 `skillforge-ue-cpp/references/flow-graph-runtime-patterns.md`；LGF 映射进入 `skillforge-lgf/references/quest-world-flow-orchestration.md`。新增 CPP-76..83、LGF-49..53 行为样本。未执行 FlowGraph UE5.7/5.9 UBT、PIE/Dedicated/JIP、历史 Save runtime migration 或大规模 graph benchmark。


## 2026-09-14 — R14 SimpleQuest

- 固定 `TheGeebus/SimpleQuest@46978ad2c81ba90f21836e7c468141523dedb95d`；对应 tree `daf658bd6c86f54ca024d76e58a9a81908635617`。
- 0.8.1 / UE5.6–5.8 / MIT，Current-to-target。
- 新证据：authoring graph -> compiled runtime；ObjectiveGuid/ContentGuid；Manager sole writer / StateSubsystem read side；domain-shaped versioned snapshot；deferred activations；late observer catch-up；named outcomes + PathIdentity；scoped advancement hold；Dedicated/client mirror。
- 新长期规则写入 UE C++ `quest-objective-runtime-patterns.md` 与 LGF `quest-objective-contracts.md`。


## 2026-09-14 GenericGraph 第十六轮研究

固定 `jinyuliao/GenericGraph@f9b8fe3de6bc2ef39ee771658ac4a8bf48c2e078`（tree `373cc9d89894a05b8204714370fd7972c87b3387`，MIT，2023-07-15）。默认分支最后明确的引擎迁移只到 UE5.1，README 仍写 UE4，因此分类为 `Historical architecture sample`，不作为 UE5.7/5.8 Editor API 权威。研究时另以 UE5.8 当前官方 API 校准 `UAssetDefinition`、ToolMenus、UEdGraph/UEdGraphSchema 等现代入口。

本轮源码级发现：

- Runtime/Editor 两模块与 extensible Graph/Node/Edge、Schema、explicit edge、custom editor 的总体方向仍可吸收；
- Runtime 没有显式 Node/Edge stable identity，拓扑主要靠 UObject pointer、数组和 `TMap<ChildNode, Edge>`；
- `TMap<ChildNode, Edge>` 天然限制同一 Start→End 的平行语义边；
- `RebuildGenericGraph()` 先 Clear 当前 runtime topology，再就地重建，没有 staging / atomic publish / last-known-good；
- `SaveAsset_Execute()` 以保存副作用触发 rebuild，没有 source/compiled fingerprint/revision；
- Schema 的 cycle/self/cardinality/node hooks 是很好的 early feedback，但 compiler/cook 应重新全图验证；
- `bCanBeCyclical` 只控制 Editor 连线，runtime `Print/GetLevelNum/GetNodesByLevel` 无 visited；rootless SCC 也会被 RootNodes 模型遗漏；
- 2023 修复只证明 editor sorting 的 cycle traversal 增加 visited，不能外推到 runtime/layout 全部 cycle-safe；
- TreeLayout/AutoLayout 多处递归/层级遍历没有 cycle guard；ForceDirected 有 O(N²) repulsion、无 cycle-safe attractive traversal，并存在固定源码坐标轴混用风险；
- context menu 每次 `TObjectIterator<UClass>` 扫描派生节点类型，不适合大型项目热路径；
- Runtime Build.cs 仍依赖 Slate/SlateCore，Editor public dependency 含 UnrealEd，现代 Foundation 应收紧模块边界；
- Legacy `FAssetTypeActions_Base` 在当前 UE 仍可能存在，但 UE5.8 官方 `UAssetDefinition` 已是 replacement direction，新代码不能把 legacy API 固化成 Foundation ABI。

SkillForge 正式新增：

- UE C++ `generic-graph-authoring-patterns.md`；
- LGF `graph-authoring-foundation.md`；
- CPP-102..109；
- LGF-64..68。

RED 基线针对 13 个新合同为 13/13 缺失；GREEN 同一 probe 为 13/13 命中。最终运行验证状态记录在本轮 validation report。

## 2026-09-15 GitHub 项目蒸馏：TodayYueC/ChronicleEngine（R17）

固定 `TodayYueC/ChronicleEngine@b2fb37b14b7537c30d6ebf16cf612671bd0286e9`（MIT，2026-04-30）。源码虽新，但 host 主基线仍为 UE5.3、HEAD 插件为 `0.12.0-dev` Beta、UE5.7 只有作者 smoke 证据，active Editor 仍使用 `FAssetTypeActions_Base`，因此针对 LGF UE5.7/未来5.8 采用门分类为 `Stable-but-old`，而不是 Current production template。Epic UE5.8 当前资料用于校准 `UAssetDefinition`、registered subobject/Iris 与 FText localization identity。

R17 最重要的新证据是 Chronicle 的 Editor Graph 为从 `UDialogueTree` 重建的 transient projection，说明 R16 的“职责分离”不应被机械实现成所有 Domain 都保存 AuthoringGraph + CompiledGraph 两份资产。正式规则改为：复杂 lowering/优化域继续 compiled artifact；语义同构域可使用 canonical semantic definition + transient editor projection，但 stable Node/Edge/Choice ID、whole-definition validation、version/migration、cook stripping、derived caches 与 live revision fence仍全部保留。

Runtime 还暴露两个此前正式规则未明确覆盖的问题：其 Save cursor 未覆盖 SubDialogue return stack / pending async wait 等 continuation；异步完成只靠 EventTag 缺少 operation identity。R17 新增 ContinuationFrames/PendingAwait 与 AwaitId/ExecutionGeneration 合同。Condition evaluator 的 parsed AST cache 值得保留，但 runner 的最终 bool cache 可读取 external getter，却主要由 runner 自身变量写入触发清理；因此新增 compiled-expression cache 与 dependency-revisioned result cache 分离规则。

未发现 `UPROPERTY(Replicated...)`、Server RPC、`OnRep_`、`HasAuthority` 或 FastArray active path，所以 Chronicle 不作为多人 Authority/JIP 证据；R15 既有 Conversation Authority/JIP 合同保持。完整证据与拒绝照搬清单见 [ChronicleEngine 蒸馏](project-distillations/chronicleengine.md)。

## 2026-09-15 — R17.1 ChronicleEngine hardening

R17.1 不新增外部项目，只复查 R17 与 `TodayYueC/ChronicleEngine@b2fb37b14b7537c30d6ebf16cf612671bd0286e9` 的漏项和 Skill 内部一致性。

两项源码反例补入正式合同：第一，`UDialogueTree::PostLoad()/EnsureStableGuids()` 在 durable GUID 缺失时会 `FGuid::NewGuid()`，这只能视为方便 authoring 的实现，不可作为已发布 Save/Network identity 的 Runtime repair；生产流程必须在 Editor/commandlet/deterministic migration 阶段生成/映射并 resave，Shipping/Dedicated 不能随机自愈。第二，`UVariableBank` 只有一份 `LocalVariables`，nested SubDialogue return frame 也没有 per-call local scope；因此 nested dialogue 的 locals 应是 continuation call-frame state，并进入 Save/JIP active scope stack。

同时修复 R17 之后仍残留的文本冲突：`dialogue-runtime-patterns.md` 与 LGF Dialogue 不再把 `Authoring UEdGraph -> compiled runtime artifact` 写成所有 Domain 唯一路径。统一合同为：Runtime 永不依赖 `UEdGraph`；语义同构时可使用 canonical semantic definition + transient editor projection，需要 lowering/压缩/cook stripping/ABI 隔离时使用独立 compiled artifact。

评测方法也收紧：R17 的 0/7→7/7 被明确保留为 semantic Reference coverage，不冒充模型 Behavior Eval。R17.1 新增 CPP-114、CPP-115、LGF-72，并完成 0/3→3/3 的 semantic RED/GREEN；但当前 ChatGPT artifact harness 没有 fresh-context subagent/model runner，因此 CPP-110..115 / LGF-69..72 的真实 raw-answer Behavior RED/GREEN 仍标记 `pending / 未证明`，已生成可复现 packet 留待 Codex/Agent 环境执行。
