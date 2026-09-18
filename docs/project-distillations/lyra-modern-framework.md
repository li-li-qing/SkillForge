# Lyra Starter Game：现代 UE 框架与技术时效性蒸馏

日期：2026-09-14

本轮目标不是把 SkillForge/LGF 改造成 Lyra，而是完成两件事：

1. 建立以后所有 GitHub/UE 样例都必须经过的**技术时效性门**；
2. 从当前 Lyra 文档和 UE5.7 可见的 Lyra-like 实现中，提炼仍适用于 LGF 的模块化初始化、GAS 生命周期、Experience、Input、Inventory/Equipment 和 UI 组合规则。

---

## 1. 研究快照与证据层级

### 1.1 主证据：Epic 当前 Lyra 文档

研究时 Epic Developer Community 当前显示 UE 5.8 文档。

重点页面：

- Lyra Sample Game；
- Abilities in Lyra；
- Lyra Inventory and Equipment；
- Lyra Input Settings；
- Upgrading the Lyra Starter Game；
- Game Framework Component Manager；
- Game Features API；
- Common UI；
- Common User Plugin。

这些页面用于回答“Epic 当前还在推荐/保留什么机制”。

### 1.2 UE5.7 次级 GitHub 证据

`XistGG/XistCommonGameSample@7e01e1fed344a741f80fa82b7161c86c494a410b`

- README 明确标记：UE 5.7 Lyra-like HUD & Input Setup；
- 仅聚焦 CommonUI + Enhanced Input；
- 单机简化样例，不具备 Lyra 全套多人复杂度；
- 适合核对 Lyra-style InputTag/CommonUI/Input Context 分层；
- 不作为多人 Authority/GAS/Inventory 的证据。

### 1.3 其他次级材料

X157 Lyra notes：用于理解 Experience、Input、Inventory 和 Pawn Extension 的结构关系。

公开的 Lyra 5.7 readiness/analysis 报告：用于确认 5.7 项目仍包含 LyraGame、CommonGame、CommonUser、GameplayMessageRouter、ModularGameplayActors 等模块及其复杂度。

### 1.4 限制

当前 GitHub connector 无法访问 `EpicGames/UnrealEngine` 私有仓库，因此本轮没有把“某个公开 GitHub mirror”冒充 Epic 官方源码。

本轮不复制 Lyra 源码；当前行为结论以：

1. Epic 当前官方文档；
2. 用户当前 UE5.7/LGF 约束；
3. 可公开读取的 UE5.7 Lyra-like 工程；

交叉确认。

---

## 2. 技术时效性分级制度

以后每个项目都必须进入以下四档之一。

### Current

满足大部分：

- 与目标 UE 主版本接近；
- 最近仍维护；
- 关键 API 与当前文档/源码一致；
- 没有明确被后续引擎版本替代。

可以吸收机制；具体 API 仍需要目标工程验证。

### Stable-but-old

项目较旧，但核心机制仍然成立。

例：

- GAS PredictionKey 的概念可来自旧资料；
- 具体函数、macro、任务类必须在当前 UE 重新确认。

### Historical

旧实现已经被 UE/Lyra 后续版本明确改写，但仍能解释：

- 为什么新系统出现；
- 旧设计有什么竞态/成本；
- 迁移要避免什么。

### Reject

不进入正式规则：

- 明显权限漏洞；
- 已知不能满足目标网络拓扑；
- 被现代方案完整取代且无独特价值；
- 只为了样例演示牺牲生产边界；
- 与当前项目架构冲突且收益不足。

---

## 3. 为什么“旧 GitHub 项目”必须专门检查

UE5 的底层与高层框架都在快速变化：

- TObjectPtr/TWeakObjectPtr 使用；
- ModularGameplay；
- GameFramework Init State；
- Iris；
- Enhanced Input；
- CommonUI；
- Online Services；
- Mover/Network Prediction；
- GAS API 与 replication 行为；
- GameFeature callback 签名；
- engine headers 与模块依赖。

