# MothCocoon/FlowGraph：Quest / World Event / Graph Runtime / Save ABI 蒸馏

> 第十三轮外部 UE 项目蒸馏。研究日期：2026-09-14。
>
> 最新设计锚点：`MothCocoon/FlowGraph@c616a5d2afa8124cb7c1d66b1071fd499f2be7db`，默认分支 `5.x`，MIT，提交日期 2026-08-31。
>
> LGF UE5.7 兼容锚点：`v2.3-5.7@8211b25999068407cb7b40b8c97e18b52d4832ca`。
>
> 当前 `5.x` 是 Flow 2.4 in works，release note 标记为首个 UE5.9 release；因此本报告严格区分“最新设计方向”和“UE5.7 可直接验证 API”。

---

## 1. 为什么现在研究 FlowGraph

前十二轮已经把 LGF 的多数底层 ownership 收敛：

- Inventory / Equipment / Save；
- GAS prediction / TargetData / grant lifetime；
- Pawn + Mover；
- GASP/动画线程与 Linked Layers；
- CommonUI / Input；
- MassEntity hybrid simulation；
- StateTree / Utility AI decision owner。

下一层问题是：

> 多个已经正确分层的 gameplay domain，如何被任务、剧情、章节、世界事件、遭遇战和教程“编排”起来？

如果没有 orchestration 层，项目通常会退化成：

```text
Quest Blueprint
 -> 直接 AddItem
 -> 直接 ApplyGameplayEffect
 -> 直接 SpawnActor
 -> 直接 MoveTo
 -> 直接改 UI
 -> 直接写 Save
```

结果是 Quest 系统成为第二个 Inventory、第二个 Combat、第二个 Save、第二个 AI。

FlowGraph 很适合研究这一层，因为它不是“Quest plugin”本身，而是一个 design-agnostic graph runtime：

- UObject node；
- root/sub graph runtime instances；
- latent node lifecycle；
- SaveGame；
- gameplay tags；
- multiplayer notification projection；
- debugger；
- editor validation；
- patch compatibility。

本轮目标不是决定“LGF 必须安装 FlowGraph”。

目标是把这些机制蒸馏成 LGF 可长期维护的 Quest / World Flow contract。

---

# 2. 技术时效性审计

## 2.1 仓库活跃度

当前仓库仍活跃：

- 默认分支：`5.x`；
- 固定最新研究提交：`c616a5d2...`；
- 日期：2026-08-31；
- MIT；
- C++；
- 大量 issue / PR / release 历史；
- runtime/editor/debugger 三个模块持续维护。

因此不是 Historical 项目。

但“活跃”不等于“当前目标 UE5.7 可直接使用 default branch”。

---

## 2.2 关键版本分叉

当前 `Flow.uplugin`：

```text
Version = 2.4
Runtime module: Flow
DeveloperTool: FlowDebugger
Editor: FlowEditor
IsBetaVersion = false
```

但 `docs/Releases/Version24.md` 明确：

```text
Flow 2.4 (in works)
first release for UE 5.9
```

所以：

```text
latest 5.x
 !=
LGF 5.7 API baseline
```

---

## 2.3 UE5.7 正确锚点

Flow 2.3 release note：

```text
first release for UE5.8
last for UE5.6
separate Flow 5.8 / 5.7 / 5.6 release tags
```

本轮固定：

```text
v2.3-5.7
 -> 8211b25999068407cb7b40b8c97e18b52d4832ca
```

它才是 LGF 当前 UE5.7 直接编译/运行验证的起点。

---

## 2.4 双锚点研究法

以后类似插件统一：

```text
latest branch
 = 学最新 architectural intent

target-engine tag
 = 学目标项目 API contract
```

例如 2.4 新设计若 UE5.7 tag 不存在：

- 可以学习模式；
- 可以 backport；
- 可以 adapter；
- 不能写成 UE5.7 已原生可用。

这是本轮最重要的 freshness 结论之一。

---

## 2.5 Staged asset migration 比 API migration 更隐蔽

Flow 2.3 对 Data Pins 有明确升级警告：

```text
如果来自 2.2 之前版本
不要直接升级到 2.3 之后
先到 2.2/2.3
加载并 resave assets
再继续升级
```

这意味着：

> “当前代码能编译”并不能证明旧内容资产可以跨多个版本直接迁移。

长期运营项目必须同时维护：

- C++ API migration；
- serialized asset migration；
- SaveGame migration。

三者不能混为一个版本号。

