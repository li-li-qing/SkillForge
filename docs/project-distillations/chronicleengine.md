# TodayYueC/ChronicleEngine — R17 Narrative / Dialogue / Event Framework 源码蒸馏

日期：2026-09-15  
SkillForge 基线：用户上传的 R16 ZIP（SHA-256 `519de24eb226d4b555b643e63f9135d36585a94cad38924496f2d49c2cc936e9`）  
研究对象：`TodayYueC/ChronicleEngine`

## 0. 结论先行

R17 的最终技术时效性分类是：**Stable-but-old**。

这里的 “old” 指 **目标引擎采用边界**，不是仓库年代。ChronicleEngine 的源码在 2026 年仍有更新，而且包含不少值得吸收的现代工程机制；但其主工程仍固定 UE 5.3，HEAD 插件仍是 `0.12.0-dev` Beta，UE5.7 只有作者侧 smoke 证据，Editor 仍主动使用 `FAssetTypeActions_Base`，并且 active runtime 没有任何 Authority/RPC/replication/JIP 路径。对 UE5.7/5.8 Production Framework 来说，它不能被当作“当前 API + 已验证多人架构”的模板。

这轮最重要的产出不是再造一套 Narrative Skill，而是对 R13～R16 做三处精炼：

1. **修正 R16 的过度绝对化**：Graph Authoring 与 Runtime 必须职责分离，但不等于永远要序列化两份 Graph。若 authoring schema 与 runtime semantic definition 同构，可以让 canonical semantic definition 成为唯一持久化真值，`UEdGraph` 只是 transient editor projection。
2. **强化 Dialogue Save ABI**：只保存 Tree/Node/Line cursor 不足以恢复 nested SubDialogue、call/return、latent event。Continuation frames 与 pending await 都属于会决定下一次 transition 的 canonical state。
3. **新增 async correlation 与 cache correctness 合同**：GameplayTag 是 event type，不是一次异步执行的 identity；compiled AST cache 与 mutable result cache 也不能混为一谈，外部可变依赖必须有 revision/invalidation。

ChronicleEngine 同时再次验证了之前已经建立、无需重复新增的结论：stable Node/Choice/Edge identity、Dialogue/Quest truth 分离、Save schema/content migration、Authority/JIP、Localization identity、Runtime/Editor split、无界 traversal 禁止等仍然成立。

---

## 1. 固定证据

### 1.1 Repository snapshot

- repository：`https://github.com/TodayYueC/ChronicleEngine`
- default branch：`main`
- exact commit：`b2fb37b14b7537c30d6ebf16cf612671bd0286e9`
- commit date：2026-04-30 11:34:37 UTC
- commit message：`Add step-by-step usage tutorial`
- license：MIT
- stars / forks：研究时快照约 1 / 0；仅作为社区规模信息，不作为质量证明
- repository archived：否
- 可见 branch：仅 `main`
- tag：`v0.5.0`
- public release：`v0.5.0` prerelease，2026-04-26

固定 commit URL：

`https://github.com/TodayYueC/ChronicleEngine/commit/b2fb37b14b7537c30d6ebf16cf612671bd0286e9`

### 1.2 Engine / plugin version evidence

`ChronicleHost.uproject`：

```text
EngineAssociation = 5.3
```

`Plugins/ChronicleEngine/ChronicleEngine.uplugin`：

```text
Version = 12
VersionName = 0.12.0-dev
IsBetaVersion = true
```

README/Release 文档描述主基线 UE5.3，并记录 UE5.7 editor build smoke；这些是作者验证证据，不等于本轮在 UE5.7/5.8 重新编译通过。

`v0.5.0` release 与当前 HEAD 不是同一代码版本。release 的 “UE5.7 smoke / BuildPlugin passed” 不能替 `0.12.0-dev` HEAD 背书。

### 1.3 当前 Epic API 校准

本轮对目标 UE5.7/5.8 的技术时效性使用当前 Epic UE5.8 文档做校准：

