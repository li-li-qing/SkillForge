# TheGeebus/SimpleQuest 源码蒸馏（R14）

> 目标：不是把 SimpleQuest 整个搬进 LGF，而是从当前 UE5.6–5.8 Quest Framework 中提取 Objective / Step / State / Save / Network / Authoring 的可复用生产合同。

## 1. 固定研究快照

- 仓库：`TheGeebus/SimpleQuest`
- 默认分支：`main`
- 固定 commit：`46978ad2c81ba90f21836e7c468141523dedb95d`
- commit 日期：2026-09-14
- commit：`Merge pull request #19 from TheGeebus/develop – 0.8.1: Conditions, Endings, and Eleven Chapters`
- 对应 tree：`daf658bd6c86f54ca024d76e58a9a81908635617`
- License：MIT
- 插件版本：0.8.1
- README 目标：UE 5.6–5.8
- 研究时仓库活跃，非 archived。

### 1.1 Commit 和 Tree 不得混用

本轮最先纠正的研究错误就是把 `daf658bd...` 当成 commit。

实际：

```text
commit 46978ad2...
  ↓ points to
tree daf658bd...
```

外部项目蒸馏必须固定 commit SHA；tree SHA 只用于该提交的目录树内容寻址。

## 2. 技术时效性判断

结论：**Current-to-target**。

依据：

- 当前提交就是 2026-09-14 的 0.8.1 合并；
- README 明确 UE 5.6–5.8；
- `SimpleQuest.uplugin` 版本 0.8.1；
- Runtime / UncookedOnly / Editor 分离；
- StateTree / GameplayStateTree 是显式依赖；
- 0.8.x release 本身在继续做 Dedicated Server、Conditions、Endings、Save、Observer 等现代 multiplayer quest 问题。

但 `Current-to-target` 不等于“可无条件依赖”。

LGF 仍只吸收 active-code 证据和设计合同，第三方 plugin API 通过 adapter 隔离。

## 3. 模块边界

SimpleQuest 当前结构的优点是 Runtime 与 authoring/editor 分层明显。

主要插件：

```text
SimpleCore
  Runtime
SimpleCoreUncookedOnly
SimpleCoreEditor

SimpleQuest
  Runtime
SimpleQuestUncookedOnly
SimpleQuestEditor
```

这对 LGF Quest 工具很重要：

- UEdGraph / schema / compiler / pin reconstruction 留在 UncookedOnly / Editor；
- Shipping runtime 只消费编译结果；
- Runtime 不应该为了“任务图”被迫依赖 GraphEditor/UnrealEd。

## 4. 核心架构判断

SimpleQuest 最强的架构不是某个 Objective 类，而是：

```text
Authoring Graph
      ↓ compile
Runtime Quest Definition
      ↓
Quest Manager (sole writer)
      ↓
World facts / quest records / runtime state
      ↓
Quest State Subsystem (read side)
      ↓
Observer / UI / journal / telemetry
```

这与 R13 FlowGraph 不同。

FlowGraph 更偏通用 latent world/narrative orchestration；SimpleQuest 已经收敛成 Quest domain model。

## 5. Authoring Graph 不参与 Shipping 运行遍历

`UQuestlineGraph` 的注释直接说明：它拥有视觉 `UEdGraph`，同时持有 compiler output。

运行时重要字段包括：

- `CompiledQuestTags`；
- `CompiledIdentityTag`；
- `CompiledNodeAliases`；
- `EntryNodeTags`；
- `CompiledSourceHash`；
- `CompiledNodes`；
- `CompiledQuestlineRewards`；
- deactivation routes；
- listener/setter group tags。

这意味着：

```text
Graph layout
Pin widget
Editor node
      ↓ compile once
Runtime maps / arrays / tags / IDs
```

而不是：

```text
Quest progress signal
→ runtime traverse UEdGraph
→ inspect pin widget
→ find next node
```

### LGF 吸收

LGF 如果建立 Quest Editor，也应采用 compiler boundary，而不是把 Editor Graph 做成 runtime truth。

## 6. 编译结果本身需要 freshness evidence

