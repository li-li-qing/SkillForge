# NotYetGames/DlgSystem 源码蒸馏（R15）

> 目标：从当前 DlgSystem 18.0.8 中提取 Dialogue authoring、participant adapter、Node GUID、Localization、Resume、IO tooling 的成熟机制，同时把其全局 Memory、index choice、部分复制能力放回正确的风险位置，再转换为适合 LGF Multiplayer ARPG 的 Conversation Authority 合同。

## 1. 固定研究快照

- 仓库：`NotYetGames/DlgSystem`
- 默认分支：`master`
- 固定 commit：`d705231216bd64558d437b87a57928689b1e7fef`
- commit 日期：2026-06-22
- commit message：`Increase version number to 18.0.8`
- 对应 tree：`cac042505f4d32364bfadad2a15a2b8ddfa1f7e3`
- Plugin：18.0.8
- License：MIT
- README 支持：UE 5.6 / 5.7 / 5.8
- 研究时仓库：638 stars / 104 forks，非 archived。

近期相邻提交明确包含：

- UE 5.8 support；
- UE 5.8 warning compatibility；
- UE 5.7 string-property include compatibility。

因此本轮技术时效性结论是：**Current-to-target（适用于 UE5.7 架构研究）**。

这不代表它的 multiplayer dialogue 已经达到 LGF 所需的 Authority/JIP 生产标准。

## 2. 模块边界

插件当前只有两个核心模块：

```text
DlgSystem
  Type=Runtime
  LoadingPhase=PreDefault

DlgSystemEditor
  Type=UncookedOnly
  LoadingPhase=PreDefault
```

Runtime 主要包括：

```text
Dialogue / Context / Manager
Participant Interface/Data
Node / Edge
Condition / Event
Memory
Localization / TextArgument
IO JSON/Config
GameplayDebugger
Runtime tests
```

Editor 主要包括：

```text
Dialogue Graph / Schema
DlgCompiler
Graph Nodes / Slate
Details customizations
K2 helper nodes
Search / Browser
Human-readable/Twine Commandlets
Factories / editor utilities
```

这个边界本身是正确方向：Authoring Graph 属于 Editor，运行时消费编译后的 Dialogue/Node 数据。

## 3. DlgSystem 最值得保留的第一件事：Graph compile boundary

`FDlgCompilerContext::Compile()` 不是把编辑器 Graph 留给 runtime 遍历，而是从 `UDialogueGraph` 重建 `UDlgDialogue` 的运行时 Nodes。

编译过程：

1. 找 roots；
2. BFS 遍历图；
3. 重排 node index；
4. 修复 child target index；
5. 标记 primary/secondary edge；
6. 处理 orphan；
7. 写 `Dialogue->SetNodes(ResultDialogueNodes)`；
8. 修复旧 index 与 GUID 引用；
9. 确保每个 node 有有效 GUID。

这说明 runtime index 是 compiler 产物，不是内容 ABI。

### 关键规则

```text
Editor Graph Node position
        ≠
Runtime NodeIndex
        ≠
Stable NodeGuid
```

NodeIndex 适合运行时数组定位，NodeGuid 才适合作为长期语义身份。

## 4. NodeGuid 是源码明确认可的长期身份

`UDlgNode` 源码直接写着：

```text
The Unique identifier for each Node.
This is much safer than a Node Index.
```

并且 compiler 在 node 缺 GUID 时生成它。

所以 LGF Dialogue 不应该再讨论“要不要 stable NodeId”——答案已经很明确：要。

推荐：

```text
DialogueDefinitionId + NodeGuid
```

进入：

- save；
- resume；
- analytics；
- content migration；
- external writing pipeline；
- debug；
- Quest objective handoff。

## 5. DlgMemory 给了一个非常好的迁移案例

`FDlgHistory` 同时保留：

```text
VisitedNodeIndices
VisitedNodeGUIDs
```

源码还花了很长注释解释旧存档兼容三种情况。

其核心策略是：

- 新数据优先 GUID；
- 旧 save 只有 index 时仍能读取；
- 当 GUID 数据不足以覆盖旧 history 时，不伪装“已经迁移成功”，而是继续 fallback index。

这是一个很好的 **legacy read bridge**。

### 但长期状态不应继续 index-only

