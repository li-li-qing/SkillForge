# LGF Graph Authoring Foundation：共享编辑器基础，不共享业务真值

用途：当 LGF 同时出现 Quest、Dialogue、World Flow、Combo/Ability、AI 辅助图等多个图资产需求时，用本页决定 **哪些能力应提炼到共用 Graph Authoring Foundation，哪些必须留在各业务域 runtime**。

本页基于 GenericGraph 的历史架构机制、FlowGraph / SimpleQuest / DlgSystem 已完成蒸馏，以及 LGF 当前的 Authority / Save / Avatar / GAS / Mover 边界。

---

## 1. 总原则

LGF 可以共享：

```text
Graph authoring infrastructure
```

但不要建立：

```text
Universal gameplay graph runtime truth
```

最终结构：

```text
LGF Graph Authoring Foundation
  ├─ Stable IDs
  ├─ Domain Schema interface
  ├─ Compiler pipeline
  ├─ Structured diagnostics
  ├─ Search / diff
  ├─ Migration primitives
  ├─ Editor node registry
  └─ Layout helpers
            ↓
   typed compiled definitions
     ├─ Quest Definition
     ├─ Dialogue Definition
     ├─ World Flow Definition
     ├─ Combo Definition
     └─ other domain definitions
```

而各 domain 继续拥有：

- Authority；
- runtime state；
- Save schema；
- network protocol；
- domain events；
- gameplay side effects。

---

### 1.1 Foundation 统一合同，不强制 two persisted Graph assets

R16 的 authoring → compiler → compiled definition 仍是复杂 Domain 的默认强方案，但 Foundation 不应把“两份持久化 Graph”本身做成 ABI。LGF 允许两种实现：

```text
A. Persisted Authoring Graph -> Compiler -> Persisted/Generated Runtime Definition

B. Canonical Semantic Definition -> transient editor projection -> Runtime Instance
```

B 是 **projection-first**：canonical definition 是 topology / semantic 的 single truth；`UEdGraph`、pins、Slate nodes 只在 Editor 中重建，所有 mutation 通过 Domain service/model 回写并走 transaction/undo。它适合 Dialogue 这类 authoring schema 与 runtime schema 几乎同构、无需复杂 lowering 的域。

两种形态都必须共享 stable ID、DomainSchema validation、content/schema version、migration、deterministic cache、live revision fence。NodePos、breakpoint、协作 soft-lock、selection 等必须进入 `WITH_EDITORONLY_DATA`、Editor sidecar 或 UncookedOnly 数据，并由 cook gate 证明不进入 Shipping/Dedicated runtime。若存在 runtime 压缩、优化、内容裁剪/安全、跨版本二进制 ABI 等需求，则使用独立 compiled artifact。

统一底线只有一条：**Runtime 不直接依赖/遍历 `UEdGraph`**。它可以消费 B 中的 canonical semantic definition，也可以消费 A 的 compiled artifact；Foundation 不把“必须有第二份持久化 compiled graph”写成通用 ABI。

## 2. 为什么不做 UniversalGraphRuntime

看起来很诱人：

```text
UUniversalNode
UUniversalEdge
UUniversalGraphInstance
ExecuteNode()
```

然后 Quest/Dialogue/Ability/AI 都继承。

长期问题：

### Quest

需要：

- Objective state；
- Player/Party/World scope；
- reward ledger；
- advancement hold；
- save migration。

### Dialogue

需要：

- ConversationInstance；
- participant binding；
- Choice revision；
- localization；
- local vs durable dialogue memory。

### Ability / Combo

需要：

- GAS activation；
- PredictionKey；
- montage/movement；
- input windows；
- authoritative damage。

### AI

需要：

- StateTree execution；
- DecisionGeneration；
- Mass/Pawn promotion；
- move/ability interruption。

把它们塞进一个 `Execute()`，最终会让 Common Graph 成为第二个 Gameplay Framework。

---

## 3. Foundation 可以共享的最小 ABI

推荐只共享 domain-neutral 类型，例如：

```text
FGraphDefinitionId
FGraphNodeStableId
FGraphEdgeStableId
FGraphCompiledHeader
FGraphDiagnostic
FGraphContentRedirect
FGraphCompilerContext interface
FGraphDomainPolicy interface
```

其中：

```text
FGraphCompiledHeader
  GraphDefinitionId
  GraphDefinitionVersion
  CompilerVersion
  CompiledRevision
  ContentFingerprint
```

Foundation 不应该暴露：

- `UFlowAsset`；
- `UDlgDialogue`；
- SimpleQuest plugin classes；
- GenericGraph classes；
- 第三方 GraphEditor 类型；
- domain-specific Reward/Ability/Conversation runtime object。