一个 UE5.0 工程可能“思路正确”，但复制到 UE5.7/5.8：

- API 已变；
- 生命周期假设已失效；
- 官方样例自己已经重写；
- 网络竞态已经有标准解决方案。

因此不能用仓库热度代替当前证据。

---

## 4. Lyra 自己就是最好的“旧模式被淘汰”案例

Epic 升级文档明确记录：

### UE 5.0

Lyra 初版没有现在的 Pawn Init State 系统。

### UE 5.1

`LyraHeroComponent` 与 `LyraPawnExtensionComponent` 初始化流程被改写成：

- `IGameFrameworkInitStateInterface`；
- `GameFrameworkComponentManager` Init State。

官方说明目的包括：

- 修复 network replication race conditions；
- 更容易扩展 feature-specific components。

结论：

> 任何仍在教“照 Lyra 5.0 BeginPlay/固定顺序初始化 Pawn feature”的教程，都只能是 Historical。

### UE 5.2+

继续引入/加强：

- Iris；
- Replication Graph；
- dedicated server；
- seamless travel；
- native gameplay tags 等现代网络/框架能力。

### UE 5.3

继续调整：

- TObjectPtr；
- Enhanced Input；
- replay/network fixes；
- Lyra-specific input settings。

### 当前 5.8 文档

仍保留：

- Pawn Extension readiness；
- PlayerState ASC；
- AbilitySet；
- PawnData；
- GameFeature/Experience；
- Inventory/Equipment lifecycle；
- CommonUI + Enhanced Input。

这说明这些**机制**目前仍值得研究。

---

## 5. Current：Pawn 初始化不是时间顺序，而是依赖图

当前 Game Framework Component Manager 文档给 Lyra 的状态：

```text
InitState.Spawned
  ↓
InitState.DataAvailable
  ↓
InitState.DataInitialized
  ↓
InitState.GameplayReady
```

真正的价值不是四个名字，而是：

- 每个 feature 明确依赖；
- 复制/加载到达顺序可以乱；
- check 可以重复调用；
- init 操作必须幂等；
- 未满足依赖就停在当前 state；
- ready 可以诊断。

### 对 LGF 的意义

玩家以后可能：

- 吸收 NPC；
- 切换完全不同 Pawn；
- 变成 Prop；
- 骑乘 NPC/宠物；
- 死亡重生。

这些都不能假设：

`PossessedBy -> ASC ready -> Mover ready -> Mesh ready -> Anim ready -> Equipment ready`

固定顺序永远成立。

应该表达为 readiness graph。

---

## 6. Current：PlayerState ASC + Replaceable Avatar

Lyra 当前文档继续把长期 ASC state 放在 PlayerState 的模式作为重要方案。

优点：

- Attributes/Effects 可以跨 Pawn 变化保留；
- Pawn-specific grants 可以随 Pawn revoke；
- 设备/Experience/GameFeature 可以成为独立 grant source。

关键不是“ASC 一定在 PlayerState”，而是要把：

- stable owner；
- current avatar；
- grant source；

三个身份分开。

### 6.1 OnSpawn 能力的细节

AbilitySet 可以在 Pawn possession 之前已经给到 PlayerState ASC。

但需要 Avatar 的 OnSpawn ability 不应该因为 AbilitySpec 已经存在，就在无有效 Avatar 时提前执行。

这是 Init State 的实际价值之一。

---

## 7. Current：AbilitySet 是可逆 grant transaction

Lyra AbilitySet 当前仍包含：

- Gameplay Abilities；
- Gameplay Effects；
- Attribute Sets；
- optional input tag；
- `GrantedHandles` bookkeeping。

与前面 Obsidian/AyaDog/GASShooter 的结论互相加强：

```text
Grant Source
  ↓
Give abilities/effects/attributes
  ↓
Store exact handles
  ↓
Source teardown
  ↓
Revoke exactly those handles
```

