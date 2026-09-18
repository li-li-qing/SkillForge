# LGF Quest / World Flow 编排合同

> 用于 LGameplayFramework 接入任务、剧情、世界事件、遭遇战编排、对话触发、教程和章节流程。参考 FlowGraph 的现代设计，但保持 LGF Foundation、Authority、GAS、Inventory、Mover、StateTree、Mass、StableAgentId 与现有 Save 系统为 canonical owner。

## 1. LGF 中 FlowGraph 的位置

默认层次：

```text
Quest / World / Narrative Definition
              |
              v
      Flow / Graph Orchestrator
              |
          Intent / Command
   +----------+----------+----------+
   |                     |          |
Inventory Authority     GAS       World Service
   |                     |          |
   +----------+----------+----------+
              |
      Canonical Domain State
              |
      Snapshot + Projection
        /             \
      UI           Client FX
```

Graph 是 orchestration owner，不是所有 domain truth 的 owner。

## 2. Quest truth 放稳定 owner，不放 Avatar

用户未来会：

- 死亡换 Pawn；
- 吸收 NPC；
- 变成场景物体；
- 骑任意 NPC/宠物；
- Mass promotion/demotion；
- 旅行/切地图；
- 断线重连。

所以：

```text
QuestInstance
branch/progress
reward ledger
world event state
```

不能挂在当前 shape Pawn 作为唯一真值。

### 2.1 推荐 owner

个人任务：

```text
PlayerState / Stable Player Agent / Quest Authority Service
```

世界任务：

```text
GameState / World Event Authority Service / server persistent record
```

NPC 长期剧情：

```text
StableAgentId + Narrative State Record
```

当前 Pawn/Avatar 只负责：

- 任务 marker presentation；
- 当前 interaction context；
- cinematic attachment；
- 本地 UI anchor；
- contextual dialogue trigger。

### 2.2 Avatar switch

```text
old Avatar detach
 -> bump AvatarGeneration
 -> remove presentation bindings
 -> keep QuestInstance unchanged
 -> attach new Avatar
 -> re-resolve current quest interaction/marker/context
```

绝不：

```text
Copy Quest UObject from old Pawn to new Pawn
```

---

## 3. Stable Quest identity

推荐业务身份：

```text
QuestDefinitionId
QuestInstanceId
StableOwnerId
GraphDefinitionVersion
NodeStableId
QuestRevision
```

世界事件：

```text
WorldEventDefinitionId
WorldEventInstanceId
WorldStateRevision
```

不要使用：

- Actor pointer；
- Pawn name；
- Flow runtime UObject name；
- array index；
- current map actor name；
- FMassEntityHandle。

---

## 4. Quest Graph 只提交 typed domain command

错误：

```text
GiveRewardNode
 -> Inventory.AddItem()

DamageBossNode
 -> Health -= 100

EquipNode
 -> Spawn Weapon Actor
```

正确：

```text
Graph Node
 -> FLGFQuestDomainCommand
 -> Authority service
 -> validate
 -> execute idempotently
 -> result
 -> graph continues
```

## 5. Quest Domain Command identity

至少：

```text
QuestInstanceId
GraphDefinitionId
NodeStableId
NodeActivationGeneration
RequestId
SemanticOperationId
StableOwnerId
TargetStableId
ExpectedQuestRevision
PayloadVersion
Payload
```

Authority 重验：

- QuestInstance 仍 active；
- Node 当前允许发该 operation；
- Owner 对 target/domain 有 capability；
- Inventory/GAS/world 当前状态仍合法；
- request 没处理过；
- reward 没领取过。

### 5.1 idempotency ledger

不可逆 side effect：

```text
GiveItem
GiveCurrency
UnlockFeature
GrantAchievement
SpawnUniqueBoss
ClaimReward
```

必须有 stable ledger key。

例如：

```text
QuestInstanceId + SemanticRewardId
```

不要仅用 transient activation pointer。

---

## 6. Result 驱动 Graph，不要“调用成功就继续”

Graph Node 等待：

```text
Success
Reject
Cancel
Timeout
OwnerGone
TargetInvalid
AlreadyCommitted
```

再选输出。

不要：

```text
Submit request
Trigger Out immediately
```

否则 domain reject 后 graph 已走到下一步。

### 6.1 stale result fence

结果回来校验：

```text
QuestInstanceId
NodeStableId
NodeActivationGeneration
RequestId
AvatarGeneration if request depended on current avatar
```

