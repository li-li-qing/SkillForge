---
name: skillforge-lgf
description: "使用、接入、扩展、排查或维护 LGameplayFramework（LGF）插件及其消费工程，包括 Foundation、Request/Authority、背包交互、GAS、GASP/Mover、PSD/PSS、武器动画、UI 路由和项目文档。Use for LGameplayFramework integration and development. 普通 UE C++、CommonUI、GAS 或名为 LGame 的目录不自动触发；先确认实际使用 LGF。"
---

# LGameplayFramework 接入与开发

把用户要做的玩法对应到 LGF 已有模块、真实扩展点和验证路径。用户可以用蓝图或 C++ 接入；语言选择不改变数据所有权。先复用实际能力，需要项目装配的部分明确交代。

## 开始任务

1. 确认 LGF 插件根、消费工程、当前提交/未提交改动与引擎版本。定位实际 `.uproject`、目标文件和配置；目录名不等于 Target 名，缓存里的临时 HostProject 不等于消费工程。
2. 明确本轮是学习/解释、项目接入、故障修复、插件扩展还是文档维护。以用户可见的成功行为确定最短调用链；仅学习或维护技能不顺带改插件源码、资产或架构方案。
3. 从当前 `Docs/README.md`、根 README 和相关 API/Tutorial 章节进入，再核对头文件、实现和依赖。源码说明当前行为，决策说明获准的设计；旧快照和文件名不能替代这两种证据。
4. 将能力标成已实现、需项目配置/扩展、尚在方案或不支持。没有检查资产内部时，不把节点、Widget、GASP 动画或地图写成已存在。

## 按任务读取

| 任务 | 参考 |
|---|---|
| 学习框架、选模块、寻找现有实现与文档 | [项目地图](references/project-map.md) |
| 新项目接入、蓝图门、背包等最小玩法闭环 | [接入路径](references/integration.md) |
| 请求结果、Host/Remote 差异、ActionLock、FastArray、共享仓库 | [网络与状态](references/network-and-state.md) |
| UMG/CommonUI、页面返回、输入锁、HUD、世界空间 UI | [UI 平台](references/ui-platform.md) |
| Character/Pawn、Mover、GAS 就绪、换 Avatar、装备 Mesh 与动画 | [Avatar 与资产](references/avatar-and-assets.md) |
| 测试、文档、迁移、Backlog/WorldMap 决策或未来经验收录 | [验证与演进](references/validation-and-evolution.md) |
| 删除危险蓝图节点、Request 结果接线、API/新手教程审查 | [蓝图接口与教程交接](references/blueprint-api-handoff.md) |
| GASP/Mover/ALS-R 接入、Root Motion、PSD/PSS、网络动画优化与动画源 | [跨层集成](references/gasp-mover-integration.md) |
| 多刀刃命中、连续 Section、续招网络时序与真实伤害验收 | [多刀刃连击](references/multi-blade-combo-validation.md) |
| GAS LocalPredicted、PredictionKey、TargetData、多来源 Ability grant、预测拒绝与多表现层回滚 | [GAS 战斗预测](references/gas-combat-prediction.md) |
| 新武器动画完整实施、生成器审查、人工测试交接 | [动画实施与交付顺序](references/animation-delivery-workflow.md) |
| 双剑延迟、方向错、根与身体周期、持剑重复混合 | [武器动画诊断](references/weapon-animation-diagnostics.md) |
| 切武器卡住、Socket/Trace、owner 漏播、取消不停 | [装备与能力生命周期](references/equipment-ability-lifecycle.md) |
| 旧库迁移、新案例证据与工作区清点工具 | [迁移依据](references/migration-evidence.md) |
| 需要确认某条项目事实来自哪个版本或文件 | [取材依据](references/sources.md) |
| 从 GitHub/外部 UE 项目吸收架构、网络或性能模式 | [外部项目模式迁移](references/external-project-patterns.md) |
| 评估旧 UE 项目技术时效性、吸收 Lyra InitState/Experience/PawnData 而不重写 LGF | [Lyra 现代框架映射](references/lyra-modern-framework-mapping.md) |
| Inventory/Equipment/Stash 跨容器事务、Container capability、Hotbar link、replicated Item subobject transfer 或 Save graph rebuild | [Container Transaction 合同](references/container-transaction-contracts.md) |
| 大地图大量 NPC、环境生物、MassEntity/MassGameplay、Mass 与 Actor/Pawn promotion、Mass combat bridge、宠物/坐骑规模化 | [Mass AI Scaling](references/mass-ai-scaling.md) |
| StateTree、Utility AI、近战 Chase/Attack 抖动、GAS 意图执行、AI interruption、Mass/promotion 决策连续性、宠物/坐骑玩家命令优先级 | [AI 决策编排](references/ai-decision-orchestration.md) |
| 任务/剧情/世界事件 Flow、Quest Authority、Graph Save ABI、SubGraph、JIP 投影、版本迁移 | [Quest / World Flow 编排](references/quest-world-flow-orchestration.md) |
| Quest Objective/Step、任务 Journal、Player/Shared/World scope、named outcome、late catch-up、advancement hold、任务奖励与存档 | [Quest / Objective 合同](references/quest-objective-contracts.md) |
| Dialogue/Conversation、稳定 Participant、Node/Choice ID、Localization、Save/Resume、Quest/StateTree/GAS/Inventory 对话边界、变身/骑乘时 participant rebind | [Dialogue / Conversation 合同](references/dialogue-conversation-contracts.md) |
| Quest/Dialogue/Combo/World Flow 等多个 Graph 共用作者工具、Stable Node/Edge ID、DomainSchema、编译产物、内容迁移、Editor/Runtime 分层或 live revision | [Graph Authoring Foundation](references/graph-authoring-foundation.md) |

精确签名和长教程仍从项目现行文档/代码按主题读取；不一次性加载全部模块。参考可持续增加，保留解决问题需要的细节，但不复制一套容易漂移的 API 全文。

## 实施准则

- 输入/UI 走真实 Request 或玩家拥有的 Agent；Authority 校验和修改真值，复制/结果通知驱动表现。Listen Host 可在 Request 内直接走 Authority 分支，需核对等价校验，不能强制给自己发 RPC。
- 阅读每个入口的实际返回类型和调用端。提交成功不等于业务完成；带 Server/Authority 名字的函数也不一定是 RPC。不要为统一命名或文档而改生产 API。
- 项目角色、美术、动画、界面和数值配置优先放消费工程；可复用行为或缺失扩展点才考虑改插件。修改前沿 owner、模块、请求、复制、保存、资产生命周期找到真实落点。
- UIData/ViewData 是呈现快照；长期状态、临时 Avatar 和本地 UI 各自维护自己的职责。禁止通过 UI 或 Proxy 绕过 Authority 修改库存、奖励、伤害等真值。
- 修复同类问题前核对前提是否相同，检查 Blueprint 引用、保存格式和网络可见范围。已授权删除危险旧路径时不为隐藏断线保留兼容包装；说明替代节点与迁移影响，避免把局部问题扩展为全部模块重构。

通用 UE C++、蓝图、UI 和排障技能可按任务组合，但不是硬依赖。共享同一份目标、证据和验证结果；LGF 专属约定不外推到没有使用插件的 UE 项目。

## 交付

说明采用的现有能力、实际修改/接线、验证结果和剩余条件。区分静态阅读、UHT/UBT、蓝图/资产检查、PIE 网络与发行构建。没有编辑器时交付明确的资产创建、节点/连线和验收步骤，不声称资产已修改或游戏已通过。
