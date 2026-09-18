# UE 自定义 Graph：Authoring、Compiler、Stable ID 与 Runtime Artifact 合同

用途：当项目需要 Quest、Dialogue、Ability、Combo、Narrative、World Event、AI 辅助图等自定义 Graph 资产时，用这份参考审查 **编辑器图、编译产物、运行时拓扑、稳定身份、版本迁移与工具性能**。

这不是 `jinyuliao/GenericGraph` 的 API 教程。该项目固定源码只明确迁移到 UE5.1，本页吸收其仍成立的结构思想，并按 UE5.7/5.8 重新收敛生产合同。

---

## 1. 先判技术时效性：热门旧项目只能当机制样本

固定研究样本：

```text
jinyuliao/GenericGraph
commit f9b8fe3de6bc2ef39ee771658ac4a8bf48c2e078
commit date 2023-07-15
last explicit engine migration: UE5.1
license: MIT
```

分类：`Historical architecture sample`。

原因：

- README 仍写 UE4；
- 默认分支最后实质提交在 2023；
- 明确的 UE5 升级提交只到 5.1；
- 插件 descriptor 没有 5.7/5.8 engine evidence；
- Editor 资产入口仍以 legacy `FAssetTypeActions_Base` 体系为中心；
- 当前 UE5.8 官方已经提供 `UAssetDefinition` 作为 Asset Actions 的替代系统之一。

因此研究输出必须拆成两栏：

```text
Architecture mechanism
    可以吸收

Concrete Editor API / module / callback signature
    target-engine recheck required
```

不要因为：

- stars 很多；
- 仓库未 archive；
- 旧代码还能被某个版本编译；
- 某 API 在 5.8 仍存在；

就把它称为 UE5.7/5.8-current template。

### 1.1 API 仍存在，不等于新项目还应优先使用

一个典型例子：

```text
legacy AssetTypeActions
    5.8 仍可能存在

UAssetDefinition
    当前官方 replacement direction
```

新项目的默认动作应是：

1. 查目标 UE 版本官方 API；
2. 看新系统是否已替代旧入口；
3. 旧 API 若保留，只作为 compatibility adapter；
4. Foundation public ABI 不绑死 legacy editor 类型。

同样适用于：

- AssetTools；
- ClassViewer；
- ToolMenus；
- GraphEditor；
- editor style API；
- package save delegate；
- asset editor toolkit；
- factory / asset definition 注册。

---

## 2. 总体结构：Authoring 与 Runtime 是两个职责产品，不等于必须持久化两份 Graph

首先分离的是 **职责、依赖和 ABI**，不是强制的资产数量。大型/复杂 Graph 仍优先采用显式编译链：

```text
Authoring UEdGraph
    ↓
Domain Schema + Compiler
    ↓
Compiled Graph Definition
    ↓
Runtime Instance / Domain Runtime
```

但当 authoring schema 与 runtime semantic definition 高度一致、没有昂贵 lowering/压缩/安全裁剪时，也允许 **projection-first**：

```text
Canonical Semantic Definition   ← single persisted semantic truth
    ↑                ↓
mutation/service      transient editor projection (UEdGraph)
    ↓
Runtime Instance + rebuildable lookup/cache
```

这时 `UEdGraph` 只是可丢弃、可重建的 transient editor projection；所有增删改通过 authoritative semantic model/service 回写，并参与 `Modify()` / transaction / undo。不能因为 Editor 有 node/pin 对象，就形成第二份 topology truth。

无论选择哪种形态，都必须保留：

- stable Graph/Node/Edge/Choice identity（只要该实体需要 Save/Network/Analytics/迁移引用）；
- whole-definition validation，而不是只信 Editor 拖线检查；
- schema/content version、migration/redirect 和 historical fixtures；
- deterministic derived caches；
- live revision/session fence；
- Runtime/Editor module boundary。

`NodePos`、breakpoint、soft lock、selection、layout hint 等纯 authoring metadata 应使用 `WITH_EDITORONLY_DATA`、Editor sidecar 或 UncookedOnly 数据，并通过 cook/package gate 证明 Shipping/Dedicated 不依赖它们。需要 runtime 优化、内容裁剪/加密、跨版本稳定二进制 ABI 或明显不同的 runtime schema 时，再选择独立 compiled artifact，而不是为了形式统一机械复制两份数据。