旧节点结果不得推进新节点。

---

## 7. Durable Quest State 与 Flow Notify 分层

### 7.1 durable truth

Authority 保存/复制：

```text
QuestInstanceId
QuestDefinitionId
GraphDefinitionVersion
Current semantic objectives
objective counters
branch choices
claimed rewards
world flags
revision
```

### 7.2 transient events

GameplayMessage / Flow Notify / RPC event 可以：

```text
QuestStepChanged
ObjectiveCounterChanged
DialogueAvailable
ShowToast
PlaySequence
MarkerChanged
```

但 event 不是 truth。

### 7.3 UI open / JIP

```text
UI opens / client joins
 -> fetch/current snapshot revision R
 -> build quest VM
 -> subscribe delta after R
```

不能要求 UI 从“过去曾广播过什么”推断当前任务。

---

## 8. Shared / Party / World Quest ownership

明确三类：

```text
Individual Quest
Party Quest
World Quest
```

每类必须定义：

- Authority owner；
- member visibility；
- join policy；
- leave policy；
- contribution ledger；
- reward ownership；
- JIP state；
- disband behavior；
- Save owner。

### 8.1 Party quest

不要把 party progress 复制成每人一份可独立修改真值。

```text
PartyQuestAuthority
 -> canonical revision
 -> per member projection
```

### 8.2 Contribution

若奖励与贡献有关，保存：

```text
StablePlayerId -> contribution
```

而不是当前 Pawn pointer。

---

## 9. Graph Save ABI 是发布合同

任务图一旦随着正式版本发布并进入玩家 Save：

```text
GraphDefinitionId
NodeStableId
QuestInstance state
```

就是兼容面。

### 9.1 禁止直接删除 persisted node

推荐：

```text
Node 17 old objective
 -> mark Deprecated
 -> old saves restore N17
 -> migrate to N42
 -> N17 pass-through/tombstone
 -> new quests no longer enter N17
```

### 9.2 Node ID 永不复用给不同语义

如果旧 `N17` = GiveSword：

绝不能未来把 `N17` 变成 GiveHorse。

否则老 Save 可能发错奖励。

---

## 10. Quest Save 需要两个版本

```text
SchemaVersion
GraphDefinitionVersion
```

### SchemaVersion

描述 serialization shape。

### GraphDefinitionVersion

描述 authored business semantics。

两者独立升级。

---

## 11. Migration 先 staging，再 live

```text
Load bytes
 -> parse version
 -> migrate into staging QuestRecord
 -> validate IDs / definitions / node mappings
 -> resolve owners and targets
 -> verify reward ledger
 -> create staging graph instances
 -> validate active subgraphs/latent states
 -> atomic publish/switch
```

失败：

- 保留现有 live state；或
- 进入明确 recoverable safe state；
- 不留下半迁移任务。

### 11.1 historical fixtures

CI 至少保留：

- N-1 Save；
- N-2 Save；
- launch Save；
- active latent node；
- active child graph；
- already claimed reward；
- removed DLC/content；
- corrupted record。

---

## 12. Cold Load 与 in-game Load

### Cold load

世界尚未开始时：

```text
restore stable owners
 -> restore quest graph
 -> bind world signals
 -> spawn avatar
 -> project UI
```

### in-game load

必须：

```text
block new quest operations
 -> quiesce current graphs
 -> staging restore
 -> validate
 -> switch
 -> resync clients
 -> release old graphs
```

不要在 old graph active 时直接再创建 new graph。

---

## 13. Latent Quest Node 的语义存档

保存：

```text
NodeStableId
ActivationGeneration
WaitSemantic = WaitForBossDeath
TargetStableAgentId
RemainingTime
ExpectedDomainRevision
```

不保存：

```text
DelegateHandle
FTimerHandle
Raw UObject pointer
AbilityTask pointer
Mover request object pointer
```

加载后重建订阅。

---

## 14. FlowGraph / StateTree / Mass / GAS 分工

这是 R13 最重要的 LGF 边界。

```text
FlowGraph
 = Quest / Narrative / World orchestration

StateTree / Utility
 = 单个 Agent decision owner

Mass
 = 大规模低成本 simulation

GAS
 = Ability execution / cost / effects / targeting

Mover/Nav
 = movement truth

Inventory
 = item truth
```

### 14.1 不要 FlowGraph 抢 Agent brain

