# Flow Graph / Quest / World Event 运行时合同

> 用于 UE5.7/5.8 的任务、剧情、世界事件、关卡事件图、异步节点、子图、SaveGame、多人事件投影和编辑器图工具设计。本参考从 `MothCocoon/FlowGraph` 的 UE5.7-compatible 2.3 与 2026-08 当前 2.4/UE5.9 分支抽取长期机制；目标不是要求项目依赖 FlowGraph，而是建立可移植的 Graph Runtime 合同。

## 1. 先固定目标版本，不把 `5.x` 当成单一 API

FlowGraph 是维护活跃的项目，但当前默认 `5.x` 分支不是用户 UE5.7 的直接 API 基线。

研究锚点：

- 最新架构方向：`MothCocoon/FlowGraph@c616a5d2afa8124cb7c1d66b1071fd499f2be7db`；
- 该提交位于 Flow 2.4 in works，release note 标明是首个 UE5.9 版本；
- UE5.7 对应发布：`v2.3-5.7@8211b25999068407cb7b40b8c97e18b52d4832ca`；
- 2.3 同时提供 UE5.6 / 5.7 / 5.8 专门 release；
- 2.3 的 Data Pin 升级有明确 staged migration / resave 要求。

因此必须使用双锚点：

```text
latest branch
    -> 学最新设计方向、bug fix、演进意图

target-compatible tag
    -> 学当前消费工程可以直接验证的 API / serialization / editor behavior
```

禁止：

```text
仓库叫 5.x
-> 默认所有 5.x 引擎共享同一 API
```

### 1.1 外部 Graph 项目的证据等级

继续使用统一外部项目门：

1. `Declared`：README、release note、header 有描述；
2. `Compiled`：目标版本可编译；
3. `Runtime-active`：固定源码存在真实调用链；
4. `Verified`：目标工程 UBT/PIE/DS/JIP/Save migration 已验证。

Graph 系统尤其容易出现：

- 新 editor API 存在但 packaged runtime path 仍旧；
- soft pointer 存在但 active runtime 仍 `LoadSynchronous()`；
- SaveGame 字段存在但没有完整 migration；
- client notify 存在但没有 durable JIP snapshot；
- “async preload”框架存在，但某个 SubGraph active create path 仍同步。

所以不能以 class/header 存在替代 active-code evidence。

---

## 2. 第一原则：template asset != runtime instance

Graph asset 是**定义模板**，运行中的 Quest / World Event 是**实例**。

FlowGraph 的 `UFlowSubsystem::CreateFlowInstance()` 会从 template 创建 transient `UFlowAsset` runtime instance，并调用 `InitializeInstance(Owner, TemplateAsset)`。这个分离是值得保留的核心设计。

### 2.1 Template 应拥有

```text
GraphDefinitionId / AssetGuid
Node definitions
NodeStableId / NodeGuid
pin definitions
connections
static parameters
editor metadata
asset dependencies
GraphDefinitionVersion
migration metadata
```

### 2.2 runtime instance 应拥有

```text
QuestInstanceId / WorldEventInstanceId
StableOwnerId
RuntimeGeneration
active node states
recorded/completed node states
subgraph instances
runtime parameter snapshot
pending domain requests
latent subscriptions/timers
revision / sequence
finish reason
```

模板不能承载玩家进度。

错误：

```text
DA_MainQuest / FlowAsset
  CurrentNode = KillBoss
  Count = 2/5
```

如果两个玩家共享这个 asset，他们会互相覆盖。

正确：

```text
Quest Definition Asset
  GraphDefinitionVersion = 12
  NodeStableIds = ...

Player A Runtime Quest Instance
  QuestInstanceId = QA
  ActiveNode = N17
  Count = 2

Player B Runtime Quest Instance
  QuestInstanceId = QB
  ActiveNode = N05
  Count = 0
```

### 2.3 不把 UObject identity 当 business identity

禁止长期依赖：

- pointer；
- UObject name；
- transient instance name；
- PIE package name；
- array index；
- editor graph pointer。

持久化/网络/调试使用：

```text
GraphDefinitionId
GraphDefinitionVersion
QuestInstanceId
StableOwnerId
NodeStableId
RuntimeGeneration
```