DlgMemory 也明确注释：节点位置变化后旧 index 可能指错，应该使用 GUID。

因此 SkillForge 吸收为：

```text
legacy index reader
→ explicit migration condition
→ semantic GUID state
→ current writer only writes new semantic schema
```

而不是永远双写 index/GUID。

## 6. DlgMemory 本身不能作为多人生产模型

源码也主动承认：

```text
TODO: investigate if this is multiplayer friendly,
it does not seem so as there exists only a single global dialogue memory
```

`FDlgMemory::Get()` 返回的是 process-static singleton。

这意味着如果直接照搬：

- 多个本地/网络玩家可能共享错误历史；
- Party/World/Player scope 无法表达；
- Dedicated Server 上所有玩家都可能混在一个 global memory；
- 断线/JIP 的 ownership 不清晰。

LGF 必须改成：

```text
PlayerDialogueMemory[StablePlayerId]
PartyDialogueMemory[StablePartyId]
WorldDialogueMemory[WorldInstanceId]
ConversationLocalMemory[ConversationInstanceId]
```

## 7. Participant Interface 很强，但“Participant UObject”不应等于 durable identity

`IDlgDialogueParticipant` 同时暴露：

### Presentation

- GetParticipantName；
- GetParticipantDisplayName；
- GetParticipantGender；
- GetParticipantIcon。

### Condition query

- CheckCondition；
- GetFloatValue；
- GetIntValue；
- GetBoolValue；
- GetNameValue。

### Event mutation

- OnDialogueEvent；
- ModifyFloatValue；
- ModifyIntValue；
- ModifyBoolValue；
- ModifyNameValue。

作为小型 dialogue plugin，这个 adapter 很灵活。

但 LGF 如果把当前 Pawn 直接作为 durable participant，会与现有 Stable Owner / Replaceable Avatar 冲突。

### LGF 转换

```text
ParticipantRoleId
  -> StableAgentId
    -> AvatarGeneration
      -> current Pawn/Component adapter
```

对话节点里写的 “Merchant” 是 role，不是 Actor pointer。

## 8. 这对用户的吸收/变身/坐骑需求尤其重要

用户未来要求：

- 吸收任意 NPC 后变成对方；
- 变成树桩/车/灯等场景物；
- 所有 NPC/宠物都可能成为坐骑；
- 不同形态有不同 Mesh/Skeleton/Animation。

所以：

```text
Stable Player identity
        ≠
Current visible body
```

对话进行中变身时，应该发生：

```text
old Avatar presentation unbind
→ generation++
→ resolve new current avatar adapter
→ rebuild camera / face target / voice / portrait / gesture
```

而不是：

```text
Pawn changed
→ Participant identity disappeared
→ Dialogue reset
→ enter events fire again
→ rewards duplicate
```

## 9. DlgContext 的 Participants map 是 runtime binding，不是 persistence identity

`UDlgContext` 内部使用：

```text
TMap<FName, UObject*> Participants
```

网络复制为了绕过 Map UObject 复制问题，会 flatten 成：

```text
TArray<UObject*> SerializedParticipants
```

然后 `OnRep_SerializedParticipants()` 调 `GetParticipantName()` 重建 map。

这个机制说明 participant name 是 role lookup 的关键。

但 LGF 还需要再加一层：

```text
RoleId -> StableAgentId -> current UObject
```

这样切 Pawn 后可以重绑。

## 10. DlgContext 支持 Replication plumbing，但不能等同于 authoritative multiplayer

当前源码有：

```cpp
IsSupportedForNetworking() -> true
DOREPLIFETIME(Dialogue)
DOREPLIFETIME(SerializedParticipants)
```

这是一种 UObject replication 基础能力。

但研究中没有找到：

- `HasAuthority` dialogue progression gate；
- generic Server RPC choice request；
- Conversation revision；
- stable ChoiceId；
- complete active node/JIP snapshot protocol。

而且 SpeechSequence 源码还有 explicit TODO：应该 proper replicate ActualIndex，而当前做法是 hack。

所以结论必须是：

> DlgSystem 有 replication plumbing，不等于它已经构建了完整 server-authoritative dialogue protocol。

## 11. 生产多人对话应该有 ConversationInstance

LGF 推荐 canonical：

