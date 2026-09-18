# LGF、GASP 与 Mover：从真实链路接入

用于装备风格、移动动画、锁定朝向、运行时重定向与能力位移的跨层任务。方法来自旧开发技能及 LGame UE 5.7 案例；资产名、状态编号与当前实现必须重新发现。详细故障检查见 [武器动画诊断](weapon-animation-diagnostics.md)、[装备与攻击生命周期](equipment-ability-lifecycle.md)。

## 先画实际运行链

读取当前工程与插件描述、相关 Build.cs、Pawn 实例/CDO、组件和实际可达 AnimBP。至少确定：

| 责任 | 必须定位的对象与数据 |
|---|---|
| LGF | Request/Agent、服务器 Equipment/Combat/ASC、公开复制快照与状态桥 |
| Mover | Backend、Input Producer、UpdatedComponent、PrimaryVisualComponent、Modes/Modifiers/Layered Moves |
| GASP | 主 AnimInstance、状态选择、Chooser Context、PSD/PSS、Pose History、Trajectory、Blend Stack 内部图和 Update/Post Selection 函数 |
| 外观 | 动画源 Mesh、Runtime Retarget 的 Source/Target、可见 Mesh、Socket 与权威 Trace 表示 |

目录中存在示例资产，不等于玩家引用它。比较实际对象路径；双 Mesh 不靠“第一个 SkeletalMesh”猜播放源。隐藏源的动画更新顺序、可见性裁剪、LOD 与 Dedicated Tick 条件都要检查。

同步动作不证明使用 LeaderPose。先从实际图确认是 LeaderPose、Copy Pose 还是 Runtime Retarget；采用 attach 父源的重定向链时，核对取姿势源、attach 与 Tick 前置依赖。不要因显示 Mesh 跟着动就换成另一种绑定机制。

LGF 决定玩法是否合法及状态真值；Mover 模拟碰撞移动；GASP 消费状态生成姿势。已使用官方 GASP Mover Pawn 时保护它的父类、组件、主 AnimBP、Trajectory/Pose History 和平滑契约，不为接一把武器另建移动系统。普通 CMC 工程也不因本参考被强制迁移到 Mover。

## PSD/PSS 与选择契约

第三方动画接入先核对五个对象：源 Mesh、源 Skeleton、离线重定向目标 Skeleton、运行时动画源 Mesh、最终显示 Mesh。采用标准动画源 + Runtime Retarget 时，离线目标是标准源，不能直接为每个外观再生成一套玩法动画。核对 IK Rig 链、Retarget Root、A/T Pose、手脚与骨盆；不要用 Mesh 高度/Socket/Foot IK 掩盖错误重定向。已错的派生从真实原源修复，不重复转码错误结果。

- **PSD** 是候选动画及搜索索引；**PSS** 是搜索特征的 Schema，包括骨架、轨迹和骨骼采样。数量更多不保证更正确。
- 先建立状态×步态×方向×风格的素材覆盖表，包括 Idle/Start/Loop/Stop/Pivot/空中与回退；不因素材存在就新增移动能力。
- 搜索特征相容时复用现有 PSS，只为有证据的特征差异派生。候选检查 Skeleton、完整时间轴、Loop、Root、曲线、Notify、BranchIn、采样区间和实际索引。
- 当前 GASP 可能由 Chooser 返回 PSD，也可能返回 Sequence 再通过 BranchIn 接管搜索；先查完整可达链。不要把所有版本解释成同一种节点图，或为“升级”强行切到另一种实验性 Pose Match 路径。
- Context 类型、Property Binding 和运行时传入对象必须一致。UE 5.7 的 GameplayTagColumn 容器绑定不能用单个 GameplayTag 内存代替；MultiEnum 掩码和 Bool 的序列化迁移应读目标版本实现，不能按显示行索引猜。
- 复制/插行时保留原条件、输出与其他行，明确空手、其他武器、缺素材回退。输出 Tags 采用合并语义时不能 Resize(1) 覆盖未知原值。

