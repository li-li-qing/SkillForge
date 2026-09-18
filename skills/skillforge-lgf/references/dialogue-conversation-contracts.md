# LGF Dialogue / Conversation Contracts

Use this reference when LGameplayFramework adds dialogue assets, NPC conversations, player choices, subtitles/voice projection, quest dialogue, social AI states, conversation save/resume, or multiplayer conversation replication.

This contract adapts `NotYetGames/DlgSystem@d705231216bd64558d437b87a57928689b1e7fef` to LGF's existing stable-owner / replaceable-avatar, GAS, Mover, Quest, Inventory, StateTree and networking rules. It does **not** copy DlgSystem's global memory or partial replication model.

## 1. LGF target architecture

LGF keeps the authoring/runtime boundary but does **not** require every Dialogue domain to persist two graphs. The domain chooses one of the Graph Foundation shapes:

```text
A. Dialogue Authoring Graph -> compile + validate -> DialogueDefinition DTO

B. Canonical DialogueDefinition DTO <-> transient UEdGraph editor projection

Either definition
        ↓
LConversationAuthority / Conversation Service
        ↓ sole semantic writer
ConversationInstance + Scoped Dialogue Memory
        ↓
Conversation Read Model / Presentation DTO
        ↓
CommonUI / subtitles / portrait / camera / voice / animation
```

Runtime, Shipping and Dedicated Server never depend on `UEdGraph`. Choose A when Dialogue needs lowering/compaction/cook stripping or a separate runtime ABI; choose B when the semantic definition itself is already the correct runtime form. Both shapes keep stable IDs, validation, migration, deterministic derived caches and revision fencing.

External domains remain authoritative:

```text
Quest       owns quest phase/objectives/rewards
Inventory   owns item/currency truth
GAS         owns abilities/effects/combat action truth
WorldState  owns world facts
StateTree   owns AI decision/task lifecycle
Mover       owns predicted movement
```

Dialogue coordinates them with typed requests. It does not absorb their mutable state.

## 2. DialogueDefinition is authored content; ConversationInstance is runtime state

Never merge these concepts.

### DialogueDefinition

Immutable/cooked data:

```text
DialogueDefinitionId / DialogueGuid
DefinitionVersion
Nodes by NodeGuid
Choices by ChoiceId
ParticipantRoleIds
Conditions
Semantic events/commands
Localization refs
Voice/presentation refs
```

### ConversationInstance

Mutable, owner/scope-specific state:

```text
ConversationInstanceId
ScopeKey
DialogueDefinitionId
CurrentNodeGuid
ConversationSubstate
ParticipantBindings
Visited/local memory
Revision
LifecycleState
Pending/Held semantic work
```

Multiple instances may execute the same definition concurrently without sharing mutable progress.

## 3. Stable Agent is the dialogue participant truth; Pawn is presentation

This is mandatory for LGF because the user intends:

- respawn/change Pawn;
- Prototype-style absorb NPC and transform;
- transform into scene props;
- mount arbitrary NPC/pets;
- switch mesh/skeleton/animation profiles.

Use:

```text
ParticipantRoleId
   -> StableAgentId / PlayerId / NpcPersistentId
      -> AvatarGeneration
         -> current Pawn / Mesh / Anim / sockets / camera target
```

Do not store the current Pawn pointer as the only participant identity.

### Example

A dialogue definition says:

```text
Role.Player
Role.Merchant
```

Runtime binding might be:

```text
Role.Player   -> Agent.Player.42
Role.Merchant -> NPC.Vendor.1039
```

If Player.42 transforms from humanoid Pawn to wolf Pawn, the role binding is unchanged. Only the presentation adapter resolves again.

## 4. Avatar rebind contract during an active conversation

On stable owner's AvatarGeneration change:

1. invalidate old avatar callback generation;
2. unbind old face target / socket / camera / animation delegates;
3. keep `ConversationInstanceId`, current NodeGuid and Revision unchanged unless gameplay semantics require interruption;
4. resolve current Pawn/mesh/animation/presentation adapter;
5. validate that the new form can participate under current dialogue policy;
6. reapply local camera/face/gesture presentation;
7. reproject current subtitle/choice read model;
8. do **not** replay irreversible enter events to rebuild visuals.

If the new form cannot converse, Authority explicitly pauses/ends with a reason; it does not accidentally lose dialogue state because an Actor pointer died.

## 5. Stable choice identity is required for multiplayer LGF

Never send:

```text
ServerChooseOption(2)
```

as the sole semantic command.

Use:

```text
FConversationChoiceRequest
  ConversationInstanceId
  ExpectedRevision
  ChoiceId
```