```text
ConversationInstanceId
ScopeKey
DialogueDefinitionId
DefinitionVersion
CurrentNodeGuid
Substate
ParticipantRoleBindings
Visited/local semantic memory
Revision
LifecycleState
```

Authority 是唯一 semantic writer。

客户端只消费 read projection。

## 12. Choice Index 是本轮发现的重要缺口

`FDlgEdge` 当前关键路由字段是：

```text
TargetIndex
```

UI/Context 的选择也使用 `OptionIndex`。

但 edge 本身没有稳定 ChoiceGuid。

在本地单机 runtime 中可以接受；在多人、save、analytics 中不能直接用。

### LGF 必须补

```text
StableChoiceId / EdgeGuid
```

网络命令：

```text
SelectChoice(
  ConversationInstanceId,
  ExpectedRevision,
  ChoiceId
)
```

而不是：

```text
SelectChoice(2)
```

## 13. 为什么 Choice index 会错

假设客户端看到：

```text
0: Pay 100 gold
1: Threaten
2: Leave
```

在发送请求前，服务器 canonical state 变化，Pay option 被隐藏：

```text
0: Threaten
1: Leave
```

此时 `2` 已经不是同一语义。

因此 visible array position 永远只是 presentation index。

## 14. Authority Choice validation

服务器收到 ChoiceId 后至少检查：

- caller 是否是合法 participant/owner；
- ConversationInstance 是否存在；
- ExpectedRevision 是否匹配；
- 当前 NodeGuid；
- ChoiceId 是否属于当前 node；
- condition 是否 canonical satisfied；
- 距离/interaction/session permission；
- external transaction 是否可执行；
- 是否已有 transition commit。

成功才 revision++。

## 15. Condition 系统很灵活，但 API 不保证纯函数

`FDlgCondition` 支持：

- participant callback；
- participant int/float/bool/name；
- reflected class variable；
- WasNodeVisited；
- HasSatisfiedChild；
- custom UObject condition。

问题是 `CheckCondition()` 和 CustomCondition 理论上都可以偷偷 side effect。

所以 LGF 规则必须比 sample 更严格：

```text
Condition = pure read predicate
```

条件执行时禁止：

- 扣钱；
- 加/删物品；
- ApplyGE；
- 改 Quest；
- 改 world fact；
- advance conversation。

## 16. Condition 强弱组合值得保留，但语义要稳定

DlgSystem `EvaluateArray` 有 strong/weak 概念：

- strong condition：全部必须通过；
- weak：至少一个 weak 通过。

这说明 condition engine 可以支持可读组合语义。

LGF 更适合把 authored condition 编译成 typed expression/tree，而不是大量 string reflection callback。

## 17. Event 系统揭示了 domain ownership 风险

`FDlgEvent::Call()` 当前可以：

- OnDialogueEvent；
- ModifyInt/Float/Bool/Name；
- reflection 修改 Class variable；
- ProcessEvent 调 Unreal Function；
- custom event UObject。

对于通用 narrative plugin 这很灵活。

但 LGF 的核心域不能允许对话成为万能 mutation engine。

例如：

```text
ModifyInt("Gold", -100)
```

不能替代 Inventory/Economy transaction。

## 18. LGF 的事件应该转为 typed semantic command

```text
Dialogue authored event
→ semantic command descriptor
→ owning domain
→ Authority validation/transaction
→ structured result
```

示例：

```text
PayMerchantCommand
AcceptQuestCommand
GrantAbilityCommand
SetWorldFactCommand
BeginCombatCommand
```

不可逆命令增加 idempotency：

```text
ConversationInstanceId + NodeGuid + EventId + Revision
```

## 19. Quest 与 Dialogue 必须保持两个真值域

R14 已经把 Quest Manager 定为 sole writer。

R15 必须保证：

```text
Dialogue current node/choice
= Conversation truth

Quest phase/objective/reward
= Quest truth
```

Dialogue Condition 可以读取 Quest read model。

Dialogue Event 只能发送 typed Quest Request。

不允许 Dialogue Node 直接写 Quest manager internal state。

## 20. Dialogue Objective 的正确接法

如果 Quest Objective 是：

> 和 NPC 交谈并选择和平结局

应当：

```text
Conversation Authority
→ ConversationResolved(DefinitionId, Outcome.Peace, InstanceId, Revision)
→ Quest Objective subscription
→ Quest Authority verifies ObjectiveGuid/current state
→ objective progress/resolve
```

