# Lyra 现代框架经验映射到 LGF

目标：只吸收当前 Lyra/UE 仍然成立、且能补强 LGF 的框架合同。LGF 不改造成 Lyra fork，不引入第二套 Inventory、Mover、GameplayCamera、Foundation 或 Authority 模型。

## 1. 来源时效性先分级

外部 Lyra 教程、GitHub fork 或旧 sample 先标：

- `Current`
- `Stable-but-old`
- `Historical`
- `Reject`

当前 LGF 主线为 UE5.7，具体接口以目标 5.7 工程、当前引擎源码和 LGF 实现为准。Epic 5.8 Lyra 文档用于确认哪些机制仍被官方保留，但不能直接把 5.8 类签名复制进 5.7。

### 已确认的关键版本变化

- Lyra 5.0 的 Pawn init flow 属于旧路径；
- 5.1 改成 `IGameFrameworkInitStateInterface` + GameFrameworkComponentManager Init State，官方说明用于修复网络初始化竞态；
- 当前 5.8 官方文档仍保留这套 Init State 思想；
- 因此 LGF 吸收 readiness contract，不复制 5.0 初始化顺序。

## 2. LGF Avatar Readiness

LGF 未来的玩家 Avatar 可能是：

- 普通 Pawn；
- 吸收后的 NPC 形态；
- Prop 形态；
- 骑乘宠物/载具；
- 死亡重生的新 Pawn。

这些路径共同的问题是依赖到达顺序不稳定。

建议 LGF 的可观测状态至少能表达：

```text
Spawned
  ↓
DataAvailable
  ↓
DataInitialized
  ↓
GameplayReady
```

名字可以与 Lyra 不同，语义要存在。

### 2.1 DataAvailable

至少检查当前 Avatar 所需：

- stable PlayerState/ASC；
- Controller/ownership；
- Mover/Pawn movement host；
- Form/Pawn data；
- Input owner；
- Skeletal Mesh 或 Prop visual root；
- animation/retarget capability；
- Equipment projection dependency；
- Camera owner；
- network role。

### 2.2 DataInitialized

完成：

- `InitAbilityActorInfo` 或 LGF 等价 ActorInfo rebind；
- Mover input/sync 初始化；
- 当前形态兼容 Ability/Effect grant；
- InputTag/MappingContext 注册；
- Equipment presentation 重建；
- animation layer / retarget 绑定；
- GameplayCamera context 激活；
- 旧 generation callback fence。

### 2.3 GameplayReady

只有在上述业务依赖完成后，才允许：

- 近战命中；
- Traversal；
- 装备切换；
- Quickbar ability；
- 需要当前 Avatar 的 OnSpawn ability；
- 本地交互输入。

## 3. Readiness 不是 Tick 轮询

借鉴 Lyra 的是“状态依赖 + 通知”，不是每 Tick：

```text
if (ASC && Pawn && Input && Mesh && Camera) Ready = true;
```

推荐：

- 依赖变化时触发 check；
- check 可重入；
- 每个 init step 幂等；
- 输出阻塞原因；
- 使用 AvatarGeneration；
- stale callback 不能推进新 Avatar。

## 4. PlayerState 是稳定状态，Pawn 是可替换 Avatar

这与 LGF 当前方向一致，不需要引入 Lyra 类。

**PlayerState/稳定宿主：**

- ASC；
- 长期 Attribute；
- Inventory truth；
- 长期 Equipment intent；
- Quickbar identity；
- Quest/Progression；
- 长期 granted ability source registry。

**当前 Avatar：**

- Mover；
- collision；
- world transform；
- current mesh/prop；
- animation/retarget；
- current equipment actors；
- trace sources；
- camera context；
- temporary form grants。

## 5. Persistent 与 Pawn-scoped AbilitySet

Lyra 当前文档的重要提醒：AbilitySet 可以先授予 PlayerState，但需要有效 Pawn 才能激活依赖 Avatar 的 OnSpawn ability。

LGF 映射：

- 长期 grant：账户/职业/角色永久能力；
- Avatar grant：当前形态能力；
- Equipment grant：当前装备来源；
- temporary feature grant：副本/玩法规则临时能力。

所有非长期 grant 都必须：

- 有 source identity；
- 有 exact SpecHandle/GrantedHandles；
- generation-aware；
- source 结束时精确 revoke。

这与双刀同 AbilityClass 不可按 class 猜删的现有规则完全一致。

## 6. PawnData 思想如何映射

不创建 `ULyraPawnData` 依赖，而是吸收 DataAsset composition 思想。

LGF 可形成项目侧 Form/Pawn 配方：

```text
FormData
├─ Pawn/Visual Class
├─ Ability Sets
├─ Input Config
├─ Tag Relationship / Ability Policy
├─ Camera Profile
├─ Animation Profile
├─ Movement Profile
└─ Equipment Compatibility
```

它是**静态配方**，不是 runtime truth。

不要存：

- 当前 HP；
- 当前 Item runtime；
- 当前 prediction key；
- 当前 Combo Sequence；
- 当前 AvatarGeneration；
- 当前 Mover sync state。

## 7. Experience 不替代 LGF Foundation

LGF 已经有：