## 模拟、输入与线程

移动意图与朝向意图分开。沿 Enhanced Input → Input Producer → 模拟输入/速度 → Gait/RotationMode → 选择结果检查；Ctrl 是慢走还是蹲伏由实际 Mapping Context 决定。

持续模式用 Movement Mode，临时位移用合适的 Layered Move，参数约束用当前版本支持的 Modifier/策略。保存并清理返回 Handle；同类匹配字段与 NetSerialize 一致。多个限速来源需要可组合策略，不能各自保存旧 Shared Settings 再按任意次序恢复。验证攻击锁仍允许重力、落地、受击位移等获准行为，不能冻结整个 Mover。

GAS 属性不自动驱动 Mover；动画换成慢跑也不等于服务器限速。项目只建立缺失的桥，不重复现有输入/轨迹适配。模拟重演不得重复伤害、消耗或奖励。GAS PredictionKey、跨层事务 ID、Mover Move Handle 是不同身份域，不能混作一个 ID。

Game Thread 收集 Gameplay/资源状态，动画线程读取当前工程允许的快照或 Property Access；AnyThread 不遍历可变 ASC/Equipment 或同步加载资源。换 Pawn、重建 AnimInstance、Teleport/Correction 后明确缓存与 Pose History 的重置或重新播种。

## Root Motion：先分清数据与消费

Locomotion 保留根轨迹供搜索，不意味着根轨迹直接驱动胶囊。攻击则需核对 Montage 根运动消费路径。不要批量删 root，也不要同时让官方 Layered Move 和自建桥消费同一段位移。

分别记录输入选择、身体姿势、胶囊位移三条链。每个值注明 Mesh-local、Actor-local 或 World-space。当前后端已通过 PrimaryVisualComponent 转换时，桥继续输出约定的 Mesh-local；基准转换恰好一次。用实际组件 Transform 旋转基向量验证，不凭资产名或 Yaw 心算统一补 90°。

UE 5.7 排查入口：MoverComponent 的 ConvertLocalRootMotionToWorld、USkeletalMeshComponent 同名实现、实际 Layered Move。数据从 Montage 提取不代表生命周期不依赖 AnimInstance 正在播放；复核非重模拟步的中断检测。其他版本须重查。

只有官方现有路径确实不能满足合同才扩展桥。须明确播放时间与模拟时间、跨 Section/区间提取、缩放/受限 Warp、结束与取消、Rollback/Resim。不得用 SetActorLocation 或可见 Mesh 偏移掩盖模拟错误。

Motion Warping 还需要有效目标、实际 Warp 窗口与真正被消费的 root，只有 Warp Target 不会自动推进角色。服务器校验目标、范围与最大修正，结束/取消清理目标。原 GASP Traversal 已有的窗口与移动模式不要再套一套战斗桥。

### 吸附爆冲与转换分支

旧战斗案例提示：SkewWarp 遇到窗口净位移接近零、环形/自旋或大幅 Root 旋转时，可能出现不合理修正。先比较完整源轨迹、实际窗口净位移与累计路程、Warp 前后逐帧增量；不能仅凭“Root Motion 已启用”认定适合吸附。证实载体不合适后，选经审查的 root 动作，或让动画只作表现、由现有权威 Mover 位移路径承担移动；仍保持单一 consumer。不靠缩短距离、修改 Capsule 掩盖根轨迹问题。

使用 `bFollowComponent` 与 Offset 时分别标注目标组件局部空间与世界空间，并用旋转/移动目标验证。检查当前引擎 Local/World root-motion delegate 的执行阶段，以及 PrimaryVisualComponent 是否为空、是否真是播放 Montage 的源 Mesh；错误源/回退分支不能沿用正常分支“已转换一次”的结论。

### UE 5.7 旧事故的按症状核查入口