---

# 3. 模块与职责图

当前插件主要模块：

```text
Flow
  Runtime

FlowDebugger
  DeveloperTool

FlowEditor
  Editor
```

Runtime 核心主要包括：

```text
UFlowSubsystem
UFlowAsset
UFlowNode / UFlowNodeBase
UFlowComponent
UFlowNode_SubGraph
FlowSave
Flow Data Pins
Flow AddOns
Flow Preload Policy
Deferred Transition / Execution Gate
Specific runtime nodes
```

这个拆分是好的：

- runtime 不依赖完整 editor；
- debugger 可以单独作为 DeveloperTool；
- graph authoring 复杂度留在 editor module。

LGF 自己以后做 Graph/Quest tooling 时也应保持：

```text
runtime truth
!=
editor tooling
!=
debug visualization
```

---

# 4. FlowAsset：Definition 与 Runtime Instance 分离

这是本轮最值得迁入 LGF 的机制之一。

`UFlowAsset` 既可以是 authored template，也可以创建 transient runtime instance。

`UFlowSubsystem::CreateFlowInstance()` 的方向是：

```text
LoadedFlowAsset template
 -> NewObject transient runtime asset instance
 -> InitializeInstance(Owner, TemplateAsset)
 -> template tracks ActiveInstances
```

因此：

```text
Definition Asset
 !=
Runtime Flow Instance
```

---

## 4.1 Template 中的数据

`UFlowAsset` template 包含：

- `AssetGuid`；
- `TMap<FGuid, UFlowNode*> Nodes`；
- graph/pin connections；
- custom inputs / outputs；
- allowed/denied node classes；
- params；
- editor metadata。

这是**定义**。

---

## 4.2 Runtime instance 中的数据

runtime instance 又有：

- `TemplateAsset`；
- `Owner`；
- `NodeOwningThisAssetInstance`；
- `ActiveSubGraphs`；
- `ActiveNodes`；
- `RecordedNodes`；
- `FinishPolicy`；
- runtime node state。

这是**运行状态**。

---

## 4.3 LGF 映射

Quest definition：

```text
QuestDefinitionId
GraphDefinitionId
GraphDefinitionVersion
NodeStableIds
static objectives
static rewards
static narrative metadata
```

Quest runtime：

```text
QuestInstanceId
StableOwnerId
RuntimeGeneration
ActiveNodeIds
objective progress
branch state
reward ledger references
subflow instances
pending requests
revision
```

不要让 DataAsset 本身保存玩家任务进度。

---

# 5. NodeGuid：编辑器 ID 会变成 Save ABI

`UFlowNode` 有：

```text
FGuid NodeGuid
```

Flow save record直接保存：

```text
FFlowNodeSaveData
  NodeGuid
  NodeData
```

这改变了 NodeGuid 的性质。

在尚未发布时，它是 editor identity。

一旦进入玩家 Save：

```text
NodeGuid = persistence ABI
```

---

## 5.1 这意味着什么

发布后不能随意：

- 删除 active node；
- 重新生成 GUID；
- 把旧 GUID 给另一种业务语义；
- 让旧 GUID 的 irreversible output 完全改变含义。

这和数据库 primary key 很像。

---

# 6. Flow Node 是 feature object，不是 function call

README 与源码都明确把 Flow Node 设计成 UObject gameplay feature。

一个节点可以长期 active：

- 等 Timer；
- 等 Actor；
- 等 LevelSequence；
- 等 GameplayTag notify；
- 等 domain action；
- 创建 SubGraph；
- 保存自己的 runtime state。

因此正确心智不是：

```text
ExecuteNode()
returns
```

而是：

```text
Activate
 -> pending/working
 -> output
 -> Complete / Abort
 -> Cleanup
```

---

# 7. Node state model

Flow 当前：

```text
NeverActivated
Active
Completed
Aborted
```

这是一个健康模型。

它比：

```text
bool bDone
```

强很多，因为 Save/Load、debug 和 Abort 都需要知道节点为什么结束。

LGF Quest Node 同样应至少有：

```text
NeverStarted
Active
Completed
Aborted
Failed(optional semantic result)
```

注意：

`Failed` 可以是业务输出结果，而 `Aborted` 是生命周期结束原因，二者不一定相同。

---

# 8. Finish 与 Deactivate

固定源码中：

```text
UFlowNode::Finish()
 -> Deactivate()
 -> FlowAsset->FinishNode(this)
```

这说明 Node Finish 不只是改一个 bool，而是：

