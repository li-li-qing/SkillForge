# jinyuliao/GenericGraph 源码蒸馏：从 UE5.1 历史 Graph 插件提炼现代 Authoring Foundation

研究轮次：R16  
日期：2026-09-14  
目标：为 SkillForge / LGF 提炼可复用的自定义 Graph authoring/compiler/runtime 基础设施规则；不把旧 UE Editor API 当成 UE5.7/5.8 模板。

---

## 0. 结论摘要

`jinyuliao/GenericGraph` 是一个非常典型的“**架构思想仍有价值，但技术接口已经明显过时**”的项目。

固定样本：

```text
Repository: jinyuliao/GenericGraph
Default branch: master
Commit: f9b8fe3de6bc2ef39ee771658ac4a8bf48c2e078
Commit date: 2023-07-15
Tree: 373cc9d89894a05b8204714370fd7972c87b3387
License: MIT
Repository language: C++
Research-time stars: 770
Research-time forks: 168
```

最后明确的引擎迁移提交：

```text
bc270c007694c1d4a455fe26d82d0bb4f132e86a
2023-06-11
"Plugin conversion to UE 5.1"
```

README 仍明确称：

```text
Generic graph data structure plugin for ue4
```

因此分类：

```text
Historical architecture sample
```

而不是：

```text
Current UE5.7/5.8 implementation reference
```

这轮最重要的结果不是“把 GenericGraph 搬进 LGF”，而是将 R13 FlowGraph、R14 SimpleQuest、R15 DlgSystem 中重复出现的作者工具共性继续下沉为一套现代合同：

```text
Shared Graph Authoring Foundation
    ├─ Stable Graph / Node / Edge identity
    ├─ Domain topology policy
    ├─ Schema feedback
    ├─ Whole-graph compiler validation
    ├─ Staged compiled artifact
    ├─ Structured diagnostics
    ├─ Search / diff / migration
    ├─ Node type registry
    └─ Editor-only layout

Domain Runtime Truth
    ├─ Quest
    ├─ Dialogue
    ├─ World Flow
    ├─ AI / StateTree
    └─ Ability / Combo
```

**共享 authoring infrastructure，不共享 gameplay truth。**

---

# 1. 技术时效性审计

## 1.1 为什么不能因为 stars 高就当现代模板

当前仓库仍有较高 stars/forks，并且 GitHub metadata 没有 archived。

但技术时效性看的是：

1. 默认分支真实 commit；
2. 目标引擎版本证据；
3. 当前官方 replacement；
4. active implementation；
5. target UE build/runtime verification。

GenericGraph：

- default branch 最后 commit：2023-07-15；
- 明确 engine conversion：UE5.1；
- README：UE4；
- plugin descriptor：Version 1.0，无 EngineVersion；
- 没有 UE5.7/5.8 branch/tag 证据。

所以：

```text
popular
!= current

not archived
!= maintained for target engine

UE5.1 compatible
!= UE5.7/5.8 current
```

## 1.2 Descriptor 证据

文件：

```text
GenericGraph.uplugin
```

模块：

```text
GenericGraphRuntime
  Type=Runtime
  LoadingPhase=PreDefault

GenericGraphEditor
  Type=Editor
  LoadingPhase=Default
```

这是一个值得保留的早期模块边界思想。

但 descriptor 没有：

- 目标 EngineVersion；
- 5.7/5.8 compatibility；
- contemporary feature gate；
- modern asset definition metadata。

## 1.3 UE5.8 当前官方校准

当前 UE5.8 官方 API 仍保留不少旧类型，例如：

- `FAssetTypeActions_Base`；
- `UFactory`；
- `UEdGraphSchema`；
- conversion-node connection response。

但是官方 `UAssetDefinition` 文档明确把 Asset Definition 定位为 Asset Actions 的替代系统之一。

因此这轮新增一条非常重要的 freshness 规则：

```text
Old API still exists
!=
Old API is current recommended default
```

GenericGraph 的 `FAssetTypeActions_GenericGraph` 可以作为历史机制样本，但新 LGF Graph Editor 首先应该评估目标 UE5.7/5.8 的：

- `UAssetDefinition`；
- ToolMenus；
- current Asset Registry / editor registration；
- current GraphEditor APIs。

---

# 2. 模块与源码地图

## 2.1 Runtime

核心：

```text
Source/GenericGraphRuntime/Public/GenericGraph.h
Source/GenericGraphRuntime/Public/GenericGraphNode.h
Source/GenericGraphRuntime/Public/GenericGraphEdge.h

Source/GenericGraphRuntime/Private/GenericGraph.cpp
Source/GenericGraphRuntime/Private/GenericGraphNode.cpp
Source/GenericGraphRuntime/Private/GenericGraphEdge.cpp
```

