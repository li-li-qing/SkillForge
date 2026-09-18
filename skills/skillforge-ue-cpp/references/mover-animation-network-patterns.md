# Mover、动画线程、Traversal 与物理/镜头网络模式

用于 Pawn + Mover、GASP/PoseSearch、Linked Anim Layer、Root Motion、Traversal、PhysicsControl/Ragdoll 和 GameplayCamera 同时参与的 UE C++ 任务。核心目标不是复制某个示例框架，而是把 **预测模拟、Authority、物理、动画表现、本地镜头** 分成可验证的所有权域。

本参考的直接案例之一是 `SAM-tak/GASP-ALS-R@a227dfecfcb2719c2541218cf026c05dfe3290ec`。该快照刚合并 Mover 路线，并含自定义 UE 5.8.2 的项目证据；因此这里提炼的是模式。目标工程若是 UE 5.7，必须重新读取目标引擎的 Mover、GameplayCameras、PhysicsControl 和 PoseSearch API，不把案例函数签名当跨版本保证。

## 1. 先划分所有权

| 域 | 默认 Owner | 负责 | 不负责 |
|---|---|---|---|
| Gameplay / GAS | Authority ASC / Ability | 能否执行动作、成本、取消、Tag、业务副作用 | 每帧胶囊模拟、最终骨骼 pose |
| Mover | Movement simulation | 输入重演、Movement Mode、Layered/Instant Move、同步状态、胶囊/Actor frame | 动画美术选择、奖励/伤害决定 |
| Animation | AnimInstance / Linked Layers | PoseSearch、blend、overlay、IK、aim offset、视觉过渡 | Authority gameplay truth |
| PhysicsControl | physics runtime | 刚体、Control/Body Modifier、ragdoll physics | 独立推导第二套 Gameplay 生命周期 |
| Camera | LocalPlayer / PlayerCameraManager context | 本地 camera rig/evaluator/focus | 服务器命中真值、玩家奖励 |

GameplayTag 可以连接这些域，但 Tag 是**身份/信号**，不意味着所有系统都能根据同一个 Tag 独立 Start/Stop 同一业务生命周期。

## 2. Mover：模拟外采样，模拟内只消费记录状态

`ProduceInput` 一类入口运行在 movement simulation 之前。它可以读取本地控制器、GAS、物理姿势和玩家意图，然后把影响模拟的事实记录进 Mover input。**Resimulation 不会重新执行这一段采样逻辑。**

因此：

1. 会改变重演结果的外部状态必须提前捕获；
2. Mover simulation/resimulation 不重新读取 live Mesh、AnimInstance、PhysicsControl、ASC 或非确定性 World 查询来决定同一个历史 frame；
3. Replay 输入中只放模拟真正需要的最小状态；不要把整个 Actor/UObject 图塞进去。

典型记录项：

- RotationMode / Stance / Gait；
- jump edge / directional intent；
- “当前是否禁止 capsule resize”这样的 GAS 派生 flag；
- ragdoll pelvis/top-body transform 或其他 physics snapshot；
- 已经过滤/量化的 lock-on / aim intent（如果设计确实要求进入预测模拟）。

### 2.1 自定义 Mover data 的完整合同

新增一个 custom input/sync/persistent struct 时，至少同时定义：

- `NetSerialize`：哪些字段上网、量化/条件序列化、load 时的默认复位；
- equality / `ShouldReconcile`：什么差异足以触发 Authority correction；
- `Interpolate`：连续量和离散量如何处理；
- `Merge`：缺帧/输入合并时谁覆盖谁；
- `Clone` / copy 语义及 UObject 引用规则；
- Debug string / trace，便于比较 Authority 与 Proxy。

离散 GameplayTag、enum、bool 通常采用 nearest/step，不做数值插值；Transform/Vector 等连续量才考虑插值。**新增字段但忘记 ShouldReconcile / Interpolate / Merge 是网络 bug，不只是代码风格问题。**

