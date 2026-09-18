---
name: skillforge-ue-cpp
description: "编写、修改和审查 Unreal Engine 5 C++，涵盖 UObject 反射、所有权、生命周期、模块依赖及蓝图接口。Use when UE C++ work involves UCLASS, UPROPERTY, UFUNCTION, delegates, async callbacks or Build.cs. 普通 C++、MFC 和纯蓝图布局不触发。"
---

# UE C++ 基础开发

以当前工程的源码、版本和目标为依据，保持改动范围与任务一致。跨模块接口、对象生命周期与蓝图调用方共同构成完成条件。

## 工程定位

先读取当前项目的说明、`.uproject`、相关 `.uplugin`、`Build.cs` 和实际 `Target.cs`；将 EngineAssociation 对应到真实引擎，必要时查看 `Engine/Build/Build.version`。确认模块类型、目标平台、构建配置和可用工具，再给命令或选择 API。

已能从工程确定的值不再问用户。版本未知且会影响接口选择时，说明需要的具体证据；先推进不依赖该差异的部分。旧项目路径、目标名、DebugGame 配置和网络拓扑都不是默认值。

## 根据改动检查

- **声明与接口**：检查反射宏、参数类型、`GENERATED_BODY()`、对应 `.generated.h` 且它是该头文件最后一个 include；跨模块类型和函数需要合适的 API 导出。先看既有公开接口，再决定是否扩展。
- **对象与状态**：明确谁拥有对象、谁只是观察、谁发起与结束一次操作。`UPROPERTY` 跟踪的成员强引用、弱引用和资源路径解决不同问题；指针类型不能代替线程与业务有效性检查。
- **生命周期**：订阅、timer、异步请求、输入句柄与其拥有者的结束路径配对。取消后仍考虑已排队回调；在实际使用对象的位置重新验证，并拒绝旧请求覆盖新状态。
- **模块边界**：由所用类型和符号定位依赖模块，区分 Public/Private 依赖以及 Runtime/Editor 边界。不要通过添加大量无关依赖掩盖包含或导出错误。
- **蓝图契约**：操作、查询、事件与异步结果各有明确语义。检查空值、失败结果、对象上下文与调用成本；仅在任务涉及多人状态时加入权限、复制或 RPC 检查。

遇到具体错误可以结合排障方法，但不以“C++ 修改”为由对整个项目做全面重构。

## 按需参考

