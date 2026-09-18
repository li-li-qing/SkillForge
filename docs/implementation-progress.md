# 第一版实施记录

依据：用户确认的“SkillForge 第一版：跨 Agent 基础技能库”。

- [x] 检查现有仓库与资料；保留独立工作树及其未完成内容。
- [x] 在当前目录建立 `codex/skillforge-foundations` 分支。
- [x] 排障：基线、正文、参考、用例、前向验证。两例均保持正确；已独立复制校验，不宣称改善。
- [x] UE C++：基线、正文、参考、用例、前向验证；完成独立复制与内容审查。声明检查覆盖增加；CPP-01 定向复查和独立评分已记录。
- [x] 蓝图：基线、正文、参考、用例、前向验证；独立复制校验通过。源码语义与实际资产操作的验证层级分别记录。
- [x] UI：基线、正文、参考、用例、前向验证；独立复制校验通过。完成最终内容审查，实际界面验证未执行。
- [x] GitHub 来源与项目经验记录；公开来源固定提交，本机资料固定 SHA-256，候选与已核验机制分开。
- [x] 独立复制、结构、触发、组合与最终审查。28 项校验器测试、4 包复制通过；24 个触发标签与 5 个组合集合符合期望，正文组合另有非盲文本检查。

实施决定：四个新技能在当前工作目录交付，不操作现有 `feature/skillforge-v1` 工作树；其内容不属于本次基线。验证依赖与临时输出使用被忽略的临时目录。初版取材时保留了三个被本地 Git exclude 排除的原资料目录，后续清理按用户最新要求执行，见下文。

审查修正：校验器已补上 YAML 非字符串名称与单段绝对 POSIX 路径的负例，保留 UE 虚拟资产根路径；两个问题均有失败复现和修复后通过记录。C++ 技能根据首次前向回答补充明确的构建目标来源、配置和执行状态要求，并单独复查 CPP-01，原始评测回答保持不变。

结果及限制集中记录于 [第一版验证报告](../evals/runs/2026-09-12/summary.md)。真实工程编译、编辑器/界面运行与其他 Agent 的安装适配未执行，不属于本次结构和文本验证的通过声明。

目录清理：按用户后续要求，删除已取材的 `Advanced_UI_Layout_Skill_v4`、`lgf-ue5-devkit`、`replicated-suite-maintenance` 三个旧目录及本轮生成的 Python 缓存；移除对应的本机 Git exclude 条目，补充 README 目录导航。来源记录与正式评测证据继续保留。另一工作树仍有未提交的 router 技能和测试，不作为旧资料删除。


## 2026-09-14 外部 UE 项目蒸馏启动

- [x] 第一项目：`tomlooman/ActionRoguelike@a3f9a182c985b1732d9f72ae8b92e4845babfa3f`，按 Action/Network/AI/StateTree/Asset/Save/Performance/FastArray/UI 分模块源码审查。
- [x] 新增项目级完整报告，不复制第三方源码。
- [x] UE C++ 技能补入 replicated subobject、Authority revalidation、PrimaryAsset async pipeline、SaveGame、pool/deferred/hot-cold/FastArray 生产边界。
- [x] LGF 技能补入外部项目二次映射规则，明确 GAS/Request/Authority/FastArray 的拒绝照搬项。
- [x] 新增 CPP-03..07、LGF-16 定向行为样本。
- [ ] 真实 UE 5.7.4 编译、PIE 网络和性能基准未在本轮执行；本轮结论为源码/技能层验证。

## 2026-09-14 外部 UE 项目蒸馏第二轮

- [x] 第二项目：`intrxx/Obsidian@bbe55b5b4c0ae4761ab57868398aca1c3b6b8c0b`，按 Item model / Inventory / Equipment / Stash / GAS grants / Loot / Save / UI message / Network 分模块源码审查。
- [x] 记录 GPL-3.0 许可边界，不复制第三方实现。
- [x] UE C++ 技能新增 ARPG 物品与容器架构参考。
- [x] LGF 外部项目迁移参考新增 Obsidian 映射与拒绝照搬项。
- [x] 新增 CPP-08..11、LGF-17 定向行为样本。
- [ ] 未构建 Obsidian 公开仓库，未执行 UE PIE/Dedicated/JIP/带宽/大库存性能基准；源码与 Skill 结论不能替代运行验证。