Listen Server / P2P-style listen host 也遵循同一 simulation contract：Host 有 Authority 身份不代表可以绕过 Autonomous/SimulatedProxy 的同步语义。

## 3. Mode、Layered Move、Instant Effect、Persistent State、Modifier 怎么选

不要看到 Mover 就把所有状态都实现成 Movement Modifier。

| 需求 | 更合适的机制 |
|---|---|
| 长时间互斥移动模型：Walking/Falling/Swimming/Traversal/Ragdoll | Movement Mode |
| 与当前 Mode 组合的临时位移：Montage root、冲刺、击退 | Layered Move |
| 瞬时速度/位置/几何改变 | Instant Movement Effect |
| 跨 Mode 保留且参与重演的状态：stance 中间高度、eye height | Persistent Sync State |
| 对当前模式参数做可组合约束，且目标版本真正支持 | Modifier |
| 纯展示/分类状态 | 不一定属于 Mover；可能只需 Anim/UI local state |

真实工程要读取目标引擎实现和现有后端。某项目保留 Modifier 类但通过 compile switch 禁用，不能据此写成“标准做法”。

## 4. Capsule / Stance 变化也是预测状态

Crouch、prone、形态改变常同时修改：

- capsule half height/radius；
- collision enable/weld；
- foot-preserving pivot；
- mesh relative offset；
- eye height；
- movement-base/floor query cache。

它们不是单纯视觉。预测/重演系统若只改组件尺寸却没更新同步状态或缓存，可能出现：

- 远端脚底抖动；
- floor query 使用旧尺寸；
- based movement 丢失 base；
- correction 后再次应用 pivot，造成双偏移；
- collision-only change 没触发需要的 invalidation。

推荐：中间 stance 几何放 persistent state；真正发生几何改变时通过 Mover 支持的 effect/update path 一次性应用；finalization 对 Proxy 只“投影同步状态”，不要重跑自己的 stance timer。

## 5. AnimInstance：Game Thread 采样，Worker Thread 消费

推荐边界：

### Game Thread

可以读取：

- ASC owned tags；
- Mover velocity/acceleration/floor；
- MotionWarp target；
- 当前 Avatar/component；
- 需要的 gameplay/presentation flags。

然后写入紧凑、稳定的动画快照，例如：

- velocity / movement intent；
- ground normal / gravity up；
- stance/gait/rotation tags；
- view rotation；
- current action tag；
- trajectory predictor reference（前提是目标 API 的线程合同允许）。

### `NativeThreadSafeUpdateAnimation` / AnimGraph / Linked Layer

只消费：

- 已缓存值；
- AnimInstanceProxy；
- Property Access；
- 明确 thread-safe 的不可变/只读数据。

不要在 AnyThread：

- 遍历 ASC；
- 查 Actor/Component hierarchy；
- 同步加载资源；
- 修改 Inventory/GAS/Mover gameplay truth；
- 发 Authority gameplay 副作用。

ABP 可以拥有 `IsMoving`、Pivot、Landing、Turn-in-place、IK、AimOffset 等**pose semantics**，但这些不是 Gameplay Authority。

## 6. PoseHistory / MotionMatch 的同步 fence

PoseHistory 常由 `FAnimNode_PoseSearchHistoryCollector` 在并行动画评估中写入，而 Ability/Gameplay code 可能在 Game Thread 发起 MotionMatch。

如果目标引擎要求同步，应使用官方允许的 parallel-evaluation completion path（案例中是 `HandleExistingParallelEvaluationTask(..., bPerformPostAnimEvaluation=true)`）后再读 PoseHistory，避免 data race。

这类调用是**性能 fence**：

- 适合 Traversal/Roll/Landing 等离散动作激活；
- 不适合 Tick、每帧 weapon overlay、持续 Aim update；
- 用 Unreal Insights / Anim Insights 观察 parallel evaluation stall；
- action spam 时考虑候选预过滤、Chooser cache、触发节流；
- 禁止在 fence 附近再做 `LoadSynchronous`。