Runtime 数据模型：

```text
UGenericGraph
  NodeType
  EdgeType
  GraphTags
  RootNodes
  AllNodes
  bEdgeEnabled

UGenericGraphNode
  Graph
  ParentNodes
  ChildrenNodes
  Edges: TMap<ChildNode, Edge>

UGenericGraphEdge
  Graph
  StartNode
  EndNode
```

## 2.2 Editor

核心：

```text
Source/GenericGraphEditor/Private/GenericGraphAssetEditor/
  AssetEditor_GenericGraph.cpp
  AssetGraphSchema_GenericGraph.cpp
  EdGraph_GenericGraph.cpp
  EdNode_GenericGraphNode.cpp
  EdNode_GenericGraphEdge.cpp
  ConnectionDrawingPolicy_GenericGraph.cpp

Source/GenericGraphEditor/Private/AutoLayout/
  AutoLayoutStrategy.cpp
  TreeLayoutStrategy.cpp
  ForceDirectedLayoutStrategy.cpp
```

其他：

```text
GenericGraphFactory
AssetTypeActions_GenericGraph
GenericGraphNodeFactory
Editor settings / commands / styles
```

---

# 3. 最值得保留：Runtime 与 Editor 分层的方向

GenericGraph 在很早期就区分：

```text
Runtime graph objects
vs
UEdGraph / Slate editor representation
```

例如：

`UGenericGraph` 在 `WITH_EDITORONLY_DATA` 下才有：

```text
UEdGraph* EdGraph
bCanRenameNode
bCanBeCyclical
```

Node 的 editor-only 字段包括：

```text
NodeTitle
CompatibleGraphType
BackgroundColor
ContextMenuName
Parent/Children limit metadata
```

方向正确：

```text
Presentation/editor metadata
!=
shipping runtime state
```

但现代化后需要进一步做到：

```text
Authoring UEdGraph
!=
Compiled runtime definition
```

而不只是用 `#if WITH_EDITORONLY_DATA` 包几个字段。

---

# 4. Authoring Graph → Runtime Graph：正确方向，编译合同不够强

## 4.1 当前 Rebuild 流程

核心文件：

```text
EdGraph_GenericGraph.cpp
```

`RebuildGenericGraph()`：

1. `Clear()` 当前 runtime graph；
2. 遍历 editor `Nodes`；
3. 把 runtime node 加到 `AllNodes`；
4. 从 Pins/LinkedTo 构建 `ChildrenNodes` / `ParentNodes`；
5. edge editor node 映射成 runtime edge；
6. edge `Rename` 到 Graph；
7. node `Rename` 到 Graph；
8. 找 `ParentNodes.Num()==0` 的 root；
9. 根据 editor X 位置排序。

这是一个原始 compiler：

```text
UEdGraph topology
→ Runtime topology
```

这个方向应保留。

## 4.2 问题：就地 Clear + rebuild

当前逻辑先：

```text
Graph->ClearGraph()
```

再逐步重建。

如果中间失败：

- invalid edge；
- missing child；
- bad object；
- 新规则 validation fail；

没有明显的：

```text
staging artifact
atomic commit
last-known-good
```

现代编译应改成：

```text
Capture authoring snapshot
→ Validate
→ Build staging definition
→ Verify
→ Atomic publish
```

编译失败：

```text
keep last-known-good
```

或：

```text
block save/cook
```

不能留下半图。

---

# 5. SaveAsset 触发 rebuild：不能作为生产一致性协议

文件：

```text
AssetEditor_GenericGraph.cpp
```

当前：

```text
SaveAsset_Execute()
  → RebuildGenericGraph()
  → FAssetEditorToolkit::SaveAsset_Execute()
```

这意味着 runtime artifact 更新依赖 Editor Save side effect。

对小型工具足够。

长期运营项目需要显式：

```text
SourceRevision
SourceFingerprint
CompilerVersion
CompiledRevision
CompiledFingerprint
CompileStatus
```

否则：

- 设计师修改没保存；
- commandlet import；
- source control merge；
- cook without opening editor；
- automation patch；

都可能产生 stale artifact。

### 5.1 LGF 规则

```text
SaveAsset
!= compile protocol
```

可以 Save 时自动 compile，但 CI/cook 仍独立验证：

```text
source fingerprint == compiled fingerprint
```

---

# 6. Node identity：Editor 有 GUID，Runtime 没有 stable semantic ID

## 6.1 Editor node

`UEdNode_GenericGraphNode` 继承 `UEdGraphNode`。

新节点创建时：

```text
NodeTemplate->CreateNewGuid()
```

所以 authoring layer 有 `NodeGuid`。

## 6.2 Runtime node

`UGenericGraphNode` 没有：

```text
NodeStableId
NodeGuid
```