- 改节点 lifecycle；
- 从 graph active set 移除；
- 进入 recorded/finished tracking；
- 允许 graph 完成判断。

这是值得保持的 ownership。

---

# 9. Keep / Abort FinishPolicy

`EFlowFinishPolicy`：

```text
Keep
Abort
```

源码注释明确给出语义：

> 节点可以根据 Flow 是正常结束还是 aborted 采取不同 teardown；例如 Spawn node 在 Abort 时可以清理 spawned actor。

这是比“StopGraph”更好的业务模型。

---

## 9.1 LGF 映射

例如剧情生成临时守卫：

```text
Quest completes normally
 -> guards become world residents
 -> Keep

Quest abandoned / load rollback
 -> guards disappear
 -> Abort
```

不能统一：

```text
OnGraphDestroy -> DestroyAllSpawnedActors
```

---

# 10. Cleanup 必须 source-owned

每个 latent node 自己负责：

- delegate handles；
- timers；
- async load requests；
- sequence callbacks；
- temporary actors；
- domain request listener；
- SmartObject claim；
- exact Ability activation/request；
- child graph。

Graph shutdown 不应该猜：

> “世界里名称像这个 quest 的对象都删掉”。

---

# 11. Stale callback 问题

典型：

```text
Quest node N10 starts async dialogue asset load
player abandons quest
new QuestInstance starts N10 again
old load callback returns
```

如果只看：

```text
NodeGuid == N10
```

仍可能误命中新实例。

所以需要：

```text
QuestInstanceId
RuntimeGeneration
NodeStableId
NodeActivationGeneration
AsyncRequestId
```

共同 fence。

---

# 12. Deferred Transition：FlowGraph 最有价值的 runtime 细节之一

Graph 系统非常容易出现重入：

```text
A output
 -> B input
 -> B Finish parent
 -> parent destroys A
 -> A call stack still continues
```

FlowGraph 新版加入 `FFlowDeferredTransitionScope`。

其记录：

```text
NodeGuid
PinName
FromPin
```

并由 scope flush。

---

# 13. Execution Gate

Deferred queue flush 会观察：

```text
FFlowExecutionGate::IsHalted()
```

如果 debugger 或执行 gate halt：

- 停止 flush；
- 不继续递归执行；
- 后续可以 resume 或 clear。

这使图执行拥有 safe point。

---

# 14. Scope FIFO 与 global FIFO

`UFlowSubsystem::TryFlushAllDeferredTriggerScopes()` 的注释非常有价值：

```text
per-asset FIFO reasonably preserved
not strict global FIFO across assets
```

这是正确的诚实边界。

如果世界事件真的要求全局排序：

```text
WorldEventSequence
```

应该显式存在。

不要把 TArray/TMap iteration order 误当业务顺序。

---

# 15. Transition storm / cycle

FlowGraph 有防 recursion/reentry 的机制，但长期项目还应该加 budget：

```text
max immediate transitions/frame
max deferred triggers/scope
max graph starts/frame
max child graph depth
```

并输出：

```text
GraphInstanceId
NodeId
FromPin
ToPin
Sequence
```

用来诊断 event storm。

---

# 16. SubGraph ownership

`UFlowNode_SubGraph`：

- 保存 soft Flow Asset；
- 创建 child graph instance；
- child 继承 owner；
- child 记录 owning SubGraph node；
- parent 记录 ActiveSubGraphs；
- Cleanup 时 RemoveSubFlow；
- Save 时记录 child instance name。

核心：

```text
SubGraph Node
 = child runtime graph lifecycle owner
```

---

# 17. SubGraph parent-child registry

创建：

```text
FlowSubsystem::CreateSubFlow
 -> CreateFlowInstance
 -> InstancedSubFlows.Add(SubGraphNode, Child)
 -> Child.NodeOwningThisAssetInstance = SubGraphNode
 -> Parent.ActiveSubGraphs.Add(...)
```

移除：

```text
Parent.ActiveSubGraphs.Remove
InstancedSubFlows.Remove
Child.FinishFlow(policy)
Child.NodeOwningThisAssetInstance = null
```

这个对称性应该写成 Graph Runtime invariant。

---

# 18. Self recursion 默认关闭

SubGraph 有：

```text
bCanInstanceIdenticalAsset = false
```

默认禁止 graph 创建自己。

这很合理。

如果项目要递归任务模板：

```text
explicit opt-in
+ max depth
+ cycle key
+ instance budget
+ Save restore validation
```