Optional diagnostics:

```text
ExpectedNodeGuid
ClientRequestId
```

The UI's array index is not authoritative identity.

### Authority validation

Server verifies:

- caller owns/controls an allowed participant;
- ConversationInstance exists and is visible to caller;
- revision is current;
- current NodeGuid is correct;
- ChoiceId belongs to the node;
- canonical condition set still passes;
- target domain command can commit;
- interaction range/session rule still passes if required;
- no transition is already committed.

Then it increments Revision and publishes the new read model.

## 6. Conversation scope is explicit

Recommended LGF scopes:

```text
Player     -> StablePlayerId
Party      -> StablePartyId
Interaction-> ConversationInstanceId shared by selected participants
NPC        -> StableNpcId if the NPC owns long-lived state
World      -> StableWorld/ShardId
```

Avoid ambiguous “global dialogue history.”

A node restriction must say what “once” means:

```text
OncePerConversation
OncePerPlayer
OncePerParty
OncePerWorld
```

## 7. Conversation memory layout

Separate at least:

```text
FConversationLocalState
FPlayerDialogueMemory
FPartyDialogueMemory
FWorldDialogueMemory
```

Long-term visited semantics should use NodeGuid, not compiled NodeIndex.

Recommended persistence keys:

```text
ScopeKey + DialogueDefinitionId
```

and, for active sessions:

```text
ConversationInstanceId
```

Do not place all player histories into a process-static singleton.

## 8. Quest ↔ Dialogue boundary

LGF R14 already establishes Quest Manager as sole writer and Quest State/Journal as read side. Dialogue must respect it.

### Dialogue reads Quest

Conditions query:

```text
QuestReadModel.HasQuest(...)
QuestReadModel.GetPhase(...)
QuestReadModel.HasOutcome(...)
QuestReadModel.GetObjectiveProgress(...)
```

They do not mutate quest state.

### Dialogue writes Quest

A semantic choice emits a typed command:

```text
AcceptQuestRequest
AdvanceQuestRequest
ResolveDialogueObjectiveRequest
```

Quest Authority revalidates and owns reward ledger/idempotency.

### Ownership rule

```text
Conversation position = Dialogue domain truth
Quest progress         = Quest domain truth
```

Do not duplicate quest progress inside conversation variables merely to drive UI.

## 9. Dialogue-driven quest completion

If a quest objective is “complete this conversation with outcome X”:

1. Conversation Authority resolves a stable semantic outcome;
2. emits a typed `ConversationResolved` domain event with ConversationInstanceId/DefinitionId/OutcomeId/Revision;
3. Quest Authority consumes it idempotently for the matching ObjectiveGuid;
4. Quest Authority decides whether objective/quest may advance;
5. rewards remain Quest/Inventory/GAS domain operations.

Never let a dialogue node directly mark arbitrary quest tags complete.

## 10. StateTree / AI conversation boundary

Dialogue is not the AI brain.

Conversation requests scoped AI intents:

```text
Social.FacePartner
Social.HoldPosition
Social.DisableCombat
Social.PlayGesture
Social.LookAt
```

StateTree/AI owner grants/denies them and owns cleanup.

Use a token:

```text
ConversationInstanceId
IntentId
AvatarGeneration
```

On dialogue end/cancel/avatar replacement:

- cancel/release all owned AI intents;
- stale StateTree task completion cannot re-enter the ended conversation;
- AI can resume prior policy through its own transition rules.

## 11. GAS boundary

Dialogue can request gameplay semantics such as:

- healing;
- applying reputation effect;
- teaching ability;
- entering an interaction ability;
- social/emote ability.

But GAS remains Authority owner.

Use:

```text
Dialogue choice
→ typed GAS request / ability activation request
→ GAS validates tags/cost/cooldown/target
→ result
→ dialogue transition
```

Do not directly add/remove GameplayEffects from UI/client dialogue graphs.

## 12. Inventory / economy boundary

Dialogue choice “Pay 100 gold” should be:

```text
Choice condition reads affordability
→ client sends ChoiceId
→ Authority resolves payment semantic command
→ Inventory/Economy transaction revalidates and consumes
→ on success dialogue advances
```

Use idempotency:

```text
ConversationInstanceId + NodeGuid + ChoiceId + semantic transaction id
```

A reconnect/retry must not pay twice or grant twice.

## 13. Network model

Recommended canonical owner is server/Authority.

### Server state

```text
ConversationInstance
Revision
semantic participant bindings
current NodeGuid/substate
scoped memory
```

### Client projection

