# Linked Animation Layer 与 AnimBP 边界

用于 GASP/ALS 风格 locomotion、武器 overlay、瞄准/交互 override、runtime retarget 和多人动画 Blueprint 接入。

## AnimBP 不拥有 Authority 真值

AnimBP / Linked Layer 适合：

- Motion Matching / state selection；
- blend / additive / overlay；
- IK、AimOffset、spine/foot correction；
- TurnInPlace、Pivot、Landing 等 pose semantics；
- 读取 C++ 与 Property Access 暴露的只读 animation snapshot。

不适合直接拥有：

- 是否允许攻击/Traversal；
- 伤害、奖励、Inventory；
- Mover Authority movement state；
- GAS cost/cooldown/ability lifetime。

动画 Notify 可以发受控表现/窗口信号，但服务器判伤仍由 Authority gameplay logic 验证。

## 用正交 Layer 避免巨型状态机

建议拆：

1. Base locomotion；
2. Overlay：武器/手持姿态；
3. Delta/Additive Overlay：握把、aim correction；
4. Override：完整上半身交互/瞄准；
5. Ragdoll/Recovery。

不要为每把武器复制整个 locomotion state machine。用 GameplayTag/配置映射到 Layer Class，默认 fallback 明确。

## 动态 Link / Unlink 是生命周期操作

`LinkAnimClassLayers` / `UnlinkAnimClassLayers` 放在装备、Overlay Ability、Avatar 切换等**状态边界**，不是 Tick。

切换时：

- 结束旧 Task/Ability presentation；
- 清旧 Layer 的 notify/delegate/缓存；
- Unlink 旧 class；
- Link 新 class；
- 重新 `GetLinkedAnimLayerInstanceByClass`；
- 缓存新 instance 前验证当前 Mesh / AnimInstance generation。

换 Pawn、换 Mesh、Reinitialize Animation 后，旧 linked instance 指针一律视为失效。不要保存跨 Avatar 的强引用并继续调用。

## Thread Safe Blueprint

标记 `BlueprintThreadSafe` 不代表任意 UObject 访问都安全。线程安全动画函数只读：

- AnimInstance 内已缓存 primitive/struct；
- Property Access snapshot；
- AnimInstanceProxy 允许的数据。

需要 ASC/Mover/Actor/World 的查询先在 Game Thread C++ 或明确的 GT update 阶段采样，再把值喂给图。

## Skeleton / Interface / Retarget

动态 Layer 前检查：

- SkeletalMesh/Skeleton 与 AnimBP target skeleton；
- Anim Layer Interface 一致；
- Runtime Retarget 的 source/target 方向；
- 当前形态是否真的支持该 weapon/overlay；
- linked class 未加载时的 fallback。

Prop 或非人形 Avatar 不兼容时，保留长期 loadout intent，但不要硬 Link 人形 Layer。

## 多人验证

分别看：

- Listen Host；
- Remote Autonomous；
- SimulatedProxy；
- JIP；
- 快速切武器；
- Traversal/Ragdoll 中途换 Overlay；
- Pawn/mesh/AnimInstance 重建；
- Dedicated Server 不执行视觉 AnimBP 时 gameplay 仍能结束。

视觉一致和 Authority gameplay correct 是两组验收，不互相替代。

## Property Access 不是自动线程安全：为变量标注写相位

这里的 `write phase` 指一个字段在本帧由谁、在哪个阶段完成最后写入，以及 worker 读取期间是否保持稳定。

ALS-Refactored 的 Linked AnimInstance 对 `GetParent()` 有一个非常重要的限制：只有那些在 Parent AnimInstance 的 Game Thread `NativeUpdateAnimation()` 阶段完成写入、随后 parallel animation evaluation 期间保持稳定的变量，才适合通过 Property Access 给 worker thread 读取。

因此 AnimBP 评审时，不只问“节点是否标了 BlueprintThreadSafe”，还要问：

| 问题 | 需要回答 |
|---|---|
| 谁写这个字段？ | Character、GT AnimInstance、worker、PostUpdate、async callback？ |
| 本帧最后何时写？ | parallel evaluation 前还是期间？ |
| Worker 读的是什么？ | snapshot/value 还是 live UObject state？ |
| 重建 AnimInstance 后呢？ | 旧 property access / linked instance 是否失效？ |

推荐把 AnimInstance 暴露字段明确分成：

- `GT Snapshot`：可供 Property Access / linked worker read；
- `Worker Derived`：只在当前动画求值链内部使用；
- `PostUpdate Result`：下一帧再进入 snapshot；
- `Gameplay Truth`：ASC/Mover/Equipment/Actor 等，先在 GT 采样，Linked Layer 不直接追对象。

`BlueprintThreadSafe` 只是函数调用承诺，不能把一个正在被其他线程修改的 UObject 字段变成线程安全。

## GameplayTag Blend 仍然只是 Pose Router

ALS-R 的 `Blend Poses by Gameplay Tag` 思想适合扩展武器、stance、overlay：未知 tag 走默认 pose，新 tag 不必扩 C++ enum。

但 GameplayTag AnimNode 只负责：

`cached presentation tag -> pose/layer selection`

不负责：

`tag -> Authority ability legality / damage / inventory / movement outcome`

大型形态/武器库还应在 tag 变化时预解析 layer/pose index；不要为了“数据驱动”在每个 AnimNode 每帧建立 GameplayTagQuery 或扫描大表。

## URO / SimulatedProxy 不是 Blueprint 全局开关

动画 Blueprint 和角色蓝图不能为了修一个 listen-server jitter，就给所有 Pawn 开 `AlwaysTickPose` 或绝对 Mesh rotation。

至少按：

- Local / Remote Autonomous / SimulatedProxy / Dedicated；
- 可见 / 不可见；
- URO on/off；
- static / moving / rotating base；
- 当前动作是否真的依赖 server-side pose；

决定更新策略。换 Pawn、坐骑、Skeleton、runtime retarget source 时清旧 foot-lock / smoothing / transition history，再建立新形态状态。