---

# 19. Soft object reference 不代表异步

这是本轮一个重要反例。

SubGraph 使用：

```text
TSoftObjectPtr<UFlowAsset>
```

但 `CreateSubFlow()` 当前 active runtime path 中仍有：

```text
SubGraphNode->Asset.LoadSynchronous()
```

所以：

```text
Soft pointer exists
!=
runtime async
```

---

# 20. 2.3 preload 改进也不能过度宣传

2.3 release note：

- preload 改成 policy-driven；
- async-safe；
- per-project extendable。

但 current `UFlowNode_SubGraph::PreloadContent()` 的源码注释仍说：

```text
CreateSubFlow currently synchronous-only
async UFlowAsset load could be added later
```

结论：

- preload framework 是 Accepted Mechanism；
- SubGraph async runtime load 还不能写成 Verified Feature。

---

# 21. Production asset loading

LGF 推荐：

```text
Quest becomes eligible
 -> gather graph/VO/sequence deps
 -> AssetManager async preload
 -> PendingActivation
 -> revalidate QuestInstance/revision
 -> create graph
 -> run
```

而不是在玩家点 NPC 的那一帧：

```text
LoadSynchronous 200 MB narrative pack
```

---

# 22. SaveGame core data

Flow 当前核心 save structs：

```text
FFlowNodeSaveData
  NodeGuid
  NodeData bytes

FFlowAssetSaveData
  WorldName
  InstanceName
  AssetData bytes
  NodeRecords

FFlowComponentSaveData
  WorldName
  ActorInstanceName
  ComponentData
```

并使用：

```text
FObjectAndNameAsStringProxyArchive
ArIsSaveGame = true
```

---

# 23. SaveGame 优点

值得吸收：

- Node/Asset/Component 分层保存；
- Node SaveGame properties；
- subsystem 统一收集 active runtime graphs；
- project 可以接管外层 save container；
- node `OnSave/OnLoad` 扩展；
- SubGraph child restore；
- CanSave 支持 transient graph。

---

# 24. SaveGame 缺的业务层

这些 core structs 中没有看到通用：

```text
SaveSchemaVersion
GraphDefinitionVersion
StableOwnerId
QuestInstanceId
RewardLedgerVersion
```

所以 Flow Save 很适合作为 runtime graph serialization 层，但不应直接承担整个 ARPG Quest persistence business schema。

---

# 25. WorldName / ActorInstanceName 风险

这些字符串可用于 world-bound graph 恢复辅助。

但不适合作为长期唯一 identity：

- Actor rename；
- respawn；
- Pawn replacement；
- World Partition；
- PIE prefix；
- server travel；
- player transform。

LGF 应加 Stable IDs。

---

# 26. In-game load 需要专门路径

FlowGraph 自己的文档明确提醒：

> FlowComponent 自动 LoadRootFlow 主要发生在 BeginPlay；world 已 active 后读档，项目自己负责手动 load。

这不是小细节。

说明：

```text
Cold Load
!=
Active World Load
```

---

# 27. Active World Load 生产流程

推荐：

```text
Block new Quest Commands
 -> Quiesce old graphs
 -> Parse save into staging
 -> Schema migration
 -> Graph version migration
 -> Resolve stable owners
 -> Restore graph/subgraphs in staging
 -> Validate reward ledger
 -> Switch canonical Quest state
 -> Rebuild client projection
 -> Dispose old runtime
```

不要在 live graph 旁边直接 Load 同一个 quest。

---

# 28. Signal Mode 是 shipped save compatibility pattern

FlowGraph `SignalModes.md` 解释得非常清楚：

如果 Save 记录一个 active node，发布补丁后直接删除这个 node，旧存档就无法继续。

因此提供：

```text
Enabled
Disabled
PassThrough
```

PassThrough：

- 不执行旧节点内部逻辑；
- 仍保留 node identity；
- 触发输出；
- 完成。

这是很好的 tombstone 思路。

---

# 29. Graph patch 的正确策略

```text
Shipped node N17
 -> mark deprecated
 -> retain N17
 -> PassThrough / Redirect
 -> new connections go to N42
 -> migration moves saved semantic state
```

等支持的历史 Save horizon 结束后再考虑真正删除。

---

# 30. Connection 与 Node Save identity 的不同

Flow 文档指出 connections 不直接 serialized 到 SaveGame，因此 patch connection 比删除 Node identity 更安全。

但：

```text
safer
!=
always safe
```