### 2.1 Authoring UEdGraph 负责什么

允许包含：

- `UEdGraph`；
- `UEdGraphNode`；
- pins；
- NodePos；
- comments；
- selection；
- Slate cached geometry；
- editor graph decoration；
- auto-layout state；
- context menu metadata；
- details-panel-only options。

这些是 authoring truth，不是业务 runtime truth。

### 2.2 Compiled Runtime Definition 负责什么

应该只包含运行所需的稳定数据，例如：

```text
GraphDefinitionId
GraphDefinitionVersion
CompilerVersion
ContentFingerprint
Nodes[]
Edges[]
EntryPoints[]
DerivedLookupTables
DomainPayload
```

运行时不要依赖：

- `UEdGraphPin*`；
- `SGraphNode*`；
- NodePos；
- editor selection；
- editor object path 偶然顺序；
- Slate geometry；
- right-click menu registry。

### 2.3 Runtime Instance 再与 Definition 分开

定义：

```text
CompiledDefinition
= authored immutable content
```

实例：

```text
RuntimeInstance
= current progress / active node / variables / generation / owner / network revision
```

Quest、Dialogue、AI、Combo 的实例状态不能写回 Definition。

---

## 3. Stable Identity：Node、Edge、Graph 都必须有自己的长期 ID

最低要求：

```text
GraphDefinitionId
NodeStableId
EdgeStableId
```

### 3.1 不能拿什么当稳定身份

不能把以下值升级成 Save / Network / Analytics identity：

- UObject pointer；
- UObject name；
- UObject path；
- `TArray` index；
- NodePos；
- child order；
- `RuntimeIndex`；
- `TMap` key 的内存地址；
- transient replication handle。

### 3.2 UEdGraphNode::NodeGuid 的正确定位

现代 UE 的 authoring node 本身有 `NodeGuid`，它对 editor diff 很重要。

可以把它作为：

- semantic stable ID 的来源；
- authoring/compiled mapping 证据；
- migration helper；
- diff anchor。

但不要假设：

```text
UEdGraphNode::NodeGuid
== 所有 domain 的永远 stable business ID
```

更稳妥的是 runtime-consumable semantic definition（canonical 或 compiled artifact）显式保存：

```text
AuthoringNodeGuid
SemanticNodeStableId
```

如果二者长期一一映射，也要把规则写清楚。

### 3.3 Edge 不能借 Node pair 充当 identity

坏设计：

```text
Edge identity = (StartNode, EndNode)
```

这会阻止平行边：

```text
A --Choice.Accept--> B
A --Choice.Bribe--> B
```

两条边端点一样，但语义完全不同。

正确：

```text
EdgeStableId
StartNodeId
EndNodeId
TransitionSemanticId / DomainPayload
```

### 3.4 Copy / Duplicate / Rename / Move 的 ID 规则

默认：

```text
rename node
→ preserve NodeStableId

move node position
→ preserve NodeStableId

copy/paste node
→ new NodeStableId

duplicate graph for new content
→ new GraphDefinitionId
→ new node/edge IDs unless explicitly authoring a derived/migrated identity
```

只有显式 migration 操作才允许：

- alias；
- redirect；
- tombstone；
- merge map；
- split map。

### 3.5 Durable ID 不能在 Runtime/PostLoad 随机“修好”

如果 `GraphDefinitionId` / `NodeStableId` / `EdgeStableId` 已经可能被 Save、Network、Analytics、Quest/Dialogue handoff 或 content migration 引用，那么 **Runtime load 不是创建身份的时机**。

拒绝：

```text
PostLoad()
  if (!StableId.IsValid())
    StableId = FGuid::NewGuid();
```

这种代码对未发布的临时资产看似方便，但对 durable identity 会把“缺失/损坏/旧 schema”静默变成一个新的随机业务实体。相同内容在不同机器、不同 Cook、不同加载时机可能得到不同 ID；旧 Save、远端请求和分析数据不会显式报错，只会失去引用。

生产合同：

