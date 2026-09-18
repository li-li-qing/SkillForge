# Sixze/ALS-Refactored 项目蒸馏：第六轮

检查日期：2026-09-14  
来源：`Sixze/ALS-Refactored`  
固定源码快照：`b754d6f0f2bb03741d301f8fb88077ebfe561e17`（main）  
固定 Tree：`a2aa72d355385621f05154b15c8863be0862f2ec`  
许可证：MIT。

> 本轮目标不是把 ALS-Refactored 并入 LGF。LGF 已明确采用 **Pawn + Mover + GASP/GAS + GameplayCamera** 路线，因此本轮专门从 ALS-R 中蒸馏其成熟的 **网络预测、SimulatedProxy、动画线程、Linked Anim Blueprint、RootMotionSource、Push Model/Iris、URO、movement-base 和相机工程经验**，并把 CMC 特有实现翻译成 Mover 语义。

## 1. 版本与证据边界

### 1.1 README 与当前 main 存在版本漂移

固定提交的 README 发布表仍写：

- ALS-R 4.17；
- Unreal Engine 5.7。

但同一固定提交的 `ALS.uplugin` 已写：

- `VersionName = 4.18`；
- `EngineVersion = 5.8.0`。

因此本轮对“当前 main”的判断顺序是：

1. 固定 commit；
2. `.uplugin`；
3. 当前源码；
4. README 作为发布说明与设计目标。

不能因为 README 还写 5.7，就把当前 main 的具体 API 当成 LGF UE5.7 可直接复制实现。

### 1.2 许可边界

仓库 metadata 与许可证文件都指向 MIT。与上一轮 GASP-ALS-R 不同，ALS-R 本身的源码研究没有“整个仓库一部分 UE-only content、一部分 MIT C++”那种复杂分区。

仍然遵守 SkillForge 原则：

- 不复制整段第三方实现进 Skills；
- Skills 记录机制、风险、接口边界与迁移策略；
- 真正迁代码时再按具体文件检查 copyright / license。

## 2. 当前模块地图

`ALS.uplugin` 当前固定提交主要模块：

| 模块 | 类型 | 主要职责 |
|---|---|---|
| `ALS` | Runtime | Character、CMC locomotion、Animation、Actions、RootMotionSource、ControlRig 节点 |
| `ALSCamera` | Runtime | 第三/第一人称 camera component、lag/trace/pivot |
| `ALSExtras` | Runtime | 示例 character/input/content integration |
| `ALSEditor` | UncookedOnly | AnimGraph node、editor tooling |

依赖里包含：

- ControlRig；
- EnhancedInput；
- GameplayTagsEditor；
- PropertyAccessNode；
- EngineCameras；
- Niagara；
- MetaSound；
- ACL。

它不是 GAS/Mover 项目，但在网络 locomotion 与动画工程上非常成熟。

## 3. 和 GASP-ALS-R / LGF 的定位差异

| 领域 | ALS-Refactored | GASP-ALS-R | LGF 目标 |
|---|---|---|---|
| Pawn 基类 | `ACharacter` | `APawn` | Pawn 路线 |
| Movement | CMC | Mover | Mover |
| Prediction | SavedMove / NetworkMoveData | Mover Input/Sync | Mover Input/Sync |
| 临时 traversal movement | CMC RootMotionSource | Mover LayeredMove | Mover LayeredMove/Mode |
| 动画 | ALS AnimInstance + Linked BP | GASP + Linked Layers | GASP + Data-driven layers |
| Gameplay policy | Character functions / RPC | GAS | GAS / LGF Combat |
| Camera | ALS Camera Component | GameplayCamera | GameplayCamera |
| Physics | ALS ragdoll | PhysicsControl | PhysicsControl / target project policy |

所以这轮真正的价值是：

> **从一个成熟 CMC 工程中抽取“为什么网络动画能稳定”的合同，再翻译到 Mover，而不是把 CMC 搬回来。**

## 4. CMC 网络：Rotation / Stance / Gait 不只是复制属性

