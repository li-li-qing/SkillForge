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