换 Mesh、AnimInstance、Skeleton 或 runtime retarget source 后，PoseHistory / trajectory cache 是否需要清空、重新播种必须显式决定。

## 7. Root Motion：Montage 时间和 Mover 位移分权

一种可靠模型是：

1. ASC/Ability 播 Montage，负责 animation time、section、notify；
2. 禁止 AnimInstance 自己把同一段 root motion 应用到 Actor；
3. 把 root delta 作为 Mover Layered Move 输入；
4. MotionWarp 只修正 Layered Move 消费的 root，不成为第二个位移系统。

### 7.1 生命周期必须保留 Move identity

创建 Layered Move 后保留可取消的 `cancel handle` / operation identity，并关联：

- AbilitySpec/PredictionKey；
- Montage instance ID；
- Section/start position/play rate；
- Warp targets；
- 临时 GameplayEffects / collision state。

End、Cancel、Interrupt、Avatar switch、target invalidation 时成对：

`stop/transition montage -> cancel matching LayeredMove -> clear warp targets -> remove temp effects/delegates`

停止 Montage **不自动证明**排队的 Mover move 已停止。迟到 Notify 也必须检查 Montage instance / action generation，不能终止下一次动作。

## 8. Traversal：客户端选动画，服务器验证约束包络

为了响应速度，AutonomousProxy 可以本地：

`trace -> Chooser -> MotionMatch -> build TargetData -> predicted GameplayEvent`

服务器不一定需要重复昂贵 PoseSearch，但绝不能把 `TargetData` 当 Authority truth。

### 8.1 Authoritative envelope validation

服务器至少重新验证：

- Ability 当前仍可激活、Tag/stance/action lock 仍成立；
- TargetPrimitive 仍存在、允许交互、没有换 generation；
- 与服务器 Avatar 的距离/方向/reach；
- obstacle height/depth；
- surface normal / slope / walkability；
- moving target 当前速度与相对 transform；
- Front/Back/Floor warp 位置在服务器允许的几何 envelope；
- SelectedMontage 属于服务器批准的该动作候选集合；
- play rate / selected time / action tags 在允许范围。

`UPackageMap::SerializeObject` 能解析 `SelectedMontage` 或 TargetPrimitive，只证明引用能到达，不证明客户端有权选择它。

服务器可以“cheap validate，不重复 full MotionMatch”：例如根据服务器重新 trace 的几何分类出合法 ActionTag/Chooser bucket，再验证客户端 montage 是否属于 bucket。失败则拒绝/纠正并清预测 MotionWarp、Layered Move 和 Ability state。

## 9. Overlay / Linked Anim Layer

Overlay 系统适合拆成：

- base locomotion；
- overlay（武器/携带 pose）；
- delta/additive overlay（握把、轻微修正）；
- full override（交互/瞄准/特殊动作）；
- ragdoll/recovery layer。

GameplayTag 适合作为稳定 identity，Task/Component 负责把 Tag 映射到 Anim Layer Class。Link/Unlink 发生在**状态边界**，不是每 Tick。

缓存当前 linked instance 时要考虑：

- AnimInstance 重建；
- Mesh/Skeleton 替换；
- Avatar switch；
- Ability remove；
- GameFeature 动态注册/注销。

不要每帧重新构造 Overlay Tag mask 再扫描全部 ASC tags；若成为热点，缓存 mask 或使用 GameplayTag event/change callback 驱动状态切换。

## 10. Ragdoll：一个生命周期 Owner，三个执行域

推荐职责：