- **new semantic entity / duplicate-as-new-content**：在受控 authoring/migration 阶段生成新 ID；
- **rename / move / reload / recook same shipped entity**：保持原 ID；
- **legacy asset missing ID**：Editor migration、commandlet 或确定性 upgrade 生成/映射 ID，记录 schema/content version 与 redirect/tombstone，然后 resave；
- **Shipping/Dedicated/Cook validation**：无法迁移的 durable ID 直接阻断、隔离内容或进入显式 recovery；不能随机自愈后继续。

测试至少覆盖：同一资产跨两次独立加载 ID 不变、历史 Save 能 resolve、duplicate 获得新 ID、迁移 fixture 稳定、Cook/CI 检出 missing/duplicate IDs。

---

## 4. Canonical topology：只选一份结构真值

GenericGraph 同时维护：

- AllNodes；
- RootNodes；
- ParentNodes；
- ChildrenNodes；
- Edges map。

这种结构适合查询，但如果全部都被当 canonical serialization truth，很容易漂移。

### 4.1 推荐 canonical records

runtime-consumable semantic records 使用：

```text
Nodes[]
  NodeStableId
  NodeType
  Payload

Edges[]
  EdgeStableId
  StartNodeId
  EndNodeId
  Payload
```

其余全部派生：

```text
IncomingEdgesByNode
OutgoingEdgesByNode
RootNodes
LeafNodes
TopologicalOrder
SCCIndex
ReachabilityCache
RuntimeIndexByNodeId
RuntimeIndexByEdgeId
```

### 4.2 Load/compile 时重建 derived caches

加载后：

```text
Validate canonical records
→ Build runtime indices
→ Build incoming/outgoing adjacency
→ Build domain-specific caches
→ Publish immutable definition
```

不要把历史缓存“相信着用”。

### 4.3 必须检查的结构错误

至少包括：

- duplicate NodeStableId；
- duplicate EdgeStableId；
- missing start endpoint；
- missing end endpoint；
- invalid self-loop；
- invalid parallel edge；
- node type incompatible；
- root policy violation；
- cardinality violation；
- unreachable node；
- orphan component；
- cycle policy violation；
- domain payload invalid。

---

## 5. Graph Schema 是交互入口，Compiler 才是最终验收

推荐：

```text
Domain Graph Policy
    ↓
Editor Schema feedback
    ↓
Compiler whole-graph validation
    ↓
Cook / CI validation
    ↓
Runtime defensive assertions
```

### 5.1 Editor `CanCreateConnection` 只提供早期反馈

拖线时检查：

- self connection；
- direction；
- type compatibility；
- parent/child limit；
- cycle；
- parallel edge；
- graph-specific restriction。

有价值，但不能作为唯一防线。

原因：

- 资产可能来自旧版本；
- copy/paste 可能绕过旧规则；
- policy 可能更新；
- import/merge/commandlet 可能生成连接；
- corrupt asset 不一定经过 UI。

### 5.2 Compiler 必须全图重验

编译器对整个图运行同一 policy：

```text
Node validation
Edge validation
Topology validation
Cross-node semantic validation
Domain payload validation
Version/migration validation
```

不要因为 Editor 当初阻止非法连接，就在 compiler 里省略检查。

### 5.3 Node hook 只是补充，不是规则源头

可以支持：

```text
Node.CanConnectTo(...)
Node.CanConnectFrom(...)
```

但核心 topology policy 应集中：

```text
DomainSchema / GraphPolicy
```

否则：

- Node A 认为合法；
- Node B 认为非法；
- Editor 与 cook 又有第三套解释。

### 5.4 诊断必须可用于 CI

不要只返回一句：

```text
"Can't create connection"
```

结构化诊断：

```text
ErrorCode
Severity
GraphDefinitionId
NodeStableId?
EdgeStableId?
Message
FixHint
SourceLocation?
```

`fix hint` 例如：

```text
GRAPH_PARALLEL_EDGE_NOT_ALLOWED
FixHint: Merge transitions or enable parallel-edge policy for this graph type.
```

---

## 6. Compile Contract：不要“先 Clear live artifact 再 rebuild”

GenericGraph 的 save path 先 rebuild，同一 runtime graph 被原地清空和重填。