`UAlsCharacterMovementComponent` 定义了：

- `FAlsSavedMove`；
- `FAlsCharacterNetworkMoveData`；
- `FAlsCharacterNetworkMoveDataContainer`；
- `FAlsNetworkPredictionData`。

它们携带：

- RotationMode；
- Stance；
- MaxAllowedGait。

### 4.1 `SetMoveFor()`

客户端创建 SavedMove 时，把当时 movement state 复制进去。

这表示：

> 这些状态是“这一历史运动帧的输入”。

不是“等服务器下一次普通属性复制回来即可”的 UI state。

### 4.2 `CanCombineWith()`

如果新旧 SavedMove 的：

- RotationMode；
- Stance；
- MaxAllowedGait

不同，则不能合并。

这非常重要。

如果错误地合并：

```text
Frame A: Running / Standing
Frame B: Crouching
```

服务器可能只收到一个被合并后的 move，历史 simulation 就丢失 stance transition boundary。

### 4.3 `PrepMoveFor()`

Prediction correction / replay 时，ALS 会把 SavedMove 的：

- RotationMode；
- Stance；
- MaxAllowedGait

重新恢复到 MovementComponent，然后重新 RefreshGaitSettings。

这就是 CMC 世界里的 replay-safe state。

### 4.4 Server `MoveAutonomous()`

服务器消费 custom network move data，设置 movement state，然后再执行 CharacterMovement 的服务器 simulation。

完整链：

```text
Local intent
   ↓
SavedMove
   ↓
NetworkMoveData
   ↓
Server MoveAutonomous
   ↓
Correction
   ↓
PrepMoveFor historical replay
```

## 5. 映射到 LGF Mover

不能写成：

```text
LGF Pawn
+ UCharacterMovementComponent
+ FAlsSavedMove
```

而是翻译为：

```text
LGF / GAS / local input
        ↓ sample before sim
Mover Input Cmd
        ↓
Mover Simulation
        ↓
Mover Sync/Persistent State
        ↓
Authority Correction / Resimulation
```

对应关系：

| CMC | Mover 语义 |
|---|---|
| FSavedMove | Recorded Mover Input |
| FCharacterNetworkMoveData | Mover input/network state |
| PrepMoveFor | Resim restores recorded state |
| CanCombineWith | Input merge/reconcile semantics |
| RootMotionSource | LayeredMove / movement transaction |

上一轮 GASP-ALS-R 已经证明 Mover 侧同样需要：

- NetSerialize；
- ShouldReconcile；
- Interpolate；
- Merge；
- Clone/copy。

这两轮互相验证了同一个原则。

## 6. 不要复制 CMC `PhysWalking()`

ALS-R 为解决特定行为复制并修改了 `UCharacterMovementComponent::PhysWalking()` 的大段 Engine 实现。

源码自己留了明确 TODO：

> 新引擎版本发布后，需要同步上游源码。

这就是典型 engine fork debt。

长期风险：

- Epic 修 walking edge case，项目不会自动获得；
- Chaos / movement-base patch 要人工合并；
- Large World fix 可能漏；
- network prediction 修复可能漏；
- 新版函数内部 invariant 改动可能让旧 copy 静默失配。

对于 LGF：

> 已经迁往 Mover，就不再因为 ALS-R 成熟而倒退回复制 CMC physics body。

## 7. Push Model：不是只有 `bIsPushBased`

ALS Character replication 使用：

```text
FDoRepLifetimeParams
bIsPushBased = true
COND_SkipOwner
```

然后各 setter / mutation path 使用 `MARK_PROPERTY_DIRTY_FROM_NAME`。

### 7.1 三段合同

Push Model =

1. Engine/project enable；
2. property declaration；
3. mutation dirty mark。

少一段都不完整。

### 7.2 为什么 Skill 需要强调

AI 很容易生成：

```cpp
Parameters.bIsPushBased = true;
```

然后在 5 个不同函数直接写属性，忘记 mark dirty。