`NodeGuid` 可以作为 authored stable node identity，但一旦进入 shipped SaveGame，它就变成 save ABI，后文详述。

---

## 3. Flow Node 是 latent runtime object，不是“蓝图函数节点”

FlowGraph 的核心价值不是画线，而是让一个 Flow Node 表示一个完整、可长期激活的 gameplay feature。

Node 可以：

- 订阅 delegate；
- 启动 Timer；
- 等待 world event；
- 等待 LevelSequence；
- 等待 Domain Command；
- 创建 SubGraph；
- 持有 SaveGame 字段；
- 触发多个 outputs；
- 被 Complete 或 Abort。

因此节点必须使用真正的生命周期合同，而不是把它当一次函数调用。

## 4. Flow Node lifecycle：Complete vs Abort 必须显式

推荐统一状态：

```text
NeverActivated
   -> Active
      -> Completed
      -> Aborted
```

这和 FlowGraph 的 `EFlowNodeState` 方向一致。

### 4.1 标准节点拥有关系

节点自己创建/注册的东西，节点自己负责结束：

```text
Activate / Execute
  Register delegate H1
  Start timer T1
  Request async A1
  Spawn presentation P1
  Start domain request R1

Complete
  unregister H1
  clear T1
  cancel/ignore A1 if still pending
  keep/commit P1 according to policy
  detach R1 callback

Abort
  unregister H1
  clear T1
  cancel/ignore A1
  rollback/remove transient P1 where appropriate
  cancel R1 if source-owned
```

### 4.2 Finish Policy

Graph/Node 结束至少区分：

```text
Complete / Keep
Abort / Cancel
```

不要只用：

```text
DestroyGraph()
```

例如 Spawn NPC 节点：

- Quest 正常完成：NPC 可能应保留；
- Quest Abort / world teardown：临时 NPC 可能必须移除。

“对象消失”不是业务语义。

### 4.3 teardown 要幂等

```text
Cleanup()
Cleanup()
Abort after Finish
world teardown after Abort
```

都不能 double-remove delegate、double-return pool、double-grant/refund。

### 4.4 stale async callback fence

任何 latent callback 至少验证：

```text
Weak GraphInstance
QuestInstanceId
RuntimeGeneration
NodeStableId
NodeActivationGeneration
OwnerStableId / AvatarGeneration where relevant
```

回调时：

```text
if graph gone -> ignore
if runtime generation changed -> ignore
if node no longer Active -> ignore
if owner changed -> re-resolve or reject
```

不要让旧任务的 HTTP/async asset/ability/move callback 在新任务实例上继续跑。

---

## 5. Graph transition 要有 reentrancy boundary

Graph 输出通常会立即触发下游输入。如果下游：

- 完成当前节点；
- 结束父图；
- 删除子图；
- 再触发当前节点；
- 修改 active node container；

就很容易发生递归重入和 iterator invalidation。

FlowGraph 当前使用 deferred transition scope + execution gate，这是一个值得抽象的机制。

### 5.1 Deferred Transition contract

```text
Node A output
   -> enqueue {GraphInstanceId, NodeId, PinId, FromPin, Sequence}
   -> close current mutation scope
   -> flush queue
   -> revalidate destination
   -> execute destination
```

结构/生命周期敏感的跳转不要任意递归直接进入。

### 5.2 scope 内顺序和跨图顺序要分开

一个 scope 可以定义：

```text
FIFO within one graph instance / one transition scope
```

但不要默认：

```text
Graph A event #10
一定早于
Graph B event #9
```

FlowGraph 当前 subsystem 自己也明确说明跨 template/instance flush 不是 strict global FIFO。

如果业务真的需要跨图全局顺序，建立显式：

```text
WorldEventSequence
QuestLedgerSequence
ServerCommandSequence
```

而不是借用容器遍历顺序。

### 5.3 Execution Gate

调试暂停、异常 shutdown 或 domain transaction barrier 可以阻止 queue flush。

要求：

- halt 优先于继续递归；
- 未 flush 队列可在 safe point 恢复；
- shutdown 可以 clear，不执行残留 side effect；
- clear/flush 结果有诊断。

### 5.4 transition budget

对用户可编辑图必须防：

```text
A -> B -> A
```

和：

```text
10000 immediate transitions in one frame
```

至少限制：