以下来自旧 mover-ue57 参考（其源码核验记录为 2026-08-28），本次未重跑引擎；先读实际 Build.version、Backend、Mover README 和实现，不能当作所有版本仍有缺陷：

| 症状 | 需要核对的合同 |
|---|---|
| 禁止输入后仍偶尔移动 | 多个 InputProducers 的集合与执行顺序，过滤是否被后续生产者覆盖；Possess/重建后重测 |
| Fixed 模拟下短按漏掉或重复 | 多个渲染帧如何聚合到一个模拟帧；区分按住值与按下边沿，不假定一帧渲染对应一帧模拟 |
| 回滚后结果不同 | Sim Blackboard 缓存是否会失效，是否能从该历史帧记录状态重算；不能用当前 Gameplay 状态填历史值 |
| Editor 正常、Cook 后 Mover 数据缺失 | 实际 Cook 产物中的组件数据与 `bOptimizeBPComponentData` 路径；确认关联后做隔离 A/B，不无条件关闭全项目优化 |

这些分支的修复需回归对应后端、输入时序、重模拟或 Cooked 实例；PIE 正常不替代打包验证。

## 验证最低信息

分别记录静态资产、索引、实际选中并播放的动画/时间、位移消费与坐标，以及人工视觉和真实联网。构建成功、选择命中、最终位置收敛都不能替代脚滑、过渡自然度与中途纠正检查。

## GASP-ALS-R 最新 Mover 路线补充（2026-09-14）

外部案例 `SAM-tak/GASP-ALS-R@a227dfecfcb2719c2541218cf026c05dfe3290ec` 在 2026-09-13 合并了 `feature/mover`。它与 LGF 的 Pawn + Mover + GASP 方向高度相关，但当前文档包含自定义 UE 5.8.2 的实现证据；LGF 目标是 UE 5.7，因此只吸收责任模型，所有 Mover/GameplayCamera/PhysicsControl/PoseSearch API 都要回到目标 5.7 源码重核。

### Replay-safe Mover 输入

该案例把 `ProduceInput` 明确视为 simulation 外采样：本地控制端在这里读 GAS stance flag、PhysicsControl ragdoll transform、Rotation/Gait/Stance，再写进自定义 Mover Input。Resim 不重跑这一采样，因此 LGF 要坚持：

- 会改变 simulation 结果的 live GAS/physics/targeting 决定，先记录进 Mover Input/Sync/Persistent State；
- simulation/resimulation 不重新读当前 Mesh/AnimInstance/PhysicsControl 得出同一历史 frame 的结论；
- 自定义 state 增字段时同时定义 `NetSerialize`、`ShouldReconcile`、`Interpolate`、`Merge`；离散 Tag 用明确 step/closest 语义；
- Proxy finalization 消费同步 state 重建 stance geometry，不能自己运行另一套计时。

这一点对 LGF 的 P2P/Listen Host 同样成立：Host Authority 不能成为“跳过 replay contract”的特例。

### Mover 机制按语义选

案例源码当前把 `GAR_USE_MOVEMENTMODIFIER` 设为 0，说明“有 Modifier 类”不等于当前生产路径使用 Modifier。LGF 不应规定 Rotation/Gait/Stance 一律用 Modifier。

- 长期互斥移动模型：Movement Mode；
- Montage/冲刺/击退等临时位移：Layered Move；
- 瞬时 jump/geometry effect：Instant Movement Effect；
- stance 中间 capsule/eye-height：Persistent Sync State；
- 参数约束只有目标 UE5.7 backend 确实适合时才用 Modifier。

Capsule resize、foot pivot、movement-base/floor cache 是模拟正确性的一部分。Correction 后不能重复 pivot，也不能只改可见 Mesh 掩盖碰撞状态错误。

### Animation Game Thread / Worker Thread

案例主 AnimInstance 在 `NativeUpdateAnimation` 读取 ASC/Mover/MotionWarp 等可变对象，更新 movement/tag/transform 快照；`NativeThreadSafeUpdateAnimation` 再只刷新 linked layer/pose cache。LGF 延续这一边界：