生产级编译推荐：

```text
Parse authoring graph
→ Validate
→ Normalize
→ Plan stable IDs/migrations
→ Build staging artifact
→ Compute fingerprint
→ Run deterministic checks
→ Commit atomically
```

### 6.1 Compile failure 的两个合法策略

开发器可以选择：

**A. Block save/cook**

```text
compile fail
→ asset cannot be promoted/cooked
```

**B. Keep last-known-good**

```text
compile fail
→ authoring graph remains dirty
→ runtime compiled artifact remains previous valid revision
→ editor displays stale/invalid state clearly
```

不能：

```text
Clear valid runtime data
→ compile halfway fails
→ save half graph
```

### 6.2 Compiled artifact 要带版本指纹

至少一种：

```text
GraphDefinitionVersion
CompilerVersion
SourceHash
ContentFingerprint
CompiledRevision
```

用途：

- stale compile detection；
- network revision fence；
- save migration；
- deterministic cook；
- diff；
- content hot reload。

### 6.3 Deterministic compile

相同 semantic graph 输入应得到稳定：

- stable IDs；
- node/edge deterministic order；
- fingerprint；
- diagnostics order。

Editor X/Y 可以作为显示排序 hint，但不能决定业务身份。

---

## 7. Cycle support 是算法合同，不是一个 bool

GenericGraph 有 `bCanBeCyclical`，但 runtime `Print/GetLevelNum/GetNodesByLevel` 没有 visited-set。

结论：

```text
AllowCycle = true
```

不等于“系统真正支持 cycle”。

### 7.1 所有 general-graph traversal 必须有终止机制

可选：

- visited set；
- white/gray/black DFS；
- generation mark；
- maximum nodes/edges budget；
- maximum depth；
- cancellation token。

### 7.2 DAG-only 算法必须明确拒绝 cycle

例如：

- topological order；
- tree level；
- tree layout；
- simple parent chain。

若遇 cycle：

```text
Reject
```

或先：

```text
Find SCC
→ condense to DAG
→ run DAG algorithm on SCC graph
```

不要返回“看起来像 level”的伪结果。

### 7.3 rootless strongly-connected component

一个完全闭环：

```text
A → B → C → A
```

每个节点都有入边，因此：

```text
RootNodes = []
```

但图并不为空。

所以 general graph 的遍历入口应从：

```text
All canonical nodes
```

构建 component/SCC，而不是只从 roots 出发。

### 7.4 测试矩阵

至少：

- simple DAG；
- diamond DAG；
- self-loop；
- 2-node cycle；
- N-node cycle；
- root + downstream cycle；
- rootless SCC；
- disconnected components；
- shared child；
- very large graph；
- traversal budget exceeded。

---

## 8. 每个 Domain 都需要自己的 topology policy

不要做：

```text
bool bCanBeCyclical
```

然后让所有业务共享。

推荐：

```text
FGraphTopologyPolicy
  bAllowCycle
  bAllowSelfLoop
  bAllowParallelEdge
  RootPolicy
  ReachabilityPolicy
  Min/MaxIncoming
  Min/MaxOutgoing
  AllowedNodeTypes
  AllowedEdgeTypes
```

更重要的是 domain-specific policy：

### Quest

可能：

```text
merge allowed
cycle rejected
explicit terminal required
```

### Dialogue

可能：

```text
cycle allowed
parallel semantic choices allowed
entry nodes required
```

### Combo

可能：

```text
bounded return loop allowed
unbounded zero-cost cycle rejected
```

### State-like graph

可能：

```text
cycles expected
transition priority must be deterministic
```

Policy change属于 content-breaking change，必须触发：

```text
GraphDefinitionVersion bump
+ full revalidation
+ migration impact review
```

---

## 9. Edge 是一等公民时，必须有一等 identity

GenericGraph 的显式 edge UObject 设计方向正确：有些领域的语义确实在“连接”上，而不是节点上。

例如：

```text
Dialogue Choice
Quest Branch
Combo Input Window
State Transition
Probability / Weight
Condition / Cost
```

### 9.1 Canonical edge record

```text
EdgeStableId
StartNodeId
EndNodeId
EdgeType
SemanticTag / SemanticId
Conditions
Payload
Priority
```