不能把 Quest progress 塞进 Dialogue local int variable 再由 UI 猜。

## 21. StateTree 与 Dialogue 的边界

NPC 开始交谈经常需要：

- 停止移动；
- 看向玩家；
- 暂停战斗；
- 播表情；
- 进入 social state。

Dialogue 不应直接修改 StateTree internal task。

使用 scoped intent/token：

```text
ConversationInstanceId
+ AIIntentId
+ AvatarGeneration
```

Conversation End/Cancel/Avatar switch 时统一 release。

## 22. GAS 与 Dialogue 的边界

Dialogue 选择可触发 GAS 行为，但流程应是：

```text
Choice
→ GAS typed request
→ Authority cost/tag/cooldown/target validation
→ success/failure
→ conversation commit
```

对话 UI 或 client graph 不能直接 ApplyGameplayEffect 给服务器真值。

## 23. Inventory/Economy 与 Dialogue 的边界

“支付 100 金币”：

```text
UI显示可支付（advisory）
→ client ChoiceId
→ Authority revalidate inventory/currency
→ reserve/consume transaction
→ success
→ advance dialogue
```

如果支付失败，Dialogue 保持原 canonical state，并返回结构化失败原因。

## 24. DlgSystem 的 Resume API 做对了一件事：明确推荐 GUID

`UDlgManager::ResumeDialogueFromNodeIndex` 的文档直接说：

```text
You should most likely use ResumeDialogueFromNodeGUID
```

GUID 版还接受 visited Node GUIDs。

这强化了本轮 stable identity 结论。

## 25. 但 Resume 还暴露一个更深的问题：enter event 是否重放

Resume API 有：

```text
bFireEnterEvents
```

这说明恢复 active node 时，side effect replay 是必须明确的政策。

在大型 ARPG 中不能只用一个 bool。

建议分类：

```text
BusinessCommand       never blindly replay
IdempotentCommand     same semantic key can retry
PresentationEvent     local rebuild allowed
EphemeralAudio        local presentation policy
```

## 26. Save 的三个版本层必须分开

DlgSystem 的 Dialogue 对象有长期 CustomVersion 演化。

LGF 需要：

```text
DialogueDefinition CustomVersion
ConversationSave SchemaVersion
Content Semantic Redirect Version
```

三者不能混成一个 `Version=7`。

## 27. Content migration 必须覆盖 active conversation

常见 patch：

- 改 node 名；
- 移 node；
- split node；
- merge node；
- 删除 choice；
- 重新排序 choice；
- participant role 改名；
- asset rename/move。

如果 save 的 CurrentNodeGuid 已消失：

- redirect；
- semantic checkpoint；
- restart；
- abort with reason。

不能默默用“新的同 index 节点”。

## 28. Localization 是 DlgSystem 的强项之一

`FDlgLocalizationHelper` 不是把对话存成普通 FString。

它处理 `FText` namespace/key，并在 stable localization keys 模式下尽量保留原 key。

正确身份分离：

```text
Semantic Line/Node/Choice ID
          ≠
FText Namespace+Key
          ≠
Rendered translated string
```

## 29. 为什么不能用台词文本作为 ID

同一句话可能：

- 改中文翻译；
- 改英文 source；
- 同文案出现在两个不同语义节点；
- 加动态参数；
- 因文化本地化完全改写。

所以 analytics/network/save 绝不能用 rendered text 当 identity。

## 30. TextArgument 是不错的 projection 模式

DlgSystem 通过 `{identifier}` 提取参数，然后从 participant/context 获取：

- int/float；
- class text；
- display name；
- gender；
- custom text。

最终 `FText::Format`。

LGF 应吸收“动态值属于 presentation projection”这个思想。

但不能让 text formatting 成为 mutation hook。

## 31. Reflection 在 hot presentation path 也需要警惕

DlgSystem 支持直接 reflection 获取 class variable，方便作者。

LGF 如果字幕频繁刷新：

- 不要每 frame reflection；
- line change 时构建 projection；
- underlying fact change 时 dirty/update；
- 常用变量走 typed read model/cache。

## 32. enum ordinal 也是内容 ABI

DlgSystem 的 TextArgument enum 等历史代码保留了 backwards compatibility 的顺序。

这说明：

