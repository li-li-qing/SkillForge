# SAM-tak/GASP-ALS-R 项目蒸馏：第五轮

检查日期：2026-09-14  
来源：`SAM-tak/GASP-ALS-R`  
固定源码快照：`a227dfecfcb2719c2541218cf026c05dfe3290ec`（main）  
快照特征：2026-09-13 合并 `feature/mover`。

> 本轮研究目标与前四轮不同：不是再看 Inventory/GAS 框架，而是深入 **Pawn + Mover + GASP Motion Matching + ALS 风格 Linked Animation Layers + GAS Action Ability + Motion Warping + PhysicsControl Ragdoll + GameplayCamera** 的真实源码边界。对 LGF 的目标是优化现有 UE5.7 动画/移动 Skills，不复制第二套 GAR 框架。

## 1. 许可、版本与证据边界

### 1.1 许可不是一个 SPDX 能概括

GitHub repository metadata 对许可证显示为 `NOASSERTION / Other`。README 与仓库文件给出了更细的边界：

- UE-only Content 受 Unreal Engine 内容许可约束；
- 项目原创 C++ 与 ALS-Refactored 派生 C++ 使用仓库的 `LICENSE-for-cpp-source-codes`，其文本为 MIT 路线；
- 标记为从 Unreal Engine source 派生的代码继续受 Unreal Engine EULA 约束；
- 因此不能把整个项目统一标成 MIT，更不能把 Content 当普通 MIT asset 搬进其他生态。

对 SkillForge 的处理：**吸收模式，不复制受限实现；每次真正迁代码前重新检查具体文件头和许可证。**

### 1.2 当前 main 更接近 UE5.8.2，不是 LGF 的 5.7 构建证明

当前专门 Character 文档记录了项目在 custom UE 5.8.2 上的 Mesh/Anim 初始化 workaround。`GAR.uplugin` 同时依赖：

- Mover；
- NetworkPrediction；
- GameplayCameras；
- PhysicsControl；
- PoseSearch；
- Chooser；
- MotionWarping；
- AnimationWarping；
- GameplayAbilities；
- ModularGameplay。

这些都是引擎小版本变化较快的区域。

LGF 当前目标是 UE5.7，因此本轮结论分成：

1. **架构/所有权模式**：可以写回 Skills；
2. **具体 API/成员名**：只能作为案例，必须在 LGF 真实 5.7 Engine source 重新确认；
3. **资产结构**：没有在 LGF Editor 中实际创建/迁移，不写成已经完成。

## 2. 模块地图

`GAR.uplugin` 当前主要模块：

| 模块 | 类型 | 职责 |
|---|---|---|
| `GAR` | Runtime | Character、Mover、GAS、Animation、Overlay、Traversal、Ragdoll |
| `GARCamera` | Runtime | GameplayCamera state / perspective / shoulder |
| `GARExtras` | Runtime | 示例扩展 |
| `GARUncookedOnly` | UncookedOnly | 开发期内容 |
| `GAREditor` | Editor | 测试/编辑器工具 |

核心 runtime 责任链：

```text
AGarCharacter (APawn)
├─ UGarCharacterMoverComponent
│  ├─ Walking / Falling / Sliding / Traversal / Ragdoll Modes
│  ├─ Mover Input / Sync / Persistent State
│  └─ Trajectory Predictor + MotionWarping Mover Adapter
├─ UGarAbilitySystemComponent
│  └─ GAS Actions / Overlay abilities / tags
├─ UGarAnimationInstance
│  ├─ cached movement state
│  ├─ Pose Search / Blend Stack semantics
│  └─ Linked Anim Layers
├─ UGarPhysicsControlComponent
│  └─ Physical animation + Ragdoll
├─ MotionWarpingComponent
├─ Overlay / DeltaOverlay / Override Components
└─ UGarGameplayCameraStateComponent (GARCamera)
```

这正好覆盖用户 LGF 未来的 Pawn + Mover + GASP 方向。

## 3. 最关键架构：把一个“角色动作”拆成不同所有权域

GAR 最新实现最值得 LGF 学习的不是某个类，而是它逐渐形成了以下边界：