- UObject、回调、委托或切关：读 [所有权与生命周期](references/ownership-lifecycle.md)。
- 反射、跨模块接口、蓝图暴露、构建：读 [反射与构建](references/reflection-build.md)。
- 迁移历史经验或需要回归场景：读 [案例与核验](references/cases.md)。
- 联网 Gameplay、复制 UObject、FastArray、数据驱动 Spawn、存档、对象池或高频系统：读 [Gameplay 运行时架构审查](references/runtime-gameplay-patterns.md)。
- 完整 Gameplay Framework 组合、PlayerState/Pawn 长短生命周期、AbilitySet 可逆授予、客户端 mutation RPC、InputTag 热路径或 AI Director：读 [Gameplay Framework 组合与生命周期模式](references/framework-composition-patterns.md)。
- Pawn+Mover、CMC SavedMove 迁移、预测重演、GASP/PoseSearch、Traversal、Layered Root Motion、Linked Anim Layer、Push Model/Iris、URO/SimulatedProxy、PhysicsControl/Ragdoll 或 GameplayCamera：读 [Mover、动画与网络模式](references/mover-animation-network-patterns.md)。
- GAS LocalPredicted、PredictionKey/Scoped Prediction Window、TargetData、AbilityTask、SourceObject/SpecHandle、Ability RPC batching、动态 AttributeSet、EffectContext 或预测 Montage 回滚：读 [GAS 预测、TargetData 与能力生命周期](references/gas-prediction-targetdata-patterns.md)。
- 从 GitHub/Epic Sample 吸收外部架构、判断旧项目是否过时、研究 Lyra/ModularGameplay/InitState/Experience/GameFeatures/Input/Inventory-Equipment 生命周期：读 [外部项目时效性门与现代 Lyra 模式](references/external-project-freshness-and-lyra.md)。
- ARPG 物品 Definition/Instance、Struct-first/ItemState、stable handle、Grid Inventory、Equipment/Stash、随机词缀、GAS 装备授予或物品存档：先读 [ARPG 物品与容器架构](references/arpg-item-inventory-patterns.md)；大规模 value semantics、generation handle、MutationKey、嵌套容器和事务再读 [物品值语义、稳定句柄与容器事务](references/item-value-semantics-and-transactions.md)。
- 跨 Inventory/Equipment/Stash 的 Authority transaction、container capability、server operation allowlist、replicated Item subobject transfer、frame-coalesced FastArray projection、线程所有权或版本化 snapshot rebuild：读 [Container Transaction、FastArray 与 Replicated Subobject 生产合同](references/container-transactions-and-subobjects.md)。
- 大规模 NPC/群体模拟、MassEntity/MassGameplay、Processor/Query、Signal、Simulation/Representation/Replication LOD、MassReplication、ZoneGraph、SmartObject 或 Mass StateTree：读 [MassEntity / MassGameplay 数据导向 AI 与大规模实体合同](references/mass-data-oriented-ai-patterns.md)。
- StateTree、Utility Selector/Consideration、Utility AI 评分、AI 决策切换迟滞、Task Completion、StateTree+GAS、StateTree+Mass 或决策调试：读 [StateTree / Utility AI 决策与执行合同](references/statetree-utility-ai-patterns.md)。
- 任务/剧情/世界事件 Graph、Flow Node 异步生命周期、SubGraph、Deferred Transition、Graph Save ABI、JIP/多人通知或 FlowGraph 版本迁移：读 [Flow Graph / Quest / World Event 运行时合同](references/flow-graph-runtime-patterns.md)。
- Quest Objective、Quest Step/Outcome、编译后运行时定义、Quest Manager/State CQRS、late-registration catch-up、advancement hold、Quest snapshot 或 Dedicated/JIP quest mirror：读 [Quest / Objective 运行时合同](references/quest-objective-runtime-patterns.md)。
- Dialogue/Conversation、Participant role、Node/Choice stable identity、对话条件/事件、Localization、Save/Resume、多人 Authority/JIP 或 Dialogue 与 Quest/StateTree/GAS/Inventory 边界：读 [Dialogue / Conversation 运行时合同](references/dialogue-runtime-patterns.md)。
- 自定义 UEdGraph/UEdGraphSchema、Graph/Node/Edge stable identity、authoring→compiled runtime artifact、cycle/SCC、parallel edge、Graph compiler、现代 AssetDefinition/ToolMenus、auto-layout 或大型 Graph 编辑器性能：读 [自定义 Graph Authoring / Compiler / Runtime 合同](references/generic-graph-authoring-patterns.md)。

## 验证与交付

涉及构建或构建验证方案时，交付三个具体信息：**目标来源**（要读取哪个当前工程的 `Target.cs` 或已验证构建入口）、**目标/平台/配置**（尚未取得时列出缺少的证据）、**执行状态**（实际命令和结果，或尚未执行）。这样即使本轮只分析生命周期问题，也能让下一位执行者确定验证目标，而不是留下“按实际目标编译”的空泛结论。

从上述证据和真实引擎位置生成命令。反射声明变化需要正常 UHT/构建及受影响蓝图的编译、节点与调用检查，不能只用 Live Coding 结果代替。

按变更选择运行验证：异步生命周期覆盖关闭、重开、切关和过期请求；模块边界覆盖实际需要的目标；联网行为才验证相关网络角色。报告实际改动、证据、已运行的命令及结果，分别标记未做的编译、编辑器或运行检查。

复制注册/FastArray、异步生命周期、接口与构建审查见 [复制审查补充](references/replication-review.md)。