- Blueprint authored enum；
- serialized enum；
- external JSON enum；

都不是随便 reorder 的 C++ 私有实现。

新增值优先 append 或显式 value + migration。

## 33. Default participant world scan 只适合 convenience

`StartDialogueWithDefaultParticipants` 会扫描世界找到 participant interface。

Manager 还明确注释 Actor scan：

```text
DO NOT CALL EACH FRAME
```

多人/大地图 LGF 应改成 participant registry：

```text
StableAgentId -> active participant adapter
ParticipantRole -> chosen StableAgentId
```

Interaction Authority 在开始时明确传入绑定。

## 34. LoadAllDialoguesIntoMemory 也不能变成默认大项目启动逻辑

小项目可以。

大型 ARPG 应：

- AssetManager/PrimaryAsset/registry；
- soft definition refs；
- async preload；
- hot cache；
- interaction request completion 后 revalidate。

不要为了一个 NPC 对话把所有 narrative assets 常驻。

## 35. IO 工具链值得保留

Runtime 有 JSON/Config Parser/Writer。

Editor 有：

- Human-readable text commandlet；
- Twine export；
- Browser/Search；
- external tool scripts。

这说明 DlgSystem 很重视 narrative writer workflow。

LGF 以后如果非程序人员大量写剧情，这个方向值得借鉴。

## 36. 外部 writer pipeline 必须保 stable IDs

生产流程建议：

```text
JSON/Twine/Sheet
→ versioned parse
→ stable-ID resolve
→ diff plan
→ apply
→ compile
→ roundtrip/oracle
```

已经发布的 DialogueGuid/NodeGuid/ChoiceId/localization key 不能因为“重新导入”自动全部换掉。

## 37. DlgSystem IO test 的证据边界

仓库有 `FDlgIOAutomationTest`，覆盖 writer/parser roundtrip。

但源码注释明确：要运行这个 test 先移除 `EAutomationTestFlags::Disabled`。

所以不能宣传“当前 CI 已自动保证全部 IO”。

本轮也没有执行目标项目 UE Automation。

## 38. 当前源码没有给出完整 network test matrix 的证据

没有看到：

- Dedicated dialogue progression suite；
- JIP/reconnect suite；
- stale revision；
- duplicate choice；
- simultaneous race；
- unauthorized participant。

所以 R15 的 Multiplayer 合同是 **SkillForge 对源码缺口的生产补强**，不是“DlgSystem 已经实现这些”。

## 39. Listen Host 与 Remote 必须走同一 semantic validation

不要：

```text
Host click -> direct ChooseOption
Remote click -> Server RPC validate
```

导致 Host 绕过安全规则。

应该：

```text
Host local intent ----┐
Remote RPC intent ----+-> ProcessChoiceAuthority()
AI server intent -----┘
```

transport 不同，业务 validation 同一份。

## 40. Dedicated Server 不应等待 presentation callback

禁止 gameplay truth 等：

- widget animation finished；
- audio finished；
- montage notify；
- facial animation；
- camera blend。

如果设计必须“语音播完才能继续”，Server 使用 semantic duration/hold policy，client audio completion 不作为唯一 authority proof。

## 41. JIP 应该 snapshot first

新客户端获取：

```text
ConversationInstanceId
Revision
DialogueDefinitionId
CurrentNodeGuid
SpeakerRole
ParticipantBindings
CurrentLineProjection
ChoiceProjection
```

然后订阅 delta。

不能指望收到“StartDialogue”历史 event 才知道当前状态。

## 42. Revision 是多人 Conversation 的核心缺失字段

没有 revision 时：

- 双击 choice；
- 延迟 packet；
- client stale choice；
- reconnect old UI；

都很难区分。

推荐每个 semantic transition：

```text
Revision++
```

所有 command 和 delta 都带 revision。

## 43. Conversation UI 是 projection，不是 graph owner

UI View：

```text
ConversationInstanceId
Revision
CurrentNodeGuid
SpeakerPresentation
Line
Choices[] {ChoiceId, Text, Enabled/Reason}
```

UI 不能：

- 直接 mutate graph node；
- 直接 mark visited；
- 直接发 Quest reward；
- 本地认为 choice 成功就先 advance canonical state。

## 44. SpeechSequence 暴露了“NodeGuid 还不够”的 substate 问题