| 域 | GAR 当前责任 | LGF 应吸收的原则 |
|---|---|---|
| GAS | 动作可否激活、Tag、cancel/block、能力 lifetime | Gameplay policy / Authority truth |
| Mover | capsule/actor movement、prediction/resim、Mode/Layered Move | Simulation truth |
| AnimInstance | pose state、Motion Matching、Blend Stack、Layer | Presentation truth |
| MotionWarping | 目标约束 | 位移修正，不是第二 movement owner |
| PhysicsControl | rigid body/control profiles/ragdoll physics | Physics truth |
| GameplayCamera | LocalPlayer camera context | Local visual/focus truth |

一个系统可以读取另一个系统的**快照/信号**，但不能因为看到同一个 GameplayTag 就自行复制生命周期。

例如 Ragdoll：

- Ability 决定什么时候想进入/离开；
- Ragdoll Task 是 Start/Stop 唯一生命周期 owner；
- PhysicsControl 真正开关 physics；
- Mover 根据 recorded physics pose 驱动 capsule/frame；
- Linked Anim Layer 做 blend/get-up 表现。

这是以后 LGF 大型动作系统应统一的模式。

## 4. AGarCharacter：APawn + Mover，而不是 CharacterMovement

当前角色是 `APawn` 路线，并使用自定义 `UGarCharacterMoverComponent`。这与用户正在把 LGF 移动体系改为 Pawn + Mover 的方向直接一致。

值得吸收的不是 AGarCharacter 本身，而是：

- Pawn 的输入通过 `IMoverInputProducerInterface` 产生 Mover input；
- Gameplay Ability 不直接用 `SetActorLocation` 伪造根运动；
- Mover 自定义 Mode 承担 Traversal/Ragdoll/Sliding；
- MotionWarping 有 Mover adapter；
- Animation 从 Mover trajectory/state 读取，而不是 CharacterMovement 假数据。

### 4.1 不要反向把 LGF 强制变成 GAR

LGF 已有自己的：

- Full Foundation；
- ASC/Combat；
- Avatar binding；
- Equipment；
- Animation state provider；
- Mover integration 规划。

因此只能把 GAR 的责任边界映射进去，禁止：

- 引入第二个 AbilitySystem owner；
- 复制一套 Gar GameplayTags；
- 把 LGF Equipment 换成 GAR Overlay 真值；
- 因为 GAR 用某种 Mover Mode 就删除 LGF 现有可工作的扩展点。

## 5. ProduceInput 是模拟外采样，不是模拟本身

`AGarCharacter::ProduceInput_Implementation` 的源码注释非常重要：

- 在 movement simulation 之前执行；
- 对 locally controlled pawn 生成 command；
- 服务器/非控制 client 不一定执行；
- reconcile/resimulation 不重新执行该逻辑。

这给 LGF 一个明确的 Mover 规则：

> **影响历史 simulation 的 live 外部状态必须先记录到 Mover input/sync；resim 只消费记录，不重新读取“现在”的世界。**

GAR 在这里捕获：

- `bBlockCapsuleResize`：来自 GAS tag；
- `bHasRagdollTransform` + `RagdollTransform`：来自 PhysicsControl；
- RotationMode；
- Stance；
- Gait；
- jump edge；
- move/orientation intent。

### 5.1 Ragdoll transform 为什么必须在这里捕获

代码明确强调：

> capture before controller/block-input early returns; replay consumes this snapshot, never a fresh read of local skeletal mesh inside Mover simulation.

如果 Resim 重新读取当前 ragdoll pelvis，历史 frame 就会使用“未来的 physics pose”，Authority 和 client 必然可能分叉。

同理未来 LGF 的：

- lock-on target direction；
- aim assist result；
- shape-specific stance；
- mount steering constraints；

如果进入预测移动结果，也必须决定是“recorded input”还是“simulation deterministic query”。不能边写边猜。

## 6. FGarCharacterMoverInputs：自定义 Mover Data 的完整模板

该 struct 不只放字段，它实现：

- equality；
- `Clone()`；
- `NetSerialize()`；
- `ShouldReconcile()`；
- `Interpolate()`；
- `Merge()`；
- debug `ToString()`。

包含：

- RotationMode；
- Stance；
- Gait；
- bBlockCapsuleResize；
- bHasRagdollTransform；
- RagdollTransform。

### 6.1 SkillForge 新增规则

以后任何 LGF Mover custom state review 都必须问：

```text
字段加入了吗？
↓
NetSerialize 呢？
ShouldReconcile 呢？
Interpolate 呢？
Merge 呢？
默认值 / loading reset 呢？
Proxy finalization 怎么消费？
```

只加 `UPROPERTY` 不算功能完成。

### 6.2 离散状态不能乱插值