- `UAssetDefinition`：官方明确说明 Asset Definitions 是 `FAssetTypeActions_Base` / Asset Actions 体系的替代方案；新项目不应因为旧类仍存在就默认继续使用旧入口。  
  `https://dev.epicgames.com/documentation/unreal-engine/API/Editor/AssetDefinition/UAssetDefinition`
- UObject replication：当前官方文档区分 legacy `ReplicateSubobjects` 与 registered subobject list，并说明 Iris 只支持 registered subobject list。  
  `https://dev.epicgames.com/documentation/unreal-engine/replicating-uobjects-in-unreal-engine`
- Text Localization：`FText` 的本地化 identity 由 Namespace + Key 构成，Source String 参与 stale translation 校验；原始字符串导入与 localization identity 必须分离。  
  `https://dev.epicgames.com/documentation/unreal-engine/text-localization-in-unreal-engine`

因此本轮遵守：**API 仍存在 ≠ 目标版本现代默认；README 说支持 ≠ active code 已验证。**

---

## 2. Source Map

### 2.1 Plugin modules

ChronicleEngine 当前只有三类 module：

```text
ChronicleEngine           Runtime
ChronicleEngineEditor     Editor
ChronicleEngineTests      Editor tests
```

没有独立 Developer / UncookedOnly module。

### 2.2 Runtime module

核心目录：

```text
Public/Core
  ChronicleTypes.h

Public/Data
  DialogueDatabase.h
  DialogueTree.h
  DialogueTrigger.h
  SpeakerProfile.h

Public/Runtime
  ChronicleDialogueSubsystem.h
  DialogueConditionEvaluator.h
  DialogueRunner.h
  DialogueTextParser.h
  DialogueTriggerManager.h
  VariableBank.h

Public/Presentation
  ChronicleDialogueChoiceButton.h
  ChronicleDialogueCueDirector.h
  ChronicleDialogueDefaultWidget.h
  ChronicleDialoguePresentationController.h
  ChronicleDialogueWidget.h
  DialoguePresenter.h

Public/Samples
  ChronicleDialogueDemoActor.h
  ChronicleExampleQuestAdapter.h
```

Runtime `Build.cs` public dependencies：Core/CoreUObject/Engine/GameplayTags/UMG；private 仍依赖 Slate/SlateCore。

这意味着 Domain runtime 与默认 Presentation 仍处在同一个 Runtime module。对 Dedicated Server 或大型 Foundation 来说，这不是最干净的模块边界；可参考机制，但不应照搬依赖面。

### 2.3 Editor module

主要能力：

```text
Asset/
  ChronicleAssetTypeActions
  ChronicleDialogueAuditLibrary
  ChronicleDialogueJsonLibrary
  DialogueAssetFactories
  DialogueImporterBase

Editor/
  ChronicleDialogueEditorLibrary
  ChronicleDialogueGraph
  ChronicleDialogueGraphNode
  ChronicleDialogueGraphSchema
  ChronicleDialogueNodeDetails
  DialogueTreeEditorToolkit
  SDialogueTreeEditor
```

依赖包括 AssetTools、GraphEditor、Json、PropertyEditor、Slate、UnrealEd 等，Editor/Runtime 大方向分离正确。

### 2.4 Tests

测试源码分成：

- `ChronicleRuntimeTests.cpp`
- `ChroniclePipelineTests.cpp`
- `ChronicleEditorWorkflowTests.cpp`

可见测试覆盖变量、condition、linear dialogue、choice、random、jump、sub-dialogue、inline tags、pipeline/editor workflow 等；测试使用 EditorContext automation。未发现 Dedicated/JIP/network test suite。

本轮**没有执行 Chronicle 自己的 UE automation tests**，所以报告只把“测试源码存在”和“作者声称通过”作为两层不同证据。

---

## 3. Ownership 与 lifecycle

`UChronicleDialogueSubsystem` 是 `UGameInstanceSubsystem`，持有：

```text
UDialogueRunner
UChronicleDialoguePresentationController
UDialogueTriggerManager
```