一个 Conversation current node 里面还可能有：

- sequence entry；
- line index；
- nested selector；
- local hold。

所以 save/network state 不只是 CurrentNodeGuid。

需要：

```text
CurrentNodeGuid + stable Substate
```

不要只复制一个临时 int hack。

## 45. 选择 Random/Selector 时 Authority 必须唯一决定

如果随机 branch 影响剧情/奖励：

- Server/Authority 选择；
- 保存结果或 deterministic seed；
- clients 接收 result。

不能每个 client 自己跑 random selector。

## 46. DlgSystem 的 NodeData 扩展点值得吸收

Node/Edge 可以带 generic/typed extension data。

LGF 可类似：

```text
FInstancedStruct DialogueNodeExtension
```

但扩展数据仍需：

- schema/version；
- cook validation；
- ownership boundary；
- network/save classification。

不能让任意 extension UObject 成为绕过 Authority 的后门。

## 47. GameplayDebugger/Search 体现了 semantic debugging 的价值

DlgSystem 有 GameplayDebugger、Browser、Search，并可显示 GUID。

LGF Debug HUD/Inspector 应优先显示：

```text
ConversationInstanceId
DialogueDefinitionId
NodeGuid
Revision
Role -> StableAgent binding
ChoiceIds
last command/result
```

比只显示“当前台词文本”更可诊断。

## 48. 与 R13 FlowGraph 的关系

R13 给的是通用异步 graph runtime：

- latent node；
- subgraph；
- deferred transition；
- save ABI。

Dialogue 在它之上还需要：

- participant roles；
- speaker/text/voice；
- choices；
- localization；
- conversation memory；
- narrative content migration。

所以 R15 不重复 FlowGraph，而是增加 Dialogue domain contract。

## 49. 与 R14 SimpleQuest 的关系

R14 给的是：

```text
Quest Authority
Quest State/Journal CQRS
Objective
Outcome/Path
Reward ledger
```

R15 给：

```text
Conversation Authority
Participant semantic binding
Node/Choice identity
Localization
Conversation memory
Resume
```

两者通过 typed read/command 接口连接，不互相直接写内部数据。

## 50. 与 R12 StateTree 的关系

StateTree = AI decision/task lifecycle。

Dialogue = conversation semantic lifecycle。

“NPC 正在说话”可以影响 StateTree，但不能让 Dialogue UObject 变成整个 NPC brain。

## 51. 与 R5/R6 Avatar/Animation 的关系

对话 presentation 可能需要：

- Linked Anim Layer/overlay；
- gesture ability；
- face target；
- GameplayCamera；
- Motion/turn-to-target。

这些都是 Avatar generation-bound presentation。

Conversation canonical state 不跟 AnimInstance 生命周期走。

## 52. 对用户吸收 NPC 功能的直接意义

吸收 NPC 后，玩家可能：

- 看起来像 NPC；
- 使用 NPC voice/gesture；
- 被世界当作 disguise；

但：

```text
true stable identity
current visual form
world perceived identity
```

可能是三件不同的事。

Dialogue condition 必须明确查询哪一层，而不是读显示名猜身份。

## 53. 对场景物体变身的意义

变成箱子/树桩时：

- Stable Agent conversation state 可以继续；
- Avatar presentation profile 可能没有 mouth/facial socket；
- UI/voice 仍可显示；
- interaction policy 决定是否强制结束。

不要因为没有 skeletal mesh 就让 dialogue truth 崩溃。

## 54. 对骑乘所有 NPC 的意义

Mount 是另一 Actor/Pawn/presentation identity。

Rider 的 Dialogue role 不应自动变成 mount。

如果 mount 也能讲话：

```text
Role.Player -> Rider stable agent
Role.Mount  -> Mount stable agent
```

两个语义角色分别绑定。

## 55. 推荐 LGF Conversation DTO

```cpp
FConversationInstanceState
{
  FGuid ConversationInstanceId;
  FConversationScopeKey Scope;
  FPrimaryAssetId DialogueDefinitionId;
  FGuid CurrentNodeGuid;
  FConversationSubstate Substate;
  TMap<FGameplayTag, FStableAgentId> ParticipantBindings;
  uint32 Revision;
  EConversationLifecycle Lifecycle;
};
```

实际类型按 LGF 现有 ID 系统适配，重点是语义，不是照抄签名。