- 单 scope transition count；
- single-frame graph transition budget；
- recursion depth；
- repeated edge / cycle diagnostic。

Graph 是 authoring tool，不能假设内容永远正确。

---

## 6. SubGraph：父节点是 child graph 的 lifecycle owner

SubGraph 不只是“调用另一个 asset”。

推荐 ownership：

```text
Parent Runtime Graph
  -> SubGraph Node N17
       -> Child Runtime Graph C52
```

父 SubGraph node 拥有：

- child create；
- start；
- saved child instance identity；
- custom input/output routing；
- finish result；
- cleanup；
- abort；
- preload/flush。

### 6.1 parent-child registry 必须成对

```text
CreateSubFlow
  add subsystem child map
  add parent active-subgraph map
  set child NodeOwningThisAssetInstance

RemoveSubFlow
  remove parent map
  remove subsystem map
  child FinishFlow(policy)
  clear child owner-node pointer
```

只做 Spawn 不做 remove 会把 graph runtime 变成 hidden leak。

### 6.2 recursion

默认拒绝：

```text
QuestA -> QuestA -> QuestA ...
```

如果确实需要递归 graph：

```text
explicit allow
+ recursion depth
+ per-instance budget
+ cycle key
+ restore validation
```

不要用“designer 应该不会连错”作为 safety mechanism。

### 6.3 SubGraph parameter contract

父图传给子图的是参数/input context，不是共享 mutable graph state。

推荐：

```text
Parent immutable/owned data
 -> child params snapshot / typed provider
 -> child runtime
 -> typed custom output result
```

避免 child 任意持有 parent UObject 内部字段并跨 SaveGame 恢复。

---

## 7. Soft reference != async runtime

这是这轮最容易被误判的地方。

FlowGraph 的 SubGraph `Asset` 是 `TSoftObjectPtr<UFlowAsset>`，但当前 active `CreateSubFlow()` 仍能走：

```text
Asset.LoadSynchronous()
```

而当前 SubGraph `PreloadContent()` 注释也明确写着 CreateSubFlow 仍是 synchronous-only，async asset load 是 TODO 方向。

所以：

```text
TSoftObjectPtr
!=
async safe
```

### 7.1 Production 推荐

长剧情/任务依赖：

```text
Quest activation request
 -> dependency manifest
 -> AssetManager async preload
 -> PendingActivation
 -> callback generation revalidation
 -> create graph instance
 -> Start
```

或者在区域/章节加载时预驻留。

### 7.2 禁止热路径 sync load

禁止：

```text
combat hit
AI decision
per-frame graph tick
UI hover
network RPC handler
 -> LoadSynchronous quest/subgraph asset
```

### 7.3 Editor sync load 与 runtime sync load 分开评价

Editor palette/context pin 重建中同步加载资产可能是可接受的 editor tradeoff。

不能因为 editor 里有 `LoadSynchronous()` 就直接判 runtime 性能问题；也不能因为 sync load 位于 SoftObjectPtr 后面就当作 async。

必须确认 active path。

---

## 8. SaveGame：NodeStableId 是持久化 ABI

FlowGraph 的 save record 直接包含 NodeGuid + serialized NodeData，这是非常重要的设计信号。

一旦玩家存档里出现：

```text
GraphDefinition X
NodeGuid N17 = Active
```

`N17` 就不再只是 editor implementation detail。

## 9. Shipped graph 的 Save ABI 规则

发布后默认禁止：

- 删除 active/persisted node 而无 migration；
- 将旧 NodeGuid 重新给不同语义节点；
- 让旧 output pin 名映射到完全不同 irreversible side effect；
- 修改 child graph identity 却不迁移 parent saved relation。

推荐：

```text
old N17
 -> tombstone/deprecated node
 -> pass-through
 -> redirect to N42
 -> migration maps state
```

FlowGraph 的 `SignalMode::PassThrough` 正是一个很好的 shipped-save compatibility 模式：保留 node identity，但不再运行内部旧逻辑，只安全把执行流转发下去。

### 9.1 Connections 与 node identity 分开

如果连接没有进入 SaveGame，而 node identity/state 进入了 SaveGame：

- node ID 是 ABI；
- connection 可以更灵活地 patch；
- 但新的连接必须避免重复 irreversible effect。

### 9.2 staged asset migrations