- Foundation；
- Request/Authority；
- 模块生命周期；
- Inventory/Equipment；
- GASP/Mover；
- UI platform；
- persistence。

因此默认不把 Lyra Experience 作为新的根框架。

可吸收的是：

- data-driven gameplay composition；
- async readiness barrier；
- feature activation/deactivation 对称性；
- Pawn/Ability/Input/UI bundle 一起启停的思想。

如果未来需要：

- DLC；
- mod；
- 动态玩法包；
- 同一 executable 切换巨大规则集合；

才评估 GameFeatures adapter。

## 8. GameFeatures 风险门

当前 Epic 5.8 API 页面仍把 GameFeatures 标为 Beta。

因此 LGF 不能写：

> “Epic Lyra 用，所以 Production 默认应该用。”

必须回答：

- 动态卸载是否真实需求；
- package/chunk/hotfix 是否获益；
- console/platform 是否验证；
- patch/upgrade 成本；
- save 是否跨 feature version；
- Dedicated Server 是否需要同样 feature；
- 是否可以用静态模块 + DataAsset 获得 80% 收益。

## 9. Inventory / Equipment 生命周期映射

Lyra 5.8 官方文档仍区分：Inventory Item 长期存在；Equipment Instance 只在 equipped 期间存在。

LGF 直接采用这个生命周期语义，但不降级 LGF 数据模型。

### LGF Inventory

长期：

- ItemId；
- DefinitionId；
- quantity；
- durability/affix/item state；
- save identity；
- container position。

### LGF Applied Equipment

当前 generation：

- Equipment source entry；
- spawned actor；
- socket binding；
- trace PartId；
- Ability SpecHandle/GrantedHandles；
- Linked Anim Layer；
- overlay/reticle；
- presentation subscription。

Unequip：只撤 Applied Equipment，不删 Inventory identity。

## 10. 双刀/多刀刃的 Lyra 对照结论

Lyra 生命周期拆分强化 LGF 当前双刀合同：

```text
Inventory Item Left / Right
       ↓ equip
Equipment Generation Left / Right
       ↓
SourceObject + exact SpecHandle
       ↓
PartId + TraceSourceBinding
       ↓
Combo Sequence / HitWindow
```

左右武器：

- 可以授予同一个 AbilityClass；
- 仍必须有不同 source identity；
- Unequip 右手不得清左手 ability；
- 切回背包不销毁 Item runtime state；
- 新 Avatar generation 重新创建 equipment presentation。

## 11. Input 组合

Lyra 当前输入文档仍采用：

- feature 注册 Input Config/Mapping；
- Enhanced Input 管当前 Mapping Context；
- CommonUI 决定 UI input routing；
- Ability 通过 InputTag 关联。

LGF 已有自己的 Input/Ability 路线，只吸收：

1. feature/input source 拥有自己的 registration handle；
2. Avatar detach 时 remove；
3. UI input owner 与 gameplay input owner 分层；
4. Ability InputTag 到 SpecHandle 使用缓存/索引；
5. 变身/骑乘可切 Mapping Context，不硬编码全局 switch。

## 12. GameplayCamera 不与 Lyra Camera 并行

Lyra 的 Camera/PawnData 组合思想可以学习，但 LGF 已决定 GameplayCamera 路线。

所以：

- FormData 可选择 Camera Profile；
- Avatar readiness 负责激活/停用当前 camera context；
- 不再引入另一套 Lyra Camera owner；
- 旧 Avatar 的 camera rig 必须在新 Avatar 启用前清干净。

## 13. CommonUI/Gameplay UI

LGF 已有 UI platform；Lyra 只用于验证：

- UI layer/router 才是 input/focus owner；
- feature 可以注入 HUD extension；
- feature unload 必须移除 extension；
- Widget 仍然只是 gameplay truth 的投影。

不要复制 Lyra HUD Blueprint 树来替代现有 UI Foundation。

## 14. 旧 Lyra 教程的使用规则

### 可以用

- 找类名；
- 找数据流；
- 找系统组合思想；
- 发现旧问题；
- 比较升级前后差异。

### 不能直接用

- 函数签名；
- deprecated controller id/input API；
- 5.0 Pawn init；
- 旧 GameFeature callback 参数；
- 旧 CommonUI/Input 配置截图；
- 旧 Net/replication 假设。

## 15. LGF 验收矩阵

### Avatar readiness

- Remote PlayerState 慢到；
- PawnData/FormData 慢到；
- InputComponent 晚一帧；
- Equipment snapshot 先于 Mesh；
- Camera context 先于 possession；
- 连续两次 Avatar swap；
- 旧 async callback 晚到。

### Feature lifecycle

- enable；
- duplicate enable；
- disable；
- re-enable；
- PIE restart；
- reconnect；
- JIP；
- Dedicated Server；
- packaged build。

### Inventory/Equipment

- 同 Item 反复 equip；
- 左右手交换；
- 收纳/手持；
- 掉落；
- 死亡；
- 变身；
- JIP；
- save/load 后重新投影。

## 16. 最终原则

Lyra 对 LGF 的价值：

> **学习 Epic 如何把多个现代 UE 子系统组合起来，并观察 Epic 自己如何淘汰旧版本模式。**

不是：

> **把 LGF 重写成 Lyra。**