禁止：

- 按 AbilityClass 猜删；
- 按 Tag 扫一圈删除；
- Pawn 被销毁但 source handles 丢失；
- 同类左右武器互相误删。

---

## 8. Current：PawnData 是 Avatar composition recipe

当前 Lyra 的 PawnData 可以抽象为：

- Pawn class；
- AbilitySets；
- InputConfig；
- TagRelationshipMapping；
- Camera Mode；
- 其他当前 Pawn 的静态配置。

非常适合 LGF 未来：

```text
FormData / AvatarData
├─ Visual/Pawn Class
├─ Movement Profile
├─ Animation Profile
├─ Ability Sets
├─ Input Config
├─ Camera Profile
├─ Equipment Compatibility
└─ Tag/Ability Policy
```

### 不应该放进配方

- 当前生命；
- runtime Item instance；
- PredictionKey；
- Combo Sequence；
- current AvatarGeneration；
- Mover sync state。

---

## 9. Current mechanism：Experience 是异步玩法组合

Lyra Experience 的可迁移价值：

- 数据驱动选择玩法；
- 加载所需 Game Feature Plugins；
- 加载 PawnData/Input/UI 等 bundle；
- 执行 Actions/ActionSets；
- 完成后发 Experience Loaded。

因此：

> BeginPlay 不等于 Gameplay Ready。

如果项目依赖异步内容组合，必须有 readiness barrier。

### 9.1 旧请求防护

Experience/feature callback 需要检查：

- World 仍然有效；
- match/session 没切换；
- generation 没过期；
- feature state 没改变；
- 旧 callback 不重复 grant/input/HUD。

---

## 10. Current but conditional：GameFeatures

Lyra 广泛使用 Game Feature Plugins。

但当前 UE5.8 API 页面仍将 GameFeatures 标成 Beta，并提示 shipping caution。

这是一条非常重要的现代性结论：

> “当前 Epic Sample 使用” ≠ “你的 Production 项目无条件应该使用”。

### 适合采用

- 真正需要动态玩法包；
- DLC/mod；
- 大量 experience 按需启停；
- chunk/packaging 能从 feature 边界获益；
- 团队接受版本升级与平台验证成本。

### 可以不用

如果只是：

- 一个 ARPG 主玩法；
- 模块都常驻；
- 不需要 runtime unload；

静态模块 + DataAsset composition 可能更稳。

---

## 11. Current：Inventory 与 Equipment 生命周期拆分

Epic 5.8 官方 Lyra Inventory/Equipment 文档仍明确：

### Inventory Item

- 所有者拥有期间长期存在；
- 可以只作为虚拟 Item；
- UI 使用其信息；
- 不要求有世界 Actor。

### Equipment

- 从 Inventory 中拿出来正在使用；
- equipped 时才产生 Equipment instance；
- 可 spawn 可见 Actor；
- 可授予 abilities；
- 可改变 UI；
- unequip 时销毁装备期实例/表现。

### 对 LGF

这与当前 LGF 多刀刃需求非常一致：

```text
ItemId（长期）
 ↓ Equip
EquipmentGeneration（临时）
 ├ SpecHandle
 ├ PartId
 ├ TraceSource
 ├ Socket
 ├ Anim Layer
 └ Presentation Actor
```

Unequip 只撤 generation，不删除 ItemId/runtime state。

---

## 12. Lyra Inventory 不是 ARPG 容器上限

不能因为 Lyra 是 Epic Sample，就反向删掉 LGF 已有：

- Grid；
- shared stash；
- container transaction；
- stable generation handle；
- nested container；
- affix runtime state；
- save identity；
- 双刀 source isolation。

Lyra 在这里提供的是**生命周期设计证据**，不是完整 ARPG 需求集合。

---

## 13. Current：Input 是 Feature + Enhanced Input + CommonUI 三层组合

