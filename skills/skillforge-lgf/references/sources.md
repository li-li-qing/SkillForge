# 取材依据与适用版本

取材日期：2026-09-12。主来源为用户授权阅读的 LGameplayFramework 本地 Git 仓库，提交 `2088589f207ce696b7e73095e2dd7df351f1a0c4`（2026-09-11，添加文档），开始取材时工作树干净。本技能自行归纳调用契约和检查路径，没有复制插件源文件或资产。

消费工程现场为 `Game.uproject`，EngineAssociation 为 `5.7`；实际目标有 `GameEditor`、`Game`、`GameServer`。这是取材现场记录，后续使用必须重新发现工程和目标。插件描述文件 VersionName 为 `1.0.0`、IsBetaVersion 为 true，没有独立 EngineVersion 字段，不能把描述中的 UE5.7 当作所有版本已兼容。

## 阅读范围和证据强度

阅读根 README、文档导航、现行状态/审计、架构与维护指南，以及与接入有关的 API/Tutorial 章节；沿关键符号核对了交互、Foundation、ActionLock、AbilitySet 授予、导航、库存、Quest、Dialogue 和迁移扫描的声明/实现。没有逐行审计全部模块。

现场清点为 53 模块（32 Runtime、20 ClientOnly、1 Editor），Source 中 964 个文件，其中 53 个 Build.cs；发现 158 处自动化测试宏声明、17 个 uasset、0 个 umap。这些数量只说明扫描范围和存在性，不能证明测试通过或资产内部接线正确。当前 Docs 的 2026-09-11 快照来自压缩包，其“缺少宿主”的限制不代表本次真实工作区也没有宿主。

本轮仅做静态文件、符号与 Git 状态核对，没有运行 UHT/UBT、Commandlet、蓝图编译、PIE、网络回归或 Cook/Package。行为评测验证的是文字方案，不是客户端行为。

## 采用结论与落点

下列路径均相对插件根；准确签名、行号和行为应以执行任务时的文件为准。

| 主题 | 核对来源 | 采纳理由与限定 |
|---|---|---|
| 现行能力与模块边界 | `LGameplayFramework.uplugin`、`Docs/README.md`、`Docs/Current/IMPLEMENTATION_STATUS.md`、`Docs/Architecture/NETWORK_AND_RUNTIME_BOUNDARIES.md`、各 Build.cs | 区分 Runtime/ClientOnly/Editor；不按模块名推断依赖，不把文档快照当当前运行结果 |
| 蓝图交互 | `Source/LGameplayFrameworkInteraction/Public/Interaction/LInteractableActorBase.h` 及对应 Private 实现 | 核实三个 K2 BlueprintNativeEvent 和默认行为；默认执行失败是扩展点，不是不能蓝图实现 |
| ActionLock 分端语义 | `Source/LGameplayFrameworkCombat/Public/Components/LGameplayActionLockComponent.h` 及对应 Private 实现 | 核对 bool、共享 RequestBudget、owner 分支、自然完成/取消/替换事件；只作为该提交的行为，不推广成通用动作锁规则 |
| Foundation 与死亡恢复 | `Source/LGameplayFrameworkFoundation/Public/Foundation/LGameplayFoundationActors.h` 及对应 Private 实现、Foundation.Build.cs | 核对默认组件、PlayerState 长期状态、Character 与 Pawn 的 C++ virtual 钩子；完整 Foundation 有真实依赖成本，配置开关不等于裁掉模块 |
| Mesh 与动画装配 | `Docs/Architecture/MOVEMENT_ANIMATION_INTEGRATION.md`、`Source/LGameplayFrameworkEquipment/Public/Equipment/Interfaces/LEquipmentAttachmentResolverInterface.h`、`Source/LGameplayFrameworkCombat/Public/Components/LCombatMotionWarpStatics.h` | 两种装备挂点用途和 MotionWarp 辅助边界；指南对 GASP/通用 Mover 的装配限制不当作资产运行结果 |
| AbilitySet 授予 | `Source/LGameplayFrameworkAbility/Private/Ability/LGameplayAbilityComponent.cpp` 及对应 Public 头文件 | 真正授予入口位于组件，不仅检查 LAbilitySet 数据验证；软类 Get() 未加载返回 AssetNotLoaded，Server 名字不代表 RPC |
| UI 平台 | `Source/LGameplayFrameworkUINavigation/Public/UINavigation/LGameplayUINavigationSubsystem.h`、UINavigation.Build.cs、现行 UI 架构文档 | 每 LocalPlayer 导航真值、Receipt/完成通知、精确 InstanceId、Provider 边界；无需为导航内核硬加 CommonUI |
| 库存与保存 | `Source/LGameplayFrameworkInventory/Private/Inventory/LInventoryComponent.cpp` | 存在动态复制条件和业务快照恢复；不统一改 OwnerOnly，不把 FastArray 内部身份作为存档身份 |
| 重试与迟到请求 | `Source/LGameplayFrameworkQuest/Private/Quest/LQuestComponent.cpp`、`Source/LGameplayFrameworkDialogue/Private/Dialogue/LDialogueAgentComponent.cpp` | Quest 缓存对照 RequestId 与业务参数；Dialogue 请求含会话/节点语境。执行任务仍需核对完整权限和状态链，不声称已审计全部事务安全 |
| 迁移检查 | `Source/LGameplayFrameworkUIEditor/Private/LGameplayUIMigrationScanner.cpp` 及对应 Public 头文件、`Config/FilterPlugin.ini` | Commandlet 存在，写迁移 JSON，Critical/High 返回非零；旧 Python 脚本不存在。产物打包完整性需要另行检查 |
| 规划与维护 | `Docs/Guides/MAINTENANCE_WORKFLOW.md`、`Docs/Decisions/README.md`、`LGameplayFramework_Backlog.md`、`重构文档/WorldMapArchitecture/README.md` 及结构确认稿 | 现行导航、冻结历史与未完成前置分开；学习任务不自动推进 P1 或重构 |