Runner 内部再持有 `UVariableBank`、当前 `UDialogueTree`、history、memento、sub-dialogue return stack、condition result cache 与 runtime lookup。

优点：

- Runtime state 没写回 DataAsset；
- `TObjectPtr`/UPROPERTY ownership 基本符合现代 UObject 生命周期；
- `StartDialogue()` 显式初始化运行时结构；
- Tree 切换会重建 lookup。

边界：

- 单 `UGameInstanceSubsystem` + 单 Runner 更像 local/single-session orchestration，不是多人世界里可并发多个 authoritative ConversationInstance 的最终模型；
- 没有 Server owner / PlayerState / ActorComponent / replicated subobject 设计；
- 因此不能把“Subsystem ownership 清楚”外推为“多人 Conversation ownership 已解决”。

---

## 4. Graph data model：优点与缺口同时存在

### 4.1 Stable identity 已做到一半

`UDialogueTree` / `FDialogueNode` 有：

```text
TreeGuid
NodeGuid
```

但：

- `FDialogueChoice` 没有 stable ChoiceId；
- `FDialogueEdge` 没有 EdgeGuid；
- edge/choice 仍依赖 slot/index；
- `ResolveEntryNode()` 还允许通过 `LineID` 找 entry，导致 Line identity 与 entrypoint identity 混用。

这再次证明 R15/R16 的规则没有过度设计：**Node 有 GUID 不等于整个 durable graph identity 已完成。**

### 4.2 Canonical semantic asset + transient UEdGraph 是真正值得吸收的新点

Chronicle 的 `UChronicleDialogueGraph` 并不是第二份持久化 topology truth。

编辑器打开时：

```text
UDialogueTree semantic data
        ↓
RebuildFromDialogueTree()
        ↓
transient UEdGraph / UEdGraphNode / pins
```

Editor mutation 再通过 `UChronicleDialogueEditorLibrary` 修改 `UDialogueTree`，然后重建投影。

这是 R17 对 R16 的主要纠错：

```text
“Authoring / Runtime 必须分离”
        ≠
“所有 Domain 都必须保存 AuthoringGraph + CompiledGraph 两份资产”
```

如果 authored semantic model 已接近 runtime definition，可以只有一份 canonical semantic definition，并将 `UEdGraph` 作为 transient projection。

但 Chronicle 当前也暴露了这个模式的前提：

- durable Node/Edge/Choice ID 必须完整；
- whole-definition compiler/validator 必须强；
- editor-only state 必须真正 editor-only；
- content version/migration 必须存在；
- runtime derived lookup 必须可重建；
- cook/package 必须验证 Editor metadata 不进入 Shipping truth。

### 4.3 Runtime/PostLoad 随机补 GUID 是 durable identity 反例

R17.1 复查 `UDialogueTree::PostLoad()` / `EnsureStableGuids()` 后补到一个此前漏掉的 Production 风险：当 `TreeGuid` 或 `NodeGuid` 无效时，active code 会直接 `FGuid::NewGuid()`。

这对尚未发布的临时 authoring 资产很方便，但一旦 ID 被 Save / Network / Analytics / migration 引用，就不能把 Runtime/PostLoad 当作身份创建阶段。否则同一个缺 ID 的内容可以在两次独立加载、不同机器或不同 Cook 中获得不同 durable identity，旧 Save/远端引用会静默失联。

SkillForge R17.1 因此补充规则：

```text
new semantic entity / duplicate-as-new-content -> controlled authoring stage may allocate a new ID
rename / move / reload same shipped entity      -> preserve durable ID
legacy missing ID                               -> editor/commandlet/deterministic migration + resave
Shipping/Dedicated unresolved durable ID         -> validation/recovery failure, never random repair
```

需要历史 fixture 证明 deterministic migration，而不是用 `PostLoad NewGuid()` 把错误隐藏掉。

### 4.4 Editor metadata 混入 Runtime DataAsset

当前 `UDialogueTree` 直接带：

- `FVector2D Position`（node 数据里）；
- breakpoint/editor state；
- soft-lock metadata。