SimpleQuest 的 `CompiledSourceHash` 很有价值。

它表达：

> runtime compiled result 是 authoring source 的派生缓存，需要能证明它是不是 stale。

LGF Quest compiler 应至少维护：

```text
DefinitionVersion
SourceHash / CompileHash
CompilerVersion
```

Cook/CI 在 stale 时失败，而不是让 Shipping 带着旧 compiled data。

## 7. QuestlineID 与 DisplayName 明确分离

`UQuestlineGraph` 的 `QuestlineID` 用于 GameplayTag semantic namespace。

而 `DisplayName` 的注释明确说：

> purely presentational，changing it never affects compiled tag identity。

这是非常好的长期合同。

因此：

```text
QuestlineID = identity
DisplayName = presentation
```

而不是：

```text
DisplayName = save ID
```

## 8. Objective stable identity

`UQuestObjective` 拥有 persistent `FGuid ObjectiveGuid`。

同时它还有：

- DisplayName；
- ObjectiveDescriptor；
- SignalBindings；
- active/completed/failed/frozen runtime flags；
- CurrentProgress / TargetProgress；
- progress snapshot/restore；
- signal subsystem binding；
- manager binding。

这证明 Objective UObject 主要是：

```text
runtime behavior + lifecycle + adapter
```

而不是 durable identity。

Durable identity 是 ObjectiveGuid / owning content identity。

## 9. Step 的语义数据

`FQuestStep` 包含：

- `SourceNodeGuid`；
- Step descriptor；
- QuestEvents；
- RequiredObjectives；
- StepConditions (`FInstancedStruct`)；
- `bPauseOnArrival`；
- `bYieldAfterComplete`；
- YieldSubsystemFlags。

这比“一个 Step 只有一个 Objective”成熟很多。

它说明 Quest Step 本身可以是一个编排 boundary：

```text
Step
 ├─ conditions
 ├─ multiple objective requirements
 ├─ events
 ├─ arrival policy
 └─ completion/yield policy
```

## 10. Objective Index 不是唯一 identity

RequiredObjectives 同时有 ObjectiveIndex 与 ObjectiveGuid。

LGF 应把 index 看成：

```text
compiled/runtime optimization
```

而 GUID 看成：

```text
semantic/save identity
```

数组顺序改变时，不能仅靠 index 恢复旧存档。

## 11. Manager / State CQRS 是当前源码明确合同

`UQuestManagerSubsystem` 的类注释非常明确：

- opaque orchestration；
- sole writer；
- lifecycle state machine；
- activation cascade；
- loaded instance registry；
- giver registry；
- async-load orchestration；
- push facts/events；
- display data registry。

并且明确说 adopter 不应直接进入 Manager。

Request side 应从 Blueprint Library 等稳定 facade 进入。

Read side 由 `UQuestStateSubsystem` 提供。

这是典型 CQRS：

```text
commands -> manager
queries  -> state subsystem
```

## 12. StateSubsystem 是纯读面

`UQuestStateSubsystem` 注释强调：

> Writes are exclusive to UQuestManagerSubsystem via friend access.

并且：

> Reads are pure.

Read side 保存/暴露：

- resolution history；
- entry history；
- prereq status cache；
- known quest tags；
- runtime records；
- current phase；
- display data；
- activation provenance；
- path identity；
- quest clock。

UI 不需要读 Manager 内部对象。

## 13. Quest clock 也是一个值得学习的语义域

StateSubsystem 定义了 Quest Time：

- 跨 level 连续；
- 跨 save 连续；
- pause 时不推进；
- 使用 gameplay time，不是 wall clock。

这比在每个 quest record 里随便存 `FDateTime::Now()` 更一致。

如果 LGF 需要：

- “接任务 10 分钟后失败”；
- “多久前完成”；
- “冷却多久后可重接”；

应先定义时间域。

## 14. Resolution history 与 current phase 分层

StateSubsystem 不只存“是否完成”。

它还保存：

- resolution count；
- chronological history；
- latest resolution；
- outcome lookup；
- path lookup；
- entry history；
- refusal history。

这样前置条件可以问：