本机已有的 LGF 审计技能仅作为检查线索；新技能侧重框架接入与开发，并用上述现行源码重新核对。使用本包不依赖该旧技能、特定 Agent 或个人路径。发现旧指南与当前实现冲突时保留冲突事实，不能为了符合指南而擅改实现。

## 关键文件指纹

SHA-256 用于确认取材基线，不要求未来文件保持不变；变更后重新核对受影响结论。

| 文件 | SHA-256 |
|---|---|
| `LGameplayFramework.uplugin` | `280ae5b36a1fbc263047b7f75f9be33e2e0490aeabe004115023de0f5c873647` |
| `Docs/Current/IMPLEMENTATION_STATUS.md` | `5fe353588e1246079df49229a34c56271da83f63ff41ebd76d3e030249ea8bdd` |
| `Source/LGameplayFrameworkCombat/Private/Components/LGameplayActionLockComponent.cpp` | `917b172aacb1c5486ad82cf26ce4446d55cb1cca55d13dc3ac42562ae9c95766` |
| `Source/LGameplayFrameworkAbility/Private/Ability/LGameplayAbilityComponent.cpp` | `92fa9178556d353fba5727f44d9b5b0f35bff4c6388fb251e44eb4e8742a4b5b` |
| `Source/LGameplayFrameworkFoundation/Private/Foundation/LGameplayFoundationActors.cpp` | `cd03cfcb571994310fc2c866ff7ae517f41381edfc687537655f1e0b6582a502` |
| `Source/LGameplayFrameworkUINavigation/Public/UINavigation/LGameplayUINavigationSubsystem.h` | `6f0586b52c81a26b60131e9132390d8b3c3649b22c244e26e9ea3d5cc9d47c99` |
| `Source/LGameplayFrameworkQuest/Private/Quest/LQuestComponent.cpp` | `93442cf62cf09e1f3d61e3041abd33299c9138213dbcbc93bda1749625009f0f` |
| `Source/LGameplayFrameworkInteraction/Public/Interaction/LInteractableActorBase.h` | `95d191305331bc751834f9ebcfc819aeab0e49a725b698ee643f94495b06e892` |

## 更新依据

收到实际开发反馈后，按[验证与演进](validation-and-evolution.md)记录触发条件、证据、修复和验证；修改相关主题并补对应反例。无法确定的原因保持候选状态。社区方案将来可以纳入比较，但需要标明来源/版本/许可证，并核对是否适合 LGF 当前所有权、复制和模块边界。

## 2026-09-14 消费工程案例补充

新增材料来自另一消费工程 LGame 的 UE 5.7 源码与历史报告，不等同前述 Game 插件提交。具体符号、旧结论取舍及未运行范围见 [迁移依据](migration-evidence.md)。当前源码检查不得泛化成所有 LGF 分支已有相同配置。