GAR 对 Rotation/Stance/Gait 采用 closest state（Pct<0.5 用 From，否则 To），这是合理例子。

- GameplayTag / enum / bool：step/nearest；
- Vector / transform / speed：按实际语义插值；
- event edge：不能通过普通插值生成。

## 7. FGarCharacterMoverSyncState：Input 和 Sync 不是一回事

项目还定义独立 `FGarCharacterMoverSyncState`，包含 RotationMode/Stance/Gait，并实现同样的 reconcile/interpolate/merge 语义。

这提醒 LGF：

- Input 是“本 frame 想做什么/采样了什么”；
- Sync State 是“模拟后达成了什么”；
- Presentation replicated field 只是“别人显示什么”。

不要把三个域合成一个 Replicated GameplayTag 变量，然后既当 input 又当 simulation state 又当 UI truth。

### 7.1 当前源码可继续审查的细节

`FGarCharacterMoverSyncState::NetSerialize()` 当前直接 `bOutSuccess = true`，而 Input 版本会合并 `Ar.IsError()`。这不是本轮要修的第三方代码，但说明即使架构很先进，具体 serializer 仍需逐字段 review。

## 8. Movement Modifier：文档存在不等于运行时正在用

`UGarCharacterMoverComponent.h` 当前：

`#define GAR_USE_MOVEMENTMODIFIER 0`

也就是源码实际上没有把 Rotation/Gait/Stance 全走 Movement Modifier；而是以 input/sync/replicated tags 等组合管理。

因此 SkillForge 已纠正一个潜在过度抽象：

> 不要规定“所有 stance/gait/rotation 都要变成 Movement Modifier”。

应该按问题选择：

- Movement Mode：长期互斥运动模型；
- Layered Move：临时叠加位移；
- Instant Movement Effect：瞬时跳跃/几何变化；
- Persistent Sync State：跨 Mode/Resim 的中间状态；
- Modifier：目标版本真正支持且适合的参数约束。

## 9. 当前 Mover source 还有一个必须保留的风险证据

Header 中 `GetLifetimeReplicatedProps` 的声明在 `#if !GAR_USE_MOVEMENTMODIFIER` 下被注释，而 cpp 在对应条件下存在 `UGarCharacterMoverComponent::GetLifetimeReplicatedProps` 定义。

静态阅读上这是一个需要真实 UBT 验证的声明/定义不一致风险。本轮没有本地拉取 GAR 工程并使用其 custom UE5.8.2 编译，所以：

- 不宣称该 commit build-green；
- 不把源码直接 copy 到 LGF；
- 项目报告保留这一 active-development 信号。

## 10. Stance / Capsule：不是“把 CapsuleHeight 改一下”

Mover 文档与源码为 stance 建立了：

- `FGarMoverStanceState` persistent state；
- `FGarMoverCapsuleResizeEffect`；
- Mover timestep 驱动 interpolation；
- foot-preserving pivot；
- eye height；
- collision/weld state；
- mesh offset；
- floor query / movement-base cache invalidation；
- proxy finalization 投影同步 geometry。

这对未来 LGF 变形尤其重要。

### 10.1 变 Prop / 骑宠物可能改变 Capsule

如果 NPC/Prop/坐骑改变碰撞体：

- 不能只在 Avatar Attach 时 SetCapsuleSize；
- 如果变化进入 predicted movement，它必须成为 simulation state；
- correction/resim 要能重建同一个中间尺寸；
- foot/pivot 与 based movement 不能错位；
- Proxy 不应该自己跑一套 shape transition timer。

## 11. Animation 主线程/工作线程分界

`UGarAnimationInstance` 很适合拿来验证用户“运行时/算法 C++ 化、保留 ABP”的方向。

### 11.1 NativeUpdateAnimation（Game Thread）

当前会读：

- ASC OwnedGameplayTags；
- Mesh component transform；
- MotionWarp target；
- LocomotionAction；
- Mover velocity / acceleration / deceleration；
- gravity；
- view rotation；
- movement intent；
- floor hit；
- trajectory predictor。

然后形成 `FGarCharacterMovementState`、tag snapshot 等。

### 11.2 NativeThreadSafeUpdateAnimation（worker-safe stage）

当前只：

- 刷新 LayeringAnimInstance；
- 通过 AnimInstanceProxy curves 刷 PoseState。

这形成清晰边界：

```text
Mutable UObject / GAS / Mover
       ↓ Game Thread sample
compact animation state
       ↓
NativeThreadSafeUpdate / AnimGraph
       ↓
Pose
```