结果通常不是 crash，而是最危险的：

- Server 值已变；
- Local Host 看起来正常；
- Remote client 某些状态永远不更新。

因此所有 push property 都要有 mutation authority audit。

## 8. `COND_SkipOwner` 不是“省带宽模板”

ALS 对很多 desired/presentation state 使用 SkipOwner，因为 owner 已有本地预测/即时输入。

但迁移到 LGF 时每个字段都要问：

- Owner 是否真的有同源 local state？
- server correction 是否有另一条通道？
- Owner 被 server 拒绝时怎么知道？
- Listen Host 有没有本地 OnRep 缺失问题？

不能因为 ALS 使用 SkipOwner，就把所有 gameplay state 都照抄。

## 9. Iris：NetSerialize 之外还有 descriptor 支持

`Engine.ini` 明确配置：

```text
SupportsStructNetSerializerList = AlsRootMotionSource_Mantling
```

这说明自定义 RootMotionSource 即使已经实现传统 `NetSerialize`，Iris 仍有自己的兼容/descriptor要求。

### 9.1 对 Mover 自定义 state 的启示

LGF / UE C++ Skill 以后遇到：

- custom Mover input；
- custom sync state；
- LayeredMove payload；
- traversal transaction；

必须分别验证：

```text
Legacy replication
Iris replication
```

不把其中一个“能编译”外推成另一个已支持。

## 10. CMC Actor smoothing 与 ALS View smoothing 分开

ALS 额外维护 `ViewState.NetworkSmoothing`。

这件事非常值得 LGF 学。

游戏里通常有至少三种 rotation：

1. Actor body rotation；
2. Controller/View rotation；
3. Visual mesh / aim offset rotation。

服务器位置 correction 平滑了 actor，不代表：

- AimOffset 平滑；
- TurnInPlace 平滑；
- remote camera-facing spine 平滑。

ALS 使用 CharacterMovement timestamp 为 View smoothing 构建 server/client time window。

结论：

> **Movement transform smoothing ≠ View smoothing。**

## 11. SimulatedProxy 不接受 server actor rotation 作为唯一真值

ALS 的 SimulatedProxy 收到 replicated movement 时，会保留自己 ALS rotation 体系所需的 rotation，而不是盲目使用 AActor 默认 replicated rotation。

原因是 ALS：

- 自己控制 character rotation；
- locomotion animation 和 foot lock 依赖它；
- movement base rotation 还需要单独处理。

Mover 项目也可能有类似问题：

- movement simulation rotation；
- visual facing；
- view facing；
- mounted base rotation

未必是一份值。

不要把所有 rotation 收敛问题简化成“多复制一个 Rotator”。

## 12. Teleport detection 是动画合同

ALS 在：

- local transform teleport；
- SimulatedProxy replicated location correction；
- replicated based movement change

检测明显跳变后调用 AnimInstance `MarkTeleported()`。

这说明 Teleport 不只是 Actor movement 事件。

动画还需要清：

- foot lock；
- previous velocity；
- turn history；
- transition prediction；
- smoothing target。

GASP/Mover 侧同样需要 PoseHistory / trajectory reset 或 reseed。

## 13. Animation Tick 顺序

ALS 在 `PostInitializeComponents()` 让 Mesh 依赖 Character tick：

```text
Character / movement state update
      ↓
SkeletalMesh / AnimInstance update
```

这确保 AnimInstance Game Thread snapshot 看到当前角色状态，而不是上一帧数据。

LGF/GASP 不一定使用同样 Tick prerequisite API，但必须保留**数据生产者先于动画采样者**的原则。

## 14. Game Thread Anim snapshot

ALS `NativeUpdateAnimation()` 做的工作包括：

- time dilation；
- mesh/proxy transform sync；
- ViewMode；
- LocomotionMode；
- RotationMode；
- Stance；
- Gait；
- OverlayMode；
- movement base；
- view；
- locomotion；
- in-air；
- feet；
- ragdoll。