Runtime identity 实际主要依赖 UObject pointer。

这对临时内存结构可用，但对：

- Save；
- network；
- content patch；
- analytics；
- quest/dialogue reference；

不足。

## 6.3 R16 规则

显式：

```text
GraphDefinitionId
NodeStableId
```

Authoring `UEdGraphNode::NodeGuid` 可以成为 stable ID 的来源或映射证据，但 compiled definition 必须真正保存它的 semantic identity。

---

# 7. Edge identity：GenericGraph 暴露了一个很重要的长期坑

`UGenericGraphEdge` 是一等 UObject：

```text
StartNode
EndNode
Graph
```

这是好方向，因为 Dialogue/Quest/Combo 的大量语义本来就在 edge 上。

但是：

`UGenericGraphNode` 用：

```text
TMap<UGenericGraphNode*, UGenericGraphEdge*> Edges
```

即：

```text
ChildNode -> one Edge
```

因此同一：

```text
A → B
```

只能自然映射一条 edge。

## 7.1 Dialogue 的现实需求

完全可能：

```text
A --Accept--> B
A --Lie--> B
A --Bribe--> B
```

目标节点一样，但：

- 条件不同；
- choice text 不同；
- analytics 不同；
- quest effect 不同；
- network choice ID 不同。

所以现代模型必须：

```text
EdgeStableId
StartNodeStableId
EndNodeStableId
```

端点 pair 不是 edge identity。

---

# 8. Canonical structure：不要序列化五份相同拓扑真值

GenericGraph 同时维护：

```text
AllNodes
RootNodes
ParentNodes
ChildrenNodes
Edges map
```

这些都方便查询，但如果都被当 canonical truth，任何一次 mutation 漏更新就 drift。

## 8.1 R16 推荐

canonical：

```text
NodeRecords[]
EdgeRecords[]
```

派生：

```text
RootNodes
Incoming
Outgoing
RuntimeIndex
TopologicalOrder
Level
SCC
Reachability
```

### 8.2 编译/加载后校验

```text
duplicate NodeId
edge endpoint missing
duplicate EdgeId
parallel edge policy
self-loop policy
cycle policy
root policy
reachability
node type compatibility
```

---

# 9. Schema：GenericGraph 最值得保留的 Editor 设计之一

文件：

```text
AssetGraphSchema_GenericGraph.cpp
```

`CanCreateConnection()` 集中处理：

- same-node rejection；
- pin/node validation；
- cycle policy；
- node-specific `CanCreateConnectionTo`；
- node-specific `CanCreateConnectionFrom`；
- edge-enabled conversion-node behavior。

这比把拖线合法性散落到 Slate widget 好很多。

### 9.1 但 Editor Schema 不是最终 Authority

Graph 可能通过：

- old asset；
- import；
- copy/paste；
- merge；
- commandlet；
- changed policy；

得到一个 Editor 从未“拖线创建”的非法状态。

因此：

```text
CanCreateConnection = UX feedback
Compiler full validation = content authority
```

### 9.2 Domain Node hook

GenericGraph 的 Node 可以覆写：

```text
CanCreateConnection
CanCreateConnectionTo
CanCreateConnectionFrom
```

机制可保留，但只作为 domain hook。

核心 policy 仍集中在：

```text
DomainSchema / TopologyPolicy
```

---

# 10. Cycle Checker：Editor 有，Runtime 并没有“完整支持 cycle”

Schema 内有：

```text
FNodeVisitorCycleChecker
```

如果 `bCanBeCyclical=false`，拖线时拒绝 cycle。

这是一条不错的早期验证。

但 `bCanBeCyclical=true` 后，事情远没有结束。

---

# 11. Runtime traversal 的 cycle bug 风险

文件：

```text
GenericGraph.cpp
```

这些函数：

```text
Print
GetLevelNum
GetNodesByLevel
```

都做：

```text
CurrLevelNodes
→ append every Child
→ NextLevel
```

没有：

- Visited；
- gray/black state；
- max depth；
- budget。

若：

```text
A → B → C → A
```

它们可以一直重复。

因此：

```text
Graph has bCanBeCyclical
!=
Runtime supports cyclical graph
```

这正是用户要求“不要只看项目新旧，还要判断技术”的具体案例。

---

# 12. 2023 cycle fix 的真实边界

提交历史有：

```text
Preventing infinite loop when sorting cyclical graphs
```

当前 `UEdGraph_GenericGraph::SortNodes()` 已有：

```text
TSet<UGenericGraphNode*> Visited
```

说明作者确实修了 editor sorting 的无限循环。

但不能外推为：

```text
all graph traversal cycle-safe
```

因为：