`GameThread mutable truth -> compact anim snapshot -> AnyThread pose evaluation`

ABP/Linked Layer 可负责 Start/Pivot/Land/TurnInPlace/IK/AimOffset 等 pose semantics，不拥有伤害、Ability 是否合法或 Mover movement truth。

动作 Ability 在 Game Thread 从 PoseHistory 做 MotionMatch 时，案例显式等待已有 parallel animation evaluation 完成。LGF 只允许这种同步 fence 出现在 Traversal/Roll/Landing 等离散激活点，并用 Insights 测 stall；禁止放进 Tick、持续瞄准或 Overlay 每帧更新。

### Root Motion / Layered Move 的取消合同

案例播放 Montage 后关闭 MontageInstance 的 animation-driven root motion，再把 root 数据交给 `FLayeredMove_AnimRootMotion`。这印证 LGF 的“单一位移 consumer”原则。

LGF 进一步收紧：创建 Mover Layered Move 后必须保存可取消 identity/handle，并与 AbilitySpec/PredictionKey/MontageInstance/WarpTargets 关联。Ability End、Cancel、Interrupt、Avatar switch 要同时清 Montage、matching LayeredMove、WarpTarget、临时 effect/delegate。只 StopMontage 不算已经证明 Mover move 停止。

### Traversal：local selection 不等于 Authority truth

案例允许 AutonomousProxy 本地 Trace + Chooser + MotionMatch，然后把 SelectedMontage、TargetPrimitive 和 Front/Back/Floor 点通过 TargetData 传给服务器，以避免服务器重复 MotionMatch。这个响应路线可以借鉴，但 LGF 服务器必须做 authoritative envelope validation：

- 当前 ability/tag/stance/action lock；
- target primitive 仍有效、距离/角度/高度/深度/坡度/步行性；
- moving target 当前速度与 relative transform；
- warp 点不超服务器约束；
- SelectedMontage 属于服务器批准的当前动作候选集合；
- play rate/selected time/action tag 合法。

服务器可以不重跑完整 PoseSearch，但不能因为 `NetSerialize` 能还原 UObject 就信任客户端选择。

### Overlay / Linked Anim Layer

案例把 base layering、overlay、delta overlay、override、ragdoll 分层，并用 GameplayTag -> Task/Class 注册表动态 `LinkAnimClassLayers` / `UnlinkAnimClassLayers`。LGF 可吸收这一结构：Ability 拥有“哪个 overlay gameplay state 活着”，Task/Component 负责 presentation layer linkage。

不要照搬其当前每 Tick 构造 overlay tag mask + `GetOwnedGameplayTags` + Filter 的扫描方式到大规模项目；优先缓存 mask 或用 GameplayTag change event 驱动状态边界。换 Pawn/Mesh/AnimInstance 后旧 linked instance 指针失效，必须按 Avatar generation 重新解析。

### Ragdoll 单一生命周期 Owner

案例最新 PhysicsControl 路线里 `UGarRagdollingTask` 是 Start/Stop 的唯一 owner；Ability 负责政策/转移，PhysicsControl 负责刚体，Mover 负责 capsule/frame，Linked Layer 负责 blend/snapshot。LGF 应采用同样的职责分割，而不是 GAS Tag、PhysicsControl、AnimBP 和 Mover 都各自看到状态后自行 Start/Stop。

Dedicated/服务器 remote pawn 不一定评估动画，所以 Authority 完成条件不能依赖最终 Anim blend callback。需要进入重演的 pelvis/top-body transform 在 simulation 外记录到 Mover input；Mover finalization 不能 teleport 正在模拟的 body。

## ALS-Refactored 对 LGF 的生产补充（2026-09-14）