## 2026-09-14 外部 UE 项目蒸馏第六轮

- [x] 第六项目：`Sixze/ALS-Refactored@b754d6f0f2bb03741d301f8fb88077ebfe561e17`，按 CMC prediction / Push Model / Iris / SimulatedProxy / view smoothing / threaded animation / Linked Anim / RootMotionSource mantle / moving base / URO / camera 分模块源码审查。
- [x] 记录 README 4.17/UE5.7 与当前 `.uplugin` 4.18/UE5.8 的版本证据差异。
- [x] 不移植 CMC 主链；把 SavedMove/NetworkMoveData 语义翻译到现有 Pawn+Mover replay contract。
- [x] UE C++ Mover/动画网络参考补入 Push Model+Iris、View/Visual smoothing、URO role matrix、Property Access write phase、moving-base movement transaction。
- [x] LGF GASP/Mover 与外部项目映射补入 ALS-R selective migration 与 Camera single-owner 规则。
- [x] Blueprint Linked Anim Layer 参考补入 Property Access write-phase 和 GameplayTag pose router 边界。
- [x] 新增 CPP-30..35、LGF-23..24、BP-04 行为样本。
- [ ] 未在 UE5.8 构建 ALS-R，也未在 LGF UE5.7 实际迁移；未执行 PIE/Dedicated/Iris/URO/foot-lock 性能实测。本轮结论为固定源码快照与 Skill 文本层验证。

## 2026-09-14 外部 UE 项目蒸馏第七轮

- [x] 以用户最新 `SkillForge(1).zip` 为新基线，保留 Codex 根据实际 LGF 项目加入的 `multi-blade-combo-validation.md`、LGF-25..27 与收纳/手持路径规则。
- [x] 固定 `tranek/GASDocumentation@8f76c5780bdea69e0ea2cc161ab2f435f04182eb` 与 `tranek/GASShooter@26295c548a19f221917e4a7232c12e763db64cb1`。
- [x] 分开标记 UE5.3 社区文档与 UE4-era Shooter 实现，旧 API 只作为历史机制证据。
- [x] UE C++ 新增 GAS prediction / TargetData / AbilityTask / SourceObject / batching / EffectContext 生产参考。
- [x] LGF 新增 GAS 战斗预测参考，并与实际多刀刃 HitWindow/Sequence/装备 lifecycle 合并。
- [x] 新增 CPP-36..42、LGF-28..31 行为样本。
- [ ] 未在 UE5.7/5.8 构建 GASShooter；未执行 LGF PIE/Dedicated/high-latency GAS 网络验收。具体 GAS API 在项目实施前仍需对当前 Engine source 复核。


## 2026-09-14 外部 UE 项目蒸馏第八轮

- [x] 将用户新增要求“旧 GitHub 项目需要技术革新判断”固化成 Current / Stable-but-old / Historical / Reject 四级时效性门。
- [x] 以 Epic 当前 UE5.8 Lyra 文档作为主现代性证据，明确 5.0 Pawn init 为 Historical、5.1+ Init State 为当前可迁移机制。
- [x] 固定 `XistGG/XistCommonGameSample@7e01e1fed344a741f80fa82b7161c86c494a410b` 作为 UE5.7 CommonUI/EnhancedInput 次级对照，不把单机样例外推到多人 Authority。
- [x] UE C++ 新增外部项目时效性门与 Lyra 现代模式参考。
- [x] LGF 新增 Lyra readiness/Experience/PawnData/Inventory-Equipment 选择性映射，不替换 Foundation/GASP-Mover/GameplayCamera。
- [x] 新增 CPP-43..49、LGF-32..35 行为样本。
- [ ] 未在 LGF UE5.7 实际实现 InitState adapter；未执行 GameFeatures packaged build、feature unload、Listen/Remote/JIP 或 Avatar race injection。本轮为研究/Skill 合同层验证。

## 2026-09-14 外部 UE 项目蒸馏第九轮