这些字段进入 Runtime DataAsset，并没有形成理想的 `WITH_EDITORONLY_DATA`/Editor sidecar/UncookedOnly 隔离。

所以 Chronicle 的 “projection-first” 思路值得吸收，**具体数据边界不能照搬**。

---

## 5. Graph validation / compiler 边界

`UDialogueTree::IsValidTree()` 目前主要验证：

- Tree/Root GUID 合法；
- root node 存在；
- edge endpoints 存在。

没有看到完整生产级校验：

- duplicate NodeGuid；
- duplicate/ambiguous Edge/Choice identity；
- node-type cardinality；
- unreachable/orphan policy；
- domain-specific cycle policy；
- content version/compiler fingerprint；
- redirect/tombstone migration。

Editor library 有很多方便的 mutation、audit、JSON/CSV import/export，但还不能代替 R16 建立的 whole-definition compiler gate。

因此 R16 的 Graph compiler / diagnostics / migration 规则继续保留；R17 只修正“必须有两份持久化 Graph”这一形态假设。

---

## 6. Runtime traversal 与 lookup：明确可吸收

### 6.1 Traversal budget

`UDialogueRunner::ProcessCurrentNode()` 使用固定最大 traversal steps（1024）来避免错误图导致无限同步 traversal。

这是一条很实际的 Production pattern：

```text
cycle support / malformed content / jump loop
→ runtime traversal 必须有 hard termination budget
```

它验证 R16 的 general-graph bounded traversal 规则。

### 6.2 Runtime lookup

Runner 会建立：

- NodeGuid -> index lookup；
- NodeGuid -> outgoing edge indices；
- outgoing edge 预排序。

Tree switch 时重新 build，而不是每次 transition 线性扫全部 Nodes/Edges。

这部分值得吸收：**canonical semantic records + rebuildable runtime cache**。

### 6.3 Condition parser cache

Condition evaluator 把 expression parse/compile 结果缓存成 AST，并有容量保护。这也是正确方向：避免每次判断重复 tokenize/parse。

但它同时引出了本轮一个新的 cache correctness 问题，见第 9 节。

---

## 7. Save ABI：README “Complete” 不能直接接受

作者文档/PRD 把 Runtime/Save/Rollback 标为 Complete，并有相关 automation test 源码；但 active `FDialogueSaveData` / `LoadState()` 只能证明一部分 cursor/state snapshot。

### 7.1 当前 SaveData 有什么

可见字段包含：

- `CurrentTreeGuid`
- `CurrentNodeGuid`
- `CurrentLineIndex`
- Runner state
- global/local variables
- history
- seen hashes

### 7.2 当前 SaveData 缺什么

Runner 实际还有会影响下一步 transition 的隐藏状态：

- `SubDialogueReturnStack`
- waiting event identity/state
- presented choice slot mapping
- runtime lookup/cache
- definition/content/compiler version/fingerprint
- participant bindings
- pending external semantic command/correlation

而 `LoadState()` 没有根据 `CurrentTreeGuid` 自动 resolve/reassign 当前 tree，也没有重建 runtime lookup，更没有恢复 nested return stack。

因此：

```text
Save cursor != Save continuation
```

如果在 SubDialogue 内、latent async event 内、或隐藏 sequence/call stack 中存档，只靠 CurrentTree/Node/Line 不足以证明恢复后下一步语义一致。

### 7.3 Rollback 的边界

`PerformRollback()` 使用 memento `FDialogueSaveData` 恢复，所以继承同样的 continuation 缺口。

而且已经发出的 Quest/Inventory/GAS/World side effect 不会因为 runner memento 恢复而自动撤销。

所以 Chronicle 的 rollback 最多可视为 **dialogue-local semantic/presentation rewind mechanism**，不能外推成跨 Domain transactional rollback。

R17 因此正式加入：ContinuationFrames + PendingAwait 属于 Save ABI。

### 7.4 SubDialogue locals 也是 continuation/call-frame state