固定案例：`Sixze/ALS-Refactored@b754d6f0f2bb03741d301f8fb88077ebfe561e17`。该提交当前 `ALS.uplugin` 为 4.18 / UE 5.8.0；README 的 release 表仍显示 4.17 / UE 5.7。LGF 自身目标版本仍以项目实际 Engine 为准，不能因为 README 写 5.7 就跳过 API 复核。

### CMC 网络实现只迁语义

ALS-R 用 `FSavedMove_Character + FCharacterNetworkMoveData` 把 RotationMode/Stance/MaxAllowedGait 纳入 prediction、move combine、replay 和 server MoveAutonomous。LGF 已采用 Pawn + Mover，所以对应迁移是：

- 影响 movement outcome 的状态写入 Mover Input/Sync/Persistent State；
- resim 消费 recorded state；
- 自定义字段参与 reconcile/interpolate/merge；
- 不把 `UAlsCharacterMovementComponent`、复制的 `PhysWalking` 或 CMC RootMotionSource 迁进 LGF。

复制引擎 movement body 会形成 engine-upgrade fork debt；LGF 优先使用 Mover 当前版本的正式扩展点。

### Push Model / Iris 作为完整网络合同

ALS-R 同时提供了两个提醒：Push Model 属性在 Authority mutation 后要 dirty；自定义 Mantling RootMotionSource 还显式出现在 Iris serializer 支持配置里。

因此 LGF 新增 replicated movement/presentation state 时，必须分别回答：

1. Legacy/Push Model 如何声明和标脏；
2. Iris 是否需要 custom descriptor/serializer registration；
3. 该字段是否已经在 Mover prediction 数据中，额外 property replication 是为了谁；
4. Listen/Dedicated/JIP/correction 下是否都收敛。

### SimProxy / Listen Server 的视觉链分开验收

ALS-R 的 production 经验表明：

- Actor transform smoothing；
- view/aim rotation smoothing；
- visual mesh rotation / Anim tick；

不是同一条链。

LGF 的 GASP/变身/骑乘验证也要分别测。远程 AutonomousProxy 在 Listen server 上可能需要更高 pose tick 保证 RootMotion/动画状态；URO 时 visual mesh correction 也可能必要。但这都不能做成全局默认，尤其 rotating mount/platform 会让某些 absolute rotation 修正反向产生 jitter。

所有优化应放入 Avatar animation profile / scalability policy，并覆盖：Standalone、Listen local、Listen remote、Dedicated、client SimProxy、URO 开关、static/moving/rotating base。

### Property Access 写相位

ALS-R 对 Linked AnimInstance 的警告值得直接采用：Property Access 只允许读取在并行动画求值前已经完成写入、且 worker 读取期间不会再变化的 Parent AnimInstance snapshot。

LGF 的 animation provider 应把字段分成：

- GT snapshot；
- worker pure derived state；
- post-update result；
- gameplay UObject truth。

只有第一类和官方允许的 proxy data 默认可供 Linked Layer AnyThread 消费。`BlueprintThreadSafe` 不替代这个 ownership contract。

### Mantle RootMotionSource 翻译为 Mover movement transaction

ALS-R 的 Mantle RootMotionSource 值得吸收的是：stable ID、start/target、target primitive、moving-base local space、time、NetSerialize、cancel identity。

LGF 继续用 Mover：

`GAS action -> validated traversal transaction -> Mover LayeredMove/Mode -> animation follows transaction time`

TargetPrimitive 移动时使用 base-relative 数据；target destruction/teleport/reparent 必须终止或重解 transaction。LGF 仍需 Authority 重新验证客户端 traversal envelope，不照搬 ALS-R 的轻量 server start check。

### Camera 不双栈

ALS-R CameraComponent 与 LGF/GASP 的 GameplayCamera 是两种 runtime owner 方案。LGF 不并挂第二套完整 ALS camera。可吸收 pivot、lag、trace、movement-base 算法，重新实现到 GameplayCamera rig/policy。A/B 测试用 feature gate，一次只激活一个 owner。