```text
Quest A 是否完成过？
是否以 Outcome X 完成？
是否走 Path Y 完成？
完成过几次？
```

而不需要把所有逻辑塞进一个 `bCompleted`。

## 15. Named Outcome 是第一等语义

SimpleQuest 0.8.x 明确向 named outcome 演进。

Outcome 适合表达：

```text
Victory
Spared
Betrayed
TimedOut
Refused
```

### PathIdentity 与 Outcome 不等价

StateSubsystem 同时支持：

- `HasResolvedWith(QuestTag, OutcomeTag)`；
- `HasResolvedAtPath(QuestTag, PathIdentity)`。

这是非常好的区分。

两个不同 authored paths 可以有相同 semantic outcome。

## 16. Entry 也保存 Outcome / Path 上下文

Quest entry record 不只是“什么时候开始”。

Manager 的注释说明 entry snapshot 会携带：

- Provenance；
- ActivationParamsSnapshot；
- PathIdentity；
- cascade context。

这样 save/load 能按值重建当前 live questline。

## 17. Activation provenance 是显式必填信息

Manager 的 `ActivateNodeByTag` 刻意没有把 provenance 默认成 Unknown。

注释说明原因：

> forgotten call sites should become compile errors rather than silent Unknown stamps。

这是非常好的 API 设计。

重要 provenance 不要给“方便”的默认值。

例如：

```text
InitialEntry
GiverGate
ChainCascade
ExternalAPI
Restored
```

## 18. Conditions 是 runtime contract

`FQuestStep` 持有 `TArray<FInstancedStruct> StepConditions`。

SimpleQuest 0.8.1 重点包含 Conditions。

LGF 应继续强化：

```text
Condition = pure read predicate
```

条件可能被：

- UI preview；
- giver enablement；
- watcher；
- catch-up；
- Authority request validation；

反复求值。

因此不能在 Condition 里扣物品、加状态或发奖励。

## 19. 条件与资源消费分开

正确：

```text
HasKey? -> true
AcceptQuest request
Authority revalidates HasKey
Inventory transaction consumes Key
Quest enters Live
```

错误：

```text
HasKey condition
→ condition itself removes key
```

后一种在 UI 查询时都可能误扣资源。

## 20. Advancement Hold 是非常好的 Quest-specific pattern

Manager 提供：

```text
HoldQuestAdvancement
ReleaseQuestAdvancement
IsQuestAdvancementHeld
GetActiveHoldReasons
ReleaseAllQuestAdvancementHolds
```

Hold 返回 `FQuestAdvancementHold` handle。

理由必须提供 `FName Reason`。

多个 hold 会组合：

```text
Audio Hold
Cinematic Hold
```

只有最后一个释放后才继续。

## 21. Hold 的 Authority timing 特别重要

源码注释非常明确：

客户端在看到 completion replicated 后才请求 hold：**永远太晚**。

因为服务器已经完成 cascade。

这条可以推广到很多系统：

> 如果要阻止 Authority transition，reservation/hold 必须在 transition 前建立。

## 22. Hold 区分 forward 与 deactivation

`bHoldDeactivation` 说明“暂停推进”并不必然意味着“所有 corrective cleanup 也暂停”。

这比一个 `bPaused` 更准确。

LGF Quest pacing 应保留 policy 维度。

## 23. Hold 的 Save policy 是明确设计选择

SimpleQuest 会在 save capture 前释放所有 holds。

理由：

> pacing 不应该跨 save/load 恢复成看起来卡死的游戏。

这不是唯一正确策略，但它是一个**明确策略**。

LGF 应在 schema 里明确 transient pacing 是否保存，而不是偶然由 UObject survival 决定。

## 24. Save Snapshot 是 domain-shaped，而不是 UObject dump

`FSimpleQuestSaveSnapshot` 当前：

```text
Version
PlayTime
WorldFacts
Resolutions
Entries
ActiveGraphs
DeferredActivations
ObjectiveStates
```

这比“直接序列化 Quest Objective UObject 图”更可靠。

## 25. Snapshot Version 已存在

`FSimpleQuestSaveSnapshot::CurrentVersion = 1`。

`ApplySnapshot` 可以按 Version 分支。