### 9.2 Parallel edge policy

若允许：

```text
OutgoingEdgesByNode[Start] -> TArray<EdgeHandle>
```

不要：

```text
TMap<ChildNode, Edge>
```

### 9.3 Choice identity

UI 可以显示：

```text
visible choice index = 0,1,2
```

网络请求必须使用：

```text
StableChoiceId / EdgeStableId
```

因为过滤、Localization、条件变化后可见 index 会重排。

---

## 10. Copy / Diff / Merge / Migration

### 10.1 Copy-paste

复制节点时：

```text
new semantic entity
→ new NodeStableId
```

否则会出现同图两个相同 ID。

### 10.2 Graph duplicate

“复制一份 Quest 做新 Quest”默认：

```text
new GraphDefinitionId
new NodeStableIds
new EdgeStableIds
```

“创建兼容新版本”则应显式走：

```text
ForkWithIdentityMapping
```

而不是普通 duplicate。

### 10.3 Content migration primitives

至少规划：

- redirect old node -> new node；
- tombstone removed node；
- edge redirect；
- split one -> many；
- merge many -> one；
- restart checkpoint；
- abort with structured reason。

### 10.4 Diff / merge

优先比较：

```text
Stable ID
Node/Edge type
Semantic payload
Connections by stable ID
```

不要主要依据：

- NodePos；
- UObject path；
- array index；
- random compile order。

---

## 11. Runtime/Editor module 边界

目标：

```text
Game / Server / Cook
    can load runtime definition
    without loading GraphEditor / Slate editor chain
```

### 11.1 Runtime module

只包含：

- domain-neutral graph DTO；
- stable IDs；
- compiled artifact；
- runtime lookup；
- pure validation data if needed；
- domain runtime adapter interfaces。

尽量不依赖：

- UnrealEd；
- GraphEditor；
- AssetTools；
- PropertyEditor；
- editor Slate widgets。

如果 Runtime Build.cs 出现 Slate/SlateCore，先问：

```text
shipping runtime 真需要 UI 吗？
```

### 11.2 Editor / UncookedOnly module

承载：

- UEdGraph；
- UEdGraphSchema；
- graph nodes/pins；
- UAssetDefinition；
- factory；
- ToolMenus；
- details customization；
- Slate graph node；
- auto-layout；
- diff/search；
- compiler UI diagnostics。

### 11.3 Public dependency 最小化

Build.cs 评审：

```text
Public dependency
= public headers真的暴露该module类型
```

不要因为 implementation 用到就放 Public。

---

## 12. 现代资产入口：优先评估 UAssetDefinition

在目标 UE5.7/5.8：

1. 查询当前官方 `UAssetDefinition`；
2. 查询 ToolMenus；
3. 查询当前 asset editor / factory 接入；
4. legacy `FAssetTypeActions_Base` 只作为迁移/兼容证据。

这不是说 legacy 一定不能用，而是：

```text
still supported
!=
modern default
```

把 target-engine adapter 封在 Editor module，避免业务 graph foundation 关心具体 asset browser API。

---

## 13. Node 类型发现不能每次 context menu 全局扫全部 UClass

GenericGraph context menu 用 `TObjectIterator<UClass>` 搜所有派生节点。

小项目可以，长期大型项目应改为：

```text
NodeTypeRegistry
+ cache
+ class/module/hot-reload invalidation
```

候选来源可包含：

- registered node descriptors；
- class metadata；
- module registration；
- asset registry metadata；
- explicit domain catalog。

### 13.1 缓存失效事件

至少考虑：

- module loaded/unloaded；
- Blueprint compiled；
- hot reload/live coding；
- plugin enabled/disabled；
- domain schema changed。

### 13.2 Context menu 热路径

右键菜单不应：

- sync load 所有 node assets；
- 扫描整个 project UObject universe；
- rebuild whole graph；
-运行 O(N²) validation。

---

## 14. Auto-layout 是 Editor convenience，不是 topology truth

布局可以失败，业务图不能因此损坏。

### 14.1 必须与 semantic compile 分离

```text
Semantic Compile
    headless / CI / Cook 可运行

Auto Layout
    Editor-only optional operation
```