如果重连后会导致不可逆 reward 再执行，仍要依赖 ledger/idempotency。

---

# 31. Data Pin staged migration 的长期价值

这是典型“代码/API 兼容但资产还需要中间版本”的例子。

因此 SkillForge freshness gate 新增：

```text
Target Engine Version
Target Plugin Version
Serialized Asset Migration Path
Save Migration Path
```

四个都要看。

---

# 32. FlowComponent networking

FlowComponent 是 replicated ActorComponent。

它复制：

- IdentityTags；
- RecentlySentNotifyTags；
- NotifyTagsFromGraph；
- NotifyTagsFromAnotherComponent。

并在 Push Model 可用时显式 dirty。

这个方向对 authored event projection 很实用。

---

# 33. EFlowNetMode

当前 enum：

```text
Any
Authority
ClientOnly
ServerOnly
SinglePlayerOnly
```

默认大多数 flow 使用 Authority。

这说明 FlowGraph 已经意识到 Graph execution location 是一等设计维度。

---

# 34. 但 EFlowNetMode 不等于业务 Authority framework

即使 Node 只在 Authority 运行，也不能因此越过：

- Inventory transaction；
- GAS CanActivate；
- Reward ledger；
- Container capability；
- World actor ownership。

FlowGraph 只能调用这些系统的 Authority API。

---

# 35. Replicated notify 不是 durable state

例如：

```text
Quest.Step.Completed
```

通过 replicated tag property + OnRep 到客户端，可以很好地触发 UI。

但：

```text
notify arrived
```

不是：

```text
quest completion durable truth exists forever
```

JIP 客户端可能没看到过去 notify。

---

# 36. 正确 JIP 模型

```text
Authority Quest Snapshot revision=71
 -> new client receives snapshot
 -> builds current UI/markers/dialogue availability
 -> subscribes deltas after 71
```

事件只做 delta/projection。

---

# 37. Important event envelope

LGF Quest event 建议：

```text
QuestInstanceId
QuestRevision
EventSequence
EventId
SourceNodeId
CorrelationId
PayloadVersion
Payload
```

消费者可以：

- dedupe；
- detect gap；
- reject stale；
- request resync。

---

# 38. Identity Tags registry

FlowSubsystem 使用：

```text
TMultiMap<FGameplayTag, Weak FlowComponent>
```

适合：

- authored NPC role；
- world trigger identity；
- narrative actor discovery。

---

# 39. Non-exact tag lookup 的性能警告

FlowSubsystem header 自己警告 non-exact search 可能与 registered Gameplay Tags 数量成比例。

因此：

- 低频 Quest 查找：可接受；
- 20k NPC 每帧查：不接受。

大量实体仍用：

- Mass query；
- stable ID map；
- spatial index。

---

# 40. Graph domain fit

FlowGraph 非常适合：

- Quest；
- World Event；
- Narrative；
- Encounter；
- Tutorial；
- Chapter；
- Cinematic；
- Cross-system authored event chain。

---

# 41. Graph domain anti-fit

不应作为默认：

- Mass NPC per-frame brain；
- projectile simulation；
- combat hot loop；
- movement integration；
- animation pose；
- per-item inventory mutation。

这些已有更合适的 data-oriented/domain owner。

---

# 42. FlowGraph / StateTree / Mass 的职责分离

```text
FlowGraph
 -> 世界/任务“发生什么”

StateTree
 -> 单个 Agent“现在做什么”

Mass
 -> 很多 Agent“低成本怎么活着”

GAS/Mover
 -> 高保真 Agent“具体动作如何执行”
```

这四层不能互抢 Current State。

---

# 43. Scripted override

Quest 需要 NPC 去城门时：

错误：

```text
Flow Tick -> SetActorLocation
```

正确：

```text
Flow
 -> ScriptedOverrideIntent
 -> Agent Decision Owner
 -> Mover/Nav
```

Override 有：

```text
OverrideId
Priority
Generation
Expiry
CancelPolicy
```

完成后还给 autonomous StateTree。

---

# 44. FlowGraph / GAS

Graph 请求：

```text
UseSemanticAbility(AbilityTag, TargetStableId)
```

GAS 负责：

- ability grant/source；
- CanActivate；
- cost；
- cooldown；
- target validation；
- prediction；
- gameplay effect。

Graph 等 result。

---

# 45. FlowGraph / Inventory

Quest `GiveReward`：

```text
Graph Node
 -> Reward Authority service
 -> Inventory transaction
 -> success ledger
 -> graph result
```