### 11.3 对 LGF 的结论

用户此前担心“是不是必须像 GASP 示例那样大量蓝图”。这个项目提供了很好的中间方案：

- C++：采样、trajectory analysis、状态历史、网络、安全、生命周期；
- ABP/Linked Layer：姿势连接、Animation Layer、节点级 Motion Matching/IK/Blend；
- Data Asset/Chooser/PoseSearch DB：内容数据。

不需要把 AnimGraph 全部硬编码 C++，也不应该让 ABP 负责服务器动作真值。

## 12. BlendStack / Motion Matching：C++ 做状态派生，资产做动画搜索

`UpdateBlendStackLocomotion()` 在 C++ 中计算：

- velocity / Speed2D；
- future facing；
- angular velocity；
- circling；
- stance/gait history；
- movement mode history；
- movement direction + hysteresis；
- ground normal smoothing；
- slope angle；
- aim offset。

这个分层非常适合 LGF：

- 数学、状态历史、过滤：C++；
- PoseSearch schema/database/Chooser：Data Driven；
- 最终 Graph：ABP。

## 13. PoseHistory 的真实线程同步成本

`UGarGameplayAbility_MotionMatchBase::MotionMatch()` 有一个非常重要的调用：

`HandleExistingParallelEvaluationTask(true, true)`

原因：

- PoseHistory 在并行动画 evaluation worker thread 写；
- Gameplay Ability 在 Game Thread 读取；
- 不同步会产生 data race。

### 13.1 这是正确性 fence，不是免费 API

所以：

- Roll/Traversal/Landing 激活时偶尔做一次：合理；
- 每帧 Aim/Overlay 都做：危险；
- 一次攻击按键连续做很多次：需要 profile；
- 同时同步 Load asset：更加危险。

未来 LGF 应在 Unreal Insights / Anim Insights 中观察：

- ParallelAnimEvaluation 等待时间；
- PoseSearch cost；
- action burst；
- GameThread stall。

## 14. Montage Root Motion 被交给 Mover LayeredMove

`UGarGameplayAbility_MontageBase` 的关键流程：

1. ASC 播 Montage；
2. 取得活跃 `FAnimMontageInstance`；
3. `PushDisableRootMotion()`；
4. 构建 `FLayeredMove_AnimRootMotion`；
5. 写 Montage / PlayRate / StartingPosition / Duration；
6. `Character->GetMover()->QueueLayeredMove(...)`。

这清楚证明：

> Montage 可以负责动画时间，但 Actor 位移交给 Mover simulation。

### 14.1 LGF 必须比案例再多一步：保存 Layered Move identity

当前源码展示了 queue，但本轮看到的 `EndAbility` 主要负责：

- montage notify cleanup；
- cancel 时 StopMontage；
- remove temporary GEs。

没有在这段路径里看到明确保存/取消该 `FLayeredMove_AnimRootMotion` handle 的证据。

因此 LGF 的正式规则是：

- queue 时保存真实 Mover handle/operation identity；
- End/Cancel/Interrupt/Avatar switch 成对 cancel；
- 清 Warp Target；
- 防迟到 Notify；
- 最终 Authority/Proxy capsule 必须收敛。

不能假设“Montage 停了，Mover root move 自然也停”。

## 15. Motion Warp 是修正器，不是 Movement System

Traversal 使用：

- FrontLedge；
- BackLedge；
- BackFloor；
- montage warp windows；
- `Distance_From_Ledge` curve。

项目注释自己也说明当前 traversal 是相对简单的 demonstration，统一动画 metrics 会更稳。

LGF 应记录三条独立链：

```text
动画选择
Root Motion extraction / Mover consumption
Warp target correction
```

任何一条“看起来有值”都不能证明另外两条正确。

## 16. Traversal：客户端本地选动画，然后 TargetData 给服务器

这是本轮网络安全最重要的案例之一。

`TryActivateTraversal()`：

1. 找 InstancedPerActor ability；
2. 本地 `CanActivateAbility`；
3. trace / Chooser / MotionMatch；
4. 把结果存 `FGarTraversalTargetData`；
5. `HandleGameplayEvent` 进行 LocalPredicted 触发。

`FGarTraversalTargetData::NetSerialize()` 发送：

