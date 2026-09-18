# 装备事务、武器表示与 GAS 播放生命周期

使用前核对当前 LGF 接口与项目能力策略。以下模式来自有版本范围的案例，不保证其他插件分支有同名配置。证据见 [迁移依据](migration-evidence.md)。

## 切换卡在卸下与装备之间

典型重入链：卸下 Commit → 同步成功回调 → 下一阶段 Equip → 旧能力的过渡 Tag 尚未释放 → Blocked/RetryPending。区分“这次必然进入阻挡分支”“没有重试唤醒”“最终必然超时”；外部可用性通知可能改变最后一步，不能只看局部源码下绝对结论。

逐项查调用栈、ConvergenceState、Request/OperationId、阻挡集合、Tag 计数和移除事件、最终失败原因与超时时间。保留正常单相 Equip/Unequip，也补持一把换另一把、重叠动作锁、连续选择、取消和死亡测试。

修复应在现有 Adapter/Quickbar 可用性机制：阻挡判定和解除订阅使用一致集合；解除后合并一次合适时点的重试，重查全部条件与当前事务。若同步回调会重入不完整状态，可使用带弱对象和身份核验的下一 tick 唤醒；不是任意固定延迟。EndPlay/重新绑定时清理委托和待执行回调。

武器过渡 Tag 若按设计存活到 Montage 结束，不能提前 EndAbility 或直接清 Tag 来通关；不能用加长超时、丢请求、新事务取消已进入 Equipment 的旧事务掩盖问题。

## 成对表示与单一源 Socket

一件成对武器可有多个表示部件，仍用一个库存身份和一次装备事务。准备、全部提交、卸下、部分失败清理都需覆盖；JIP/远端从现有公开快照重建，不新增第二套装备真值。

官方 Skeleton/Mesh 编辑器的 Add Socket + Preview Asset 用于校准握持，修改骨骼会改变整条骨骼姿势。核对 Socket 实际属于 Skeleton 还是 Mesh、装备定义引用、运行组件、额外 Transform Offset 和实例缓存；资产默认值修改不承诺现有 PIE 实例热更新。

采用单一动画源 Socket 的项目，必须进一步确定“共用”的是局部校准还是源骨架世界位置。本轮核对 LGame 实现：可见武器取源 Socket 相对父手骨的局部变换，再应用于重定向后的可见 Mesh 对应手骨；Authority Trace 仍跟服务器源骨架。可见剑不是机械复用源 Socket 世界位置，也不意味着必须另写一套手部 IK。

以本案例 UE FTransform 组合顺序表示：`VisibleWeaponWorld = ItemOffset * SourceSocketLocal * VisibleHandWorld`。先用当前实现和基向量验证乘法方向，勿推广到其他数学库。骨骼名不兼容时显式映射/报告失败；不落到根节点“先显示再说”。Runtime Retarget 不会自动复制另一 Skeleton 的 Socket。

这种局部变换复用仍可能需要外观级重定向手部/手指校准，但不要要求每个 Avatar 重做全部武器，也不要反复改公共源 Socket 来迁就一个外观。附着更新发生在姿势更新后；显式检查可见性继承，隐藏 UEFN 的子组件不能因挂接而意外隐藏。它是项目选择，不是所有骨架必须共享 Socket 的 UE 规则。

**握持 Socket 与 Trace 端点不同。** 剑在手上不证明服务器隐藏 Trace Mesh 的 trace_start/trace_end 存在或正确。核对两套表示的用途、实际 StaticMesh、端点位置、窗口和过滤；无伤害还需检查服务器攻击入口、敌我/碰撞、窗口开启和伤害应用。第三方模型用项目副本创作端点，不能顺手破坏用户握持配置。

双刃同一命中窗口同目标按玩法合同去重，独立挥击用独立窗口身份；重模拟与 Notify 重放不得重复结算。静态端点存在不等于实际命中/击空/去重已测试。

## 服务器播了、owner 没播

先将 Authority、Autonomous owner、旁观者分别记录，确认 ASC ActorInfo、当前 Avatar、实际 AnimInstance/Slot、能力 NetExecutionPolicy 与 PredictionKey。ServerOnly 能力没有本地预测，不代表 GAS 默认 Montage 复制就自动负责 owner 播放。