这些是 Game Thread 对 mutable gameplay/character state 的采样。

## 15. Worker Thread Anim math

`NativeThreadSafeUpdateAnimation()` 再做：

- Layering；
- Pose；
- View derived state；
- Feet calculation；
- Transitions。

这里主要消费：

- AnimInstance 已缓存数据；
- AnimInstanceProxy curves；
- pure math。

这正是我们要给 LGF 保留的结构。

## 16. PostUpdate 再执行 side effects

ALS 的 post animation update 才：

- 播放排队的 transition；
- 播放 TurnInPlace；
- 停止排队 Montage；
- 执行 debug display queue。

意义：

> Worker evaluation 不应该中途去执行需要修改 UObjects / montage state 的 side effect。

先计算，再在明确 GT phase commit。

## 17. Property Access 最重要的真实注释

`UAlsLinkedAnimationInstance::GetParent()` 的代码注释明确指出：

只有 Parent AnimInstance 中那些在 `NativeUpdateAnimation()` 更新的变量，才可以谨慎地让 Property Access 在 worker 侧读取。

如果变量在其他地方改变：

- Character tick；
- component callback；
- PostUpdate；
- async completion；

它可能和 worker 同时访问。

结果不是“偶尔读旧值”这么简单，而可能是：

- data race；
- undefined behavior；
- crash。

### 17.1 这是比 `BlueprintThreadSafe` 更强的规则

团队必须维护：

```text
Field -> Writer -> Write Phase -> Reader Phase
```

而不是只看函数 metadata。

## 18. Linked Anim BP 的真正价值

ALS-R README 强调多 Linked Animation Blueprint 与 Animation Layer Interface。

它的工程意义：

- Base locomotion 保持稳定；
- overlay/weapon 可以换；
- 复杂 AnimGraph 拆分；
- 项目不需要为每把武器复制完整 locomotion graph。

上一轮 GASP-ALS-R 更进一步把 Layer 生命周期与 Gameplay Ability / Task 结合。

两个项目联合后最适合 LGF 的模型：

```text
Gameplay/GAS state
       ↓ tag/profile
Animation Presentation Registry
       ↓
Linked Layer Class
       ↓
Pose
```

## 19. GameplayTag Blend AnimNode

ALS-R 自定义 `FAlsAnimNode_GameplayTagsBlend`。

输入：

- ActiveTag；
- Tags array；
- Blend poses。

逻辑非常简单：

- invalid tag -> default child；
- valid tag -> find matched pose。

这证明 GameplayTag 可以很好地替代巨大 enum。

### 19.1 但不要让 Tag Node 成为 Gameplay Policy

AnimNode 只做：

```text
presentation tag -> pose index
```

不能反向决定：

- 是否允许攻击；
- 是否真的站立；
- 是否真的可 Mantle；
- 服务器伤害窗口。

## 20. Hot Tag lookup 的尺度边界

`Tags.Find(ActiveTag)` 对 5~15 个固定 pose 完全合理。

但如果以后 LGF 有：

- 500 把武器；
- 数百 NPC form；
- 坐骑种类；

不要把完整 catalog 直接变成 AnimNode 每帧线性查找。

应该：

```text
Form/Equipment state changed
→ resolve AnimationProfile / LayerClass / compact index
→ worker consumes compact cached value
```

## 21. Movement Settings 的 DataAsset 结构

ALS-R Movement Settings 使用：

```text
RotationMode Tag
  → Stance Tag
    → Gait Settings
```

Gait Settings 又包含：

- walk/run/sprint speed；
- acceleration/deceleration/friction curve；
- rotation interpolation curve。

这是很好的设计时数据模型。

### 21.1 Runtime 不要每模拟步遍历多层 map

推荐在：

- RotationMode change；
- Stance change；
- Gait change

时解析并缓存当前 settings。

这样 DataAsset 保持可扩展，simulation hot path 保持紧凑。

## 22. Direction-dependent speed 的多人警告

ALS-R 自己在设置中明确写：