这提供 schema migration boundary。

但 LGF 仍需要 R13 已定义的第二层：

```text
QuestDefinitionVersion
```

因为 schema 不变不代表任务内容语义不变。

## 26. Derived indices 不保存

Snapshot 注释明确：

- outcome lookup indices；
- parallel indices；

不保存，apply 后从 histories rebuild。

这是正确做法：

```text
canonical save state -> rebuild cache
```

而不是保存两份可能不一致的数据。

## 27. ActiveGraphs 让 Save self-describing

Snapshot 保存 `TArray<FSoftObjectPath> ActiveGraphs`。

恢复端可以根据 save 自己知道哪些 definition 需要 restore。

这优于调用方维护另一张“当前活动任务资产列表”。

但生产中仍应：

- allowlist 合法 quest definition；
- async load；
- version check；
- missing DLC fallback。

## 28. DeferredActivation 是真正需要保存的 transient intent

这是本轮很有价值的一点。

某 node 在 prerequisite 上等待时：

- 它还没成为完成 fact；
- 也没有 current objective progress；
- 但它必须在将来条件满足时醒来。

所以 Snapshot 保存：

```text
QuestContentGuid -> FQuestObjectiveRuntimeContext
```

恢复后重新 Activate，重新决定：

```text
prereq satisfied -> fire
otherwise -> defer again
```

不保存旧 delegate handle。

## 29. ObjectiveStates 按 stable content GUID 保存

Snapshot 使用 GUID key，而不是 Objective UObject pointer。

这再次支持：

```text
runtime UObject 可重建
semantic progress 不能丢
```

## 30. Restore path 不重跑 graph entry

Manager `RestoreQuestlineGraph` 的注释明确：

- 注册 compiled instances；
- 不重新 fire entry nodes；
- 根据 restored WorldState 重建 Live objectives；
- provenance 标记 Restored；
- 不重复 lifecycle event；
- 不重复 entry record；
- 不重复 forward cascade。

这是 production save/load 的关键。

错误的 load：

```text
load save
→ StartQuestline()
→ 从 Entry 全跑一遍
```

会重复奖励和 side effect。

## 31. Pending restore stash + next-world restore

Manager 支持：

- pending restore graph stash；
- async-load restore；
- next game world initialize 自动 flush；
- idempotent arm/clear。

这比把 load 生命周期绑死 BeginPlay 更成熟。

## 32. Event-driven Objective

SimpleQuest 的整体方向是 SignalSubsystem 驱动，而不是 Objective Tick。

Objective 信号来源可能是：

- quest event routing；
- objective signal binding；
- world facts；
- external typed signal。

LGF 应吸收事件驱动，而不照搬具体 SignalSubsystem 类型。

## 33. Catch-up 是第一等功能

`UQuestObserverComponent` 明确实现 per-tag catch-up。

并且注册延迟到 Actor BeginPlay 后一 tick。

原因非常现实：

Component BeginPlay 可能先于 actor 自己完成绑定；如果立即 synthetic replay，就可能打进半初始化对象。

这条可推广：

```text
listener registration
!=
listener ready for catch-up callback
```

## 34. Catch-up 只应用到可恢复状态

Observer 配置注释明确区分：

- Activated/Enabled/Started/Completed 等可 catch-up；
- Progress/refusal 等 transient 不 catch-up。

不要把“event-driven”误解成“所有历史 event 都必须存下来重放”。

## 35. Catch-all 与 narrow delegate 会双投递

Observer 注释明确：

> bind this OR narrow delegates, not both unless you want same event delivered twice; no framework-side cross-subscription deduplication。

这提供一个重要 LGF 加强点：

如果这些 event 会修改 progress，必须有 stable event ID/dedupe。

UI presentation 可以接受有意双订阅，但业务 progress 不可以。

## 36. Event payload 含 lineage/provenance

`FQuestEventPayload` 继承 context，包含：

- Instigator；
- CustomData；
- OriginTag；
- OriginChain；
- OriginatingEventID；
- NodeInfo；
- CompletionTrigger。

这让系统可以追问：

```text
这个事件从哪来？
经过什么语义链？
```