第三方只在 adapter 层存在。

---

## 4. Stable ID 合同

所有 LGF domain graph 必须至少有：

```text
GraphDefinitionId
NodeStableId
EdgeStableId
```

### 4.1 RuntimeIndex 的定位

编译后可以生成：

```text
NodeRuntimeIndex
EdgeRuntimeIndex
```

用于：

- compact arrays；
- hot lookup；
- cache locality。

但它只在当前 compiled revision 内有效。

禁止把 RuntimeIndex 用于：

- Save；
- network request；
- analytics；
- quest reference；
- dialogue choice identity；
- live patch mapping。

### 4.2 Authoring node GUID

UE editor 的 NodeGuid 可以参与生成/追踪 NodeStableId，但 Foundation 显式保存自己的 semantic ID。

原因：

- copy/paste policy；
- graph duplicate policy；
- imported content；
- non-UEdGraph generated nodes；
- migration alias；
- domain split/merge。

---

## 5. Copy / Duplicate / Rename / Split / Merge

固定政策：

```text
rename
→ preserve ID

move visual position
→ preserve ID

copy/paste
→ new ID

normal duplicate graph
→ new GraphDefinitionId + new child IDs

explicit version migration
→ preserve or redirect IDs through migration metadata
```

### 5.1 Remove

已发布 Node/Edge 移除时：

```text
ContentRedirect
Tombstone
CheckpointRestart
AbortReason
```

至少选一种结构化结果。

不能让旧 Save 继续拿 index 碰运气。

### 5.2 Split

```text
Old Node A
→ New A1 + A2
```

migration 说明：

- active A 映射到 A1 还是 A2；
- completed A 如何解释；
- pending transition 如何迁移。

### 5.3 Merge

```text
Old B1 + B2
→ New B
```

要解决重复完成/重复奖励/重复事件。

---

## 6. Common Compiler Pipeline

Foundation 可以提供模板：

```text
Capture authoring snapshot
→ Parse
→ Domain validation
→ Topology validation
→ Stable ID validation
→ Migration planning
→ Normalize
→ Build staging artifact
→ Deterministic order/hash
→ Domain post-compile validation
→ Atomic publish
```

### 6.1 不允许 SaveAsset side effect 成为唯一一致性协议

错误：

```text
设计师点 Save
→ Rebuild runtime graph
→ 游戏假定所有东西同步
```

应有显式：

```text
Compile status
CompiledRevision
Source fingerprint
Artifact fingerprint
```

CI/cook 可验证。

### 6.2 编译失败

开发期允许两种：

```text
Block save/cook
```

或：

```text
Keep last-known-good compiled revision
```

但必须明确当前 authoring revision invalid/stale。

---

## 7. Common Structured Diagnostics

统一结构：

```text
Domain
GraphDefinitionId
DiagnosticCode
Severity
NodeStableId?
EdgeStableId?
Message
FixHint
SourceContext
```

例如：

```text
Domain=Dialogue
Code=GRAPH_DANGLING_EDGE
Node=...
Edge=...
FixHint=Reconnect the choice or remove the transition.
```

这样：

- Editor 可定位；
- CI 可聚合；
- commandlet 可输出；
- Agent 可修复；
- telemetry 可统计。

不要把业务诊断留成散落的 `UE_LOG("bad edge")`。

---

## 8. DomainSchema / DomainPolicy 是 topology 权威

不能让整个 LGF 只有：

```text
bCanBeCyclical
```

每个 domain 定义：

```text
CyclePolicy
SelfLoopPolicy
ParallelEdgePolicy
RootPolicy
ReachabilityPolicy
NodeTypeCompatibility
EdgeTypeCompatibility
Cardinality
TerminalPolicy
```

### Quest

典型：

```text
merge allowed
cycle usually forbidden
explicit terminal/outcome expected
```

### Dialogue

典型：

```text
cycles allowed
parallel choices may be allowed
conversation entries explicit
```

### World Flow

可能：

```text
latency/deferred transitions allowed
subgraph ownership
cycle depends feature
```

### Combo

可能：

```text
bounded loop allowed
zero-cost infinite loop rejected
input edge semantic identity required
```

---

## 9. Editor / Compiler / Cook / Runtime 必须共享同一 policy source

最常见漂移：

```text
Editor CanCreateConnection says A
Compiler says B
Cook不检查
Runtime默默执行 C
```

LGF 要求：

```text
DomainSchema
  ├─ Editor adapter
  ├─ Compiler validator
  ├─ Cook/CI validator
  └─ Runtime defensive check
```

Editor 可以提供更友好的交互提示，但不能自创业务规则。

---

## 10. Cycle 与 general graph

Quest/Dialogue/Ability 的 topology 不同，因此算法也不同。