禁止 Graph 直接修改 FastArray。

---

# 46. Idempotent reward

Save/Load、reconnect、重复 Notify 最容易导致：

```text
Give Sword x2
```

稳定 key：

```text
QuestInstanceId
+ RewardSemanticId
```

Authority ledger：

```text
if committed -> AlreadyCommitted
else grant -> record commit
```

---

# 47. FlowGraph / World Spawn

Unique Boss spawn 同理：

```text
EncounterInstanceId + SpawnSemanticId
```

重复 node activation 不重复 spawn canonical boss。

表现性的烟雾/粒子可不需要永久 ledger。

---

# 48. SubGraph Save identity

SubGraph 保存 child instance name 可以帮助 runtime restore。

LGF 还应该保存：

```text
ParentQuestInstanceId
ParentNodeStableId
ChildDefinitionId
ChildQuestSubInstanceId
ChildDefinitionVersion
```

避免只靠 transient name。

---

# 49. Preload ownership

Flow 2.3 开始把 preload 做成 policy。

这很好，因为不同项目策略不同：

- chapter preload；
- area preload；
- manual；
- on-near-node；
- memory pressure flush。

LGF 应保留 policy boundary，不把 preload timing 写死在 Node class。

---

# 50. Async preload callback

回调校验：

```text
WeakGraph
QuestInstanceId
NodeActivationGeneration
PreloadRequestId
```

如果 Node 已 abort：丢弃。

---

# 51. Editor validation

FlowGraph 有成熟的 editor validation 思路：

- allowed/denied node class；
- invalid/null node；
- duplicate pin names；
- asset reference restrictions；
- child graph validation。

这类 Graph system 必须把错误尽可能前移到 authoring time。

---

# 52. LGF 可以进一步增加的 validation

- NodeStableId duplicate；
- shipped ID reuse；
- irreversible node missing idempotency key；
- client-only graph with authority mutation command；
- unbounded recursion；
- missing domain service；
- hard/sync loaded heavy dependency；
- missing migration mapping；
- impossible Finish path；
- deadlocked Wait node。

---

# 53. Runtime debugger

FlowGraph 的节点/连线 runtime debug 是优秀模式。

Quest 系统最常见问题不是 crash，而是：

> “为什么没继续？”

应该能回答：

```text
QuestInstanceId
Graph version
Current node
last input
last output
waiting reason
pending request
child graph
last authority reject
```

---

# 54. Debugger 与 Save migration 结合

老存档问题还要显示：

```text
Loaded SchemaVersion
Loaded GraphDefinitionVersion
Current Version
Migration Steps Applied
Node Redirects
Tombstones
Missing content
```

否则现场很难判断是图逻辑 bug 还是 migration bug。

---

# 55. Runtime message 不等于 shipping telemetry

Editor runtime graph visualization 很好，但线上还需要 compact diagnostic snapshot。

不要要求玩家上传完整 editor graph。

---

# 56. Graph instance 数量要 profile

UObject graph/node 很适合 sparse authored content。

如果：

```text
100 quests active/player
20 nodes active average
1000 players/server
```

仍需量：

- object count；
- Save bytes；
- transition rate；
- lookup；
- GC；
- event fan-out。

不要因“不 Tick”就默认免费。

---

# 57. Event storm

一个 World Event Notify 10k actors：

```text
server event
 -> 10k FlowComponent dispatch
```

仍可能昂贵。

大规模 fan-out 应走：

- aggregate world state；
- Mass shared data/signal；
- interest/relevance partition。

---

# 58. Quest 与 Mass promotion

NPC promotion：

```text
StableAgentId stays
Narrative stable state stays
Mass runtime changes to Actor runtime
```

Quest/Flow 订阅 stable semantic actor，不应把 current FMassEntityHandle/Pawn pointer 写进永久状态。

---

# 59. 玩家 absorb NPC

玩家变成 NPC：

- 玩家 QuestInstance 不随 shape change；
- NPC 的 narrative state 不因为 mesh 被复制就自动转给玩家；
- 如果设计要求吸收记忆/任务，需要明确 `TransferNarrativeState` domain operation。

这与 Avatar stable owner 原则一致。

---

# 60. 骑乘

“骑某 NPC 到地点”任务观察：

```text
StablePlayerId
Mount StableAgentId
Ride relationship
World trigger
```

不要绑定瞬时 Mount Pawn pointer。

---

# 61. Dialogue