而不是只知道“收到一个 GameplayTag”。

## 37. Canonical tag 与 MatchedChannel 分离

Observer 注释详细区分：

- QuestTag = canonical source identity；
- MatchedChannel = 为什么这个 observer 收到事件的 delivery metadata。

这在 linked/inlined questline 非常关键。

LGF 可推广成：

```text
BusinessIdentity
DeliveryRoute
```

两者不要混。

## 38. Lifecycle event enum 兼容性

`EQuestEventTypes` 与 `EQuestLifecycleEventType` 分开：

- 一个做 multi-select bitmask；
- 一个做 Blueprint single arrival value。

源码甚至明确记录：新增值 append，避免 Blueprint-authored switch ordinal 被重排。

这是非常实用的 ABI 经验。

## 39. Event exposure 是按需成本控制

Observer 每种 event 都有开关。

未开启的 event：

- 不订阅；
- 不 catch-up；
- 不付成本。

相比“一个总线什么都收再过滤”更适合大量 Quest UI/actors。

## 40. Dedicated Server 是正式目标

README 0.8 明确将 headless dedicated server 作为 first-class。

Manager API 也明确存在：

- ClientRequest...；
- Server...；
- mirror state；
- PlayerState lifecycle；
- stable quest player key；
- pending mirror snapshots。

这比只在 Standalone 运行 Quest Graph 更接近 LGF 的目标。

## 41. Client request 仍不是 Authority validation 的证明

有 Server RPC 并不自动安全。

LGF 仍需要验证：

```text
caller owns scope?
quest exists?
phase expected?
step/revision matches?
condition satisfied?
objective complete?
hold clear?
outcome/path valid?
reward already granted?
```

SimpleQuest 提供 routing shape，不免除项目级安全审计。

## 42. Player/shared scope 是正式数据模型

Manager restore API 具有 Player 与 Shared 两套状态：

- player quest states；
- tracked player quests；
- player objective progress；
- player runtime states；
- shared quest states；
- tracked shared；
- shared objective progress；
- shared runtime states。

LGF 不应把“shared quest”临时实现成某个玩家的 quest pointer。

## 43. Stable player quest key

Manager 有 `GetPlayerQuestStableKey(APlayerState*)` 和反向解析。

这说明 Quest owner identity 不应直接等于当前 Pawn。

LGF 更进一步应使用自己的 stable account/agent/session identity contract。

## 44. Journal/read model 是 UI 的正确依赖

SimpleQuest 读侧包含 display data registry、phase、history、runtime record。

LGF 应建立：

```text
QuestReadRecord
```

让：

- Quest Journal；
- HUD tracker；
- map marker；
- NPC icon；
- dialogue choices；

从一份 read model 派生。

## 45. Giver Actor 不是 Quest Identity

StateSubsystem 会保存 last giver actor/provenance 作为 context。

但它不是 Quest 本身 identity。

未来 LGF 中 giver 可能：

- 是 Mass representation；
- 换 Pawn；
- 被玩家吸收；
- 被骑乘；
- dead/respawn。

Quest 需要 StableAgentId/role，而不是 Actor pointer 做 durable key。

## 46. Reward preview 与 reward grant 分离

Manager 有 `ResolveAdvertisedRewards` 等 pure preview path。

这很好：UI 可以预览，而不是为了“看奖励”就真正 grant。

LGF 再加强：grant 走 Inventory/Currency/Progression transaction + idempotency ledger。

## 47. Reward 与 Questline Outcome 对齐

`UQuestlineGraph` 有 `QuestlineRewards` keyed by outcome。

linked questline 被 compile inline 时，reward 也被编译进 enclosing runtime reachable data。

这避免 runtime 为了 reward 再加载 source asset。

## 48. Linked Questline 被 compile-time erase

源码注释明确：linked questline at compile time inline，source asset runtime 不必加载。

优点：

- runtime route 快；
- fewer dependency loads；
- definition self-contained。

风险：

- canonical identity/alias/placement identity 必须明确；
- source change 要使 parent compiled hash stale；
- linked asset cycle 必须在 compiler 阶段拒绝。