官方当前 Lyra Input 文档仍显示：

- GameFeatureAction 注册 Input Config；
- PlayerMappableInputConfig/映射配置属于 feature；
- Enhanced Input 负责 gameplay mapping；
- AbilitySet 可以把 input tag 关联到 ability；
- CommonUI 控制 UI/input routing。

### 13.1 XistCommonGameSample UE5.7 交叉验证

其 README 明确：

- InputAction -> GameplayTag map；
- Possession/Unpossession 切 HUD/IMC；
- CommonUI ActivatableWidget 提供 desired input config；
- 这是单机简化，不包含 Lyra 多人复杂度。

因此只采纳 input/UI 分层，不采纳其多人缺失部分。

---

## 14. UI Input Owner 不应有两套

推荐概念链：

```text
Physical Input
   ↓
CommonUI / UI Action Router
   ├ UI consumes
   └ Gameplay receives
          ↓
Enhanced Input contexts
          ↓
InputAction / InputTag
          ↓
Gameplay command / GAS spec
```

如果主菜单打开：

- 由 UI policy/router 决定 gameplay input 是否被截获；
- Pawn 不应该另写一套 `SetInputModeGameOnly()` 强制抢回控制。

---

## 15. GameFeature Input 必须对称撤销

Feature 可能注入：

- IMC；
- Input Config；
- Input binding；
- UI extension；
- AbilitySet。

启用时记录 registration/source handles。

停用时必须 remove。

验证：

- enable twice；
- disable；
- re-enable；
- Avatar swap；
- PIE restart；
- reconnect。

---

## 16. Current：CommonUI 只负责 UI/Input routing，不是 gameplay truth

Lyra 使用 CommonUI 的价值：

- layer；
- focus；
- input routing；
- platform/controller adaptation；
- activatable widget lifecycle。

它不应该成为：

- Inventory truth；
- Ability truth；
- Equipment truth；
- Quest state；
- Authority mutation owner。

这与 SkillForge 之前的 UI projection 规则一致。

---

## 17. GameplayMessageRouter 的位置

现代 Lyra-like 工程仍经常保留 GameplayMessageRouter 风格：

- gameplay subsystem/authority 发送轻量事件；
- UI/本地表现按 tag/channel 订阅；
- listener 可不存在；
- message 不等于 persistent truth。

LGF 已有 Event/Message 能力时，只吸收 channel/payload/lifetime 思想，不复制第二套消息总线。

---

## 18. Current：GameFeature deactivation 是 first-class lifecycle

如果系统支持 feature unload，就必须真正设计 teardown：

- injected components；
- AbilitySet；
- Attributes；
- input mappings；
- UI widgets/extensions；
- delegates；
- async request；
- asset handles。

“插件隐藏/没用了”不等于 lifecycle 完成。

---

## 19. 对 LGF Avatar/变身/骑乘的直接提升

Lyra Init State 可以抽象成 LGF Avatar readiness：

```text
Stable Player Identity
        ↓
New Avatar Spawned
        ↓
FormData Available
        ↓
PlayerState + ASC Available
        ↓
Mover Ready
        ↓
Visual/Anim/Retarget Ready
        ↓
Input Ready
        ↓
Equipment Projection Ready
        ↓
Camera Ready
        ↓
GameplayReady
```

每一步都有：

- generation；
- diagnostic reason；
- symmetric teardown；
- late callback rejection。

---

## 20. 与 AyaDogGames/GameplayFramework 的对照

两者都证明：

- stable PlayerState 可持 ASC/长期状态；
- Pawn 是当前世界 representation；
- Equipment 是当前应用状态；
- Input/Ability 可以 data-driven。

Lyra 额外提供：

- 更成熟的 init state coordination；
- Experience/GameFeature composition；
- CommonUI/EnhancedInput 多平台整合；
- 大版本升级演进证据。

---

## 21. 与 GASDocumentation 的对照