- **GAS Ability**：决定进入/退出政策、被谁取消、下一动作；
- **Ragdoll Task/Operation**：唯一 `ragdoll lifecycle owner`，唯一调用 Physics `StartRagdoll` / `StopRagdoll`；
- **PhysicsControl**：Control Profile、Body Modifier、simulation/freeze、top body transform/velocity；
- **Mover**：Actor frame/capsule 与预测；
- **Anim Layer**：snapshot/blend/get-up 表现。

不要让 PhysicsControl、Mover、AnimLayer 都“看到 Ragdoll Tag 就自行 Start/Stop”。

### 10.1 Remote Authority 不能依赖动画完成

Dedicated/服务器上的 remote pawn 可能不评估完整动画。业务 End 条件如果等待 Anim blend callback，会永久卡住。

生命周期完成必须有无动画评估也成立的 Authority path；blend epilog 只属于需要视觉完成的 Local/Proxy 表现。

### 10.2 Mover frame 与 simulated bodies

当 Mover 拥有 SkeletalMesh component frame，而骨骼 body 正在 Chaos 模拟时，普通 component finalization/smoothing 不能把 simulated bodies 一起 teleport。目标引擎若提供 SkipPhysicsMove/等价语义，应沿用。

需要重演的 pelvis/top-body transform在 simulation 外捕获进 Mover input/sync；模拟中不重新读当前物理 mesh。

## 11. GameplayCamera：Desired intent 与 Local context 分开

可复制：

- desired perspective；
- desired shoulder；
- gameplay 所需的有限视角意图。

本地拥有：

- camera evaluator；
- camera rig/context；
- LocalPlayer/PlayerCameraManager focus；
- blend stack。

Possess 激活 context 要幂等；UnPossess/EndPlay 先停止相关 rig，再 remove/deactivate context，避免 blending-out rig 继续引用旧 Pawn。临时 cinematic/debug camera 压在上面时，不每 Tick force ViewTarget。

如果服务器需要客户端 camera location/rotation 做射击参考，它仍是 **untrusted view sample**：做位置、角速度、视角和时间窗限制，最终命中/LOS/伤害仍由 Authority 验证。

## 12. 测试矩阵

最低覆盖：

- Standalone / Listen Host / Remote Autonomous / SimulatedProxy / Dedicated；
- 30/60/120 FPS 与 server correction；
- packet lag/loss；
- walk/run/sprint/crouch/prone；
- Traversal/Roll/Slide/Landing 中途 Cancel；
- moving platform traversal；
- ragdoll ground/air/freeze/get-up；
- Pawn/mesh/AnimInstance 切换中途动作；
- Linked Layer 快速切武器；
- first/third person、shoulder switch、临时 camera override；
- Insights：Mover resim、parallel anim task、PoseSearch、Physics、GameThread stalls。

通过“看起来动作正常”不等于网络/线程合同成立。分别记录 Authority simulation、Proxy convergence、animation visual 和 profiler 证据。

## 13. ALS-Refactored 对照：从 CMC 迁移网络语义，不迁移 CMC 架构

`Sixze/ALS-Refactored@b754d6f0f2bb03741d301f8fb88077ebfe561e17` 是本参考的第二个网络动画案例。该固定快照的 `ALS.uplugin` 已是 4.18 / UE 5.8.0，而 README 的已发布版本表仍停在 4.17 / UE 5.7；因此这里按固定提交源码取证，不把 README 版本表当当前 `main` 的唯一事实。

ALS-R 仍基于 `ACharacter + UCharacterMovementComponent`。对 Pawn + Mover 工程最重要的不是复制类层级，而是翻译它解决的问题。

### 13.1 `FSavedMove` 是 CMC 对 replay-safe input 的实现

ALS-R 把 `RotationMode`、`Stance`、`MaxAllowedGait` 同时放进 CMC 的 `FCharacterNetworkMoveData` family（项目类型为 `FAlsCharacterNetworkMoveData`）与 SavedMove 管线：

- `FAlsSavedMove`；
- `FAlsCharacterNetworkMoveData`；
- `CanCombineWith()`；
- `PrepMoveFor()`；
- server `MoveAutonomous()`。