- [x] 固定 `XistGG/XistCommonGameSample@7e01e1fed344a741f80fa82b7161c86c494a410b`，MIT，UE5.7。
- [x] 按技术时效性门标记为 LGF 5.7 Current-to-target / UE5.8+ Stable-but-old，并核对 Epic 当前 CommonUI 5.8 文档。
- [x] 蒸馏 LocalPlayer Root Layout、GameplayTag Layer、Activatable input config、InputAction->InputTag、source-owned IMC、UI Action handle、GameplayMessageRouter。
- [x] 拒绝把单机样例的 ClearAllMappings、FirstPlayerController、Pawn-owned whole HUD、blank blocker 外推到复杂多人 ARPG。
- [x] UI skill 新增 CommonUI/Input Routing 专项参考；LGF UI 平台与 UE C++ Framework 组合参考补充 LocalPlayer/Input ownership。
- [x] 新增 UI-05..09、CPP-50..51、LGF-36 行为样本。
- [ ] 未在 LGF UE5.7 Editor/PIE 实施 CommonUI Presenter adapter，未做 split-screen、Travel、Dedicated Server 或 packaged build。本轮仍是研究/Skill 合同层验证。


## 2026-09-14 外部 UE 项目蒸馏第十轮

- [x] 固定 `nulla-sutra/unreal-combee@971fa227179a99d308956b7031d5422634cefbfd`，MPL-2.0，2026-06-30。
- [x] 按时效性门分类为 Current source / Experimental adoption；descriptor 明确 Experimental，无固定 EngineVersion。
- [x] 审查 Container/FastArray、Unique/Shared/Link、Fragment Rna、registered subobjects、Transaction/Bridge、Move/Swap/Assign/Eject、Snapshot。
- [x] 新增 active-code evidence 层：README/依赖/header 不替代 compiled/runtime-active/verified 证据。
- [x] UE C++ 新增 Container Transaction / Subobject 专项参考。
- [x] LGF 新增 container capability、operation allowlist、Link ItemId、atomic write-set、subobject transfer/reconnect 合同。
- [x] 新增 CPP-52..59、LGF-37..40 行为样本。
- [ ] 未构建 Combee，也未执行 UE5.7/5.8 PIE、Dedicated Server、Iris、JIP、reconnect、packet loss、GC/Net Insights 或大库存 benchmark；Experimental 状态不能升级为 production 认证。


## 2026-09-14 外部 UE 项目蒸馏第十一轮

- [x] 先审 `getnamo/MassCommunitySample`，识别为脱离 upstream 的 UE5.1-era 历史快照，不作为当前 API 主证据。
- [x] 固定当前 upstream `Megafunk/MassSample@ca9825861f35ab4f8e152351de2adb893b51ca70`（MIT，2026-06-27，提交明确面向 5.8），并用 Epic UE5.8 当前资料校准。
- [x] 区分 MassEntity core 与仍需 Experimental feature gate 的 MassGameplay / MassAI / MassCrowd / ZoneGraph。
- [x] UE C++ 新增 Mass data-oriented AI 专项参考：archetype/fragment/query/threading/signals/LOD/replication/representation/debugger。
- [x] LGF 新增 Mass AI scaling 参考：StableAgentId、Mass↔Actor promotion/demotion、CombatOwner、pet/mount hybrid、StateTree/ZoneGraph/SmartObject 分工。
- [x] 新增 CPP-60..67、LGF-41..44 行为样本。
- [ ] 未在 LGF UE5.7/5.8 构建 Mass adapter；未执行 PIE/Dedicated/JIP/packet loss/Mass Debugger 基准或 1k/10k/50k entity 性能测量。本轮为 current-source + Skill 合同层验证。

## 2026-09-14 R12 StateTree / Utility AI 蒸馏

