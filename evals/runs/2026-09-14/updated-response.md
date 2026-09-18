# 五个场景的诊断与行动方案

本答复是给定情景下的行为测试，仅阅读下列技能及参考。没有检查 LGame 当前源码、资产、引擎或日志，没有运行 UE，也没有实施修复。下述具体 API、配置项与历史机制都必须在实际工作时核对当前版本，不能当作当前工程已具备的事实。

## 1. 卸下 Commit 同步触发装备，被 WeaponTransition 阻挡

已知链条足以解释本次进入阻挡分支，但尚不足以断言必然超时：还要检查是否已有 Tag 移除通知及重试唤醒。能力合同要求 Montage 结束才 EndAbility，因此不采用直接清 Tag 或提前结束能力的捷径；那会改变用户给定的生命周期合同。

具体排查：为同一 Request/OperationId 记录卸下 Commit、成功回调、下一阶段 Equip、ConvergenceState、阻挡 Tag 集合及计数、Tag 移除事件、重试触发和最终结果。检查正常单相请求与切换事务是否使用同一套可用性判定。

修复优先落在现有 Adapter/Quickbar 可用性与重试机制：阻挡检查和解除订阅使用一致集合，解除后合并一次重试；执行时验证弱对象、当前事务身份、阶段及全部阻挡条件。若同步回调重入尚未完成的状态，使用下一 tick 的身份校验唤醒，而非任意固定 Delay。EndPlay 和重新绑定时清理订阅及待执行回调。保留旧能力到正常 Montage 结束，不能加长超时、丢弃请求或用新事务取消已进入 Equipment 的旧事务掩盖缺陷。

验收：单相 Equip/Unequip、A 换 B、多个重叠锁逐一释放、连续选择、取消、死亡/销毁；确认释放最后一个有效阻挡后只推进当前事务且不重复提交。Blueprint Impact：计划保留请求合同，通过原结果通知反馈完成或失败；实际节点影响待源码核对。

## 2. Chooser 含 style，但跑三秒才换姿势；根 0.8s、身体 2.4s

这里至少有两条独立待核验链，不能用根轨迹脚本全绿替代姿势选择诊断。

对延迟，在同一 Pawn、世界、源 AnimInstance 和帧序列观测：装备提交 → 公开复制 → CombatStyle 快照 → Chooser 输入和输出 → BranchIn/MM/Blend Stack 候选及播放时间 → 最终分层。Chooser 输出有 style 不证明它已经成为实际求值姿势。检查状态进入与持续更新分别何时更新 ChooserOutputs、ValidAnims、BlendStackInputs，旧候选是否残留，并核对当前枚举含义。重点采集 Start/Pivot/Refacing/Switch 的选择、长度和退出提前量。仅证实特定风格缺少匹配过渡后才补素材或使用现有无候选回退；不全局过滤其他动作，不用定时强刷代替正确更新路径。

对时间轴，0.8s 与 2.4s 只能提出周期错配假设。先观察身体是否含三个重复周期、Root 是否为一个周期，核对足部接触/Phase、实际播放速率、根距离及速度。如果将单个根周期按归一化时间铺到 2.4s，可能导致根速度约为原来的三分之一，但必须由实际采样证实。优先使用同一完整来源配对身体与根；必须合成时逐周期证明对应关系及循环边界连续性。

25/25 仅能交付为该脚本覆盖的根轨迹断言通过。审查脚本是否独立于生成算法、是否实际逐帧、是否处理 API 帧间隔数与关键帧数差异；同一插值算法自证不能证明动作语义。再独立检查身体接触、滑步、循环边界和实际播放；按需要验证 PSD 有效采样范围、索引有效性及搜索结果、复制后 BranchIn 的对象身份与数据库重绑。保留原素材，修项目派生及生成器，避免重跑复发。若全身双剑还叠静态持剑层，核对实际曲线和权重，不把装备 Tag 当作全身动作覆盖双臂的证据。

## 3. ServerOnly 攻击 owner 漏播，取消成功但自然结束才停

分开处理播放可见范围与停止生命周期。

owner 漏播：分别记录 Authority、Autonomous owner 和旁观者的 ASC ActorInfo、Avatar、实际 AnimInstance/Slot、NetExecutionPolicy、PredictionKey 和复制 Montage 快照。ServerOnly 没有本地预测并不保证默认复制负责 owner。若当前引擎确实在 OnRep_ReplicatedAnimMontage 跳过 LocallyControlled，再检查当前 LGF 是否已有默认关闭的 bPlayServerMontagesOnOwningClient 项目开关；不能假定它已经存在。有则按其合同启用与验证，无则评估最小可复用扩展。继续消费原复制 Montage 状态并保留官方预测路径，不增加第二套 Multicast 播放真值。