R17.1 继续反查 `UVariableBank` 与 SubDialogue 路径发现：VariableBank 只有一份 `LocalVariables` map，初始化 local definitions 时会 `Reset()`；而 SubDialogue return frame 主要保存 return tree/node，没有独立 child/parent local scope frame。

Production 语义应更像函数调用栈：

```text
Parent Definition + Parent local scope
  push
Child Definition + Child local scope
  push ...
return/cancel -> pop/merge/discard by explicit policy
```

父/子可以有同名 local，但 child shadow 不能覆盖 parent truth。Save/JIP 需要序列化 active call/scope stack 的 stable Definition/Node/Transition IDs、scope version 与恢复所需 local values；Load 先逐层 resolve/migrate，再恢复 top frame。

Quest/Inventory/GAS/WorldState 仍是外域 truth，不应为了方便被拷进 Dialogue locals。Avatar replacement 只重绑 presentation/AvatarGeneration，不销毁 Conversation scope stack。

---

## 8. Async Event：Tag 不是 Operation Identity

当前 async event 记录 `WaitingEventTag`，完成 API 以 `NotifyEventComplete(EventTag)` 继续。

风险非常具体：

1. node A 等待 `Chronicle.Event.X`；
2. A 被取消/切树；
3. node B 或另一会话再次等待同一 tag；
4. A 的旧 callback 晚到；
5. 仅比较 tag 可能错误推进 B。

Production 需要：

```text
ConversationInstanceId
AwaitId / ExecutionToken
Source Node/Transition semantic ID
Expected Revision / Generation
```

完成回调必须匹配当前 active wait token 后才能推进。旧 Avatar generation、旧会话、duplicate、cancelled completion 均应 no-op/diagnostic。

这对 LGF 特别重要，因为未来 Dialogue 会跨 Quest/GAS/Inventory/AI 发 typed command，也会遇到变身/骑乘导致 Avatar generation 变化。

---

## 9. Condition cache：解析缓存安全，不代表结果缓存安全

这是 ChronicleEngine 带来的另一个真正新问题。

### 9.1 当前机制

- expression -> compiled AST：有 process cache；
- runner 还会 expression -> bool result cache；
- runner 自己 `SetVariable()` 时清 result cache；
- `UVariableBank` 同时支持 external getter bindings。

### 9.2 隐患

外部 getter 读到的 Quest/Inventory/GAS/WorldState 可以在**没有调用 runner SetVariable** 的情况下改变。

因此：

```text
AST 没变       -> compiled-expression cache 仍然正确
外部事实变了    -> 上一次 bool evaluation result 已经过期
```

把这两种 cache 当成同一种生命周期会产生 stale choice/condition。

### 9.3 R17 规则

- compiled AST/bytecode 可以按 definition/expression source version 缓存；
- evaluation result 只有在 dependency revisions/generations 可观察时才缓存；
- 或由 Quest/Inventory/GAS/WorldState change subscription 精确 invalidation；
- 没有 revision contract 的 external getter，在 interaction/selection 等明确边界重新 evaluate；
- client result 只做 UI advisory，Authority choice 仍按 canonical current revisions 重验。

这能同时守住正确性和性能，不需要退回“每 Tick 全量重算”。

---

## 10. Asset loading：Soft pointer 不等于 async pipeline

active runtime 中存在 `LoadSynchronous()`：

- `DialogueRunner` resolve target SubDialogue tree；
- `DialogueTriggerManager` resolve target tree；
- `DialogueDatabase` resolve culture/voice DataTable。

因此不能因为数据字段使用 `TSoftObjectPtr` 就写成“异步加载架构完成”。

对 LGF：

- 对话定义/voice/cinematic 等依赖按交互边界或 preload plan 异步准备；
- graph traversal/choice evaluation/高频 UI refresh 不允许突然 sync load；
- target tree 不 ready 时进入明确 `WaitingForDependency`/preload 状态，而不是 traversal 内阻塞。

这条已有 SkillForge 性能规则已经覆盖，本轮不重复创建新 Behavior Eval。