UE 5.7 案例的 UAbilitySystemComponent::OnRep_ReplicatedAnimMontage 跳过 LocallyControlled。若项目证实同因，优先检查当前 LGF 是否已有默认关闭的 bPlayServerMontagesOnOwningClient 项目选择；不存在时再评估最小可复用扩展，不能假定该属性已发布在所有版本。

修复仍消费原复制 Montage 状态，保留官方预测路径，不广播第二套播放真值。必须核对同资产重复实例、Section/NextSection、PlayRate、位置校正、停止快照、Avatar 更换与就绪重试。历史修复只覆盖非预测静态 Montage，不能推广成动态 Slot、混合 LocalPredicted 或所有 GAS 场景已验证。

## Cancel 返回成功，动画却播到自然结束

分别验证能力终止、战斗窗口关闭、当前 Montage 真正停止、Mover 位移结束和各端收敛。至少加取消后立即停止/明确传播上限的断言；“数秒后终于结束”可能只是原动画自然播完。

UE 5.7 的 PlayMontageAndWait 停止行为与 OnDestroy 的 AbilityEnded 参数及 bStopWhenAbilityEnds 有关；先 EndTask 会调用 OnDestroy(false)，不等于结束能力时自动停止。沿真实清理顺序核对，而不是只看配置为 true。

若明确取消需停止，先确认当前 AnimatingAbility 和 Montage 仍属于本次能力，再经 ASC 停止并清理任务；防止重入、旧取消停掉新受击动画。正常可行动点 EndAbility(false) 可能按设计保留后摇，不得全部强停。

回归覆盖首次/重复播放、自然结束/取消/替换、真实 owner/旁观者、JIP 与延迟丢包。Authority API 模拟中断不等于真正敌人受击链已执行；最终位置误差小也不证明过程无抖动。


## 收纳不一定复用手持路径

先分别追踪手持和Holstered表示的AttachMesh、Anchor、SocketName与Offset。某工程手持已用源Socket局部变换，但收纳仍直接挂可见Mesh的Avatar锚点；不能仅凭“方案A已实现”让用户修改源手部Socket调整背部。

给用户校准说明时区分Avatar公共Anchor/BaseTransform与物品专属HolsterTransformAdjustment、附加部件PartId对应的收纳调整。公共锚点会影响所有使用该锚点的武器。若用官方Add Socket/Add Preview Asset，必须将消费路径实际引用的SocketName接过去，避免只加预览却游戏不变；别改骨骼本身。多个Transform乘在一起会双重偏移，先记录再明确哪层承担校准，不擅自清用户数据。

明确Skeleton Socket与Mesh Socket的实际归属，预览只能选兼容骨架动画；不承诺PIE已生成实例实时刷新。保存后通过已实现重建流程验证，可靠兜底是重启PIE。多Avatar共享收纳方案若尚未实现，应明确当前范围，不顺手要求用户为所有未来角色重复校准。

多刀刃去重、窗口身份、连续Montage和网络输入时序见[多刀刃连击](multi-blade-combo-validation.md)。

## GAS Grant Source：同类能力不等于同一来源

双持、成套武器和模块化装备可能由多个 Item 同时授予相同 AbilityClass。装备生命周期必须记录“是谁授予”而不是在卸装时重新猜。

Authority grant 时至少建立：

`Persistent ItemId / EquipmentEntry -> runtime source context(SourceObject 等) -> exact SpecHandle/GrantedHandles`。

卸装只撤销该来源保存的 handle。同 AbilityClass、AbilityTag、InputTag 或 Montage 都不能单独作为撤销 identity。`FGameplayAbilitySpec::SourceObject` 适合作为运行时来源上下文，但不是 SaveGame 永久 ItemId；load/respawn/Avatar rebuild 后从持久 Equipment truth 重建映射。

如果能力正处于预测/TargetData/AbilityTask 生命周期，先定义 teardown 顺序和 generation：撤销 grant 不能让旧 TargetData、Montage reject、Task delegate 在下一件同类武器上继续生效。

PredictionKey、TargetData、remote termination 和多 Mesh/Layer rollback 详见 [GAS 战斗预测](gas-combat-prediction.md)。