> direction-dependent movement speed can cause jitter in multiplayer.

原因很直观：

速度上限依赖：

- 当前 movement direction；
- actor/view relation；
- prediction history。

如果 Authority 与 Autonomous 在切换边界计算不同，就会 correction。

因此未来 LGF 要做前后左右不同速度，必须把“方向分类”也纳入 prediction state / deterministic simulation。

不能只改 AnimBP stride。

## 23. Mantle 的本地 trace 很完整

ALS Mantle 本地候选检查包括：

- forward angle；
- reach；
- target primitive；
- target speed；
- step-up capability；
- wall/slope；
- downward ledge；
- capsule clearance。

这些几何规则很适合作为 traversal candidate filter 参考。

但：

> 本地 candidate filter 仍不是服务器授权。

## 24. Mantle 使用 RootMotionSource，而不是直接 Actor teleport

`FAlsRootMotionSource_Mantling` 保存：

- settings；
- target primitive；
- start loc/rot；
- target loc/rot；
- montage start time；
- duration/time。

RootMotionSource 参与 movement simulation。

这比：

```text
Tick -> SetActorLocation(Lerp)
```

可靠得多。

## 25. RootMotionSourceId = Movement Operation Identity

ALS 保存 `RootMotionSourceId`。

这条设计非常值得继续强化。

任何持续运动操作都应该可被明确指认：

- 哪一个 traversal？
- 哪一次 dash？
- 哪次 knockback？
- 哪一个 montage root transaction？

没有 operation identity，Cancel 往往只能“把同类全清掉”，容易误伤新动作。

这和 SkillForge 前几轮反复总结的 stable handle / generation identity 是同一类设计原则。

## 26. Moving platform：TargetPrimitive 的局部空间

ALS Mantle RootMotionSource 检查 movement base 是否适合 relative location。

如果适合：

- StartTransform 先按 TargetPrimitive transform 转 world；
- TargetTransform 同样处理。

因此当平台运动时，Mantle 仍然跟着目标，而不是朝“网络发送前的旧 world coordinate”爬。

LGF Mover 必须保留这个语义。

## 27. Animation montage 跟 movement transaction 时间同步

ALS RootMotionSource 每个 simulation step 根据自身 Time 计算 MontageTime，并主动同步 Montage position。

这是一条重要反转：

> **Movement transaction 是运动时间真值，Montage 跟它走。**

而不是：

> “AnimBP 播到哪，就让胶囊猜应该到哪”。

GASP-ALS-R 的 Layered RootMotion 也是同一个方向。

## 28. RootMotionSource 的 NetSerialize

它序列化：

- settings object；
- target primitive；
- packed location；
- rotation；
- montage start time。

同时实现：

- Clone；
- Matches；
- AddReferencedObjects。

这让它成为一个完整 network movement object，而不是一个临时 struct。

Mover 自定义 LayeredMove 也应该用同样的完整性思维。

## 29. ALS-R 的 Iris 配置说明自定义 movement type 需要额外工作

项目 Engine.ini 明确注册 Mantle RootMotionSource struct。

所以迁移到 Mover 后，新 custom LayeredMove / state 不能只检查：

```text
NetSerialize compiles
```

还要检查：

```text
Iris descriptor supports it
```

## 30. Server Mantle 验证不足以作为 ARPG Authority 边界

源码可见客户端本地：

- 做 trace；
- 建 Parameters；
- 本地 start；
- 发 ServerStartMantling(parameters)。

服务器入口重新检查的核心是 `IsMantlingAllowedToStart()`，没有看到完整重做 ledge envelope。

因此不作为 LGF 的安全模板。

LGF 继续要求：

- target primitive；
- distance；
- reach angle；
- surface；
- clearance；
- target speed；
- action/montage class；
- relative transform bounds

由 Authority 重新验证。

## 31. Roll RPC 也是 demo-friendly trust

客户端把：

- Montage；
- PlayRate；
- InitialYaw；
- TargetYaw

传服务器。