- SelectedAnim UObject；
- WantedPlayRate；
- SelectedTime；
- Chooser tags；
- TargetPrimitive UObject；
- FrontWallNormal；
- FrontLedgeLocation；
- UpperLedgeNormal；
- BackLedgeLocation；
- BackFloorLocation。

### 16.1 好处

Server 不必重复最昂贵的 MotionMatch，预测手感好。

### 16.2 风险

源码 `CanActivateAbility` 对“服务器拥有 remote AutonomousProxy”路径直接允许继续，并依赖 client EventData，而没有在本轮阅读到完整服务器几何重验。

这意味着 LGF 不能原样吸收。

## 17. LGF Traversal 的 Authority Envelope Validation

服务器不必重跑完整 PoseSearch，但至少做：

### 17.1 Gameplay validation

- 当前 ASC 有这个 ability；
- 当前 action lock；
- 当前 stance/gait/locomotion；
- cost/cooldown/tag；
- 没有 Dying/Unconscious 等 blocked state。

### 17.2 Geometry validation

- target primitive 仍 valid；
- 与 server pawn 的 reach/angle；
- obstacle height/depth；
- ledge normal/slope；
- floor walkability；
- target speed；
- moving platform transform generation；
- warp point 偏差上限。

### 17.3 Asset validation

- SelectedMontage 在 server-approved candidate set；
- action tags 与 montage bucket 对应；
- play rate/time 范围；
- 不允许 client 指定任意 montage/object path。

### 17.4 Reject / Correct

失败：

- End/cancel predicted ability；
- 清 predicted Warp target；
- 清 Mover action/layered move；
- 不产生伤害/奖励/消耗。

## 18. Traversal static ParameterMap：值得继续关注的 active-development 点

源码使用：

`static TMap<FGameplayAbilitySpecHandle, FGarTraversalParameters> ParameterMap`

来跨 `CanActivateAbility -> ActivateAbility` 保留本地选择结果。

本轮 code search 只看到 add/contains/read，没有找到明确 `ParameterMap.Remove` 证据。

这不等于一定泄漏（可能完整文件/生命周期还有其他机制），但它是应在生产迁移时核验的风险：

- SpecHandle 是否全局唯一到足以做 static key；
- Ability remove 后是否清理；
- Avatar/ASC 重建后旧数据是否残留；
- 多 world/PIE 是否污染。

LGF 应优先把 transient action data 绑定到 ability instance/prediction/action operation，而不是不受生命周期约束的 static map。

## 19. Overlay 系统：Tag -> Task -> Linked Anim Class

GAR 把 Overlay 设计成：

```text
Overlay GameplayAbility
   ↓ OnGiveAbility / OnAvatarSet
Register OverlayTag -> OverlayTaskClass
   ↓
OverlayModeComponent
   ↓ state transition
OverlayTask
   ↓
LinkAnimClassLayers
```

结束：

```text
Task OnFinished
   ↓
UnlinkAnimClassLayers
```

### 19.1 这是用户未来武器动画很有用的模式

枪、剑、弓、盾、乐器等不要复制整个 locomotion AnimBP。

可以：

- Base locomotion 保持 GASP；
- 装备 Tag 选择 Overlay；
- 轻微握姿用 DeltaOverlay；
- 完整动作用 Override / Montage Ability。

这样 NPC 变身或骑宠物也能按 Avatar capability 选择是否装这些 Layer。

## 20. Overlay 当前也有性能反例

`UGarOverlayModeComponent::OnOwnerTick` 当前每 Tick：

1. 遍历 `OverlayClassMap` 重建 Tag mask；
2. `GetOwnedGameplayTags`；
3. Filter；
4. 判断 overlay change；
5. Tick CurrentOverlayTask。

小项目可以工作，但大规模装备/Tag 项目不应直接照搬。

LGF 优先：

- cache overlay mask；
- GameplayTag event / tag count change 驱动切换；
- 只有真正需要连续更新的 task 才 tick；
- Link/Unlink 只在边界做。

## 21. SimulatedProxy Overlay 的显式补偿

`UGarAbilitySet::GiveToAbilitySystem` 对非 Authority 一般不 grant，但对 SimulatedProxy 有额外逻辑：遍历 GrantedGameplayAbilities，把 Overlay/Delta/Ragdoll task class 注册到 presentation component。

源码自己有 TODO：希望迁到 ASC 的 replicated abilities callback。

这说明一个很重要的事实：

> “Ability 在服务器 grant 并复制”不自动意味着所有客户端本地 presentation registry 都准备好了。

