# Avatar、能力就绪与动画资产

## 长期状态与当前 Avatar

当前 Full Foundation 的 PlayerState 聚合长期 ASC、属性、Inventory、Equipment、Quickbar、Quest 等状态；PlayerController 负责拥有侧 Agent/输入，Pawn/Character 负责当前 Avatar 与世界空间表现/战斗组件。更换外观或 Pawn 不应把长期真值随之丢弃。

切换 Pawn 时追踪旧绑定解除 → Owner/Avatar ActorInfo 更新 → 新 Mesh/输入/能力状态准备 → 当前绑定生效。长期 ASC 的 UObject 还在，不代表旧回调仍适用于新 Avatar；异步完成要同时核对对象、ASC、当前 Avatar 和操作/授予代次。

取消旧加载、解绑旧输入/Delegate、停止旧 Timer，并使用实际 GrantHandle 成对撤销和授予。确认项目语义后处理持续状态，不通过重复 GiveAbility 来“补齐看起来没生效”的输入。

## Character 与 Pawn 的死亡移动扩展

两条路线均存在 `AuthorityDisableAvatarMovementForDeath` 与 `AuthorityRestoreAvatarMovementAfterDeath`，它们是 C++ virtual，不能描述为 BlueprintNativeEvent。

- Character/CMC 路线已有 MovementMode/CustomMovementMode 保存恢复逻辑。
- Pawn 路线当前禁用默认返回 false，恢复为空；项目自选 Mover 或其他后端需要实现对称处理。

先检查真实派生类是否已覆盖。禁用前记录必要恢复状态，重复死亡、复活、Possess、Travel、销毁及网络纠正都要有明确处理。Water 的专门移动适配不能证明全框架的 Mover 死亡/根运动生命周期已经接好。

## AbilitySet：Get 不等于加载

取材时 `ULAbilitySet` 校验软类配置；真正授予的 `ULGameplayAbilityComponent::ServerGiveAbilitySet` 先要求 Authority、有效配置与稳定身份，再读已加载软类。未加载返回 AssetNotLoaded；不能把同步执行授予叫做内部同步加载。

遇到能力缺失，核对 Definition 与软引用、PrimaryAssetId 扫描/Cook、预加载完成、ASC/Avatar 就绪、Tag 冲突和操作结果。不要在 Tick、OnRep 或 UI 热刷新中加入 LoadSynchronous 来掩盖就绪问题。

需要异步就绪编排时复用项目已有加载流程，关联操作身份并处理失败/取消；没有此编排就明确列为待实现的项目接入或插件扩展，不能把 API 存在说成整个流程已自动完成。

## 可见 Mesh、权威 Trace 与动画

当前 Avatar Mesh Binding 与装备挂点区分用途。`ELEquipmentAttachmentPurpose` 的 Presentation 与 AuthorityTrace 是不同目的；视觉正确不保证服务器命中用的是正确 Mesh/Socket。当前没有由此自动实现 Holster。

Avatar 或骨骼改变时重建对应绑定。Dedicated Server 不依赖客户端可见 Widget/动画资源完成判伤，但仍可能需要权威 Trace Mesh；不能笼统删掉服务器 Mesh。

`ILAnimationStateProviderInterface` 提供只读状态边界，不等于随附了完整 AnimInstance、ABP、GASP、Chooser、Pose Search 或骨骼动画库。项目需要创建并配置实际内容；未检查二进制资产时只给装配步骤。

MotionWarp 辅助可写入/清理已有组件的 Warp Target，不等于通用 Montage→Mover 根运动桥。动画通知可以参与受控窗口信号，Proxy 动画时点不能决定服务器伤害、死亡或奖励。

回归包含已加载/未加载/错误资产、旧加载晚到、重复授予、Avatar 切换、死亡复活、不同 Mesh 用途、Host/Remote/Dedicated 与 Travel。构建、资产加载和实际网络行为分别记录。

## Persistent Loadout 与 Applied Avatar 状态