服务器主要检查当前是否允许 Rolling。

生产 PvP 不应信任客户端任选 Montage/PlayRate/Yaw。

这进一步证明：

> **网络平滑成熟 ≠ gameplay RPC authorization 同样成熟。**

研究开源项目要分模块评价，不能整个仓库一次打“production-ready”。

## 32. URO：默认关闭不代表不能用

ALS 构造时 `bEnableUpdateRateOptimizations = false`，README 则说支持 URO。

这不是冲突。

意思是：

- 系统有兼容路径；
- 默认不假设所有项目都该开启；
- 开启后要处理 visual mesh rotation / foot lock / proxy behavior。

LGF 应采用同样态度：优化功能是 profile/scalability 决定，而不是 locomotion framework 的硬默认。

## 33. Listen Server remote AutonomousProxy 的 Pose

ALS 明确让 server 上由远端玩家控制的 character 保持 pose tick，以减少 rolling 等问题。

原因：某些 server-side gameplay/movement 或视觉同步仍依赖动画 pose/montage state。

LGF 要问：

- server Authority 是否真的需要骨骼 pose？
- hit detection 用 capsule/weapon trace representation 还是 Mesh bone？
- root motion 是否由 Mover 独立模拟？

如果已经彻底让 gameplay 不依赖 server visual mesh，就可能不需要 ALS 的同样策略。

所以“AlwaysTickPose on server”是条件经验，不是硬规则。

## 34. Absolute Mesh Rotation 是一个条件 workaround

ALS 在：

- Mesh ticking；
- 非 Dedicated；
- 非 local；
- 不在 rotating movement base；
- URO active 或 Listen Server remote autonomous

时才考虑 absolute visual rotation。

这个条件集合本身比具体 API 更值得学习。

因为它表达：

> 一个优化 workaround 必须声明适用域和反例域。

## 35. Rotating movement base 是必须单独验收的场景

很多 locomotion demo 只测静态地面。

但未来用户的：

- 可骑 NPC；
- 移动船；
- 车辆；
- 平台；
- 大型 Boss 背部

都属于 moving/rotating base 类问题。

必须专门测：

- Actor correction；
- visual mesh；
- camera；
- foot lock；
- root movement transaction；
- rider/mount relative transform。

## 36. Camera：ALS 的 Component 架构

ALS Camera 是独立 Component，不要求 custom PlayerCameraManager / Controller。

它内部拥有：

- pivot target；
- pivot lag；
- movement-base-space lag；
- camera location/rotation；
- trace ratio；
- FOV；
- shoulder side。

这说明 camera 算法可以模块化。

## 37. 为什么 LGF 不应该同时引入 ALS Camera

上一轮 GASP-ALS-R 已研究 GameplayCamera manager/context。

LGF 当前路线也倾向 GameplayCamera。

同时运行：

```text
ALS Camera Tick
GameplayCamera Evaluator
```

会出现：

- 两套 lag；
- 两套 collision trace；
- 两套 shoulder state；
- 谁写最终 POV 不明确；
- 变身/骑乘时 cleanup 更复杂。

正确迁移：

> 保留 ALS camera 的算法思想，重写成 GameplayCamera rig/policy。

## 38. Control Rig / Foot IK 的吸收边界

ALS-R 有大量 ControlRig/RigUnit 与 Foot IK 工具。

可以吸收：

- foot target / pelvis offset 数据合同；
- ground trace / offset math；
- ControlRig 作为 presentation processor。

不吸收：

- 让 ControlRig 决定 gameplay stance；
- 让 IK error 反向修改 Authority movement；
- 为某个 Skeleton 固定 bone layout 并假设所有 transform form 一样。

变身系统需要 Form Animation Profile 描述：

- pelvis / feet bones；
- IK capability；
- overlay interfaces；
- retarget path。

## 39. Large World Coordinates

README 声明支持 LWC，源码也使用 UE5 常规 `FVector` / `FTransform` 路线。