---

## 11. Network / Authority / JIP：属于缺失证据，不是“简单功能”

对固定 HEAD 搜索：

- `UPROPERTY(Replicated`：无结果；
- `UFUNCTION(Server`：无结果；
- `OnRep_`：无结果；
- `HasAuthority`：无结果；
- `FFastArraySerializer`：无结果。

也没有发现 registered subobject / replicated conversation read-model / revisioned choice request / JIP snapshot 路径。

因此 ChronicleEngine 不能用于反驳 R15 的 Authority/JIP 合同，也不能因为 `UGameInstanceSubsystem` 能跑对话就称多人完成。

LGF 保持：

```text
Server/Authority ConversationInstance = canonical truth
AutonomousProxy / SimulatedProxy = projected read model / presentation
Choice request = InstanceId + ExpectedRevision + StableChoiceId
JIP/reconnect = snapshot first
```

重要属性若做 UE replication，仍需 target-version 的 replicated property/OnRep/GetLifetimeReplicatedProps 或 registered replicated subobject 方案；Chronicle 没提供这层证据。

---

## 12. Localization：FText 是正确起点，identity pipeline 仍不完整

Chronicle 广泛使用 `FText`，并提供 localization CSV import/export，这是好方向。

但 active import 中可以看到翻译/源字符串被 `FText::FromString(...)` 重新赋回 Line.Text，而本轮没有发现 `FText::ChangeKey` 或等价 deterministic namespace/key re-key pipeline。

Epic 当前文档明确：Localizable `FText` 的 identity 是 Namespace + Key，Source String 不是业务 semantic identity。

因此：

- `LineID` / `NodeGuid` / `ChoiceId` 继续与 localization namespace/key 分开；
- CSV roundtrip 必须保留或确定性重建 namespace/key；
- 不把当前英文/中文 rendered text 当 Save/Network/Analytics identity；
- 需要加入 localization identity oracle，而不是只验证翻译字符串导入成功。

这条 R15 已经覆盖，所以 R17 只把 Chronicle 作为新的反例验证，不新增重复 case。

---

## 13. Editor API freshness

ChronicleEngineEditor active 使用 `FAssetTypeActions_Base`。

这个类在 UE5.8 仍存在，所以不能说“API 已删除”；但 Epic 当前 `UAssetDefinition` 文档明确把 Asset Definitions 定义为 Asset Actions system 的替代方案，并解释了 Content Browser 右键动作避免加载资产等现代目标。

因此 R17 分类采用：

```text
FAssetTypeActions_Base exists
!=
modern default for a new UE5.7/5.8 framework
```

LGF 新 Foundation 继续优先研究 `UAssetDefinition` + ToolMenus，legacy AssetTypeActions 只作为兼容入口。

---

## 14. Tests / docs / “Complete” 的证据层级

ChronicleEngine 的文档质量比很多小型 GitHub 项目好：有 Roadmap、PRD completion matrix、Release notes、Usage tutorial、validation script 和 automation test 源码。

这是加分项，但 SkillForge 仍按证据层级拆开：

```text
README/PRD says Complete
!= class exists
!= automation test exists
!= test executed on fixed HEAD
!= UE5.7/5.8 target build passed now
!= Dedicated/JIP/production verified
```

本轮看到 Save/rollback active path 的 continuation 缺口，正好证明为什么不能只复制 PRD “Complete” 标签。

---

## 15. 可吸收机制

1. **Canonical semantic definition + transient UEdGraph projection**：适用于 schema 同构的 Domain，可减少双 truth。
2. **Runtime Node/Edge lookup cache**：canonical records + rebuildable cache，而不是每 transition 全扫。
3. **Hard traversal budget**：错误图/循环图不会把 GameThread 卡死。
4. **Compiled condition AST cache**：缓存 immutable parse result，避免重复 tokenize/parse。
5. **Editor mutation transaction**：`Modify()` + MarkPackageDirty + 重建 projection，Undo ownership 清晰。
6. **Audit / JSON / CSV pipeline**：作者工具应有 batch audit/export/import，而不是只靠可视编辑器。
7. **DataAsset semantic runtime**：运行逻辑不依赖 Editor Graph objects。
8. **Runtime/Editor modules 已基本分开**：方向正确，虽然 Presentation 仍混在 runtime module。