LGF 如果使用 Ability CDO 提供 animation presentation metadata，需要明确：

- Owner client；
- SimulatedProxy；
- JIP；
- Ability remove；

各自什么时候建立/删除本地注册表。

## 22. Ragdoll：UGarRagdollingTask 是唯一物理 owner

最新源码比早期 ALS 风格更清晰。

`UGarRagdollingTask::Begin()`：

- 检查当前 tag 有 RagdollSettings；
- `PhysicsControl->StartRagdoll(tag)`；
- 设置 `bOwnsPhysicsRagdoll`；
- `SetRagdollingTaskActive(true)`；
- 通知 override anim instance。

`End/Cancel()`：

- 统一 `StopPhysicsRagdoll()`；
- 只在 `bOwnsPhysicsRagdoll` 时 stop；
- 清动画 override state。

这就是**单一 lifecycle owner**。

## 23. Remote Authority 不等待 Animation Epilog

`IsEpilogRunning()` 对：

`HasAuthority() && !IsLocallyControlled()`

直接返回 false。

源码解释：服务器 remote pawn 不评估动画，所以 ObservingFinalBlendWeight 永远不会到 1。

这对 LGF Dedicated Server 非常关键：

- Authority 动作完成不能依赖视觉 blend callback；
- Anim blend 是本地表现 epilog；
- Server 有独立 gameplay completion path。

否则 dedicated 上 Roll/Death/Ragdoll recovery 可能永久卡死。

## 24. PhysicsControl / Mover / Mesh Frame 分权

专业 PhysicsControl 文档明确：

- PhysicsControl 是唯一 physical-animation/ragdoll component；
- Mover capsule 跟随 TopBone physics body；
- settled body 可变 Kinematic + pose snapshot；
- root body simulated 时，Mover 仍可能拥有 SkeletalMesh component frame；
- 普通 component move 要避免把 simulated bodies teleport。

这里对 LGF 的规则：

> **Actor/Mesh component transform 与 Chaos body transforms 是两个层。**

Visual smoothing/finalization 不应该重置 ragdoll body velocity。

## 25. PhysicsControl Profile：Data Driven，而不是 state switch 硬编码数值

GAR 使用：

- GameplayTagContainer -> Chooser；
- Control Profile；
- Constraint Profile；
- Body Modifier sets；
- curve -> Body Modifier set blending。

这与用户“动画 Data Driven、算法 C++”目标一致。

可把：

- Default；
- Traversal；
- InAir；
- Rolling；
- Ragdoll；

的 physics tuning 放配置/Chooser，而不是一堆 C++ if 写 drive strength。

## 26. Curve-driven Physics：隐藏物理 pose 不等于弱化 drive

PhysicsControl 文档提醒：

Curve value 负责 Animation Pose / Physics Pose blend，但不应该同时因为视觉上暂时隐藏 physics contribution 就弱化 control drive。

否则 body 会在不可见时漂移，physics contribution 再回来时产生大角度 snap。

这是一条很好的“视觉权重 ≠ 模拟约束强度”规则。

## 27. GameplayCamera：Desired State 与 Active Context 分开

`UGarGameplayCameraStateComponent` 是 PawnComponent。

复制：

- `DesiredPerspective`；
- `DesiredShoulderMode`。

本地：

- 当前 Perspective；
- current shoulder；
- camera evaluator/context；
- active PlayerCameraManager；
- camera variables。

### 27.1 Possession lifecycle

OnPossessed：

- 仅 LocalController；
- 如果相同 manager/context 已 active，直接 return；
- 先 Stop 旧 camera；
- GameplayCamerasPlayerCameraManager 路线 `ActivateGameplayCamera`；
- 普通 CameraManager 则 standalone fallback。

OnUnPossessed / EndPlay：

- stop rigs/context；
- reset ActiveCameraManager。

特别好的源码注释：**stop rigs before destroying their context**，否则 blending-out rig 可能继续引用已 UnPossess 的 Pawn。

## 28. Camera 不应该成为服务器伤害真值

当前 Camera component 还能用 Unreliable Server RPC 发送 CameraLocation/Rotation。

这对瞄准辅助有用，但 LGF 必须坚持：

- client camera transform 是 view sample；
- 服务器检查位置/角度/速率；
- 最终 trace/hit/LOS/伤害继续 Authority；
- 不因为 Camera RPC 更新频率高就直接采用命中结论。

### 28.1 当前代码条件值得二次 review