Quest 可以要求：

```text
Escort NPC to Gate
```

但应产生：

```text
ScriptedOverrideIntent{Destination=Gate}
```

由 Agent decision/execution 层接受。

不要 Flow Node 每 Tick 直接 SetActorLocation。

### 14.2 Scripted Override contract

```text
OverrideId
QuestInstanceId
Priority
Generation
Expiry
Target/Intent
CancelPolicy
```

高优先剧情 override 完成/取消后，Agent 自动回到 StateTree autonomous decision。

---

## 15. 与玩家变身/吸收 NPC

玩家吸收 NPC 后：

- NPC 的 StableAgentId narrative state 保持；
- Player 的 QuestInstance 保持在 stable player owner；
- 当前 Avatar 只是 shape；
- Quest marker/context 重新解析；
- 不把 NPC quest runtime 复制给 Player Pawn。

如果“吸收”业务真的继承 NPC 剧情状态，必须是明确 domain transaction：

```text
TransferNarrativeOwnership
```

而不是因为 Mesh/Pawn 变了就自然继承。

---

## 16. 与坐骑/宠物

玩家上马：

```text
Mount StableAgentId stays
Pet/Mount narrative state stays
Player Quest state stays
Mount autonomous movement brain pauses/switches
Flow scripted event may hold mount override
Player owns locomotion intent
```

任务“骑这匹马到城门”应观察：

```text
MountStableAgentId
RiderStablePlayerId
world trigger
```

而不是绑定某个临时 Mount Pawn UObject。

---

## 17. Mass Agent 与 World Flow

不要：

```text
20000 Mass NPC
 -> 20000 UObject quest graphs
```

世界事件：

```text
Festival World Flow
 -> WorldEventState = Active
 -> Mass signal / shared fragment / processor sees state
 -> crowd behavior changes
```

只有：

- hero NPC；
- promoted NPC；
- 有独立 authored narrative；

才需要独立 narrative runtime instance。

---

## 18. SubGraph 在 LGF 的语义

推荐：

```text
MainQuest Graph
 -> Chapter SubGraph
 -> Encounter SubGraph
 -> Dialogue SubGraph
```

父节点拥有 child runtime。

### 18.1 不能把 SubGraph 当函数库

若逻辑是纯函数/条件：

- C++ domain service；
- DataAsset rule；
- shared evaluator；

更适合。

SubGraph 用于：

- 有独立 latent lifecycle；
- 有独立 save state；
- 有独立 authored flow；
- 可嵌套调试。

---

## 19. 递归与动态生成

如果任务图允许递归：

```text
explicit flag
max depth
instance budget
cycle diagnostic
save validation
```

默认不允许 self-subgraph。

动态生成 graph 更要记录 stable semantic definition，不要只保存 runtime object name。

---

## 20. 资产加载

LGF 不把 Graph 激活变成同步加载尖峰。

推荐：

```text
Quest chapter becomes eligible
 -> async preload graph + VO + sequence + dialogue assets
 -> PendingReady
 -> activation callback validates QuestInstanceId/revision
 -> Start graph
```

### 20.1 target UE5.7

FlowGraph 当前最新 2.4 是 UE5.9 方向。

LGF 当前若采用 FlowGraph，先以：

```text
v2.3-5.7
```

做 compile/runtime baseline。

需要从 2.4 学到的新机制通过 adapter/backport 审查，不直接复制 5.9 API。

---

## 21. GameplayTag 事件与 LGF GameplayMessage

二者都可以作为 projection/event bus。

推荐统一 envelope：

```text
EventTag
QuestInstanceId
SourceStableId
Revision
Sequence
CorrelationId
Payload
```

### 21.1 durable state 不依赖事件总线

任何：

- UI；
- Map marker；
- dialogue availability；
- tracker；

都能从 current quest snapshot 重建。

事件只用于增量。

---

## 22. Quest UI projection

```text
Authority Quest Record
 -> Quest Projection/ViewModel
 -> GameplayMessage delta
 -> CommonUI/UMG
```

UI 不直接读 Flow Node UObject 内部字段作为唯一状态。

原因：

- client 可能没有同一 graph runtime；
- JIP；
- Save migration；
- ServerOnly flow；
- editor/runtime implementation may change。

### 22.1 UI mutation

UI action：

```text
Claim Reward
Select Branch
Abandon Quest
```

仍走 server command。