外部 Framework 的一个可复用证据是把长期 assignment 与当前 Pawn applied state 分开。LGF 做吸收变身、Prop 形态、骑乘或换 Pawn 时沿用已有 Full Foundation，不另建一套 Inventory/GAS：

- PlayerState/Player Agent 继续持有长期 ASC、Inventory、Loadout、Progression 与 stable ItemId；
- Pawn/Character 只持当前形态的 Mover、Mesh、AnimInstance、Attachment、Trace 与 applied equipment/presentation；
- 旧 Avatar 在 PlayerState/ASC 链接失效前撤销 Pawn 来源 GrantHandle、解绑旧 ASC/Inventory delegate、停止形态异步任务；
- 新 Avatar 在 ActorInfo、Mover/动画和必要资源 ready 后，再按该形态的兼容规则 reapply persistent loadout；
- 不兼容装备保持 loadout assignment，但不在不支持的形态强制创建 Mesh/Ability。回到兼容形态后可重新应用。

Delegate 必须 compare-and-rebind：同一 Pawn 被不同 PlayerState/Controller 重新 Possess 时，从旧长期对象解除绑定后再接新对象。异步加载和 delayed callback 同时检查 stable player identity、当前 Avatar 与 switch generation，禁止旧形态回调污染新 Avatar。

验收增加：死亡重生、NPC 变身往返、Prop 形态、载具/宠物骑乘、同 Pawn 换 Controller、形态切换中断、Host/Remote/SimulatedProxy/JIP，以及旧装备 Actor/Ability/动画 layer 没有残留或重复授予。

## GASP/Mover Avatar 切换：动画、物理与 Camera 的重绑定

吸收 NPC、Prop 形态和骑乘不仅是换 SkeletalMesh。对 GASP/Mover 路线，Avatar generation 至少覆盖：

- Mover backend / Movement Modes / persistent sync state；
- SkeletalMesh、AnimInstance、Runtime Retarget source；
- Linked Anim Layers 与 Overlay/Delta/Override task；
- PoseHistory、Trajectory Predictor、MotionWarp targets；
- PhysicsControl asset/profile 与正在运行的 Ragdoll task；
- Local GameplayCamera context / camera variables；
- 当前形态的 equipment actor、socket/AuthorityTrace binding。

### Detach old Avatar

在旧 owner 引用失效前：

1. Cancel 由旧 Avatar 发起/承载的 Traversal、Roll、Slide、Montage 等 action Ability；
2. Cancel matching Mover Layered Move，并清 MotionWarp targets；
3. End overlay/ragdoll task，Unlink 旧动态 Linked Anim Layer；
4. 撤销 Pawn 来源 GrantedHandles、equipment actor、AuthorityTrace；
5. Unbind old ASC/Inventory/Mover/Anim delegates 和 input；
6. LocalPlayer 停止旧 camera rigs/context；
7. 递增 Avatar generation，让迟到 async/notify/callback 自动失效。

### Attach new Avatar

按依赖顺序：

1. 建立 stable owner -> new Pawn 的 ASC ActorInfo；
2. 初始化/验证 Mover、collision、PhysicsControl；
3. 验证 Skeleton、AnimClass、Linked Layer Interface、Runtime Retarget；
4. 重建/重新播种 Trajectory 与 PoseHistory，不能继承旧骨架 history；
5. 注册 overlay/delta/override mapping，重新解析 linked instance；
6. 初始化 MotionWarp/Traversal 目标容器；
7. 本地拥有玩家激活新的 GameplayCamera context；
8. 最后按形态兼容规则 reapply loadout/equipment/presentation。

不兼容形态继续保留 persistent loadout assignment，但 applied equipment 为空或降级。恢复兼容形态后再重建，禁止因为 Prop 没有手骨就删除玩家的长期武器归属。

验证必须包含“动作进行中变形”：Traversal/Ragdoll/RootMotion/Overlay 切换一半时换 NPC/Prop/坐骑，旧 Layer、旧 Warp、旧 Mover move、旧 physics task 和旧 camera rig 都不能继续控制新 Avatar。