---

## 16. 明确不能照搬

1. 只给 Tree/Node stable GUID，Choice/Edge 仍靠 slot/index。
2. `FDialogueSaveData` 当完整 continuation save。
3. `WaitingEventTag` 作为唯一 async wait identity。
4. external getter 存在时把最终 condition bool 永久按 expression 缓存。
5. traversal 内 `LoadSynchronous()` TargetTree。
6. Runtime DataAsset 直接携带 NodePos/breakpoint/soft lock 等 editor-only metadata。
7. `FAssetTypeActions_Base` 当 UE5.7/5.8 新 Foundation 的现代默认模板。
8. GameInstance 单 Runner 外推成多人 authoritative conversation owner。
9. “rollback” 外推成跨 Quest/Inventory/GAS 的事务回滚。
10. README/PRD “Complete” 外推成 Production verified。
11. localization CSV 只回写字符串，却没有稳定 namespace/key oracle。
12. runtime module 把 UMG/Slate presentation 与 domain core 固定绑在一起。
13. `PostLoad()` / Runtime load 发现 durable GUID 缺失就 `NewGuid()` 静默修复。
14. SubDialogue 共用一份扁平 `LocalVariables`，return frame 不保存独立 local scope/call frame。

---

## 17. 与 R13～R16 的直接碰撞

| 已有结论 | Chronicle 证据 | R17 处理 |
|---|---|---|
| R13 Flow latent state 必须可恢复/清理 | async Event + SubDialogue 真实存在隐藏 continuation | **强化**：ContinuationFrames/PendingAwait 纳入 Save ABI |
| R14 Quest 拥有 Quest truth | Chronicle 只有 Sample Quest Adapter，没有 Quest domain runtime | **保持**：不能把 Dialogue variables 变成 Quest truth |
| R15 stable Choice/Participant/Authority/JIP | Chronicle Choice 无 stable ID，且无 replication | **再次验证**，不重复新增已有规则 |
| R15 Save schema/content migration | Chronicle Save 无 content/schema fingerprint | **再次验证** |
| R15 localization semantic identity | Chronicle `FText` 正确，但 import identity 不充分 | **再次验证** |
| R16 Authoring -> Compiler -> Runtime artifact | Chronicle transient UEdGraph 直接投影 canonical semantic asset | **修正过度复杂**：职责分离不强制 two persisted graphs |
| R16 canonical data + derived cache | Runner build Node/Edge lookup | **验证** |
| R16 bounded traversal | 1024-step budget | **验证** |
| R16 stable Edge identity | Chronicle Edge 无 ID | **验证必要性** |
| R16/R17 durable stable identity | `PostLoad()` 缺 ID 时随机 `NewGuid()` | **强化**：Runtime load 不得随机修 durable ID |
| R17 continuation frames | SubDialogue return stack 没有 per-call local scope | **强化**：active local scope stack 纳入 Save/JIP |

---

## 18. 本轮真正新增的 SkillForge 行为

### UE C++

- `CPP-110`：transient editor projection / single semantic truth contract
- `CPP-111`：Dialogue continuation stack + pending await Save ABI
- `CPP-112`：async completion AwaitId / execution generation correlation
- `CPP-113`：compiled-expression cache vs dependency-revisioned result cache
- `CPP-114`：durable semantic ID 不得在 Runtime/PostLoad 随机补造
- `CPP-115`：nested Dialogue local scope/call frame Save ABI

### LGF

- `LGF-69`：Graph Foundation 允许 projection-first，不强制两份持久化 Graph
- `LGF-70`：LGF Conversation continuation + Await token + Avatar generation fence
- `LGF-71`：LGF Dialogue 条件使用 revisioned read model 做 result-cache invalidation
- `LGF-72`：LGF Conversation nested local scope stack + Save/JIP/Avatar rebind contract