FlowGraph 2.3 的 Data Pin upgrade 明确要求旧版本先升级到 2.2/2.3、resave，再继续升级。

长期原则：

```text
asset migration can require stepping-stone version
```

不要假设：

```text
v1 asset
 -> directly open in v15
 -> automatic safe
```

CI/升级工具必须知道允许的 migration path。

---

## 10. Production Save wrapper 不应只保存 Flow 内部字节

一个通用 Flow/Quest save 至少应有：

```text
SaveSchemaVersion
GraphDefinitionId
GraphDefinitionVersion
QuestInstanceId / WorldEventInstanceId
StableOwnerId
RuntimeGeneration
ActiveNodeStableIds
NodeState records
SubGraph relation records
Domain checkpoint / reward ledger revision
Save timestamp / world partition context if needed
```

内部 node bytes 可以作为 implementation payload，但不能成为唯一身份层。

### 10.1 WorldName / ActorName 不是长期业务 identity

名字会因为：

- 重命名；
- PIE prefix；
- world partition；
- runtime respawn；
- streaming level；
- transform/shape actor replacement；

发生变化。

所以：

```text
ActorInstanceName
WorldName
Runtime UObject Name
```

最多辅助定位，不作为唯一 Save key。

---

## 11. Cold Load 与 Active-World Load 是两条流程

FlowGraph 文档明确提醒：FlowComponent 自动恢复 root flow 主要绑定 BeginPlay；如果 world 已经 active 后做 in-game load，项目要自己处理 LoadRootFlow。

这说明 Production Save 必须显式设计两条路径。

### 11.1 Cold load

```text
Load save bytes
 -> migrate/validate
 -> create world/player stable owners
 -> create quest runtime instances
 -> restore node/subgraph state
 -> bind events
 -> publish snapshot
 -> start gameplay
```

### 11.2 Active-world load

```text
request load
 -> freeze new quest/world commands
 -> capture current live state / recovery point
 -> quiesce or Abort old graph instances
 -> parse + migrate into staging records
 -> validate owners/assets/node IDs/rewards
 -> create staging/new instances
 -> restore latent semantic state
 -> atomically switch live quest projection
 -> resync clients/UI
 -> release old instances
```

禁止：

```text
live Quest A still active
+ directly Create Quest A from save
= two runtimes both listening to same event
```

### 11.3 恢复的是语义，不是 OS/engine async handle

不要持久化：

- delegate handle；
- TimerHandle；
- raw UObject pointer；
- async request pointer；
- AbilityTask pointer；
- StateTree execution frame。

保存：

```text
WaitingForBossDeath
TargetStableId = Boss42
RemainingTimeout = 8.2
ExpectedDomainRevision = 17
```

加载后重新订阅。

---

## 12. Graph networking：event delivery != canonical state

FlowComponent 展示了一个有价值的模式：

- Authority/ClientOnly/ServerOnly 等 execution mode；
- GameplayTag identity；
- Push Model replicated tag containers；
- OnRep 把服务器通知投影到客户端。

但必须正确解释。

### 12.1 replicated notify 是 transient event channel

它适合：

```text
Play VO
Show toast
Open cinematic overlay
Refresh quest marker
Trigger cosmetic local flow
```

不适合成为唯一：

```text
Quest completed truth
reward claimed ledger
branch chosen truth
boss defeated durable state
party quest progress
```

### 12.2 durable state + event projection

正确：

```text
Authority Quest State revision=42
        |
        +-- Save / replicate snapshot
        |
        +-- emit Quest.StepCompleted event #991
                    |
                 UI/cosmetic
```

JIP：

```text
join
 -> snapshot revision 42
 -> subscribe events after 42
```

而不是要求平台重放所有旧 notify。

### 12.3 事件最少身份

对重要事件：

```text
QuestInstanceId
EventId / RequestId
Revision / Sequence
Source NodeStableId
CorrelationId
Payload version
```

消费者可以：

- 去重；
- 识别 gap；
- 拒绝 stale；
- 请求 resync。

---

## 13. Authority：FlowGraph 是 orchestration，不是权限系统

一个 Quest node 说：

```text
Give Reward
Kill Boss
Unlock Door
Add Item
Activate Ability
```

不意味着 node 可以绕过对应 domain authority。

### 13.1 推荐 typed command

