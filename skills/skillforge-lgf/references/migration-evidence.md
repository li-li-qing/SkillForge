# 旧库迁移依据与使用限制

## 2026-09-15 旧 Skills 备份补查

对比旧 `lgf-development-auditor`、`lgf-gasp-integration`、`lgf-ue5-devkit` 与本包现有内容。前两者的 auditor/integration 主题参考与 devkit 对应文件大多逐文件相同，不重复复制。

| 旧资料 | 本次补充去向 | 证据边界 |
|---|---|---|
| auditor 的 blueprint-api、documentation | [蓝图接口与教程交接](blueprint-api-handoff.md) | 补节点原分类、逐引脚/结果交接、序列化影响和教程依赖；不提供未经源码确认的 API |
| combat-animation-failure-modes | [AI 决策编排](ai-decision-orchestration.md)、[跨层集成](gasp-mover-integration.md) | 补攻击进入/退出/寻路阈值、异常 Root 的 SkewWarp 与目标 Offset 排障；旧事故候选，非本轮运行复现 |
| root-motion-coordinate-spaces、mover-ue57 | [跨层集成](gasp-mover-integration.md) | 补转换阶段/错误源、输入聚合与producer顺序、rollback缓存、Cook组件数据；版本敏感内容用前重核 |
| project/gasp-character | [跨层集成](gasp-mover-integration.md) | 同步动画不等于LeaderPose，核对真实重定向来源与更新依赖；不复制历史资产树 |

已覆盖的周期配对、PSD/PSS、BranchIn、Overlay、Combo、装备取消、复制注册与SceneCapture保留现行说明。旧 UMG 的“Hidden仍可点”“BindWidget只找直接子”“固定重试三次即可修复”、固定DebugGame/路径及“为过编译把private改public”不迁移。旧 Warp Target 名称大小写断言也不推广，按实际字段类型与目标引擎核对。

本次只维护技能，未改或运行 LGame/引擎。独立文本冒烟与结构校验仅验证资料可用性，不等于 UE 运行验收；后续正文的“本轮/当前”属于原取材记录，不能当成 2026-09-15 的源码复核。

取材日期 2026-09-14。原 `lgf-ue5-devkit` 及其 `_skill_backup` 是候选资料，不是当前插件 API 真值。本次按主题重新提炼到现有 SkillForge 技能，未复制一份巨大总入口；使用本包无需原目录或作者电脑。

## 可复用主题与去向

| 原主题 | 现行参考/职责 |
|---|---|
| GASP、版本门禁、Mover、坐标、第三方素材 | [跨层集成](gasp-mover-integration.md)、[武器诊断](weapon-animation-diagnostics.md) |
| 战斗失败模式、双骨架、表示/Trace | [装备与能力生命周期](equipment-ability-lifecycle.md)、[Avatar](avatar-and-assets.md) |
| Authority、FastArray、蓝图接口、文档 | 本技能原有 network-and-state/integration/validation 参考；通用细节在 UE C++ 技能，组合可选 |
| UMG/SceneCapture/资产检查 | UE Blueprint 技能的 official-asset-workflows 参考；本技能只处理 Gameplay/Avatar 边界 |
| 构建、无 Git 复核、长任务证据 | UE C++ 与排障技能；不硬编码原工程路径、目标和检查数量 |

旧脚本中保留 [只读工作区清点](../scripts/inspect_workspace.py) 与 [原回归测试](../tests/test_inspect_workspace.py)。它只发现文件、插件与 Build.cs 路径，不解析动画内部、不证明构建图或运行链正确；多个工程/插件副本拒绝猜测。它不替代官方 UE 资产工具。

从本文件所在 references 目录执行：

```text
python ../scripts/inspect_workspace.py --help
python -m unittest discover -s ../tests -v
```

脚本实际参数以 help 为准；参数 project_root 必须是用户当前工程。