没有为了 Chronicle 名字单独建立新 Skill，也没有复制已有 stable identity/Authority/localization 规则。

---

## 19. 对 LGameplayFramework 的直接建议

### 19.1 Graph Foundation

LGF Foundation 应支持两种 Domain adapter：

```text
CompiledAuthoringAdapter
CanonicalProjectionAdapter
```

共同合同仍只有：Stable IDs、DomainSchema、validation/compiler、diagnostics、migration、search/diff、layout、revision。

Dialogue 若 semantic definition 与 runtime 足够同构，可优先 projection-first；Quest/复杂 World Flow 如果需要 flatten/lowering/优化，则继续独立 compiled artifact。

### 19.2 Conversation Save

`FConversationSaveState` 需要明确：

```text
ConversationInstanceId
DialogueDefinitionId + ContentFingerprint
CurrentNodeId + SubstateId
ContinuationFrames[]
  per-frame LocalScopeFrame / local semantic values + scope version
PendingAwait?
Participant StableAgent bindings
Revision / Generation
semantic memory
```

Avatar/Pawn/Mover/AnimInstance 永远不是 durable participant identity。

### 19.3 Async domain command

Quest/GAS/Inventory/AI command 都携带：

```text
ConversationInstanceId
SemanticCommandId
AwaitId
ExpectedRevision
Avatar/ExecutionGeneration (when relevant)
```

Authority owner负责校验，Proxy 只做预测/展示，不允许 callback 自行推进 canonical conversation。

### 19.4 Conditions

Quest/Inventory/GAS/WorldState 暴露 compact revisioned read model；Dialogue compiler可预计算 dependency set。条件结果缓存绑定 dependency revision，而不是绑定“runner 什么时候 SetVariable”。

### 19.5 Performance

继续禁止：

- Tick/world scan；
- traversal 内 `LoadSynchronous()`；
- 每次 condition 重 tokenization / GameplayTag parsing；
- 无界 graph traversal；
- 每次 UI refresh 全量重建所有 condition。

推荐：preload、compiled AST、incremental invalidation、Node/Edge lookup、bounded traversal，并用 Unreal Insights 验证实际收益。

---

## 20. 本轮未验证

本轮没有执行：

- ChronicleEngine UE5.3 UBT；
- ChronicleEngine UE5.7 UBT；
- ChronicleEngine UE5.8 UBT；
- UHT / Editor launch；
- Chronicle automation tests；
- PIE；
- Dedicated Server；
- Listen/Remote multiplayer；
- JIP / reconnect / packet loss；
- Save during nested SubDialogue 的真实 runtime reproduction；
- late async callback race reproduction；
- localization gather/cook；
- BuildPlugin；
- 100/1k/10k-node benchmark；
- LGF integration。

因此本轮结论是 **固定源码 + 当前 Engine 文档 + Skill contract distillation**，不是 ChronicleEngine 在 UE5.7/5.8 的 production certification。

---

## 21. R17 最终决策

ChronicleEngine 值得保留的不是“完整 Narrative Framework 可直接拿来用”，而是几个很实际的设计提示：

- Graph Editor 可以是 canonical semantic data 的 transient projection；
- runtime cache 应从 canonical data 重建；
- traversal 必须有硬预算；
- AST cache 与 result cache 生命周期不同；
- nested/latent dialogue 的 Save 本质是 continuation serialization；
- async completion 必须有 operation identity；
- durable ID 不能在 Runtime/PostLoad 通过随机 `NewGuid()` 静默修复；
- nested dialogue 的 local memory 是 call/scope frame 状态，必须随 continuation Save/JIP；
- docs/test claims 必须继续与 active code path 分层验证。

它没有推翻 SkillForge 的 Quest/Dialogue/Authority 边界；相反，它让这些边界变得更精确，同时删掉了 R16 中一个不必要的“所有 Graph 都必须双持久化资产”假设。