Tick 中 camera change 的 `if` 混合 `&&` 与 `||` 而没有完整括号；按 C++ precedence，rotation change 分支可能绕开前一半 role 条件。迁移时必须把网络发送条件写成显式括号/局部 bool，而不是复制原表达式。

## 29. Camera context 不每 Tick Force ViewTarget

GAR 新文档明确当前路线不每 Tick 强制 ViewTarget，也保留手动 debug target。

这是 LGF 正确方向：

- possession/focus 生命周期决定 context；
- temporary camera/cinematic 可以压栈；
- 不用 Tick 把玩家镜头抢回来。

## 30. Character 文档存在 drift：必须源代码优先

`Documents/Character.md` 的一处 overview 仍列出 `UGarPhysicalAnimationComponent`，但新的 `PhysicsControlRagdolling.md` 明确：

> `UGarPhysicsControlComponent` is GAR's sole physical-animation and ragdoll component. `UGarPhysicalAnimationComponent` is not part of GAR anymore.

因此本轮明确把“文档漂移检测”加入外部项目研究规则：

1. README 做入口；
2. 专项新文档；
3. 当前 header/cpp；
4. commit 日期；
5. 冲突时不把旧 overview 当真值。

## 31. Engine workaround：bUseRefPoseOnInitAnim 不宜泛化

项目针对 custom UE5.8.2 的 Blueprint reinstancing / child mesh collapsed 问题采用 `bUseRefPoseOnInitAnim` workaround。

这个案例说明：

- 有时“角色缩成一团”不是 retarget 或骨架错误；
- 可能是 animation initialization / transform buffer / LOD/reinstancing。

但它是版本/项目特异问题，不能写成“所有 GASP Mesh 都开启这个 flag”。

LGF 遇到类似问题应走 evidence-driven diagnosis：

- runtime pose buffer；
- component tick；
- LOD；
- anim init；
- editor reinstancing；
- packaged runtime。

## 32. 自动化测试是亮点，但不能替代网络 PIE

GAR 当前 GAREditor 下已经有：

- Mover Stance tests；
- PhysicsControl tests；
- serializer/geometry 等相关验证。

这非常值得 LGF 学习：移动/物理算法不要只靠肉眼。

但文档仍明确 full gameplay/network validation 需要做。

LGF 应同时保留：

### Automation

- NetSerialize round trip；
- reconcile/interpolate；
- stance geometry；
- cache invalidation；
- ragdoll frame/body invariants。

### PIE / Dedicated

- Host；
- Autonomous remote；
- SimulatedProxy；
- JIP；
- packet lag/loss；
- correction/resim；
- action cancel；
- moving platform traversal。

## 33. 对用户 LGameplayFramework 的直接迁移建议

### 33.1 保留现有 LGF 稳定 owner

前一轮 AyaDog 已经收敛：

- PlayerState/Agent：长期 ASC/Inventory/Loadout；
- Avatar Pawn：Mover/Mesh/Anim/Physics/Camera/applied presentation。

GAR 进一步补齐“Avatar 内部如何装动画/移动/物理”。

### 33.2 Avatar 形态描述建议增加 animation capability

未来每种可吸收 NPC/Prop/宠物形态可以有 DataAsset/descriptor：

```text
AvatarForm
├─ PawnClass / Mover config
├─ Skeletal or Prop presentation
├─ AnimProfile
│  ├─ Main AnimClass
│  ├─ Base PoseSearch profile
│  ├─ Overlay capability tags
│  └─ Runtime Retarget profile
├─ PhysicsProfile
├─ CameraProfile
├─ EquipmentCompatibility
└─ AuthorityTraceProfile
```

不要把这些能力写死在 Character subclass if/else。

### 33.3 变身 Detach

依次：

1. block new avatar actions；
2. cancel old action abilities；
3. cancel Mover LayeredMoves；
4. clear Warp Targets；
5. end overlay/ragdoll task；
6. unlink dynamic anim layers；
7. remove equipment presentation + trace；
8. unbind old mover/anim/physics delegates；
9. stop local camera context；
10. bump avatar generation。

### 33.4 Attach

1. spawn/possess new Pawn；
2. Init ASC ActorInfo；
3. initialize Mover/collision；
4. initialize PhysicsControl；
5. assign Mesh/Anim/Retarget profile；
6. reset/reseed trajectory + PoseHistory；
7. register overlay classes；
8. initialize camera context；
9. reapply compatible loadout/equipment；
10. unblock actions。