## 49. Alias 不应替代 canonical ID

一个 node 可能有多个 AssetScopedAliasTag。

因此：

```text
canonical identity
+ contextual alias(es)
```

比“直接用当前完整 tag 当唯一业务 ID”更稳。

## 50. Compiler 负责 sanitize/compose semantic tags

`CompiledIdentityTag` 注释说 runtime 不应该自己重新 compose，因为 sanitize logic 在 editor/compiler。

这是一条重要原则：

> editor/compiler 生成的 canonical semantic ID，runtime 只消费，不重复实现一套字符串规则。

否则两个模块迟早产生不同 tag。

## 51. SourceHash 可以发现 linked dependency stale

`CompiledSourceHash` 包含当前 graph + transitively linked graphs 的 authoring input。

这比只看当前 asset timestamp 更可靠。

LGF compiler 可借鉴依赖闭包 hash。

## 52. Quest Content 与 Display Data 分开

DisplayName、Description、DisplayData 可以变。

Quest semantic routing/identity 不跟着变。

这使 Localization/Art/UI 更新不会破坏 save。

## 53. Conditions 与 blocker diagnostics

StateSubsystem 不只返回 bool，还能 Query activation blockers / prereq status。

这是 UX 很需要的：

```text
为什么不能接任务？
```

不应该只有 false。

建议 LGF Condition 返回：

```text
Satisfied
ReasonTag / BlockerEnum
Optional display params
```

## 54. Progress Refused 也是正式事件

SimpleQuest 有 ProgressRefused / ActivationFailed / GiveBlocked。

这使失败不是 silent no-op。

LGF Request pattern也应提供结构化 reject reason，方便：

- UI；
- telemetry；
- debugger；
- automated tests。

## 55. Read-side catch-up 与 live event 统一形状

Observer catch-up会生成与 live event 类似的 payload。

优点：consumer 不用维护两套 UI 代码。

但必须标明：

- synthetic/catch-up；
- live；
- revision/event identity；

否则 progress consumer 可能重复执行 side effect。

## 56. Objective progress snapshot 是显式 API

Objective 本身提供：

```text
GetProgressSnapshot
RestoreProgressSnapshot
```

LGF 不要让 save layer反射扒 Objective UObject 私有字段。

每种复杂 objective 应有自己明确 snapshot DTO。

## 57. Objective state 与 Quest phase 分开

Objective：

```text
active/completed/failed/frozen
```

Quest：

```text
pending/offerable/live/blocked/resolved/deactivated...
```

不要用“objective completed”直接覆盖整个 quest phase。

## 58. Pause/Yield 是 Step orchestration policy

`FQuestStep` 有：

- PauseOnArrival；
- YieldAfterComplete；
- YieldSubsystemFlags。

这说明 pacing/coordination 可以是 Step-level explicit policy。

但对 LGF，异步 pacing 建议结合 handle-based advancement hold，不扩散 bool。

## 59. Event-driven 不等于 everything is GameplayTag

SimpleQuest 大量利用 GameplayTag，很方便层级订阅。

但 LGF 应继续区分：

- semantic type/tag；
- stable instance ID；
- domain event ID；
- payload。

一个 GameplayTag 不能同时充当 QuestInstanceId、ObjectiveGuid、EventId。

## 60. Hierarchical tag lookup 有成本

父 tag 订阅和 descendant catch-up 很强，但热路径不能无边界扫描。

StateSubsystem 为很多 query 建了 parallel O(1) indices。

LGF 也应：

- exact map for high-frequency；
- hierarchy only when semantics需要；
- cache compiled descendants；
- profile registry size。

## 61. Read models可以 append-only history + fast indices

SimpleQuest 保存 chronological resolution/entry histories，同时 runtime维护并行 lookup indices。

这是好模式：

```text
history = audit / richer query
index = hot lookup
```

Save history，load 后 rebuild index。

## 62. Refusal history 应 bounded

StateSubsystem 注释说明 refusal history 是 bounded，长 session 保留最近记录。

这避免 debug/telemetry history 无界增长。

LGF 所有 history/ledger 都要有 retention policy。