GASDocumentation 解释：

- OwnerActor/AvatarActor；
- Prediction；
- TargetData；
- SpecHandle。

Lyra 进一步展示：

- 多个 grant source 怎样进入同一 PlayerState ASC；
- PawnData/Equipment/GameFeature 如何授予；
- PawnExtension 怎样确保 Avatar ready 后才激活 Pawn-specific state。

因此二者互补，而不是互相替代。

---

## 22. 与 ALS/GASP/Mover 的边界

Lyra 的 PawnData/InitState 可以组织 Movement/Camera/Animation profile。

但是 LGF 已决定：

- Pawn + Mover；
- GASP/PSS/PSD；
- GameplayCamera；
- runtime C++ algorithm；
- data-driven animation。

所以不因为 Lyra 默认 CharacterMovement/动画方案而退回旧路线。

---

## 23. 拒绝项

本轮明确不写进 LGF Production 规则：

1. 整套复制 Lyra Foundation；
2. 复制 Lyra Inventory 覆盖现有 ARPG Inventory；
3. 仅因 Epic 使用就强依赖 Beta GameFeatures；
4. 把 5.0 Pawn init 当当前模式；
5. 把任何旧 Input/GameFeature API 签名当 5.7 authority；
6. 同时启用 Lyra Camera 与现有 GameplayCamera；
7. 把 CommonUI Widget 作为 gameplay truth；
8. 从第三方 Lyra notes 复制源码当官方证据。

---

## 24. API Recheck Required

以下都属于“机制可吸收，但实际项目改动前重新检查”：

- `IGameFrameworkInitStateInterface` 当前签名；
- `UGameFrameworkComponentManager` 事件与注册 API；
- GameFeature action lifecycle callback；
- `UGameFeatureAction_AddInputConfig` 及当前 input config 类型；
- PlayerMappable input 在 5.7/5.8 的配置变化；
- CommonUI Action Router 接口；
- AbilitySet/PawnExtension 具体 Lyra 类签名；
- Iris/Replication Graph 组合；
- Online Services/CommonUser 版本状态。

---

## 25. 技术时效性报告模板正式确定

以后每个 GitHub/UE 项目必须报告：

### Snapshot

- commit/tag；
- license；
- UE version；
- last active；
- source completeness。

### Freshness

- Current；
- Stable-but-old；
- Historical；
- Reject。

### Modern Cross-check

- 当前 UE 官方文档；
- 当前 engine source；
- 当前 official sample；
- 用户真实项目。

### Accepted

只保留机制。

### Recheck

列 API/配置。

### Rejected

列旧坑/演示性质边界。

### Target Mapping

明确映射到现有框架，不建平行系统。

---

## 26. 本轮写回 SkillForge

UE C++：

- `external-project-freshness-and-lyra.md`
- 新增 CPP-43..49。

LGF：

- `lyra-modern-framework-mapping.md`
- `external-project-patterns.md` 增加 Lyra 摘要；
- `validation-and-evolution.md` 增加技术时效性门；
- 新增 LGF-32..35。

---

## 27. 验收重点

文本/结构层：

- Skill validator；
- reference links；
- JSON schema；
- RED/GREEN semantics。

真实项目层仍待以后：

- UE5.7 编译；
- ModularGameplay InitState 实际适配；
- Listen/Remote/JIP；
- Avatar swap race injection；
- packaged build；
- 如果采用 GameFeatures，feature enable/disable/reload；
- input/UI focus；
- save/version compatibility。

---

## 28. 结论

Lyra 最值得学习的不是某个 `Lyra*` 类，而是两件事：

1. Epic 如何让多个现代 UE 系统在多人环境中组合；
2. Epic 自己如何随着 UE 演进，把旧实现降级、重写或替换。

从这一轮开始，SkillForge 对外部项目的目标不再是“收集更多模式”，而是：

> **收集仍然有效的模式，并持续淘汰已经过时的模式。**