- Runtime traversal 仍无 visited；
- TreeLayout recursion 仍无 visited；
- ForceDirected attractive traversal 仍无 visited；
- AutoLayout bounds traversal 仍无 visited。

这轮将其正式蒸馏成：

> feature-level correctness 必须审计所有 active algorithm path，不能看到一次 bugfix 就宣称整个 feature solved。

---

# 13. RootNodes 模型无法完整表达 general graph

当前 root：

```text
ParentNodes.Num() == 0
```

如果：

```text
A → B
B → C
C → A
```

三个节点都有 parent：

```text
RootNodes = []
```

图却真实存在。

这就是：

```text
rootless strongly-connected component
```

因此：

- DAG 可从 roots 处理；
- general graph 必须从 AllNodes/component/SCC 处理。

不能把：

```text
RootNodes.Num()==0
```

解释成 empty graph。

---

# 14. DAG algorithm 与 general-graph algorithm 必须拆开

## DAG-only

可以：

- topological order；
- levels；
- dependency scheduling；
- tree/DAG layout。

## General graph

需要：

- visited traversal；
- SCC；
- explicit cycle semantics；
- transition/runtime budget。

## Domain 示例

Quest：

```text
merge yes
cycle no
```

Dialogue：

```text
cycle yes
parallel edge maybe yes
```

Combo：

```text
return loop maybe yes
unbounded zero-cost loop no
```

一个 `bCanBeCyclical` 无法表达这些。

---

# 15. Node cardinality：机制值得吸收

GenericGraph Node editor metadata：

```text
ParentLimitType / ParentLimit
ChildrenLimitType / ChildrenLimit
```

`CanCreateConnectionTo/From` 提供 cardinality 限制。

这个机制很实用。

现代化后应该由 `DomainSchema` 定义，Node metadata 作为声明/override。

示例：

```text
Dialogue Choice Node
  incoming >= 1
  outgoing >= 1

Terminal
  outgoing = 0

Quest Entry
  incoming = 0
```

---

# 16. Explicit Edge / Conversion Node：值得保留

当：

```text
bEdgeEnabled=true
```

Schema 返回 conversion-node connection response，创建：

```text
UEdNode_GenericGraphEdge
+ UGenericGraphEdge
```

这种设计适合：

- Dialogue choice；
- condition transition；
- probability；
- combo input；
- weighted transition。

但现代化后 edge 必须有：

```text
EdgeStableId
```

并支持 domain policy 明确是否可以 parallel edge。

---

# 17. Authoring Node 与 Runtime Node 的 Outer 迁移

`UEdNode_GenericGraphNode::PrepareForCopying()`：

```text
GenericGraphNode->Rename(..., this)
```

重建时又：

```text
Node->Rename(..., Graph)
```

Edge 同理。

这是早期“同一个 UObject 同时服务 authoring/runtime”的工程手法。

问题：

- ownership 边界复杂；
- copy/paste identity 容易混；
- staging compile 困难；
- editor/runtime artifact 不是不可变分离；
- diff/migration 依赖 UObject lifecycle。

现代 LGF 更适合：

```text
Editor authoring UObject
→ compiler DTO
→ new/staged compiled definition
```

而不是 Rename 同一个 runtime object。

---

# 18. Graph asset subclass 作为 domain type

`UGenericGraphFactory` 创建资产时让设计者选 `UGenericGraph` 子类。

这说明：

```text
Graph class
→ domain type/policy
```

是一个可复用的思路。

例如 LGF：

```text
QuestGraphDefinition
DialogueGraphDefinition
ComboGraphDefinition
```

但是不要用 class inheritance 承担全部 schema；推荐 domain descriptor/policy interface，使内容版本和策略更容易测试。

---

# 19. Context menu node discovery：小项目可用，大项目会扩展差

Schema 的 `GetGraphContextActions()`：

```text
for TObjectIterator<UClass>
  find every child of NodeType
  filter abstract / REINST / SKEL / CompatibleGraphType
```

小插件简单有效。

大型项目问题：

- 每次右键都扫描 class universe；
- Blueprint/reinst classes；
- plugin/module 多；
- authoring menu 可能越来越慢；
- 可能触发不必要 class loading。

R16 推荐：

```text
GraphNodeTypeRegistry
+ invalidation
```

刷新：

- module load/unload；
- BP compile；
- Live Coding；
- plugin changes。

---

# 20. Module dependency：旧项目的边界债务

## Runtime Build.cs

当前 Runtime private deps 包含：

```text
Slate
SlateCore
GameplayTags
```

对于纯 runtime graph data：

- GameplayTags 可能有业务理由；
- Slate/SlateCore 应被质疑。

## Editor Build.cs

当前 public deps 包含：

```text
UnrealEd
```

private：

```text
GraphEditor
PropertyEditor
AssetTools
Slate
Kismet
ToolMenus
...
```