## 63. Save timestamp 需要同一时间域

Quest clock记录的 timestamps 跨 save 可比较。

不要混：

- World Time；
- Real Time；
- UTC wall clock；
- Server monotonic time；

否则“多久前”在读档后失真。

## 64. Quest restore不应重复 lifecycle events

Restore 必须区别：

```text
reconstruct state
```

与：

```text
new gameplay transition
```

否则：

- OnStarted 再发；
- OnCompleted 再发；
- reward再grant；
- analytics重复计数。

## 65. Runtime mirror不是第二份可写真值

Client mirror只用于 read/presentation。

任何 request 必须回 server manager。

Mirror revision/generation用于识别 stale state。

## 66. Dedicated Server不依赖UI callback

Quest progression不能等：

- Widget动画完成；
- Level Sequence客户端结束；
- AnimNotify；
- local observer callback。

如果 cinematic/presentation 必须 gate Authority，用提前建立的 hold/request protocol。

## 67. Authoring Pin rename 的长期规则

SimpleQuest repo 的提交历史持续修复 dynamic pins、stale pins、container pin refresh、outcome pins。

这说明 Editor graph 的 dynamic pin 系统本身是长期维护面。

因此：

- pin label/structure变化要 reconstruct；
- stale connections要检测并拒绝；
- semantic ID不能跟 pin display text绑定；
- compiler再做最终 route validation。

## 68. Event enum append-only 是 release ABI 教训

源码对 `EQuestLifecycleEventType` 的注释直接强调不应在中间插入，因为 BP authored switch可能依赖 ordinal。

LGF 所有存档/Blueprint-facing enum 都应有相同审查。

## 69. SimpleQuest 与 FlowGraph 的关系

二者不是互斥。

FlowGraph提供：

- generic latent graph lifecycle；
- subgraphs；
- save ABI；
- world/narrative orchestration。

SimpleQuest提供：

- quest phase；
- objectives；
- prerequisites；
- giver；
- outcomes；
- quest history；
- journal/read-side；
- advancement holds。

LGF可以：

- 自研 quest domain；
- 或在 FlowGraph 上建立 domain quest nodes；
- 或通过 adapter 集成 SimpleQuest。

不应把两套 runtime都无边界叠加。

## 70. 与 StateTree 的边界

StateTree回答：

```text
NPC下一步想做什么？
```

Quest回答：

```text
这个任务处于什么阶段？
需要什么Objective？
什么条件满足才可推进？
```

Quest可以给AI typed intent，但不替StateTree成为每帧brain。

## 71. 与 Mass 的边界

Mass Agent可以承载：

- giver marker summary；
- coarse quest role；
- world event affiliation。

真正与玩家高交互时 promotion 到 Actor/Pawn，绑定同一 durable quest state。

不为每个远距离Mass NPC建立完整Quest Manager。

## 72. 与 GAS 的边界

Quest不直接伪造 ability completion。

Combat objective只消费 Authority combat result。

如果一个 Quest step要求放技能：

```text
Quest -> Request semantic ability/action
GAS -> authoritative result
Quest -> consume result event
```

## 73. 与 Inventory 的边界

必须区分：

```text
Have 10 items
```

和：

```text
Collect 10 items over time
```

前者读当前库存；后者是累计事件/progress snapshot。

Turn-in要走Inventory Authority transaction后才推进Quest。

## 74. 迁移到 LGF 的建议

不建议立刻让 LGF Foundation 直接 public include SimpleQuest types。

建议 adapter：

```text
LGF Quest Contract
   ↕ adapter
SimpleQuest 0.8.x
```

未来插件升级、API变化或替换不会破坏Foundation ABI。

## 75. 推荐 LGF Quest 核心类型

概念上可有：

```text
FQuestDefinitionId
FQuestInstanceId
FQuestContentId/Guid
FQuestObjectiveId/Guid
FQuestScopeKey
FQuestReadRecord
FQuestObjectiveReadRecord
FQuestCommandResult
FQuestSnapshot
FQuestRewardGrantKey
```

不要求照此命名，但职责要明确。

## 76. 推荐 Request 模型