旧包重复的 Markdown/技能校验器与绑定旧名称/旧禁令的测试未迁移；库已有包校验与行为评测。固定盘符、模块数量、无限扩大审查、全面禁止 GUI、已授权操作仍反复确认，以及“未视觉就无法证明任何逻辑”均不作为通用规则。

## 本次读到的证据

项目相对路径用于定位历史取材，不是本包的运行依赖。后续应在用户实际工程重新定位符号，不能凭本页声称同一修复已合入其他 LGF 仓库。

| 结论 | 本次读取来源 | 强度 |
|---|---|---|
| 过渡阻挡与唤醒集合一致、弱回调和清理 | LGame 的 Source/LGame/Private/Quickbar/LGameQuickbarWeaponAdapterComponent.cpp；WeaponSwitchAndSaveId 历史报告 | 本轮读源码；运行属历史记录 |
| ServerOnly owner 漏播与取消不停需分别测试 | 插件 Ability/LGameplayAbilityComponent.cpp 的 OnRep_ReplicatedAnimMontage；Abilities/LGameplayAttackAbilityBase.cpp 的 EndAbility；NetworkReview.md | 本轮读源码与报告；本轮未运行联网 |
| 不能归一化拼一个 root 周期到三个身体周期 | ANIMATION_DEV_GUIDE §25.1、PosePairingReview.md 的逐骨骼与时间轴报告 | 本轮读项目规范与历史报告，未重新导出动画 |
| 原始字节误判 ScaleBox、无头几何与真实尺寸区别 | UIRootReview.md；本地 UE ScaleBox.cpp 构造默认值 | 本轮读报告及默认值源码；未加载当前 WBP |
| 方向、覆盖曲线、Ctrl 输入与零伤害预览边界 | ANIMATION_DEV_GUIDE §25—25.2 | 本轮读现行规范；具体动作质量仍属人工范围 |

这些历史报告位于 LGame 的 Saved/Analysis 下 2026-09-11 复核目录。历史网络组合报告明确 **8 项仍 Fail（Trace 端点断言），独立旧链路回归 13 项 Success**，没有“整体完成”结论；技能只提炼检查方法，不能将这些数量写成新工程门禁。

## 禁止重新推广的旧推断

- 有风格 Tag 就正在播放该风格；每次 OnEntry 都无条件重置所有 BlendStack 状态。
- raw state 数字永远等于某个状态；PSD 数量固定、PSS 越多越好。
- Tag/粗移动状态直接代表上身覆盖；要解决双剑必须建立第二套移动或表现来源系统。
- 身体能动、根轨迹验证绿，就代表周期配对与脚滑已解决。
- Runtime Retarget 会自动复制目标骨架所有 Socket；每个外观都必须重做所有武器位置。
- Ability Cancel 成功就是 Montage 已停；旁观者播了就是 owner 也播了。
- 解析器字段值等同运行期反射值；NullRHI 既不能跑任何网络，也能证明全部视觉——两种绝对说法都错误。

本轮验证只覆盖技能结构、迁移脚本/保留工具及文本行为样本，具体结果在库维护报告中。使用时按任务补实际工程验证，不抄历史绿灯。

## 动画专题补核（2026-09-14，同日后续）

重读当前 TWINKATANA_SINGLE_SOURCE_SOCKET_DESIGN 与 WeaponLoadoutPresentationComponent 的 ResolvePresentationSourceSocketTransform：补准“源 Socket 局部变换 → 可见对应手骨”，不能将原文“武器随源骨架”理解为复用源世界位置。再读 FAnimNode_WeaponOverlay 的 Evaluate/PreUpdate、HasPreUpdate 声明、LGameWeaponPoseCoverage::OverlayAlpha 与覆盖测试：补单遍求值、非有限值处理和生成类钩子检查。

新增 [动画实施与交付顺序](animation-delivery-workflow.md)，将本页故障经验落实到素材盘点、选择链、分层、附件、零伤害预览、正式逐击审核和分层验收。DirectionReview 仍是历史报告引用，当前实现读到的函数也不证明本轮运行通过；本轮没有构建、修改或运行 LGame。