## 56. 推荐 Choice DTO

```cpp
FConversationChoiceView
{
  FGuid ChoiceId;
  FText Text;
  bool bEnabled;
  FGameplayTag BlockReason;
};
```

客户端 View 可带 FText，Authority command 只需要 semantic ChoiceId/Revision。

## 57. 推荐命令结果

```text
Accepted
Rejected.StaleRevision
Rejected.UnknownConversation
Rejected.UnknownChoice
Rejected.ConditionFailed
Rejected.Permission
Rejected.Range
Rejected.DomainTransactionFailed
```

UI 不应该靠 timeout 猜为什么没跳。

## 58. 性能结论

DlgSystem 的 dialogue runtime 本身不需要像 Mass 一样极端优化。

但大型 LGF 应避免：

- 每 frame world participant scan；
- 所有 dialogue startup load；
- 每 frame reflection text args；
- 每帧重复跑所有 conditions；
- UI 反复重建全 graph。

事件驱动 read-model 更新足够。

## 59. 本轮保留/适配/拒绝表

| DlgSystem 机制 | 结论 |
|---|---|
| Runtime/Editor 分离 | 保留 |
| Graph compiler | 保留 |
| DialogueGuid/NodeGuid | 强保留 |
| NodeIndex | 仅 runtime lookup |
| Participant Interface | 适配到 stable agent adapter |
| FText namespace/key | 保留 |
| Text Arguments | 适配为纯 projection |
| Resume by GUID | 保留并扩展 |
| old index fallback | migration-only |
| global FDlgMemory | 多人真值拒绝 |
| UDlgContext partial replication | 仅证据，不当完整 protocol |
| OptionIndex command | 网络/存档拒绝 |
| reflection mutation | 核心 Authority domain 拒绝 |
| world participant scan | convenience only |
| JSON/Twine/human-readable pipeline | 保留方向，补 stable-ID roundtrip |

## 60. R15 SkillForge 正式收敛

本轮写回两份正式长期规则：

- `skillforge-ue-cpp/references/dialogue-runtime-patterns.md`
- `skillforge-lgf/references/dialogue-conversation-contracts.md`

它们把 DlgSystem 的成熟机制转成通用/项目级合同，并保留其 active-source 风险，而不是“把项目 README 摘要塞进 Skill”。

## 61. 新增行为评测

UE C++：

- CPP-93 Participant semantic identity；
- CPP-94 Conversation save/resume；
- CPP-95 Stable ChoiceId；
- CPP-96 Authority revision/JIP；
- CPP-97 Memory scope；
- CPP-98 Condition/Event domain boundary；
- CPP-99 Localization identity；
- CPP-100 Content version/import roundtrip；
- CPP-101 Replication plumbing ≠ Authority。

LGF：

- LGF-59 replaceable Avatar participant rebind；
- LGF-60 conversation Authority/read model/JIP；
- LGF-61 Quest↔Dialogue boundary；
- LGF-62 StateTree↔Dialogue scoped intent；
- LGF-63 save/resume/content migration。

## 62. 未被本轮验证的东西

本轮是源码蒸馏，不是 DlgSystem 运行验收。

没有执行：

- DlgSystem UE5.7 UBT；
- Editor 打开真实 Dialogue Graph；
- FDlgIOAutomationTest；
- Dedicated Server；
- JIP/reconnect；
- lag/loss/race；
- Localization gather/cook；
- Twine roundtrip；
- 性能 profiling。

因此不能声称这些通过。

## 63. 最终结论

DlgSystem 是一个很好的 **mature single-player/general-purpose dialogue authoring framework source**，尤其强在：

- 长期插件版本兼容；
- Editor/Runtime 分离；
- Node GUID；
- Resume by GUID；
- Localization；
- participant adapter；
- writer tooling。

它同时非常诚实地暴露了大型 Multiplayer ARPG 必须补齐的部分：

- global memory scope；
- stable choice identity；
- authoritative choice request；
- revision/JIP；
- SpeechSequence replicated substate；
- typed external domain commands。

SkillForge R15 的价值不是复制 DlgSystem，而是把这两组证据同时保留下来，并转换成适合 LGF Stable Owner + Replaceable Avatar + Quest + StateTree + GAS + Inventory 的 Conversation Contract。