必须覆盖同资产重复实例、Section/NextSection、PlayRate、位置校正、停止快照、Avatar 更换和就绪后重试；只验证非预测静态 Montage 时应明确边界，不能扩展宣称动态 Slot 或混合 LocalPredicted 正常。

取消不停：检查真实顺序是否先 EndTask 再结束能力。相关版本 PlayMontageAndWait 的 OnDestroy(false) 与 bStopWhenAbilityEnds 的能力结束分支不同，单看布尔配置为 true 不足以证明停止发生。取消需立即停时，确认 ASC 当前 AnimatingAbility 与 Montage 仍属于本次能力，再通过 ASC 停止并清理任务，防重入和旧取消误停新受击动画。正常 EndAbility(false) 如果设计允许后摇继续，则不一律强停。

分别断言能力结束、战斗窗口关闭、Montage 在明确传播上限内停止、Mover 位移停止以及各端收敛；不以数秒后自然结束为成功。回归自然结束/取消/替换、首次和重复播放、真实 owner/旁观者、JIP、延迟丢包，并实际执行受击中断链；Authority API 模拟不等于敌人受击链已验收。

## 4. raw parser Stretch=0、报告判 None、NullRHI 几何为零，要求重建 WBP

现有证据不足以支持重建整个 WBP，应先核验两处测量结果。外部解析器的 raw 0 不能直接映射到反射枚举；已有版本案例正式加载得到 ScaleToFitX，但不能据此断言本资产也一样。用当前 UE 正式加载、get_editor_property/反射与版本源码核验真正的 Stretch，并检查 WidgetTree、Slot Parent/Content、StretchDirection、SizeBox Override 及 Desired/Allotted Size。简化树遗漏子控件也不能直接认定资产损坏。

NullRHI 下先核对本地 Slate.SkipWidgetDrawingInHeadlessMode 实现与值，它可能跳过几何所需过程。可以在诊断进程临时调整官方 CVar，不永久改项目设置、不删除尺寸断言。用当前可用的窗口 API 获取并实测客户端视口尺寸，区分外框、客户区和 DPI；不能把 ResizeFrame 调用成功等同于 PIE 视口改变。

若正式加载确证根层问题，限定资产白名单并备份，只修获准根层属性，保留子控件坐标、锚点、样式、绑定及现有 Widget 身份。检查生成器是否因根已是 ScaleBox 而漏修坏属性，同时避免 Apply 无条件重写页面；异常部分树应明确报错。仅在正式资产证据证明整体不可恢复且重建确有必要时，才制定引用及布局迁移方案，而不是按 raw 0 全量重建。

验证分开记录编译、保存、关闭进程后重载、无头几何和有渲染视觉；实际分辨率/DPI 下检查绝对几何、点击区域、文字可读性及拖窗。当前仅为方案，没有改动任何 WBP。

## 5. 当前 8 个网络用例全 Fail，缺 Trace socket；装备/复制断言和 13 个旧回归绿

交付状态必须写“当前网络用例 0/8 通过，8/8 失败，共同阻塞为缺失 Trace socket；已执行的装备及复制子断言通过；13 个旧回归通过（按题设）”。若旧回归是历史结果而非本轮重跑，必须标为历史通过。不能相加包装成总体通过，更不能删去伤害断言换绿。

先明确握持 Socket 与服务器隐藏 Trace Mesh 的 trace_start/trace_end 是两种用途。检查实际服务器表示使用的 StaticMesh、端点存在性及位置、装备定义引用、运行实例、窗口和过滤；剑握在手上并不证明 Trace 已配置。修复落在获准的项目派生资产与正确引用，不破坏第三方源素材或已校准握持挂点。双刃按玩法合同检查同窗口同目标去重，独立挥击使用独立窗口身份。

修复后原样重跑这 8 个失败用例，核验真实命中、击空、伤害应用和双刃去重，再按影响跑相关回归。记录本轮目标、过滤器、执行数、日志和失败原因。静态端点存在不代表战斗验收通过；人工尚未审核逐击 Montage/Section、命中与续招窗口时，明确交付仍限零伤害预览/已验证层，不平均切窗或照搬另一武器参数。

最终报告可交付当前装备与复制子链证据和明确的 Trace 资产修复清单，但整体网络攻击验收保持未通过。这里不声称实际复现、修复、编译或重跑了任何测试。

## 实际阅读文件

- D:/Project/Skiils/SkillForge/skills/skillforge-lgf/SKILL.md
- D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/equipment-ability-lifecycle.md
- D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/weapon-animation-diagnostics.md
- D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/validation-and-evolution.md
- D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/ui-platform.md
- D:/Project/Skiils/SkillForge/skills/skillforge-ue-blueprint/SKILL.md
- D:/Project/Skiils/SkillForge/skills/skillforge-ue-blueprint/references/official-asset-workflows.md

未读取 evals、旧回答、项目生产文件或记忆；唯一写入是本答复文件。