方向上 editor deps 应留 Editor module，但现代 Build.cs 还应进一步做到：

```text
minimal public dependencies
```

避免 UnrealEd 类型经公共头泄漏到 Runtime consumer。

---

# 21. AssetTypeActions：当前官方 replacement 的具体 freshness 案例

GenericGraph：

```text
FAssetTypeActions_GenericGraph
```

负责：

- asset name；
- type color；
- supported class；
- open custom editor。

这个机制在旧 UE 很标准。

当前 UE5.8 官方：

```text
UAssetDefinition
```

被描述为 Asset Actions replacement 系统之一。

因此 R16 规则：

```text
Legacy API may still compile
but should not become new Foundation ABI without target-version review
```

新 Graph Editor adapter 优先基于目标 5.7/5.8 当前接口设计。

---

# 22. ToolMenus：部分现代化已经出现，但不能据此称项目现代

GenericGraph 2023 源码已经使用：

```text
ToolMenus
```

说明它在部分 Editor API 上有更新。

但项目整体仍：

- AssetTypeActions；
- UE5.1 target；
- old module shapes；
- historical runtime pointer design。

所以 freshness 不能按某一个 include 判断。

这和 Combee 的：

```text
include FIrisFastArraySerializer
but actual path #if 0
```

属于同类证据原则。

---

# 23. Auto-layout：TreeLayout

`TreeLayoutStrategy.cpp`：

- `InitPass` recursively visits children；
- `ResolveConflictPass` recursively visits children；
- contours recursively visit children；
- `ShiftSubTree` recursively visits children。

没有显式 visited。

如果 graph 允许 cycle：

```text
cycle-enabled graph
→ TreeLayout recursive traversal
→ stack/infinite recursion risk
```

因此：

```text
TreeLayout only for DAG/tree policy
```

或：

```text
SCC condense first
```

---

# 24. Auto-layout：ForceDirected

`ForceDirectedLayoutStrategy.cpp`：

## 24.1 O(N²)

每 iteration：

```text
for every node i
  for every node j
    repulsion
```

复杂度：

```text
O(N² × MaxIteration)
```

对几十个节点可接受。

对几千个节点必须：

- threshold；
- time budget；
- cancel；
- profiling；
- spatial approximation/barnes-hut 等替代。

## 24.2 attractive traversal cycle risk

attractive force 仍使用：

```text
RootNode
→ Children
```

无 visited。

所以同样不是 general graph safe。

## 24.3 固定源码中的坐标混用风险

可见代码：

```text
Diff.X = Child.NodePosX - Parent.NodePosY
```

X 差值使用了 parent Y。

这非常像 typo/bug。

同时计算：

```text
AttractForce = GetAttractForce(...)
```

后续实际 displacement 又使用 `Distance * Diff`，不是 `AttractForce * Diff`。

R16 不修第三方源码，但明确记录：

> Auto-layout 算法不能因为 demo “看起来能排版”就升级为生产可靠算法；必须单独验证数学正确性和规模。

---

# 25. Slate cached geometry 与 headless compile 边界

`AutoLayoutStrategy` 读：

```text
SEdNode->GetCachedGeometry().GetLocalSize()
```

作为 node width/height。

这对 Editor interactive layout 合理。

但：

```text
CI / commandlet / cook semantic compile
```

不应该需要 Slate node 已经显示过。

因此拆成：

```text
Semantic compile
  headless

Visual layout
  Slate/editor only
```

---

# 26. Graph layout 与 runtime topology 必须独立

GenericGraph layout 开始时调用：

```text
EdGraph->RebuildGenericGraph()
```

这让 visual layout 与 runtime rebuild 发生耦合。

现代化建议：

- layout 读取 normalized authoring topology snapshot；
- semantic compiler 不依赖 layout；
- layout mutation 只改 editor positions；
- NodePos 不进入 business fingerprint，除非 domain 明确需要空间语义。

---

# 27. Runtime pointer / GC 风格的历史性

当前源码大量：

```text
UGenericGraphNode*
UGenericGraphEdge*
```

作为 UPROPERTY。

在现代 UE5 项目里，GC-tracked member 应按当前引擎规范优先评估：

```text
TObjectPtr<T>
```

但是更重要的是：

```text
TObjectPtr solves GC tracking
!= stable identity
```

Save/Network 仍需要 StableId。

---

# 28. GraphTags：机制可留，热路径语义需收敛

`UGenericGraph` 有：

```text
FGameplayTagContainer GraphTags
```

可用于：

- graph classification；
- authoring search/filter；
- domain feature tags。

但是不要：

- 每次 traversal 构造 GameplayTag；
- 用 tag 容器取代 stable GraphDefinitionId；
- 用 tag 表达完整 topology policy。