这说明这些值不是“普通展示 Tag”，而是会改变历史 movement simulation 的输入状态。

迁到 Mover 时应翻译成：

`live player/gameplay intent -> recorded Mover input/sync -> prediction/resim -> proxy projection`

不要翻译成：

`FAlsSavedMove -> 自己再造一套 CMC SavedMove on Pawn`

如果一个新状态会改变加速度、速度上限、旋转、stance geometry、movement mode 或 root-motion transaction，那么它必须出现在目标 Mover backend 的 prediction/reconcile contract 中。只做普通 `Replicated` 属性可能让“当前画面”最终一致，却不能保证历史预测帧可重演。

### 13.2 不复制引擎 movement 实现作为默认扩展点

ALS-R 的 `PhysWalking()` 含从引擎 `UCharacterMovementComponent::PhysWalking()` 复制后修改的实现，并明确提醒引擎升级时要重新同步上游。

这是一种高维护成本手段。LGF / 新 UE 项目只有在满足以下条件时才考虑复制引擎 movement body：

1. 目标行为无法通过正式扩展点实现；
2. 已锁定引擎版本；
3. 有 engine-upgrade diff 清单与自动化回归；
4. 清楚哪些 bug fix / LWC / physics / networking patch 以后需要手工合并。

对于已经采用 Mover 的新架构，不应为了吸收 ALS-R 的成熟度反向引入这类 CMC fork。

## 14. Push Model 与 Iris 是两个完整合同

“项目支持 Push Model / Iris”不能缩写成给属性加一个标志。

### 14.1 Push Model

完整链至少包含：

1. 项目/引擎启用 Push Model；
2. `FDoRepLifetimeParams::bIsPushBased = true` 或目标版本等价声明；
3. 所有 Authority mutation path 在**值真正变化**后调用 `MARK_PROPERTY_DIRTY` 或目标版本等价 dirty API；
4. mutation 不得绕过统一 setter，否则会出现“服务器内存已变、客户端不再收到”的静默错误。

对高频 view/stance/aim 状态还要问：这个字段是否已经属于 movement prediction 数据？如果是，普通属性复制是不是只为了 SimulatedProxy presentation？必须把双通道目的写清楚，避免重复发同一份 truth。

### 14.2 Iris 自定义状态

Legacy `NetSerialize` 能工作，不自动等于 Iris 能工作。

自定义以下类型时都要检查目标引擎 Iris 支持：

- Root Motion / Layered Move payload；
- custom Mover input/sync；
- gameplay state struct；
- 带 UObject / component reference 的 transaction state。

要确认：

- serializer / replication descriptor 是否需要注册；
- object reference 是否能通过当前 NetRefHandle / package map 路线表达；
- packed vector / rotator / optional field 的语义是否相同；
- legacy replication 与 Iris 都有测试证据。

ALS-R 的配置显式为 `AlsRootMotionSource_Mantling` 添加 Iris struct serializer 支持，这正说明“写了 `NetSerialize`”不是全部工作。

## 15. SimulatedProxy：Actor transform、View 与 Visual Mesh 是三条平滑链

这里的 `view network smoothing` 与 Actor movement smoothing 是独立合同；不能把一个通道的收敛证明外推到另一个。

网络角色的最终位置正确，不代表动画视角连续。

至少区分：

1. **Actor / movement smoothing**：碰撞体和 actor world transform；
2. **View / aim smoothing**：控制视角、aim offset、turn-in-place 依赖的 rotation；
3. **Visual mesh smoothing**：骨架相对 actor 的 presentation transform。

ALS-R 为 view state 维护独立的 network smoothing，并依赖 movement network timestamp。原因是角色 rotation 与动画 view rotation 的职责并不完全等同于 Actor movement correction。

Mover 项目也应先问目标 backend 已提供什么，再补缺失频道。不要因为“Mover 已经预测位置”就假定 Remote aim/turn-in-place 无需单独收敛。