```text
Graph Node
 -> FQuestDomainCommand
      QuestInstanceId
      NodeStableId
      ActivationGeneration
      RequestId
      OperationId
      TargetStableId
      payload
 -> Authority domain service
 -> revalidate
 -> idempotent execute
 -> Result{Success, Reject, Cancel}
 -> graph output
```

现有 Inventory/GAS/Combat/World transaction 仍是 canonical owner。

### 13.2 ClientOnly graph

ClientOnly graph 可以控制：

- dialogue presentation；
- camera cut；
- subtitle；
- local marker；
- screen effect。

客户端节点不能凭自己激活：

- 发物品；
- 扣血；
- 完成服务器任务；
- 解锁永久成就；
- 删除 canonical world actor。

这些必须请求 Authority。

### 13.3 irreversible side effect 必须 idempotent

剧情系统最危险的问题是 Save/Load 和重复 signal 导致：

```text
GiveSword node executed twice
```

因此：

```text
RewardLedgerKey = QuestInstanceId + NodeStableId + SemanticRewardId
```

Authority 检查 ledger 后再 grant。

同理 Spawn unique NPC / Unlock feature / Achievement。

---

## 14. Identity Tag registry 只做语义发现，不做热路径数据库

FlowGraph 使用 GameplayTag registry 找 FlowComponent 是一个方便的 authored-world模式。

但源码注释自己也提醒：非 exact hierarchical tag search 成本可和 registered tags 数量相关。

所以：

### 14.1 低频 narrative query

可以：

```text
Quest.Target.Shopkeeper
Quest.Trigger.CastleGate
Narrative.Role.Prisoner
```

### 14.2 高频系统

不要：

```text
每帧 20000 NPC
 -> hierarchical gameplay tag global registry scan
```

高频查找用：

- StableAgentId map；
- exact tag index；
- spatial query；
- Mass fragment query；
- cached handle/generation。

---

## 15. FlowGraph 的适用域：author-driven sparse orchestration

最适合：

> Domain fit：FlowGraph 的主场是 **narrative orchestration**、Quest/World Event 编排，而不是海量实体热路径决策。

- main/side quest；
- world event；
- chapter flow；
- encounter orchestration；
- cinematic sequence；
- dialogue entry routing；
- tutorial；
- one-off scripted boss phase orchestration；
- cross-system authored event chain。

不适合默认用作：

- 20000 Mass NPC per-frame brain；
- projectile simulation；
- raw movement integration；
- hot combat damage loop；
- per-item inventory mutation core；
- animation pose computation。

原因不是 UObject “一定慢”，而是 authoring/lifecycle/graph-instance 成本和问题域不匹配。

---

## 16. 与 StateTree / Mass / GAS 的边界

```text
FlowGraph
 = Quest / World / Narrative orchestration

StateTree / Utility
 = single Agent high-level decision

Mass
 = large population low-cost simulation

GAS
 = gameplay ability execution / cost / effects / prediction

Mover/Nav
 = movement truth

Inventory
 = item truth
```

### 16.1 FlowGraph -> StateTree

FlowGraph 可以发：

```text
ScriptedOverrideIntent
QuestCombatPhase
EscortDestination
CinematicLock
```

但不直接改 StateTree internal active-node pointer。

### 16.2 FlowGraph -> Mass

世界事件可以：

```text
OpenFestival
 -> update shared world event state
 -> Mass processor/signal sees state
 -> group behavior changes
```

不要为每个 Mass entity 创建独立 Flow graph 来接收同一事件。

### 16.3 FlowGraph -> GAS

Graph 请求 semantic Ability/Domain action；GAS 做：

- CanActivate；
- cost；
- target；
- prediction；
- result。

Graph 等结果，不重做 GAS。

---

## 17. Preload policy：把资源加载视为节点生命周期的一部分

好的 graph node 不能在任意执行时突然 load 大资源。

推荐节点声明：

```text
Asset dependencies
Preload timing
Flush timing
Can run without dependency?
Failure policy
```

项目层 policy 决定：

- chapter preload；
- node-near activation preload；
- manual preload；
- memory pressure flush。

### 17.1 async completion fence

```text
RequestGeneration G17
 -> async load
 -> callback
 -> if node generation != G17 : discard
```

不能因为 preload 成功就假设 graph/node 仍 active。