但本轮没有建立大型坐标地图并实际网络测试，所以 Skills 不把“README 支持 LWC”提升成新的强保证。

真正迁移时仍要测试：

- far-origin movement；
- network quantization；
- root movement target；
- moving base；
- camera lag；
- traversal trace。

## 40. ALS-R 与 GASP-ALS-R 的直接对照

### ALS-R 更成熟的地方

- CMC SavedMove/NetworkMoveData 语义清晰；
- Push Model 使用完整；
- SimProxy/view smoothing 非常细；
- URO/Listen server/rotating base 条件经验丰富；
- Linked Anim / Property Access 线程注释明确；
- RootMotionSource moving-base network 处理成熟。

### GASP-ALS-R 更贴合 LGF 的地方

- APawn；
- Mover；
- GAS action ownership；
- Motion Matching / PoseSearch；
- PhysicsControl；
- GameplayCamera；
- Overlay Ability / Task；
- 用户当前目标架构。

### LGF 应该怎么组合

```text
底层选型：GASP-ALS-R / LGF Pawn+Mover
        +
网络动画工程经验：ALS-Refactored
        +
业务权威：LGF GAS/Combat/Foundation
```

而不是：

```text
把两个框架都装进角色
```

## 41. 对用户“动画算法 C++ 化、保留 ABP”的直接结论

ALS-R 再次证明最合理的边界不是“完全移除 AnimBP”。

建议：

### C++

- Game Thread snapshot；
- network state；
- movement prediction；
- locomotion derived data；
- foot lock math；
- root movement transaction；
- layer/profile selection；
- thread-safe helper；
- diagnostics。

### ABP / Linked Layer

- Pose graph；
- Motion Matching node；
- Blend Stack；
- state-machine presentation；
- ControlRig；
- IK；
- overlay composition。

### Data Asset / Config

- Form animation profile；
- movement settings；
- layer class；
- PSD/PSS；
- Chooser；
- camera policy；
- retarget profile。

这与用户当前长期方向完全兼容。

## 42. 对吸收 NPC / Prop / 骑乘的直接映射

### NPC transform

保留 PlayerState/GAS 长期 truth，替换当前 Avatar：

- Mover profile；
- Skeleton；
- AnimInstance；
- Linked Layer；
- Retarget；
- camera policy；
- physics profile。

### Prop transform

若无 humanoid animation：

- 禁用 humanoid linked layers；
- loadout assignment 保留但不 apply；
- camera 与 collision 改用 prop profile；
- 不强行跑 foot IK / gait animation。

### Pet / riding

额外测试：

- mount作为 moving/rotating base；
- rider relative transform；
- mount turn 与 rider view smoothing；
- camera pivot；
- rider foot/seat IK；
- mount AnimBP 与 rider AnimBP tick ordering。

ALS-R 的 moving-base经验在这一点上比普通 GASP sample 更有参考价值。

## 43. 性能建议

### 保留事件/边界更新

- Rotation/Stance/Gait change 时解析 settings；
- Equipment/Form change 时解析 animation profile；
- Overlay change 时 link/unlink layer。

### 不要每帧扩大

- 不每帧创建 GameplayTagQuery；
- 不每帧多层 DataAsset map search；
- 不每帧动态 link layer；
- 不每帧阻塞 parallel anim；
- 不为不可见 AI 强制完整 pose，除非 Authority logic 真的需要。

### 用 Insights 分解

- Character/Mover simulation；
- Anim GT update；
- parallel animation evaluation；
- ControlRig；
- PoseSearch；
- Camera；
- physics；
- net corrections。

## 44. 网络验收矩阵

最少覆盖：

| 维度 | 取值 |
|---|---|
| Topology | Standalone / Listen / Dedicated |
| Role | local / remote Autonomous / SimProxy |
| Network | 0 lag / 100ms / 200ms / packet loss |
| Anim | URO off / low / aggressive |
| Visibility | visible / not rendered |
| Base | static / moving / rotating |
| Action | walk / sprint / crouch / roll / traversal / ragdoll |
| Correction | normal / hard correction / teleport |
| Avatar | human / NPC / prop / mount |