---

# 29. Copy/Paste 与 Stable ID

GenericGraph Editor node 调：

```text
CreateNewGuid()
```

说明 UE authoring node 本身已有用于编辑器身份的 GUID。

现代 Foundation 应明确：

## Copy/paste node

```text
new semantic NodeStableId
```

## Duplicate graph as new content

```text
new GraphDefinitionId
new node/edge IDs
```

## Explicit migration clone

```text
identity mapping metadata
```

不能靠 UObject duplicate 默认行为决定长期 Save ABI。

---

# 30. Diff/Merge

UE NodeGuid 本来就有 graph diff 用途。

LGF 共用 authoring layer 应进一步：

```text
NodeStableId
EdgeStableId
semantic fields
```

作为 diff anchor。

NodePos 属于 presentation diff，可单独显示。

避免：

```text
array index changed
→ 看起来所有节点都变了
```

---

# 31. Content Migration

长期运营 Graph 内容必须支持：

- node remove；
- edge remove；
- node split；
- node merge；
- graph restructure；
- choice rename；
- transition replacement。

推荐：

```text
GraphDefinitionVersion
NodeRedirects
EdgeRedirects
Tombstones
SplitRules
MergeRules
CheckpointFallbacks
```

这和 R13–R15 的 NodeGuid/ObjectiveGuid/ChoiceId 迁移统一。

---

# 32. Historical fixture

每次 shipping content 变更保留：

```text
OldCompiledGraph
OldSave
ExpectedMigrationResult
```

CI：

```text
load old
→ migrate
→ validate stable references
→ compare expected state
```

不能只测试新资产 compile。

---

# 33. Structured Diagnostics

GenericGraph 当前很多错误以：

```text
LOG_ERROR
FText error message
```

输出。

生产 compiler 需要：

```text
DiagnosticCode
Severity
GraphDefinitionId
NodeStableId?
EdgeStableId?
Message
FixHint
```

原因：

- CI；
- automated fix；
- editor click-to-focus；
- metrics；
- Agent maintenance。

---

# 34. Compiler version / content fingerprint

GenericGraph 当前没有明显：

```text
CompilerVersion
SourceHash
```

现代 artifact header：

```text
GraphDefinitionId
GraphDefinitionVersion
CompilerVersion
CompiledRevision
ContentFingerprint
```

用来处理：

- stale artifact；
- live editing；
- JIP；
- network request revision；
- content hot patch；
- deterministic cook。

---

# 35. Live edit / PIE

设计师在 PIE 保存 Graph：

如果当前 runtime instance active node 使用：

```text
RuntimeIndex=7
```

新 compile 后 index 7 可能已经是别的节点。

所以实例绑定：

```text
CompiledRevision
ContentFingerprint
RuntimeGeneration
```

开发期二选一：

### Freeze

旧实例继续旧 revision。

### Migrate

```text
quiesce
→ map stable IDs
→ stage new state
→ atomic switch
→ generation bump
```

---

# 36. Network revision

对 Quest/Dialogue 等联网 domain：

客户端命令至少带：

```text
InstanceId
ExpectedRevision
StableEdge/Choice/Node ID
RequestId
```

Authority：

```text
revision mismatch
→ reject
→ snapshot/resync
```

不能让旧客户端用 index 继续驱动新 graph。

---

# 37. 为什么不能做 UniversalGraphRuntime

R13 FlowGraph：

- world/quest orchestration；
- latent node lifecycle；
- subgraph；
- deferred transition。

R14 SimpleQuest：

- objective；
- manager/state CQRS；
- outcome/path；
- reward；
- scope。

R15 DlgSystem：

- conversation instance；
- participant；
- choice；
- localization；
- dialogue memory。

GenericGraph 提供的只是底层作者机制。

把这些 runtime 合成一个 `UniversalGraphRuntime` 会丢失 domain ownership。

正确：

```text
Shared editor/compiler foundation
→ typed domain compiled definition
→ independent domain runtime
```

---

# 38. LGF 映射：Quest

共享：

- Node/Edge StableId；
- Schema；
- compile pipeline；
- diagnostics；
- diff/migration。

Quest 保留：

- Objective state；
- Quest Manager sole writer；
- scope；
- reward ledger；
- advancement holds；
- Quest Save schema。

---

# 39. LGF 映射：Dialogue

共享：

- Stable Node/Edge ID；
- graph authoring；
- connection validation；
- compiler；
- migration。

Dialogue 保留：

- ConversationInstance；
- ParticipantRole -> StableAgent；
- Choice revision；
- localization；
- scoped dialogue memory；
- Authority selection protocol。

---

# 40. LGF 映射：AI

StateTree 仍是 high-level decision owner。