---

## 18. Debugger 不是装饰，而是 graph runtime 的 Production 能力

Graph 问题通常不是 crash，而是：

> 为什么任务卡住？

最低诊断字段：

```text
GraphDefinitionId / path
GraphDefinitionVersion
QuestInstanceId
StableOwnerId
RuntimeGeneration
Active NodeStableIds
Node ActivationGeneration
Last input pin
Last output pin
Activation Sequence
External EventId / CorrelationId
Pending domain request
SubGraph tree
Save restore version
FinishPolicy
Abort reason
```

### 18.1 可视化

Editor/PIE 最好显示：

- active node；
- completed/aborted node；
- active wire；
- node message；
- pending async；
- child subgraph；
- server/client context。

### 18.2 Shipping diagnostics

Shipping 不需要完整 editor graph，但需要：

```text
QuestDebugSnapshot
ActiveNodeIds
LastTransition
LastDomainReject
RestoreMigrationLog
```

以便玩家存档问题可诊断。

---

## 19. Performance：Graph 系统主要防事件风暴，不只看 Tick

很多 FlowGraph node 不 Tick，仍可能因为事件 storm 变重。

需要测：

- active graph instance count；
- active node count；
- transition count/frame / transition rate；
- deferred queue depth；
- external notify rate；
- non-exact tag lookup rate；
- sync load count/time；
- subgraph create/destroy rate；
- SaveGame bytes；
- save/restore time；
- editor validation time。

### 19.1 常见错误

```text
no Tick
=> free
```

错误。

一个 0 Tick 系统仍可以被每秒数万个 notify 打爆。

### 19.2 budget

给：

```text
max transitions/frame
max graph starts/frame
max immediate subgraph creates/frame
max domain command submissions/frame
```

必要时分帧处理世界事件 fan-out。

---

## 20. Editor validation 与 packaged runtime 必须共同设计

Graph 工具的价值很大部分来自“在作者提交内容前发现错误”。

建议验证：

- duplicate/missing pin；
- invalid child asset；
- illegal recursion；
- missing stable ID；
- deprecated node not pass-through；
- irreversible node without idempotency key；
- client-only graph containing authority-only domain mutation node；
- SaveGame node removed without migration；
- required soft dependency absent；
- SubGraph API mismatch；
- unreachable essential finish path。

Package build 仍必须运行 runtime contract tests，不能只信 editor validation。

---

## 21. Patch compatibility：Tombstone / PassThrough 是一等设计

长期运营 ARPG 的 Quest Graph 一定会变。

所以 node 从创建第一天就应有：

```text
StableNodeId
introduced_version
deprecated_version
replacement_id
migration policy
signal/execute policy
```

推荐生命周期：

```text
Active
 -> Deprecated but loadable
 -> PassThrough/Tombstone
 -> no new authoring
 -> remove only after supported save horizon expires
```

而不是：

```text
Designer delete node
 -> git commit
 -> old saves broken
```

---

## 22. Graph Definition Version 与 Save Schema Version 分开

这两个不是同一个版本。

```text
SaveSchemaVersion
 = serialized record shape changed

GraphDefinitionVersion
 = authored quest graph semantics changed
```

例如：

- Save record 从 `int Count` 改到 struct -> Schema migration；
- Kill 3 Wolf 改成 Kill 5 Wolf -> Graph Definition migration/business policy。

同时记录才能正确决定：

- deserialize；
- migrate；
- compensation；
- restart quest；
- grandfather old objective。

---

## 23. Active latent node 的迁移比 Completed node 更危险

迁移时分类：

```text
NeverActivated
Active
Completed
Aborted
```

Active node 可能持有：

- waiting target；
- remaining timer；
- external subscription；
- domain request；
- spawned temporary actor。

迁移工具必须为 active node 定义：

```text
resume as new node
complete old node
abort old node
restart objective
manual compensation
```

不能默认 memcpy node bytes 后继续。

---

## 24. Quest/World Graph 的测试矩阵

### 24.1 基础

- Start -> Complete；
- Start -> Abort；
- repeated signal；
- invalid input；
- multiple outputs；
- cycle budget。

### 24.2 latent

- callback before cancel；
- cancel before callback；
- callback after graph destroyed；
- callback after load restore；
- timeout；
- map transition。