### 15.1 Teleport / hard correction 必须重置动画历史

当网络校正超过 teleport threshold、movement base 跳变或 Avatar 切换时，除了修 Actor transform，还要明确处理：

- view smoothing initial/target/final；
- foot lock；
- turn/pivot history；
- trajectory / PoseHistory；
- linked-layer transient state。

继续用旧历史平滑一个已经跳变的 Avatar，常见结果就是几帧强烈脚滑、AimOffset 回摆或旧脚锁把新姿势拉回。

## 16. URO 与 Mesh rotation：优化按网络角色和 movement base 条件启用

不要把这些设置写成项目全局真理：

- `AlwaysTickPose`；
- Update Rate Optimization；
- absolute mesh rotation；
- visibility-based animation tick。

ALS-R 的现实做法是按上下文决定：远程 AutonomousProxy 在 Listen Authority 上，为避免 RootMotion/rotation 相关问题，可能需要服务器持续 pose tick；当 URO 导致 Character 与 AnimInstance 更新频率不同，非本地 proxy 可以用 visual rotation 补偿；但站在 rotating movement base 上时，同一个 absolute rotation 策略反而会造成 jitter。

因此生产策略应由 `AvatarProfile + NetworkRole + MovementBase + Visibility + GameplayNeed` 决定，而不是一个 bool 覆盖全部 Pawn。

### 16.1 URO / foot-lock 的验收指标

至少记录：

- Character rotation 与 visual mesh rotation 差；
- left/right foot world error；
- pelvis offset discontinuity；
- view yaw/pitch error；
- animation update frequency；
- GameThread / WorkerThread 动画成本。

用 30/60/120 FPS、不同 NetUpdate、packet lag/loss 和 rotating/moving base 重复验证。只看本地 60 FPS 站在静态地面不构成多人优化证明。

## 17. Property Access：为动画字段声明 write phase

Property Access 与 `BlueprintThreadSafe` 是数据访问工具，不是“这个 UObject 永远可以跨线程读”的证明。

ALS-R 的 Linked AnimInstance 明确警告：读取 Parent AnimInstance 自定义变量时，只有那些在 Parent `NativeUpdateAnimation()` 中完成写入、且随后 parallel evaluation 期间不再改变的值才安全。

因此建议维护 animation field ownership matrix：

| 字段类型 | 默认写入阶段 | Worker 是否可读 |
|---|---|---|
| Character/Mover/ASC snapshot | Game Thread `NativeUpdateAnimation` 前半 | 是，快照完成后 |
| Anim curves / proxy data | animation evaluation pipeline | 按官方 proxy/node contract |
| gameplay UObject current state | 任意 gameplay tick / callback | 否，先采样 |
| PostUpdate 才写的临时结果 | Post animation update | 当前帧 worker 不应假定最新 |
| async callback 写入 | 任意 | 否，先转存到明确同步边界 |

如果团队不知道“这个变量本帧最后在哪里写”，就不能仅凭 Property Access 节点把它列为 AnyThread safe。

## 18. GameplayTag pose selection：开放扩展，但保持 Presentation 身份

GameplayTag 替代固定 enum 很适合 Overlay、Stance、RotationMode 和 layer selection，因为内容可以新增 tag 而不用修改 C++ enum。

但要守住两个边界：

1. AnimNode / Linked Layer 的 `ActiveTag -> PoseIndex` 是 presentation selection，不是 Authority gameplay policy；
2. 热路径的 tag lookup 要控制成本：小型固定数组的线性查找可以接受，大型武器/形态库则应在状态变化时预解析 index/class，而不是每个节点每帧重建 query/map。

未知 Tag 必须有 default/fallback pose，不能因为内容更新多了一个 Tag 就输出空 pose 或错用上一次 layer。

## 19. 从 RootMotionSource 提炼 movement transaction