```text
ConversationView
Revision
speaker presentation
localized line
available ChoiceIds/text
local cinematic/voice descriptors
```

Client does not need a writable copy of the graph brain.

## 14. Listen Server role discipline

A Listen Host is both local presentation and Authority, but do not bypass validation.

Use the same semantic command function for:

- remote client RPC path;
- local host interaction path;
- AI/server-driven selection path.

Only transport differs.

This prevents “host works, remote exploit/fails” divergence.

## 15. Dedicated server rule

Canonical conversation progression cannot depend on:

- subtitle widget completion;
- voice audio finished delegate;
- facial animation;
- montage notify;
- camera blend completion;
- local participant icon.

If narrative pacing depends on time/audio, Authority uses semantic timing data or explicit server-owned hold/release policy. Client presentation completion may be advisory only.

## 16. JIP / reconnect

Use snapshot first:

```text
ConversationInstanceId
Revision
DialogueDefinitionId
CurrentNodeGuid
participant semantic bindings
current line/choice projection
status
```

Then apply deltas.

Rules:

- older revision -> discard;
- duplicate -> idempotent;
- gap -> resync;
- unknown ConversationInstance -> fetch snapshot;
- participant avatar generation mismatch -> re-resolve presentation.

Do not rebuild by replaying all historic dialogue events.

## 17. Save model

LGF active conversation save should include semantic state only:

```text
SchemaVersion
ConversationInstanceId or resumable instance key
ScopeKey
DialogueDefinitionId
DefinitionVersion/content fingerprint
CurrentNodeGuid
Substate stable identity
ParticipantRole -> StableAgent binding
Visited/local state required by semantics
Revision / transition generation if useful
Pending semantic command recovery info
ContinuationFrames[]  // ReturnDefinitionId + ReturnNodeGuid + semantic transition/slot when needed
  LocalScopeFrame     // per-call Dialogue locals / scope version or resumable local snapshot
PendingAwait?         // AwaitId + source semantic command/node + revision/generation + resume policy
```

A continuation frame is durable semantic state, not a `TObjectPtr` call stack. On Load/JIP, resolve and migrate every definition/node/transition ID, rebind StableAgent participants, then rebuild derived lookup/cache before resuming. If an await cannot be restored safely, the definition chooses cancel/reissue/checkpoint restart explicitly.

### 17.1 Nested local memory is a scope/call stack, not one flat map

When Dialogue A calls SubDialogue B, each active frame owns the Dialogue-local semantic state for that definition. B may shadow an A-local name, but it must not overwrite A merely because the implementation reuses one `TMap`. Authority keeps:

```text
ConversationInstanceId
ActiveScopeFrames[]
  DialogueDefinitionId
  ReturnNode/Transition stable IDs
  LocalScopeVersion
  Dialogue-local values required for resume
  frame revision/generation when needed
```

Save/JIP snapshots serialize this active scope stack, then resolve/migrate all frames before atomically restoring the current frame. `StableAgent` participant bindings survive Avatar replacement; only presentation/avatar generation is rebound. Quest/Inventory/GAS/WorldState remain external domain truth and do not get copied into Dialogue locals.

Define child return/cancel policy explicitly: pop/discard, merge selected semantic outputs, or commit through a typed parent transition. Tests cover nested shadowing, save/reconnect inside a child, child cancel/return, schema migration and a simultaneous `PendingAwait`.

### 17.2 Pending async completion uses correlation + generation fencing

A GameplayTag identifies command/event **type**, not a unique wait. Each authoritative pending operation gets an `AwaitId` (or equivalent ExecutionToken) correlated with:

```text
ConversationInstanceId
Source NodeGuid / SemanticCommandId
Expected conversation Revision
Avatar / execution Generation when relevant
```

The Authority conversation owner advances only when the completion matches the current pending token and state. Old Avatar generation, old conversation, duplicate delivery, canceled request, or stale callback cannot advance. Quest/Inventory/GAS/AI remain sole writers and reuse the semantic idempotency/correlation key so retry/load/reconnect does not repeat a committed business mutation.

Do not save:

- current Widget pointer;
- UDlgContext-like transient UObject pointer;
- current Pawn pointer;
- NodeIndex only;
- localized rendered string as identity.

## 18. Resume event replay policy

LGF must classify dialogue events:

```text
BusinessCommand       -> never blindly replay
IdempotentDomainEvent -> replay only with same idempotency key
PresentationEvent     -> may rebuild locally
EphemeralAudio        -> local presentation policy
```

“Resume from node” is not equivalent to “enter node as if new.”

This prevents duplicate currency/item/quest rewards after load.