### DAG-only domain

允许使用：

- topological order；
- level；
- DAG reachability；
- simple dependency evaluation。

遇 cycle 直接编译失败。

### cycle-enabled domain

必须：

- cycle-safe DFS/BFS；
- visited/generation/budget；
- 必要时 SCC；
- runtime transition budget；
- debug traversal budget。

### rootless SCC

不能因为：

```text
RootNodes.Num() == 0
```

就认为 graph empty。

必须从 canonical `AllNodes` / record set 做 component analysis。

---

## 11. Canonical data + derived caches

Foundation 推荐：

```text
Canonical NodeRecords
Canonical EdgeRecords
```

派生：

```text
Incoming adjacency
Outgoing adjacency
Root/leaf
Runtime index maps
SCC index
Topological order
Domain indexes
```

所有 derived cache：

- 不单独作为 Save business truth；
- load/compile 可重建；
- fingerprint 可覆盖；
- drift 能检测。

---

## 12. Parallel Edge

Dialogue/Combo 很容易需要：

```text
A → B via Choice.X
A → B via Choice.Y
```

所以 Foundation 不能设计成：

```text
TMap<EndNode, Edge>
```

应是：

```text
EdgeStableId -> EdgeRecord
OutgoingEdgeIdsByNode -> [EdgeStableId...]
```

是否允许平行边由 DomainPolicy 决定。

---

## 13. Runtime/Editor 模块边界

建议：

```text
LGameplayGraphRuntime / Foundation Runtime
    Core/CoreUObject/Engine + truly required runtime deps

LGameplayGraphEditor or domain Editor modules
    UnrealEd
    GraphEditor
    ToolMenus
    PropertyEditor
    Slate editor widgets
    AssetDefinition
    class picker
    auto-layout
```

### 13.1 Dedicated Server

Dedicated Server 不需要：

- graph widget；
- Slate graph node；
- asset picker；
- auto-layout；
- Editor schema object。

只需要 runtime-consumable semantic definition（canonical definition 或 compiled artifact）+ domain runtime。

### 13.2 Cook

Cook validation 可以在 commandlet/editor context 读 authoring data，但最终 shipping package 不必包含 editor graph。

---

## 14. 目标 UE5.7/5.8 的 Editor API 适配

新代码先评估当前：

- `UAssetDefinition`；
- ToolMenus；
- current UEdGraph/UEdGraphSchema APIs；
- current factory/editor registration；
- Asset Registry metadata。

legacy `FAssetTypeActions_Base`：

```text
Compatibility adapter only unless target-version evidence says otherwise
```

Foundation public API 不暴露这些 editor registration 类型。

这样升级到 5.9/6.x 时只换 adapter。

---

## 15. Node type registry

多个 domain 后，右键菜单不能每次扫描所有 UClass。

Foundation 提供：

```text
GraphNodeTypeRegistry
```

注册：

```text
DomainId
NodeClass / descriptor
Display metadata
Allowed graph type
Category
Capabilities
```

缓存失效：

- Live Coding；
- Blueprint compile；
- module load/unload；
- plugin change；
- registry rebuild command。

---

## 16. Layout 不参与业务真值

共用 layout service 可以有：

- tree layout；
- DAG layout；
- force-directed；
- grid/snap；
- domain presets。

但规则：

```text
Layout failure
!=
Graph compile failure
```

除非 domain 明确把空间位置作为语义，否则 NodePos 是 presentation。

### 16.1 大图预算

- threshold；
- cancel；
- progress；
- max iteration/time；
- O(N²) warning；
- optional background pure math；
- GT apply positions。

### 16.2 Headless

CI semantic validation 不依赖：

- Slate cached geometry；
- editor tab；
- graph panel；
- viewport size。

---

## 17. Live edit / PIE session safety

每个运行实例绑定：

```text
CompiledRevision
ContentFingerprint
RuntimeGeneration
```

保存新 graph 后：

### Policy A: freeze old

```text
old session -> r17
new session -> r18
```

### Policy B: migrate

```text
quiesce
→ stable-id map
→ migrate domain state
→ atomic switch
→ generation bump
→ network resync
```

禁止：

```text
replace definition pointer
→ old active NodeRuntimeIndex 继续解释成新 graph index
```

---

## 18. Network revision fence

若 domain 联网：

客户端请求带：

```text
GraphDefinitionId
InstanceId
ExpectedCompiledRevision
StableNode/Edge/ChoiceId
RequestId
```

Authority：

```text
resolve current instance
→ compare revision
→ resolve stable id
→ domain validation
→ execute
```

旧 revision 请求：

```text
reject
→ snapshot/resync
```