ALS-R Mantle 的 `FRootMotionSource` 同时携带：

- operation identity（RootMotionSource ID）；
- start / target transform；
- moving `TargetPrimitive`；
- montage start time；
- duration/time；
- NetSerialize；
- Matches / Clone；
- target-base relative transform 处理。

真正值得 Mover 工程吸收的是这个**可预测 movement transaction**模型。

### 19.1 Moving base 优先保存相对空间

如果 Mantle、登上坐骑、抓取移动平台只保存世界坐标，目标在网络往返期间移动后，角色会 warp 到旧位置。

交易数据优先表达：

`TargetBase stable reference + local offset/rotation + action geometry`

simulation 时再得到 world target。Target 销毁、切 base、teleport 或 reference 解析失败要有显式 abort / fallback。

### 19.2 Mover 中的等价实现

不要为了复制 ALS-R 再引入 CMC RootMotionSource。Mover 路线应使用目标版本支持的 Layered Move / Movement Effect / Mode：

- 保存返回的真正 operation handle；
- NetSerialize / reconcile 数据与 handle identity 对齐；
- Montage 只跟随 movement transaction 的时间；
- Ability cancel / Avatar switch 通过 handle 清除 transaction；
- MotionWarp target 只是 transaction 的约束数据，不成为第二 movement owner。

这与本参考第 7 节的“Montage 时间和 Mover 位移分权”互相印证。

## 20. ALS-R 的网络动作不能直接当 Authority 模板

ALS-R 的 Roll/Mantle 以响应速度为优先：AutonomousProxy 可以本地开始，再发送 Server RPC。源码中 server Roll 接收客户端给出的 Montage、PlayRate 和 yaw；Mantle Server 入口可见的重新检查主要是“是否允许开始”，没有证明完整重做客户端 trace envelope。

对安全敏感的 ARPG / PvP，生产版必须继续执行本参考第 8 节的 Authority envelope validation。移动载体是 RootMotionSource、Mover LayeredMove 或普通 movement mode，都不改变这个安全边界。

## 21. Camera：算法可复用，Runtime Owner 只能有一个

ALS-R 把 camera 实现为自包含 component，GASP-ALS-R 则采用 GameplayCamera manager/context。两种架构都可以成立，但同一个 LocalPlayer/Pawn runtime 不应让两套 camera system 同时：

- Tick lag；
- 做 collision trace；
- 维护 shoulder/perspective；
- 修改最终 POV。

迁移到已有 GameplayCamera 的工程时，只吸收 ALS-R 的：

- pivot / trace 算法；
- movement-base relative lag；
- first/third-person offset；
- shoulder policy；

然后把它们重写到现有 camera rig/policy/data。不要并挂第二个 camera owner。

A/B 迁移也应使用 feature gate 保证每帧只存在一条 active evaluator chain。

## 22. ALS-R 与 GASP-ALS-R 联合结论

两个项目放在一起后，可以更清楚地区分“成熟经验”和“底层选型”：

| 问题 | ALS-Refactored | GASP-ALS-R / LGF 推荐翻译 |
|---|---|---|
| 运动预测状态 | CMC SavedMove / MoveData | Mover Input/Sync/Persistent State |
| 临时 Mantle 位移 | RootMotionSource | Mover Layered Move/Effect |
| 动画线程 | GT snapshot + worker refresh | 保留 |
| Overlay | Linked Anim BP / Tag | 保留 presentation 语义 |
| 网络属性 | Push Model / role-aware smoothing | 保留合同，映射到当前 owner |
| Camera | ALS camera component | LGF 保持 GameplayCamera 单 owner |
| Gameplay action policy | Character function / RPC | LGF 用 GAS / Authority operation |

因此，**不要把“优秀 locomotion 项目”理解成必须采用它的 movement base class**。真正可持续的是 prediction contract、thread contract、presentation layering、operation identity 和 role-aware performance policy。