## 19. Definition migration and save migration

Maintain three version lanes:

```text
DialogueDefinition CustomVersion
ConversationSave SchemaVersion
Semantic ContentRedirects
```

Content redirect table examples:

```text
OldNodeGuid -> NewNodeGuid
OldChoiceId -> NewChoiceId
OldParticipantRole -> NewParticipantRole
OldDialogueDefinitionId -> NewDefinitionId
```

CI fixtures should load saves/content from supported historical versions.

If a mapping is impossible, return a structured recovery decision rather than using a numerically matching new index.

## 20. Localization contract

LGF narrative content uses:

```text
SemanticLineId
Localization Namespace/Key
Source FText
Rendered localized FText
```

as separate fields/concepts.

Rules:

- keep stable namespace/key when source text edits;
- do not use translated text as ChoiceId or save key;
- localized participant names are presentation;
- dynamic arguments use projection/read model values;
- voice/subtitle asset IDs can be associated with SemanticLineId without becoming gameplay identity.

## 21. Dynamic text and participant transformation

Dynamic line values such as player name, gender, race/form, equipped item name, or quest count should be resolved from a read/projection snapshot.

For transform-heavy gameplay:

- stable player name/identity remains on stable owner;
- current form display name/icon may come from Avatar presentation profile;
- authored dialogue can choose whether it refers to stable identity or current disguise/form via explicit argument source;
- never infer business identity from current mesh name.

## 22. Dialogue presentation profile per avatar/form

Recommended optional adapter:

```text
FDialoguePresentationProfile
  Portrait/Icon provider
  Voice profile
  Facial/gesture profile
  Talk socket / look-at socket
  Camera framing profile
  Retarget/Anim layer semantic tags
```

This profile belongs to current Avatar generation, not persistent conversation save.

When changing form, rebuild the presentation profile and keep semantic conversation state.

## 23. Riding / mount conversations

For player mounted on an NPC/pet:

- rider stable agent remains `Role.Player` unless design explicitly makes the mount the speaker;
- mount may be a second semantic participant role;
- camera/face target selection is presentation policy;
- conversation interaction range must choose an authoritative transform source deliberately (rider capsule, mount, interaction proxy);
- dismount must not duplicate/end conversation accidentally through two Actor callbacks.

## 24. NPC absorb / impersonation

If the player absorbs an NPC and looks like that NPC:

```text
VisualFormId != StableAgentId
```

Dialogue conditions should be explicit about what they mean:

- `IsStableIdentity(NPC.X)`;
- `CurrentFormMatches(NPC.X)`;
- `HasDisguiseTag(X)`;
- relationship/reputation of stable player;
- world belief/knowledge state.

Do not use the participant display name to infer true identity.

## 25. StateTree-started conversations

AI can request a conversation start, but Conversation Authority creates the instance.

Suggested flow:

```text
StateTree intent
→ RequestConversationStart(DefinitionId, participant stable IDs)
→ Authority validates range/state/locks
→ create ConversationInstance
→ return handle/token
→ StateTree waits/observes semantic result
```

If StateTree aborts:

- request cancellation through conversation service;
- release AI/social tokens;
- do not destroy shared conversation blindly if other participant ownership rules say it continues.

## 26. Conversation holds / pacing

R14 Quest uses scoped advancement holds. Dialogue can use the same pattern when several systems pause transition:

```text
VoiceHold
CinematicHold
ChoiceUIHold
NetworkConfirmationHold
```

Use handles/reasons, not `bool bPauseDialogue`.

However, do not preserve purely presentation holds across save unless design explicitly requires it. On restore, rebuild semantic state then create fresh presentation holds.

## 27. UI boundary

CommonUI/UMG consumes read model only.

UI may issue:

```text
SelectChoice(ChoiceId, ExpectedRevision)
SkipPresentation
RequestConversationClose
```

Only semantic commands route to Authority. Pure presentation actions remain local unless they affect shared pacing.

Widget destruction/recreation does not terminate the canonical conversation by accident.

## 28. Conversation projection events

Prefer stable events such as:

```text
ConversationStarted
ConversationSnapshotChanged
LineChanged
ChoicesChanged
ParticipantPresentationChanged
ConversationEnded
ConversationRejected
```

Events carry `ConversationInstanceId` + `Revision` where ordering matters.

GameplayMessageRouter or another bus can transport projection notifications, but it is not the canonical state store.

## 29. Dialogue asset authoring pipeline

Editor graph compiles to runtime definition.

Content validation must catch:

- duplicate/missing DialogueDefinitionId;
- duplicate/missing NodeGuid;
- duplicate/missing ChoiceId;
- dangling route;
- unreachable content policy violations;
- missing participant role;
- duplicate role binding requirement;
- invalid condition/command descriptor;
- missing localization key;
- unstable generated IDs;
- stale compiled output.

Bulk conversion/import tools must show an ID remap report before destructive changes.

## 30. External narrative writer pipeline

If writers use JSON/TSV/Twine/spreadsheets:

```text
ExternalSource
→ parse/version validate
→ resolve stable semantic IDs
→ diff/plan
→ apply transactionally
→ compile runtime definition
→ round-trip/oracle verification
```

Do not implement “delete all dialogue assets and recreate” as the normal update path after shipping because it churns GUIDs/localization keys/references.

## 31. Runtime performance

Condition caching distinguishes immutable compiled AST/bytecode from mutable result cache; this is the LGF compiled AST vs result cache contract. The compiled AST may be reused while definition/expression source is unchanged; a result cache is keyed/invalidated by the real **dependency revision** set. Quest/Inventory/GAS/WorldState should expose revisioned read model generations or change subscriptions instead of letting Dialogue assume its own setter sees every change. External/dynamic getters without a revision contract are re-evaluated at explicit interaction/selection boundaries; client cached results remain advisory and Authority revalidates against current canonical revisions.

Dialogue usually is not the largest runtime cost, but LGF should still avoid:

- Actor world scans on every interaction tick;
- loading every dialogue at boot;
- string reflection every frame;
- reconstructing formatted FText every Tick with unchanged arguments;
- repeatedly traversing large Quest/Inventory structures for every choice on every frame;
- keeping heavy graph editor structures in Runtime.

Re-evaluate choices on meaningful dependency changes or on explicit interaction/selection boundaries.

## 32. Testing matrix for LGF

### Core

- definition compile;
- stable node/choice ID round trip;
- conditions;
- local/persistent history scope;
- resume from every supported substate;
- event idempotency;
- localization key stability.

### Multiplayer

- Host semantic path;
- remote client path;
- simultaneous choice requests;
- stale/duplicate revisions;
- unauthorized participant;
- out-of-range participant;
- Dedicated server;
- JIP;
- reconnect;
- packet loss/reorder;
- participant Actor replacement.

### LGF integration

- Quest objective handoff;
- Inventory payment/grant;
- GAS effect/ability request;
- StateTree social state start/abort;
- transform during active line;
- prop form;
- mount/dismount;
- death/respawn;
- skeleton/AnimInstance replacement while voice/gesture is running.

## 33. DlgSystem mechanisms LGF should retain/adapt/reject

| Mechanism | LGF verdict |
|---|---|
| Dialogue/Node GUID | Retain |
| Runtime compact index | Retain only as transient lookup |
| Editor graph compile | Retain |
| Participant interface | Adapt behind stable-agent semantic binding |
| FText stable localization keys | Retain |
| text arguments | Adapt as pure projection reads |
| Resume by NodeGuid | Retain and expand with schema/substate |
| visited-index fallback | Migration-only |
| process-global FDlgMemory | Reject |
| world participant scan | Convenience only; reject as normal multiplayer discovery |
| replicated context participant refs | Insufficient alone; wrap with canonical Authority instance |
| visible option index command | Reject for network/save |
| reflection-based authoritative mutation | Reject for Quest/Inventory/GAS/World truth |

## 34. Integration sequence for LGF

Do not start with a giant Dialogue Editor rewrite.

Recommended implementation order:

1. define stable IDs and `FConversationInstance`;
2. define participant role/stable-agent binding;
3. define Authority choice request + revision protocol;
4. define read-model snapshot;
5. implement one simple compiled/data-driven dialogue definition;
6. implement save/resume by NodeGuid/ChoiceId;
7. integrate localization projection;
8. integrate Quest typed read/commands;
9. integrate Inventory/GAS commands;
10. integrate StateTree social intent tokens;
11. add transform/mount avatar rebind;
12. only then expand authoring graph/import tooling.

This sequence validates runtime semantics before investing in editor complexity.

## 35. Definition of done for an LGF dialogue feature

A dialogue feature is not complete because it works in single-player PIE.

Require evidence for:

- semantic IDs stable across editor rebuild;
- save/resume after content reload;
- Authority validation;
- Host and Remote behavior;
- Dedicated path without presentation;
- JIP/reconnect snapshot;
- duplicate/stale request handling;
- avatar replacement while active;
- Quest/Inventory/GAS side effects idempotent;
- localization keys stable;
- no global cross-player memory leakage;
- no Editor module dependency in Shipping Runtime.