### 24.3 subgraph

- child complete；
- child abort；
- parent abort while child active；
- nested child；
- recursion rejected；
- missing child asset；
- preload then execute；
- restore active child。

### 24.4 save migration

- N-1 -> current；
- N-2 -> current；
- skipped required stepping stone -> explicit reject/tooling；
- deleted node tombstone；
- changed connection；
- renamed graph；
- split graph；
- merged graph；
- missing DLC/content；
- corrupted node payload。

### 24.5 network

- Listen Host；
- Remote Client；
- Dedicated；
- JIP；
- reconnect；
- packet loss/duplication of projection event；
- client tries canonical mutation；
- server save/load while clients connected。

---

## 25. 代码审查 checklist

### Definition / Instance
- [ ] template asset 与 runtime instance 分开；
- [ ] runtime 有 stable business instance ID；
- [ ] NodeStableId 不使用数组索引；
- [ ] shipped NodeId 不被复用。

### Lifecycle
- [ ] latent node Complete vs Abort 明确；
- [ ] cleanup 幂等；
- [ ] delegate/timer/async handle source-owned；
- [ ] stale callback generation fence。

### Transition
- [ ] reentrancy boundary；
- [ ] deferred queue ordering 已定义；
- [ ] no fake global FIFO assumption；
- [ ] cycle/event-storm budget。

### SubGraph
- [ ] parent owns child；
- [ ] create/remove registry symmetric；
- [ ] recursion bounded；
- [ ] child dependency preload；
- [ ] restore relationship validated。

### Save
- [ ] SchemaVersion；
- [ ] GraphDefinitionVersion；
- [ ] StableOwnerId；
- [ ] QuestInstanceId；
- [ ] NodeStableId；
- [ ] historical fixtures；
- [ ] active-world load path；
- [ ] atomic staging/switch。

### Network
- [ ] Authority canonical quest state；
- [ ] notify != truth；
- [ ] JIP snapshot；
- [ ] event sequence/idempotency；
- [ ] ClientOnly graph only presentation。

### Performance
- [ ] no unexpected runtime LoadSynchronous；
- [ ] no hot hierarchical tag scan；
- [ ] transition/event budget；
- [ ] graph instance counts profiled。

---

## 26. FlowGraph 2.3/2.4 的具体迁移结论

### 可吸收

- UObject node 作为 latent feature owner；
- template/runtime instance split；
- NodeGuid Save identity；
- Active/Recorded nodes；
- parent-owned SubGraph；
- FinishPolicy Keep/Abort；
- deferred transition + execution gate；
- SaveGame hooks at subsystem/asset/node/component；
- SignalMode for shipped-save compatibility；
- soft references + preload policy direction；
- runtime graph debugger / validation；
- tag-based world component discovery for authored low-frequency use。

### 需要包装/强化

- 加 project-owned SchemaVersion / GraphDefinitionVersion；
- 加 StableOwnerId / QuestInstanceId；
- 加 idempotent domain command/ledger；
- 加 active-world atomic restore；
- 加 JIP durable snapshot；
- 加 transition/event budget；
- 加 async dependency policy；
- 加 historical save migration CI。

### 不作为 LGF Production 默认模板

- 用 WorldName / ActorInstanceName 作为唯一长期业务 ID；
- 把 replicated notify tag 当 durable quest state；
- 任意 client graph 输出直接修改 Authority domain；
- 在运行触发点 `LoadSynchronous()` 大型子图；
- 给海量 Mass entity 每个创建 UObject quest graph 作为 AI brain；
- 直接复制 UE5.9-only Flow 2.4 API 到 UE5.7；
- 删除 shipped saved NodeGuid 而无 migration。

---

## 27. 最终原则

长期 Quest / World Event Graph 不是“蓝图更好看的替代品”。

它应该满足：

```text
Authored Graph Definition
        !=
Runtime Quest Instance
        !=
Canonical Domain State
        !=
Client Projection
```

并建立：

```text
Stable identity
+ explicit lifecycle
+ deferred/reentrant-safe transitions
+ versioned Save ABI
+ Authority domain boundary
+ async asset boundary
+ JIP snapshot
+ debugger/observability
```

满足这些条件，Graph 才适合成为一个长期运营 ARPG 的任务/剧情编排层。