- [x] 固定 Epic UE5.8 StateTree 为当前主证据，UtilityAIPlugin 为 Stable-but-old 机制样本。
- [x] RED：CPP-68..75、LGF-45..48；确认 R11 正式参考缺少 12 个决策合同。
- [x] 新增 UE C++ StateTree / Utility AI 生产参考。
- [x] 新增 LGF AI Decision Orchestration 参考。
- [x] 建立单一 high-level Decision Owner、DecisionContext、DecisionIntent、DecisionGeneration 合同。
- [x] 建立 utility purity、归一化、hysteresis/minimum-dwell/cooldown、debug score breakdown 合同。
- [x] 建立 StateTree active-path Tasks ANY/ALL completion 与异步取消/迟到回调拒绝合同。
- [x] 建立 StateTree -> GAS/Mover/SmartObject 执行分层，不让 selector/consideration 产生 Authority side effect。
- [x] 建立 Mass low-fidelity decision budget 与 promotion/demotion decision continuity。
- [x] 建立 pet/mount PlayerCommand 高于 autonomous utility 的优先级。
- [ ] 在真实 LGF UE5.7 工程实现 StateTree adapter 并 UBT/PIE 验证。
- [ ] 升级 UE5.8 时单独验证原生 Utility Consideration API，再决定是否替换 5.7 adapter。
- [ ] 进行 Dedicated Server、GAS cancellation、promotion/demotion、1k/10k Agent 决策性能验收。


## 2026-09-14 R13 FlowGraph 蒸馏

- [x] 固定 latest `MothCocoon/FlowGraph@c616a5d2afa8124cb7c1d66b1071fd499f2be7db`，MIT，2026-08-31。
- [x] 识别 latest 2.4 已面向 UE5.9，为 LGF UE5.7 单独固定 `v2.3-5.7@8211b25999068407cb7b40b8c97e18b52d4832ca`。
- [x] RED：CPP-76..83、LGF-49..53；确认 R12 正式参考缺少 13 个 Quest/Graph runtime 合同。
- [x] 新增 UE C++ Flow Graph / Quest / World Event runtime 参考。
- [x] 新增 LGF Quest / World Flow orchestration 参考。
- [x] 建立 template asset != runtime instance、Stable Quest identity 与 Node Save ABI。
- [x] 建立 Flow latent node Complete/Abort/Cleanup、Deferred Transition、Execution Gate、SubGraph ownership 合同。
- [x] 建立 target-compatible tag + latest branch 双锚点与 staged serialized-asset migration 规则。
- [x] 建立 Authority durable quest snapshot 与 transient Flow Notify/JIP 投影分离。
- [x] 建立 typed domain command + reward/spawn idempotency，不允许 Graph 绕过 Inventory/GAS/World Authority。
- [x] 建立 FlowGraph / StateTree / Mass / GAS / Mover 的职责边界，并覆盖 absorb/transform/mount 的 stable owner 需求。
- [ ] 未在真实 LGF UE5.7 工程接入 FlowGraph v2.3-5.7；未执行 UBT、PIE、Dedicated Server、JIP、packet loss、in-game load 或历史 Save migration runtime 验收。
- [ ] 若未来接入，必须先做 LGFQuestFlowAdapter、Stable Quest ID/version wrapper、async dependency policy 与 historical save fixtures。


## R14 — SimpleQuest Quest Domain Distillation（2026-09-14）

- 新增 CPP-84..CPP-92、LGF-54..LGF-58。
- 新增 Quest/Objective runtime 与 LGF Quest domain 两份专项 reference。
- 保持 R13 FlowGraph 通用编排合同不变；R14 只补 Quest domain state/objective/read-model/hold/save/network。
- 未宣称实际 LGF Quest runtime 已实现；本轮仅 Skills/Architecture 蒸馏。


## 2026-09-14 外部 UE 项目蒸馏第十六轮

- [x] 固定 `jinyuliao/GenericGraph@f9b8fe3de6bc2ef39ee771658ac4a8bf48c2e078` 与 tree/日期/许可；按 UE5.1 历史样本处理，不把高 stars 解释为 5.7/5.8-current。
- [x] 按 Runtime Graph/Node/Edge、Editor EdGraph/Schema、compile/rebuild、asset editor/factory、module deps、auto-layout 分模块阅读源码。
- [x] 用 UE5.8 当前官方 API 校准 AssetDefinition/ToolMenus/EdGraph/Schema，区分“API 仍存在”与“现代默认入口”。
- [x] UE C++ 新增现代 Graph Authoring / Compiler / Runtime 合同：Stable Node/Edge ID、canonical topology、parallel edge、cycle/SCC、compiler staging、structured diagnostics、last-known-good、Editor scalability。
- [x] LGF 新增 Graph Authoring Foundation：共享作者/编译基础，不建立 UniversalGraphRuntime，不改变 Quest/Dialogue/AI/GAS 各自 Authority/Save 真值。
- [x] 新增 CPP-102..109、LGF-64..68 行为用例；RED 13/13 缺失，GREEN 13/13 覆盖。
- [ ] 未执行 GenericGraph 的 UE5.7/5.8 UBT、Editor、Cook、cycle-hang reproduction 或大型图布局 benchmark；不把源码蒸馏写成目标引擎运行通过。