这与 Dialogue R15 的 ChoiceRevision、Quest revision、Inventory generation handle 是同一种 fence。

---

## 19. Save/content migration oracle

共用 migration 层至少识别：

```text
OldGraphVersion
OldNodeId
OldEdgeId
OldDomainState
```

输出：

```text
Mapped
Redirected
RestartAtCheckpoint
CompletedByMigration
AbortedStructured
```

### 19.1 历史 fixture

每次 shipped graph schema/content 变化，保留：

- old compiled artifact fixture；
- old save fixture；
- migration expected result。

CI 跑 migration oracle。

不能只测试“新图能 compile”。

---

## 20. 与现有 LGF 域的映射

### Quest

继续以：

- Quest Manager sole writer；
- Objective state；
- reward ledger；
- scope；
- advancement hold；

为真值。

Graph Foundation 只给 authoring/compile。

### Dialogue

继续以：

- ConversationInstance；
- participant semantic binding；
- Choice/Node stable identity；
- localization；
- revision；

为真值。

Graph Foundation 不直接扣钱/改 Quest。

### AI/StateTree

StateTree 保持 decision owner；不要为“统一 Graph”重写成 UniversalGraph executor。

### GAS / Combo

GAS 保持 ability/effect/cost/cooldown truth。Combo Graph 输出 typed intent/config，不直接成为第二个 AbilitySystem。

### Mass

Mass 仍是大量实体 simulation substrate；Graph authoring foundation 不成为 per-entity UObject runtime。

---

## 21. 适配第三方 Graph 项目

外部项目接入顺序：

```text
External Authoring API
→ Adapter
→ LGF normalized authoring model
→ LGF compiler/policy
→ typed domain definition
```

不要：

```text
LGF Foundation public headers include ThirdPartyGraphNode.h
```

如果某 domain 选择继续用 FlowGraph/DlgSystem 等第三方 authoring，也只在 domain adapter 暴露。

---

## 22. 维护/测试清单

### Content identity

- [ ] GraphDefinitionId stable
- [ ] NodeStableId stable
- [ ] EdgeStableId stable
- [ ] duplicate copy gets new IDs
- [ ] rename/move preserves IDs
- [ ] split/merge migration exists

### Compiler

- [ ] full graph validation
- [ ] deterministic output
- [ ] source fingerprint
- [ ] compiled fingerprint
- [ ] atomic publish
- [ ] last-known-good or save/cook block

### Topology

- [ ] self-loop policy
- [ ] cycle policy
- [ ] parallel edge policy
- [ ] root policy
- [ ] reachability policy
- [ ] rootless SCC case

### Editor

- [ ] current target API audit
- [ ] UAssetDefinition evaluated
- [ ] node registry cached
- [ ] context menu no whole-project scan
- [ ] layout cancellable
- [ ] headless semantic compile

### Runtime

- [ ] no UnrealEd/GraphEditor dependency
- [ ] stable-id lookup
- [ ] runtime index local only
- [ ] revision fence
- [ ] old handles invalid after generation bump

### Migration

- [ ] historical fixtures
- [ ] redirects/tombstones
- [ ] failed mapping policy
- [ ] save/content version separated

---

## 23. 决策规则

遇到“能不能共享”时：

### 可以共享

如果能力是：

```text
无业务副作用
+ authoring/compiler/tooling性质
+ 多domain语义一致
```

例如 stable ID、diagnostic、search/diff、compile header。

### 不应共享

如果能力决定：

- 谁拥有 Authority；
- 如何扣资源；
- 如何完成 Quest；
- 如何激活 Ability；
- 如何推进 Conversation；
- 如何保存 domain progress；

就留在 domain。

---

## 24. R16 结论

`jinyuliao/GenericGraph` 对 LGF 的正确价值不是“复制一个 UE5.1 Graph 插件”，而是让我们把前三轮 Flow/Quest/Dialogue 的共性进一步提炼成：

```text
Shared Graph Authoring Foundation
        +
Domain-owned Runtime Truth
```

吸收：

- Graph/Node/Edge 分层；
- Runtime/Editor 模块意识；
- Schema connection validation；
- explicit edge concept；
- authoring → runtime rebuild；
- layout service separation。

强化：

- stable Node/Edge identity；
- canonical topology；
- parallel edges；
- cycle/general graph correctness；
- staged compiler；
- last-known-good；
- modern UE asset API；
- module boundary；
- large graph scalability；
- revision/session fence；
- content migration oracle。

拒绝：

- 以 stars 代替时效性；
- 以 UE5.1 compatibility 代替 UE5.7/5.8 evidence；
- 一个 UniversalGraphRuntime 接管所有玩法；
- Editor SaveAsset 副作用充当 runtime consistency protocol。