```text
QuestCommand
  RequestId
  CallerStableId
  QuestInstanceId / DefinitionId
  ExpectedRevision
  Operation
  Optional Outcome/Choice
```

Authority return：

```text
Accepted/Rejected
Reason
NewRevision
UpdatedReadRecord
```

## 77. 推荐 Revision 模型

Canonical quest instance每次业务 mutation：

```text
Revision++
```

客户端delta：

```text
FromRevision -> ToRevision
```

stale request可以拒绝/重新读取。

这样比只依赖事件到达顺序稳。

## 78. Reward Ledger

每个不可逆奖励：

```text
QuestInstanceId + SemanticRewardId
```

作为idempotency key。

如果 quest可重复，QuestInstanceId/RunId区别每一轮。

## 79. Quest repeatability

SimpleQuest有 resettable replay 概念。

LGF需要明确：

- one-shot；
- repeatable；
- daily/weekly；
- world-cycle；
- per-character/per-account。

Repeatability是 QuestInstance identity的一部分，不能只清 `bCompleted`。

## 80. Shared quest consistency

Party/shared Quest必须定义：

- 谁能start/abandon；
- member join/leave；
- objective credit rules；
- reward eligibility；
- party dissolve；
- offline member；
- JIP current state。

不能把 personal quest map共用一个pointer就叫shared。

## 81. Security checklist

所有客户端quest request：

- owner scope；
- quest availability；
- current phase；
- current revision；
- objective evidence；
- outcome/path合法；
- resource transaction；
- idempotency；
- rate limit where needed。

## 82. 性能 checklist

Measure：

- active QuestInstances；
- active Objectives；
- signal subscriptions；
- catch-up cost；
- hierarchical tag queries；
- async graph loads；
- journal projection cost；
- save size；
- restore time；
- history growth。

## 83. 测试 checklist

至少：

- UE5.7 target build；
- standalone；
- listen；
- remote；
- dedicated；
- JIP；
- reconnect；
- travel；
- avatar switch；
- save prereq-deferred；
- save live objective；
- restore without duplicate events；
- late observer；
- duplicate delivery；
- dynamic pin rename；
- ObjectiveGuid rename/migration；
- named outcomes；
- two simultaneous holds；
- reward retry；
- linked questline used twice；
- missing graph/DLC；
- historical save fixture。

## 84. 明确不吸收的做法

R14明确拒绝：

1. 直接依赖当前 Pawn 作为 quest owner；
2. runtime遍历editor graph；
3. display/event/pin name作为Save ID；
4. client直接决定Objective完成；
5. client直接选择任意Outcome推进；
6. Condition有side effect；
7. 一个`bPauseQuest`处理所有异步pacing；
8. restore重新从Entry执行；
9. UI各存一份quest progress；
10. signal通知代替durable snapshot；
11. reward node直接无ledger AddItem；
12. save delegate handles/UObject pointers；
13. schema version代替content migration；
14. 因仓库今天更新就跳过active-code审查。

## 85. 最终决策

SimpleQuest是本轮到目前为止非常值得吸收的Quest domain项目，因为它补上了FlowGraph没有专门解决的：

- Objective stable identity；
- quest lifecycle/read model；
- entry/resolution history；
- conditions/blockers；
- named outcomes/path identity；
- advancement holds；
- late observer catch-up；
- domain-shaped snapshot；
- dedicated/server mirror；
- graph compiler到runtime definition。

对LGF最合适的动作不是“立刻依赖SimpleQuest”，而是将这些合同写入SkillForge，并在未来真正实现Quest模块时用LGF现有Authority/Request/Inventory/GAS/Mass/StateTree架构承接。

## 86. 本轮未做的验证

本轮没有实际执行：

- SimpleQuest UE5.7 UBT；
- Editor graph compile；
- packaged build；
- Dedicated Server runtime；
- JIP/reconnect；
- historical 0.7→0.8 save migration；
- dynamic pin rename editor interaction；
- reward retry；
- large quest graph benchmark。

因此本文结论是源码级蒸馏与Skill合同，不声称LGF已经集成或SimpleQuest所有runtime路径都已在目标工程验证。