不要为了“Graph 统一”把 StateTree runtime 替换为 UniversalGraph executor。

共用 Graph 工具最多用于：

- designer-authored high-level relationships；
- debugging visualization；
- content dependency authoring。

---

# 41. LGF 映射：Ability / Combo

可以用 Graph authoring 描述：

- combo transition；
- input windows；
- stance requirements；
- animation semantic refs。

但是：

```text
GAS remains Authority/execution truth
```

Graph edge 不直接 ApplyDamage。

---

# 42. LGF 映射：Mass

不要为每个 Mass entity 创建 UObject Graph runtime。

Mass 继续：

- data-oriented simulation；
- budgeted decision；
- promotion to full Avatar。

Graph 定义可以作为共享 immutable content，被 processor 以 compact index/ID 读取。

---

# 43. Search / discoverability

GenericGraph README 的简单 custom editor 对早期项目很好。

大型项目需要：

- search by StableId；
- search by node type；
- search by GameplayTag；
- reference browser；
- incoming/outgoing cross-asset refs；
- diff by version；
- migration impact report。

这类工具比“更漂亮的 node”对长期维护更重要。

---

# 44. Large graph scalability

需要关注：

### Context menu

不全局 class scan。

### Validation

支持 dirty-region/incremental，最后仍有 deterministic full compile。

### Layout

有 cancel/time budget。

### Rendering

大图可以：

- LOD；
- virtualization；
- collapsed subgraph；
- category filter。

### Search

用 indexes，不遍历所有 UObject 资产。

---

# 45. Auto-layout 正确定位

R16 不因为 GenericGraph 有两个 layout 算法就把自动布局作为核心能力。

排序：

```text
semantic correctness
> stable identity
> migration
> diagnostics
> authoring ergonomics
> auto-layout aesthetics
```

布局是最后一层。

---

# 46. 测试建议：Graph Foundation

## Identity

- copy node -> new ID；
- rename -> same ID；
- move -> same ID；
- duplicate graph -> all new IDs；
- explicit migration -> declared mappings。

## Compiler

- malformed edge；
- duplicate IDs；
- stale artifact；
- invalid topology；
- failed compile retains previous artifact。

## Cycle

- self loop；
- 2-cycle；
- N-cycle；
- rootless SCC；
- disconnected SCC；
- DAG。

## Parallel Edge

- disallowed domain -> diagnostic；
- allowed domain -> two edge stable IDs survive compile；
- same semantic choice duplicate -> domain diagnostic。

## Headless

- commandlet compile without SGraphNode geometry；
- cook no Editor module dependency。

## Scalability

- 100/1k/10k authoring nodes where applicable；
- context menu latency；
- validation latency；
- layout cancel。

---

# 47. GenericGraph 中具体拒绝照搬的实现

1. Runtime graph pointer topology 作为 identity。
2. `TMap<ChildNode, Edge>` 单 edge 模型。
3. `bCanBeCyclical` 单 bool。
4. runtime root-only traversal 无 visited。
5. tree layout 无 cycle guard。
6. force layout root traversal无 visited。
7. ForceDirected fixed source 的 X/Y coordinate mix 风险。
8. O(N²) repulsion 无规模 gate。
9. context menu `TObjectIterator<UClass>` 全扫描。
10. Save 时就地 Clear/Rebuild。
11. no compiled revision/fingerprint。
12. Runtime Slate dependencies 没有明确 runtime 业务需求。
13. legacy AssetTypeActions 作为新项目唯一入口。
14. authoring/runtime UObject 通过 Rename 复用生命周期。

---

# 48. GenericGraph 中具体值得继续保留的机制

1. Runtime/Editor 拆 module。
2. Graph/Node/Edge 可扩展 class。
3. Graph type 决定 allowed NodeType/EdgeType。
4. Schema 统一连接规则。
5. per-node domain connection hook。
6. cycle check 作为 editor early feedback。
7. optional explicit edge node。
8. rebuild authoring graph into runtime topology。
9. transactional editor nodes。
10. custom asset editor。
11. auto-layout service 抽象。
12. Node-compatible graph type过滤。

---

# 49. R16 对 SkillForge 的正式新增

UE C++：

```text
references/generic-graph-authoring-patterns.md
```

新增 behavior：

```text
CPP-102 .. CPP-109
```

覆盖：

- freshness / modern editor API；
- compile artifact；
- stable identity；
- topology schema；
- cycle/rootless SCC；
- parallel edge；
- canonical topology；
- copy/diff/migration；
- editor scalability。

LGF：

```text
references/graph-authoring-foundation.md
```

新增：

```text
LGF-64 .. LGF-68
```

覆盖：

- shared authoring vs shared runtime；
- content migration；
- domain topology policy；
- Editor/Runtime module boundary；
- live revision safety。