## 2026-09-15 外部 UE 项目蒸馏第十七轮

- [x] 固定 `TodayYueC/ChronicleEngine@b2fb37b14b7537c30d6ebf16cf612671bd0286e9`、commit date、MIT、branch/tag/release、UE5.3 host 与 `0.12.0-dev` Beta descriptor。
- [x] 以 Epic UE5.8 当前 `UAssetDefinition`、UObject replication/Iris、Text Localization 文档校准目标 UE5.7/5.8 技术时效性；最终分类 `Stable-but-old`。
- [x] 完整检查 Runtime/Data/Presentation/Editor/Tests、Save/Load/Rollback、async event、condition cache、soft load、stable identity、localization 与 network evidence。
- [x] RED：在只增加 Behavior Evals、未改正式 Reference 时，同一语义探针 0/7 PASS、7/7 missing。
- [x] GREEN：最小写回既有 Graph/Dialogue References 后，同一语义探针 7/7 PASS。
- [x] 新增 CPP-110..113、LGF-69..71；不重复既有 Choice/Edge identity、Authority/JIP、Localization、Save migration 规则。
- [x] 修正 R16 过度绝对化：Graph Authoring/Runtime 职责分离不强制两份持久化 Graph；允许 canonical semantic definition + transient editor projection。
- [x] 新增 Dialogue ContinuationFrames/PendingAwait、AwaitId/Generation fencing、dependency-revision condition result cache 合同。
- [ ] 未执行 Chronicle UE5.3/5.7/5.8 UBT、Editor/PIE/Dedicated/JIP、Chronicle automation tests、BuildPlugin、Save race reproduction 或 benchmark；本轮不宣称第三方项目 production verified。

## 2026-09-15 R17.1 ChronicleEngine hardening

- [x] 以 R17 `SkillForge_ChronicleEngine_R17.zip` 为唯一修订基线，不重蒸馏 R1～R16。
- [x] 统一 Graph Foundation / Dialogue Runtime / LGF Dialogue 的 projection-first 合同：Runtime 永不依赖 `UEdGraph`，但 Domain 可选择 canonical semantic definition 直接作为 runtime truth，或在需要 lowering/优化/裁剪/ABI 隔离时生成独立 compiled artifact。
- [x] 新增 CPP-114：durable Graph/Node/Edge identity 禁止在 Runtime/PostLoad 通过随机 `FGuid::NewGuid()` 静默修复；缺失 ID 进入 Editor/commandlet/deterministic migration + resave/cook gate。
- [x] 新增 CPP-115：nested Dialogue 的 local variables 属于 per-call semantic scope frame；Save/Load/JIP 需要恢复 active scope/call stack，而不是一份扁平 local map。
- [x] 新增 LGF-72：Authority Conversation 保存 nested local scope stack，Avatar replacement 只重绑 presentation，不销毁 semantic call stack。
- [x] 新 3 case 先写 Eval，再跑 formal-Reference semantic RED：0/3；最小写回 Reference 后同一 coverage probe GREEN：3/3。
- [x] `evals/README.md` 明确：grep/anchor/Reference coverage probe 不得冒充 Behavior Eval；没有 fresh-context runner 时必须标记 pending/未证明。
- [x] 为 CPP-110..115 / LGF-69..72 冻结 fresh-context Behavior Eval packet；当前 ChatGPT artifact harness 没有隔离 subagent/model runner，因此 raw baseline/forward/judgment 均诚实保留为 pending。
- [ ] 在具备 fresh-context Agent/Codex runner 的环境执行上述 10 个 case 的真实 Behavior RED→GREEN，并保存 raw response + post-freeze judgment。
- [ ] ChronicleEngine UE UBT/Editor/PIE/Dedicated/JIP/Save runtime reproduction 仍未执行；R17.1 是 Skill contract hardening，不是第三方 Production certification。