## 34. 对 ABP/C++ 分工的最终结论

用户希望“算法/运行时 C++ 化、动画 Data Driven、保留 ABP，避免蓝图”。GAR 最新代码给出的可行方案是：

### C++

- network/prediction state；
- movement math；
- tag snapshot；
- trajectory-derived history；
- action lifetime；
- overlay/task lifecycle；
- physical lifecycle；
- camera lifecycle；
- performance instrumentation。

### AnimBP / Linked Layer

- Motion Matching nodes；
- Blend Stack wiring；
- pose graph；
- IK / aim offset；
- layer composition；
- visual transitions。

### Data

- PSD/PSS；
- Chooser；
- AnimMontage；
- PhysicsControl profiles；
- Camera variables/settings；
- Form/weapon animation profiles。

这比“全部蓝图”更可维护，也比“AnimGraph 全写 C++”更符合 UE 动画工具链。

## 35. 不应直接复制的内容

1. UE5.8.2 API 到 LGF UE5.7；
2. 整个 GAR GameplayTag tree；
3. 每 Tick Overlay mask + ASC scan；
4. 客户端 Traversal TargetData 无服务器 envelope validation；
5. 没有明确 cancel handle 的 Layered RootMotion 生命周期；
6. static Traversal ParameterMap 未证实 cleanup；
7. Camera RPC 表达式未经二次网络审查；
8. 文档中已漂移的 PhysicalAnimation 引用；
9. 项目特异 `bUseRefPoseOnInitAnim` workaround；
10. UE-only Content / UE source-derived 代码越过许可证边界。

## 36. 本轮写回 SkillForge 的规则

### UE C++

新增 `mover-animation-network-patterns.md`：

- replay-safe Mover input；
- custom state serializer/reconcile/interpolate/merge；
- GT/worker animation boundary；
- PoseHistory fence；
- client traversal validation；
- root motion LayeredMove lifecycle；
- ragdoll lifecycle owner；
- GameplayCamera context ownership。

### LGF

加强：

- `gasp-mover-integration.md`；
- `avatar-and-assets.md`；
- `external-project-patterns.md`。

重点落到：

- UE5.7 version gate；
- Avatar generation；
- transform/riding rebind；
- Linked Layer cleanup；
- PoseHistory reset；
- Physics/Camera cleanup。

### Blueprint

新增 `linked-animation-layer-boundaries.md`：

- AnimBP 不拥有 Authority；
- Linked Layers 做正交 presentation composition；
- state boundary Link/Unlink；
- AnyThread 只读快照；
- Avatar/AnimInstance rebuild 后旧 linked instance 失效。

## 37. 新增行为评测

- CPP-24：Mover recorded input / resimulation；
- CPP-25：Anim GT/worker / PoseHistory fence；
- CPP-26：Traversal TargetData Authority validation；
- CPP-27：Montage RootMotion / LayeredMove cancel；
- CPP-28：Ragdoll single lifecycle owner；
- CPP-29：GameplayCamera possession context；
- LGF-21：GAR -> LGF pattern migration；
- LGF-22：Transform/Riding avatar animation rebind；
- BP-03：Linked Anim Layer / ABP responsibility。

## 38. 后续可以继续深挖的 GAR 子主题

本轮已经覆盖主链，但后续如果单独做第二轮 GAR，可继续：

- Sliding/Rolling 自定义 Mover Mode 参数；
- landing / impact velocity 到 action selection；
- GameplayCamera sight/trace 的服务器验证；
- PhysicsControl profile chooser 资产；
- GAR Editor tests 的具体断言；
- MotionWarp moving platform follow component；
- SimulatedProxy ability registration；
- BlendStack vs full PoseSearch locomotion的成本比较。

这些暂不扩大本轮范围，避免一次研究过深导致 Skills 难以维护。

## 39. 本轮结论

GASP-ALS-R 最新 Mover 路线对 LGF 最有价值的最终结论可以压缩成一句话：

> **GAS 决定动作是否合法和何时活着，Mover 负责可预测/可重演的世界位移，AnimInstance/Linked Layers负责 pose，PhysicsControl负责刚体，GameplayCamera负责本地视角；跨域只通过记录状态、稳定身份和显式 lifecycle 连接，不让任意一个系统成为全能状态机。**

这正好适用于用户未来的吸收 NPC、Prop 形态、宠物/坐骑、多武器 Overlay 与 UE5.7 Pawn+Mover ARPG。