---

# 50. 与前几轮的直接组合

## R13 FlowGraph

R13 已解决：

```text
runtime graph lifecycle
subgraph
deferred transition
save ABI
```

R16 下沉：

```text
generic compiler/stable edge/topology/editor foundation
```

## R14 SimpleQuest

R14 已解决：

```text
Quest domain model
Objective GUID
Manager/State CQRS
```

R16 不取代 Quest runtime，只提供 authoring infra。

## R15 DlgSystem

R15 已解决：

```text
Conversation participant
Node/Choice identity
Localization
network revision
```

R16 补上：

- EdgeStableId；
- parallel edge；
- compiler foundation；
- graph diff/migration；
- modern editor boundary。

---

# 51. 用户项目的具体价值

用户的 LGF 长期会有：

- Quest；
- Dialogue；
- AI；
- Combo/Ability；
- 世界事件；
- 变身/坐骑/NPC 互动。

如果每个业务独立做一套：

```text
GraphEditor
Stable ID
Compiler
Diff
Search
Migration
```

维护成本会越来越高。

R16 的推荐是只共享这些工具层。

而以下坚决不共用：

```text
Quest progression truth
Dialogue conversation truth
GAS combat truth
AI decision truth
```

这样既能减少重复，又不会产生新的中心化巨石系统。

---

# 52. 对“旧项目技术一直在革新”的本轮回答

GenericGraph 正是一个非常合适的反例。

它：

- 仍然高星；
- 仍未 archived；
- 有 UE5 compatibility；
- 架构文章仍常被引用。

但固定源码：

- 只明确到 UE5.1；
- Asset system 是 legacy route；
- Graph runtime stable ID 不足；
- cycle support 不完整；
- layout 有算法风险；
- module dependency 偏宽；
- compile artifact 没有现代 revision/fingerprint/staging。

所以以后 GitHub 学习必须判断：

```text
Repository freshness
API freshness
Algorithm correctness
Production completeness
Target-project fit
```

五层，不是只看更新时间。

---

# 53. R16 最终迁移决策矩阵

| GenericGraph 机制 | LGF 决策 | 原因 |
|---|---|---|
| Runtime / Editor modules | Adapt | 方向正确，依赖需现代化 |
| Extensible Node/Edge | Adapt | 适合 authoring，补 stable IDs |
| Explicit edge object | Keep concept | Dialogue/Combo 很需要 |
| Child->single Edge map | Reject | 不支持 parallel semantic edge |
| RootNodes cache | Keep as derived | general graph不能当 canonical |
| bCanBeCyclical | Reject as sole policy | domain topology更复杂 |
| Schema CanCreateConnection | Keep | 仅 UX early validation |
| Node connection hooks | Keep | supplemental domain policy |
| Runtime root BFS | Reject | cycle/rootless SCC 不安全 |
| Rebuild on save | Adapt | 改 staged compiler + atomic publish |
| UObject Rename editor→runtime | Reject as foundation | authoring/runtime ownership耦合 |
| TObjectIterator context menu | Reject for scale | registry/cache |
| Tree layout | Optional | DAG-only + budget |
| Force-directed layout | Optional/Rewrite | O(N²)+源码风险 |
| AssetTypeActions | Compatibility only | 目标版本先评估 UAssetDefinition |
| Slate cached geometry | Layout only | headless compiler不能依赖 |

---

# 54. 未验证项

本轮没有执行：

- GenericGraph UE5.7 build；
- GenericGraph UE5.8 build；
- UHT；
- Editor launch；
- graph create/edit/save；
- copy/paste；
- cycle graph runtime hang reproduction；
- auto-layout crash/hang reproduction；
- 1k/10k node performance；
- cook/packaged build；
- Dedicated Server。

因此：

```text
source-level architecture distillation
!=
GenericGraph target-engine runtime verification
```

---

# 55. 最终结论

GenericGraph 不是 R16 要引入的依赖，而是一块非常好的“历史剖面”。

它展示了一个 UE 自定义 Graph Framework 最基础的骨架：

```text
Custom Asset
UEdGraph
Schema
Node
Edge
Runtime topology
Editor
Layout
```

而 R16 在这个骨架上补齐今天长期项目必须拥有的部分：

```text
Stable Node/Edge IDs
Canonical records
Parallel edge
Per-domain topology policy
Cycle/SCC correctness
Staged compiler
Structured diagnostics
Compiled revision/fingerprint
Last-known-good
Content migration
Modern AssetDefinition adapter
Headless compile
Large graph scalability
Live revision fence
```

所以对 SkillForge/LGF 的最终一句话是：

> **GenericGraph 的价值是帮助我们建立现代 Graph Authoring Foundation，而不是成为 Universal Gameplay Runtime。**