---

## 23. Dialogue availability 不是另一个 Quest truth

对话系统未来接入时：

```text
DialogueOption availability
 <- QuestProjection / WorldState / StableAgent state
```

不要在 Dialogue Graph 内复制：

```text
QuestCount
BossKilled bool
RewardClaimed bool
```

否则 Quest 和 Dialogue 会漂移。

---

## 24. World Event

世界事件适合由 FlowGraph/Graph orchestration 驱动：

```text
Phase Prepare
 -> Spawn/enable objectives
 -> Broadcast snapshot
Phase Active
 -> Mass/crowd/combat systems receive intent
Phase Reward
 -> Authority contribution/reward service settles
Phase Cleanup
```

Graph 不直接保存每个玩家贡献明细；Contribution service 才是 owner。

---

## 25. Boss Encounter

FlowGraph 可拥有：

- Phase orchestration；
- gate conditions；
- cinematic；
- wave timing；
- semantic spawn request；
- phase transition。

Boss Actor/GAS owns：

- health；
- abilities；
- damage；
- cooldown；
- death。

Graph 等 canonical BossDeath event 后进入下一阶段。

---

## 26. Cleanup owner matrix

| 资源 | owner |
|---|---|
| Quest runtime graph | Quest authority service / graph subsystem |
| SubGraph | Parent SubGraph node |
| Domain request | request source node + domain service |
| Spawned temporary presentation | explicit node/encounter owner |
| GAS grant | grant source |
| Ability activation | ASC/Ability + request identity |
| Mover request | movement owner |
| UI route | UINavigation |
| Quest marker | quest projection/presentation layer |

不要让 GC 替代这个表。

---

## 27. Abort matrix

Graph Abort 时按资源类型处理：

```text
Cosmetic sequence      -> stop/fade
Temporary spawned FX   -> remove
Quest reward committed -> never undo silently
Pending reward request -> cancel if not committed
GAS ability            -> only if this flow owns exact activation and policy allows
Mover request           -> cancel exact request
SmartObject claim       -> release exact claim
SubGraph                -> Abort recursively
```

`Abort` 不是“清空世界所有相关东西”。

---

## 28. Diagnostics

每个 Quest runtime 诊断至少：

```text
QuestInstanceId
QuestDefinitionId
GraphDefinitionVersion
StableOwnerId
RuntimeGeneration
Authority role
Active NodeIds
Active SubGraphs
Last EventId/Sequence
Pending DomainRequests
Reward Ledger entries relevant to quest
Last Save SchemaVersion
Last Migration
Last Abort/Reject reason
```

### 28.1 客户端诊断

显示：

```text
ProjectionRevision
LastAppliedEventSequence
GapDetected
SnapshotSource
```

能快速判断“服务器任务没推进”还是“客户端 UI 漏事件”。

---

## 29. 测试矩阵

### Authority

- Host；
- Remote Client；
- Dedicated；
- Client tries reward mutation；
- repeat request idempotency。

### Save

- cold load；
- active-world load；
- active timer；
- active child graph；
- already claimed reward；
- old graph version migration。

### Avatar

- death respawn；
- absorb NPC；
- prop transform；
- mount/dismount；
- avatar switch during latent quest node。

### Network

- JIP；
- reconnect；
- message gap；
- duplicate event；
- stale projection revision。

### Scale

- 1 quest；
- 100 active quests；
- many party quests；
- world event fanout；
- no per-Mass-agent graph explosion。

---

## 30. LGF 不直接照搬 FlowGraph 的部分

即便采用 FlowGraph runtime，也需要 project wrapper：

- StableOwnerId；
- QuestInstanceId；
- GraphDefinitionVersion；
- SaveSchemaVersion；
- domain command gateway；
- reward idempotency ledger；
- JIP snapshot；
- active-world load transaction；
- Mass/StateTree/GAS adapter；
- project diagnostics。

而且当前目标 UE5.7 应锁 `v2.3-5.7`，不是直接追 2.4/UE5.9 branch。

---

## 31. LGF 默认原则

```text
FlowGraph defines authored orchestration
StateTree decides agent intent
Mass simulates populations
GAS executes gameplay abilities
Mover owns movement
Inventory owns items
Quest Authority owns durable quest truth
UI owns presentation only
```

如果任何新系统开始同时拥有这些真值，先停下来重新划 Authority 边界，而不是继续加同步代码。