每次至少记录：

- correction count；
- foot world error；
- mesh-body rotation error；
- view rotation error；
- movement transaction mismatch；
- animation GT/worker cost。

## 45. 本轮明确拒绝迁移的内容

1. `AAlsCharacter` 作为 LGF 新基类；
2. `UAlsCharacterMovementComponent`；
3. 复制的 `PhysWalking`；
4. CMC SavedMove 类本身；
5. CMC RootMotionSource Mantle 类本身；
6. ALS Camera runtime 与 GameplayCamera 双栈；
7. 客户端 Roll Montage/PlayRate/Yaw 直接作为服务器最终参数；
8. Mantle server 只做轻量 start check；
9. 全局 AlwaysTickPose；
10. 全局 absolute mesh rotation；
11. 全局关闭或开启 URO；
12. 仅凭 README 声明把 current main 当 UE5.7；
13. 把 Property Access 等同任意 UObject thread safe；
14. 把 Anim GameplayTag 当 gameplay Authority。

## 46. 写回 SkillForge 的正式规则

本轮没有创建第二套“ALS Skill”。

而是扩充：

- `skillforge-ue-cpp/references/mover-animation-network-patterns.md`；
- `skillforge-lgf/references/gasp-mover-integration.md`；
- `skillforge-lgf/references/external-project-patterns.md`；
- `skillforge-ue-blueprint/references/linked-animation-layer-boundaries.md`。

这样同一个问题不会出现：

```text
GASP Skill 一种答案
ALS Skill 另一种答案
LGF Skill 第三种答案
```

而是统一由现有 Skill 根据目标架构选择实现。

## 47. 本轮新增行为用例

### UE C++

- CPP-30：CMC SavedMove 语义迁到 Mover，不移植 CMC；
- CPP-31：Push Model + Iris custom struct 完整合同；
- CPP-32：SimProxy / view smoothing / URO / foot-lock role matrix；
- CPP-33：Property Access write phase；
- CPP-34：moving-base movement transaction identity；
- CPP-35：Camera single runtime owner。

### LGF

- LGF-23：ALS-R -> LGF/GASP/Mover selective migration；
- LGF-24：Transform/Riding network animation optimization matrix。

### Blueprint

- BP-04：Linked Layer Property Access write phase + GameplayTag pose boundary。

## 48. 未完成验证

本轮是源码蒸馏，不代表完成以下实际运行验证：

- 没有在本地 UE5.8 构建 ALS-R；
- 没有跑 ALS-R PIE Dedicated；
- 没有测试 Iris runtime；
- 没有测 URO CPU/foot error；
- 没有在 LGF UE5.7 实际迁移这些模式；
- 没有把 ALS camera algorithm 重做成 GameplayCamera rig。

因此正式 Skills 只写：

- 代码中明确存在的机制；
- 机制背后的跨项目规则；
- 需要实际工程继续验证的条件。

不写“LGF 已支持”。

## 49. 最终结论

ALS-Refactored 对 LGF 最有价值的不是“另一套 locomotion”，而是这些生产经验：

> **预测相关状态必须进入运动重演合同；动画线程只读有明确 write phase 的快照；SimProxy 的 movement/view/visual smoothing 分开；Push Model 和 Iris 都要闭环；URO/mesh 修正按 network role 和 movement base 条件启用；Traversal 是有 stable identity 的 movement transaction；Linked Anim Layer 保持 presentation，Camera 保持单 owner。**

结合上一轮 GASP-ALS-R 后，LGF 的方向更加清晰：

```text
LGF GAS / gameplay truth
          ↓
Pawn + Mover prediction
          ↓
GASP Motion Matching + Linked Layers
          ↓
PhysicsControl / GameplayCamera presentation domains
```

同时把 ALS-R 多年积累的网络动画边缘条件带入测试矩阵，而不是把它的 CMC 架构重新带回来。