FlowGraph 可以负责 Dialogue routing，但 dialogue availability 应从：

- Quest snapshot；
- World state；
- StableAgent narrative state；

派生。

不要复制另一份隐藏 Quest progress。

---

# 62. World Event phase

推荐：

```text
Prepare
Active
Settlement
Cleanup
```

FlowGraph orchestrates phase。

Contribution/Reward 仍由独立 Authority ledger service。

---

# 63. Boss encounter

FlowGraph 很适合：

- wave flow；
- phase gate；
- cinematic；
- arena lock；
- semantic spawn/despawn request。

Boss GAS owns combat truth。

---

# 64. Save state 不要包含 transient execution handles

禁止持久化：

- TimerHandle；
- DelegateHandle；
- UObject pointer；
- StateTree frame；
- AbilityTask pointer；
- async loader handle。

保存 semantic wait state。

---

# 65. Historical Save fixture

正式 live-service Quest 必须保留：

```text
launch save
N-3
N-2
N-1
current
```

不要只测试“刚保存马上加载”。

---

# 66. Save downgrade

新版本 Save 被旧 client 打开时：

- 明确 reject；或
- 有 backward compatible schema。

不要 silent truncate unknown nodes。

---

# 67. Missing DLC/content

如果 child graph asset 属于未安装 DLC：

Load migration 必须定义：

- block load；
- disable quest；
- tombstone branch；
- fallback reward；
- recover when DLC returns。

不能 nullptr crash。

---

# 68. FlowGraph 2.4 中的 5.9-only 风险

最新 branch 有：

- 2.4 changes；
- packaged SubGraph data pin fix；
- node generated-body change；
- additional Clang fixes。

这些说明 current source 更现代，但不意味着 5.7 tag 同 API。

每个 backport 都要确认：

```text
compile
runtime
asset serialization
editor migration
```

---

# 69. FlowGraph 2.3 中的目标优势

对 LGF 5.7，2.3 已有：

- target release；
- save container integration；
- CanSave；
- preload policy direction；
- soft class settings；
- mature node lifecycle/debugger。

因此如果未来真接入 FlowGraph，从 2.3-5.7 fork/adapter 开始比盲追 5.x 更合理。

---

# 70. 是否真的需要 FlowGraph runtime？

LGF 可选两种路线：

### A. 直接集成 FlowGraph

优点：

- editor成熟；
- runtime debugger；
- node ecosystem；
- SubGraph；
- Save；
- GameplayTag communication。

代价：

- 外部依赖；
- version sync；
- graph save ABI；
- runtime UObject model；
- project-specific Authority wrapper 仍要自己写。

### B. 只吸收机制，自建最小 Quest runtime

优点：

- 与 LGF domain 强集成；
- public ABI 可控。

代价：

- editor/debugger/migration tooling 工作量巨大。

本轮 Skills 不替用户做这个产品决策，只确保两条路都遵守同一 runtime contract。

---

# 71. 不要因为“可以自己写”低估 editor/debugger 成本

Graph runtime 本身可能几千行。

真正昂贵的通常是：

- graph editor；
- schema；
- copy/paste；
- undo；
- node reconstruction；
- validation；
- asset migration；
- runtime debugger；
- source control friendliness；
- packaged/editor parity。

这也是成熟 FlowGraph 项目值得研究的原因。

---

# 72. 不复制第三方代码

本轮只抽取：

- ownership；
- lifecycle；
- save/migration；
- network boundary；
- performance；
- tooling pattern。

正式 Skill 不复制 FlowGraph source implementation。

---

# 73. R13 写回的 UE C++ 合同

新增：

`skills/skillforge-ue-cpp/references/flow-graph-runtime-patterns.md`

覆盖：

1. target-compatible version anchor；
2. template/runtime split；
3. latent node lifecycle；
4. FinishPolicy；
5. deferred transition/reentrancy；
6. SubGraph ownership；
7. soft ref != async；
8. Node Save ABI；
9. cold/in-game load；
10. Authority vs notify projection；
11. tag lookup/hot path；
12. graph debugger/perf。

---

# 74. R13 写回的 LGF 合同

新增：

`skills/skillforge-lgf/references/quest-world-flow-orchestration.md`

覆盖：

- stable Quest owner；
- typed domain command；
- reward idempotency；
- durable snapshot + event delta；
- JIP；
- quest graph save ABI；
- Flow/StateTree/Mass/GAS 分层；
- transform/mount survival；
- world event / boss encounter；
- active-world load；
- historical save fixtures。