Semantic compile 不能依赖：

- `SWidget::GetCachedGeometry()`；
- graph panel 已经绘制；
- viewport open；
- editor tab active。

### 14.2 算法预算

Force-directed 常见成本：

```text
O(N² × Iterations)
```

需要：

- node threshold；
- max iteration；
- time budget；
- progress；
- cancel；
- profile；
- deterministic/random seed policy。

### 14.3 Cycle safety

Tree layout 遇 cycle 要：

- reject；
- or SCC-condense；
- or use general-graph layout。

不能递归 children 直到栈爆。

### 14.4 Layout 测试

测试：

- cycle；
- rootless SCC；
- disconnected graphs；
- shared child；
- parallel edges；
- 1k+ nodes；
- no Slate geometry/headless mode；
- cancellation。

---

## 15. Authoring compiler 需要真正的 staging/commit

建议数据流：

```text
UEdGraph snapshot
    ↓
NormalizedAuthoringModel
    ↓
DomainPolicy Validate
    ↓
StableId/Migration Plan
    ↓
CompiledDefinitionBuilder
    ↓
Staging artifact
    ↓
Hash + deterministic verification
    ↓
Atomic publish
```

Compile 时不要直接修改当前 runtime definition。

### 15.1 Last-known-good

如果设计师改坏图：

```text
Authoring revision 58 = invalid
Compiled revision 57 = last-known-good
```

Editor 清楚提示 stale，不要把 revision 57 伪装成 58。

### 15.2 Cook gate

Shipping cook 可以选择：

```text
source fingerprint != compiled fingerprint
→ fail cook
```

这样防止设计师忘记 compile/save。

---

## 16. Live edit / PIE / multiplayer revision fence

运行中的实例必须绑定：

```text
GraphDefinitionId
CompiledRevision
ContentFingerprint
RuntimeGeneration
```

设计师保存新图时，不允许无条件让旧实例引用新数组。

开发期两种安全策略：

### Freeze old revision

```text
existing sessions stay on r57
new sessions use r58
```

### Migrate live

```text
quiesce
→ map active stable IDs
→ validate migration
→ build new state
→ atomic switch
→ generation bump
→ notify clients
```

失败：rollback 到旧 revision。

网络请求必须带：

```text
ExpectedCompiledRevision
```

旧请求：Authority reject + snapshot/resync。

---

## 17. Graph 与 Domain Runtime 的边界

共享基础设施可以有：

```text
Stable IDs
Compiler pipeline
Schema diagnostics
Search / diff
Editor graph widgets
Layout
Content migration primitives
Compiled artifact header
```

不要强制共享：

```text
Quest runtime node base
Dialogue runtime node base
AI state execution
Ability execution
Save semantics
Network Authority
```

原因：它们的业务真值不同。

### 17.1 错误的 UniversalGraphRuntime

```text
UniversalNode::Execute()
    if Quest -> GrantReward
    if Dialogue -> SetConversationState
    if AI -> MovePawn
    if Ability -> ApplyDamage
```

这会形成新的 God Framework。

### 17.2 正确共享

```text
Graph Authoring Foundation
    ↓ compiled typed definition
Quest Runtime Adapter
Dialogue Runtime Adapter
Combo Runtime Adapter
World Flow Runtime Adapter
```

---

## 18. GC / pointer / current UE style

运行时 UObject 成员：

- 使用 UPROPERTY/TObjectPtr 等当前引擎 GC-safe 表达；
- pointer/handle 只做本 session runtime cache；
- Save/Network 使用 stable IDs；
- caches 能由 canonical records 重建。

不要复制历史代码里的裸 pointer 样式，就称为今天推荐。

---

## 19. 性能边界

### Authoring

热路径：

- context menu；
- graph drag；
- selection；
- details edit；
- incremental validation。

避免每次：

- full UClass scan；
- full graph compile；
- whole project asset load。

### Compile

按内容规模考虑：

- incremental dirty region；
- deterministic full compile fallback；
- caching；
- parallel pure validation；
- structured diagnostics aggregation。

### Runtime

运行时优先：

- dense compiled indices；
- stable id -> runtime index map；
- compact edge arrays；
- immutable definitions；
- domain-specific state separate from definition。