---

# 75. R13 新 behavior cases

UE C++：

```text
CPP-76 template vs runtime instance
CPP-77 latent node lifecycle / FinishPolicy
CPP-78 deferred transition / reentrancy
CPP-79 persistent node Save ABI
CPP-80 SubGraph ownership / recursion / loading
CPP-81 active-world save/restore
CPP-82 canonical quest state vs notify
CPP-83 domain fit / debugger / hot path
```

LGF：

```text
LGF-49 stable quest owner vs Avatar
LGF-50 typed domain command Authority
LGF-51 durable quest projection / JIP
LGF-52 shipped graph migration
LGF-53 Flow/StateTree/Mass/Avatar separation
```

---

# 76. 直接接受的设计

### Accepted

- template/runtime instance split；
- stable NodeGuid；
- Active/Recorded node state；
- latent node UObject lifecycle；
- Keep/Abort finish semantic；
- parent-owned SubGraph；
- deferred transition scope；
- execution gate；
- SaveGame integration hooks；
- SignalMode patch compatibility；
- runtime debugger；
- editor validation；
- soft reference/policy-oriented preload direction。

---

# 77. 需要改造后接受

### Adapt

- Flow save records -> add project schema/definition/stable owner IDs；
- notify replication -> pair with durable snapshot；
- IdentityTag registry -> only low-frequency authored discovery；
- SubGraph loading -> preload/async adapter；
- Root owner -> map to stable Quest authority domain；
- Graph nodes -> typed domain commands；
- Save migration -> historical fixture CI。

---

# 78. 明确拒绝

### Reject

- UE5.9 current branch API 直接复制到 UE5.7；
- transient runtime name 作为 Quest ID；
- client flow 直接发 canonical reward；
- notify event 代替 quest truth；
- SoftObjectPtr 等于 async 的错误推理；
- per-Mass-entity Flow brain；
- shipped NodeGuid 删除/复用无 migration；
- active-world load 时叠加两份 graph instance；
- graph node 直接改 Inventory FastArray / ASC raw truth。

---

# 79. 最终 LGF architecture

```text
Stable Player / World / Agent Authority
           |
      Quest Runtime Record
           |
  Quest/World Flow Orchestrator
           |
       typed intent
    /       |       \
Inventory  GAS     World
Authority Authority Authority
           |
      canonical state
           |
   snapshot + events
     /            \
   UI         client cosmetic
```

Agent side：

```text
Flow scripted override
       |
       v
StateTree Decision Owner
       |
GAS / Mover / SmartObject
```

Population side：

```text
World Flow state
 -> aggregate/Mass signal
 -> batch simulation
```

---

# 80. 后续与 SimpleQuest / Dialogue 的关系

这轮只研究 FlowGraph。

下一轮如果继续 `TheGeebus/SimpleQuest` 或 `NotYetGames/DlgSystem`：

- 不重写 R13 graph runtime 基础；
- 专门比较 quest objective model、dialogue graph、conditions/events、localization、authoring UX；
- 只有新增机制才写回 Skills。

这样保持“一次一个项目”，避免多个 Graph 框架的细节混淆。

---

# 81. 本轮没有验证什么

未执行：

- FlowGraph UE5.7 UBT；
- Flow 2.3-5.7 packaged build；
- Flow 2.4 UE5.9 build；
- LGF 实际 FlowGraph dependency integration；
- Dedicated Server；
- JIP；
- packet loss；
- historical Save migration runtime；
- 100/1000 active Quest graph performance；
- World Partition travel；
- AssetManager preload integration。

因此本轮状态是：

```text
fixed-source research
+ Skill architecture contracts
+ textual/eval validation
```

不是 runtime production certification。

---

# 82. 下一步真实接入时的验收建议

如果以后决定把 FlowGraph 接进 LGF UE5.7：

1. 锁 `v2.3-5.7`；
2. 单独 plugin fork/submodule；
3. UBT Editor + Client + Server；
4. 建 `LGFQuestFlowAdapter`；
5. 禁止 Flow node 直写 canonical domains；
6. 加 Stable Quest IDs/version wrapper；
7. 加 historical save fixtures；
8. 加 JIP snapshot；
9. 加 async dependency adapter；
10. PIE Host/Remote；
11. Dedicated；
12. in-game load；
13. transform/mount during active quest；
14. profile active graph/node/event count。

只有这些通过，才能从 `Current source / accepted mechanism` 升级为 `Verified in LGF`。