不要让 Editor UObject graph 直接成为 runtime hot path。

---

## 20. 必测项目

### Compiler

- duplicate IDs；
- dangling endpoints；
- stale compiled artifact；
- invalid topology；
- parallel edge policy；
- invalid node type；
- migration redirect；
- deterministic output；
- failed compile preserves last-known-good。

### Topology

- DAG；
- cycles；
- rootless SCC；
- disconnected components；
- shared child；
- multiple roots；
- self-loop；
- parallel edges。

### Editor

- copy/paste ID regeneration；
- duplicate graph；
- undo/redo；
- class reload；
- node registry invalidation；
- commandlet compile without Slate；
- large graph menu latency；
- cancel auto-layout。

### Runtime/network if domain uses it

- revision mismatch；
- JIP snapshot；
- save migration；
- live edit generation；
- old request rejection。

---

## 21. GenericGraph 固定样本：保留与拒绝清单

### 保留

- Runtime / Editor module 分层方向；
- Graph / Node / Edge 可扩展类型；
- Editor schema 统一拖线规则；
- per-node connection policy hook；
- optional explicit edge node；
- authoring graph rebuild into runtime structure；
- cycle checker as editor feedback；
- auto-layout作为独立 editor service；
- asset factory / custom editor整体工作流。

### 不直接迁移

- UE5.1-era 具体 Editor API；
- legacy AssetTypeActions 作为新项目默认；
- runtime raw pointer 拓扑作为长期身份；
- `TMap<ChildNode, Edge>` 作为 edge canonical store；
- `bCanBeCyclical` 一个 bool 覆盖全部 domain；
- root-only traversal 代表 general graph；
- save 时先 clear live runtime graph 再 rebuild；
- context menu 每次全局 `TObjectIterator<UClass>`；
- runtime Slate/SlateCore 依赖没有业务理由；
- recursive tree layout 在 cycle-enabled graph 上直接运行；
- force-directed O(N²) 无规模门；
- Slate cached geometry 参与 headless semantic compile。

---

## 22. 审查输出模板

评审一个自定义 Graph 系统时，按以下顺序输出：

```text
1. Freshness
2. Authoring/Runtime boundary
3. Stable IDs
4. Canonical topology
5. Domain topology policy
6. Schema feedback
7. Compiler full validation
8. Compile staging/atomic publish
9. Save/content migration
10. Cycle/general-graph semantics
11. Editor module/API modernity
12. Layout/search/discovery scalability
13. Runtime performance
14. Network revision if applicable
15. Verification gaps
```

结论必须区分：

```text
Mechanism accepted
API recheck required
Pattern rejected
Runtime verification missing
```

---

## 23. 快速决策表

| 问题 | 推荐 |
|---|---|
| Runtime 是否直接遍历 UEdGraph？ | 否。Runtime 不依赖 UEdGraph；可直接消费 canonical semantic definition，或在需要 lowering/优化/裁剪时消费独立 compiled artifact |
| NodePos 能否当 ID？ | 不能 |
| RuntimeIndex 能否存档？ | 不能 |
| Edge 是否需要 stable ID？ | 需要，尤其 choice/transition |
| A→B 能否多条边？ | 由 domain policy 明确 |
| CanCreateConnection 是否足够？ | 不足，compiler/cook 全图复验 |
| Cycle support 是否只要 bool？ | 不够，所有算法都要 cycle contract |
| RootNodes 空是否等于空图？ | general graph 中不等于，可能 rootless SCC |
| Save 时能否原地 Clear + rebuild？ | 不建议，stage + atomic publish |
| 编译失败怎么办？ | block save/cook 或保留 last-known-good |
| Context menu 可否每次全局扫类？ | 大项目不建议，registry/cache |
| Layout 可否依赖 Slate geometry？ | 仅 Editor convenience，CI compile 不依赖 |
| FAssetTypeActions 是否仍能用？ | 可能能；新项目先评估 UAssetDefinition |
| Runtime module 可否依赖 UnrealEd？ | 不可 |
| 各业务是否共用 UniversalGraphRuntime 执行器？ | 不建议，共享 authoring foundation 即可 |

