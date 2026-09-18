# Dialogue / Conversation Runtime Patterns

Use this reference when a UE C++ task involves dialogue authoring graphs, dialogue participants, branching choices, conversation save/resume, localization, dialogue-side events and conditions, multiplayer dialogue, JIP/reconnect, or integration with Quest, StateTree, Inventory, GAS, and replaceable Pawns.

This reference distills production-oriented lessons from `NotYetGames/DlgSystem@d705231216bd64558d437b87a57928689b1e7fef` (DlgSystem 18.0.8, UE 5.6–5.8) and deliberately strengthens the sample where its active multiplayer path is incomplete.

## 1. Version and evidence gate

Pinned research snapshot:

- repository: `NotYetGames/DlgSystem`;
- default branch: `master`;
- commit: `d705231216bd64558d437b87a57928689b1e7fef`;
- commit date: 2026-06-22;
- tree: `cac042505f4d32364bfadad2a15a2b8ddfa1f7e3`;
- plugin version: 18.0.8;
- license: MIT;
- README-supported engine range: UE 5.6 / 5.7 / 5.8;
- active nearby commits add UE 5.8 support and a UE 5.7 include fix.

Treat this as **Current-to-target** evidence for UE 5.7 architecture, but never infer that every subsystem is production-ready for multiplayer merely because it compiles on a current engine.

Use this evidence ladder:

1. descriptor / supported engine claim;
2. current header/cpp implementation;
3. explicit TODO / migration comments;
4. tests;
5. target project UBT / Editor / PIE / Dedicated / JIP / lag verification.

DlgSystem is especially useful because it contains both mature ideas and explicit multiplayer limitations. Preserve both.

## 2. Authoring graph and runtime dialogue are different products

Do not execute editor graph objects as Shipping conversation truth. **This is a dependency/authority boundary, not a requirement to persist two graph copies.**

Two production shapes are valid:

```text
A. Authoring UEdGraph / editor nodes
          ↓ compile + validate
   DialogueDefinition runtime artifact
          ↓
   ConversationInstance runtime state

B. Canonical semantic DialogueDefinition  ← authoritative mutation/service
          ↕ transient editor projection (UEdGraph)
   ConversationInstance runtime state
```

Use A when the runtime schema needs lowering, compaction, cook/security stripping, binary ABI isolation, or materially different hot-path layout. Use B when authoring semantics and runtime semantics are already isomorphic: the canonical semantic definition is the one persisted truth and the `UEdGraph` is disposable/rebuildable editor UI. In both shapes, Runtime/Shipping/Dedicated must not depend on `UEdGraph`, pins, Slate widgets, or editor object identity.

DlgSystem uses shape A: its editor compiler reconstructs runtime `UDlgDialogue::Nodes` from editor graph nodes, walks the graph breadth-first, reassigns compact node indices, repairs references, and guarantees node GUID creation. This proves an important distinction:

```text
NodeIndex = compiled/runtime position
NodeGuid  = durable semantic identity
```

A compiled index may change when graph layout/topology changes. Therefore an index can be a local hot-path lookup, but it is not a safe save/network/content-migration key.

### Production rule

Whichever shape is chosen, the Runtime-consumable semantic definition (canonical or compiled) contains at least:

- DialogueDefinitionId / DialogueGuid;
- NodeGuid;
- stable ChoiceId / EdgeId where choices cross durable boundaries;
- target node mapping;
- participant role IDs;
- condition descriptors;
- event/command descriptors;
- localization identities;
- optional voice/presentation asset references;
- definition schema/content version.

Editor-only graph node pointers, positions, pins, selection state, widgets, and comments do not belong in Shipping state.

## 3. Stable node identity is separate from compact index

DlgSystem explicitly documents `NodeGUID` as safer than Node Index. Its memory model also carries a compatibility bridge from historical visited indices to visited GUIDs.

Use:

```text
DialogueGuid + NodeGuid
```

for:

- save/resume;
- analytics;
- content migration;
- quest/dialogue handoff;
- debugging references;
- external authoring/import references.

Use `NodeIndex` only as an ephemeral compiled lookup after resolving the stable ID.

### Resume contract

Save:

```text
DialogueDefinitionId
CurrentNodeGuid
Conversation substate
VisitedNodeGuids / memory needed by semantics
Participant bindings by stable identity
Revision
```

Load:

1. resolve DialogueDefinitionId;
2. migrate content version if needed;
3. map CurrentNodeGuid through redirects/migration;
4. rebuild runtime NodeIndex / derived lookup from the current semantic definition or compiled artifact;
5. rebind participants;
6. re-evaluate presentation/read data;
7. resume without replaying irreversible enter side effects unless policy explicitly requests replay.

Never persist only `NodeIndex` for newly shipped content.

## 4. Choice identity needs the same treatment as node identity

DlgSystem's `FDlgEdge` is addressed primarily by `TargetIndex`, and the public `ChooseOption` API consumes visible option position. That is acceptable as an in-process UI convenience, but not as a durable multiplayer contract.

Production systems should distinguish:

```text
VisibleChoiceIndex    = current projection order
StableChoiceId        = semantic authored identity
TargetNodeGuid        = durable destination identity
```

Recommended request:

```text
SelectChoice(
  ConversationInstanceId,
  ExpectedRevision,
  StableChoiceId
)
```

Authority then resolves `StableChoiceId` against its current conversation state.

### Why index-only requests fail

The same integer may mean a different choice after:

- conditions hide an option;
- localization/UI sorting changes presentation;
- content is patched;
- a client is one revision behind;
- a participant state change causes re-evaluation;
- a graph is recompiled and edge order changes.

If a project cannot add authored edge GUIDs, derive a deterministic semantic route ID at compile time and freeze its migration contract. Do not hash rendered text.

## 5. Participant role identity is not an Actor pointer

DlgSystem's participant interface is a useful adapter surface, but production durable identity must be one layer above the current UObject.

Use:

```text
ParticipantRoleId
      ↓
StableAgentId / PlayerId / StableNpcId (when applicable)
      ↓
Current Actor / Pawn / Component adapter
```

`ParticipantRoleId` answers “who speaks/acts in this authored conversation role?”

`StableAgentId` answers “which persistent game entity currently fills that role?”

The current Actor/Pawn answers only “which runtime object currently presents that entity?”

### Rebind rule

When a Pawn respawns, transforms, mounts, dismounts, or is replaced:

- keep the semantic participant binding;
- invalidate the old Actor adapter generation;
- resolve the new current adapter;
- rebuild icon/voice/face-target/socket/camera presentation bindings;
- reject delayed callbacks from the old avatar generation.

Do not restart a conversation solely because its presentation Pawn changed unless game design explicitly requires it.

## 6. Participant interface: split read adapters from command adapters

DlgSystem combines participant presentation, condition queries, and mutation events in one interface. This is convenient, but large production frameworks should make the conceptual split explicit.

### Read side

Examples:

- display name;
- gender/pronouns;
- portrait/icon;
- relationship rank;
- quest read state;
- inventory read state;
- tags/facts;
- dialogue-local variables.

These should be side-effect free.

### Command side

Examples:

- give item;
- consume item;
- advance quest;
- grant ability/effect;
- change faction;
- start combat;
- trigger world event.

These go through typed domain commands owned by the target domain.

Do not make a single string callback such as `ModifyIntValue("Gold", -100)` the authoritative economy transaction.

## 7. Dialogue conditions are pure predicates

DlgSystem supports conditions backed by participant callbacks, reflected variables, node-visited state, and custom objects. The API does not force callback purity, so SkillForge must.

Condition contract:

```text
Condition(Input Read Snapshot) -> {Satisfied, Reason/Blocker}
```

A condition must not:

- remove inventory;
- apply GameplayEffects;
- mutate quest progress;
- write world facts;
- advance the conversation;
- emit irreversible analytics/business events.

### TOCTOU rule

Client or UI may evaluate an advisory copy to show/disable choices, but Authority re-evaluates the canonical condition at command time before committing the choice.

If choosing a dialogue option consumes resources:

1. pure condition says whether the option appears/is likely usable;
2. client submits typed intent;
3. Authority transaction revalidates canonical resource state;
4. transaction commits resource mutation;
5. only then does the conversation transition commit.

Define rollback/ordering explicitly when both must be atomic.

### 7.1 Compiled-expression cache is different from evaluation-result cache

Treat the two caches as different correctness classes:

```text
compiled-expression cache
= expression source -> parsed AST / bytecode

evaluation-result cache
= expression + dependency revision(s) -> mutable result
```

The first is normally safe while the expression source/version is immutable. The second is safe only when every fact the expression can read has an observable **dependency revision**, generation, or subscription that invalidates the cached result.

A variable exposed through an external getter, Quest read model, Inventory/GAS state, world fact, or participant adapter may change without going through the dialogue runner's own setter. In that case, clearing the cache only from `SetVariable()` leaves a stale boolean. Either bridge the dependency through a revisioned read model / precise invalidation subscription, or re-evaluate at a defined interaction/selection boundary. Do not keep an indefinite result cache merely because the AST cache is valid.

Hot-path rule remains: cache parsing/tokenization and stable tag resolution, avoid world scans/reflection/synchronous loads, and profile before widening mutable result caches.

## 8. Dialogue events are semantic intents, not arbitrary reflection writes

DlgSystem event types can call participant events, mutate named values, modify reflected class variables, or invoke an Unreal function by name. This is flexible authoring, but it is too permissive as an Authority boundary for core domains.

Preferred production model:

```text
Dialogue Event Descriptor
      ↓
Typed Domain Command
      ↓
Owning Domain Authority
      ↓
Result / failure reason
      ↓
Conversation transition or projection
```

Examples:

```text
QuestRequest.Accept / ResolveChoice
InventoryTransaction.Grant / Consume
GASRequest.ApplySemanticEffect
WorldFactRequest.Set
AIIntent.BeginSocialInteraction
```

For irreversible side effects, include an idempotency/correlation key such as:

```text
ConversationInstanceId
+ NodeGuid
+ SemanticEventId
+ Revision or transition generation
```

This prevents duplicate grant after reconnect, retry, replay, or duplicated event delivery.

### 8.1 Async event completion needs an operation identity

For an asynchronous dialogue node, a GameplayTag describes **what kind of event** is running; it is not the identity of one execution. A wait that can overlap/repeat needs an explicit token such as:

```text
ConversationInstanceId
AwaitId / Execution Token
Source NodeGuid / SemanticEventId
Expected Revision / Generation
```

Completion validates the active execution token, conversation, generation/revision, expected wait state, and Authority/owner before it can advance. A late completion from a canceled node, previous Avatar generation, old conversation, or duplicate delivery becomes a no-op/diagnostic event. Never resume only because `CompletedTag == WaitingTag`.

Save/Load/JIP must define whether a pending await is persisted, reissued with the same semantic correlation, canceled, or restarted from a checkpoint. The same correlation/idempotency identity should cross Quest/Inventory/GAS/AI domain commands so retry/reconnect cannot double-advance or double-grant.

## 9. ConversationInstance is canonical runtime state

Do not treat a mutable `UDlgContext*` as the persistence or network identity.

Recommended canonical structure:

```text
ConversationInstanceId
ScopeKey / OwnerKey
DialogueDefinitionId
DefinitionVersion / ContentHash
CurrentNodeGuid
ConversationSubstate
ParticipantRoleBindings
Visited / local semantic memory (only what behavior needs)
Revision
Lifecycle state
Pending semantic work / holds if needed
```

Optional read-model fields may include currently available ChoiceIds, but the Authority should be able to recompute/validate them.

### 9.1 Continuation frames and pending await state are part of canonical state

`CurrentNodeGuid` is insufficient when the runtime supports nested sub-dialogues, call/return nodes, sequences with hidden cursors, or latent events. Any hidden state that can change the **next semantic transition** must be persisted or deterministically recomputable.

A durable save may therefore include semantic continuation frames; each return definition/node is identified semantically rather than by a live object pointer:

```text
ContinuationFrames[]
  ReturnDefinitionId
  ReturnNodeGuid
  ReturnSemanticSlot/TransitionId (if needed)
  LocalScopeFrame / LocalScopeId / resumable local snapshot (when nested calls own locals)

PendingAwait?
  AwaitId
  SourceNodeGuid / SemanticCommandId
  ExpectedRevision / Generation
  ResumePolicy
```

Do not persist `TObjectPtr<UDialogueTree>`, node array indices, delegate handles, task UObjects, or local lookup pointers as the durable frame. Load must resolve/migrate every referenced definition and stable ID, then **rebuild runtime lookup** tables/caches and rebind participants/dependencies before resuming. Missing or unmigratable frames require an explicit abort/checkpoint/restart policy.

### 9.2 Nested dialogue locals are call-frame state

If SubDialogue / call nodes have local variables, a single flat `LocalVariables` map is not sufficient. Treat each active dialogue call as a semantic scope frame:

```text
Frame 0: Parent DefinitionId + Parent locals
Frame 1: Child DefinitionId  + Child locals
Frame 2: Nested child ...
```

Entering a child pushes the caller continuation **and its local scope**; the child receives a new local scope according to the definition policy. Returning/canceling pops, commits, merges, or discards that child scope according to an explicit rule. A child must not accidentally overwrite parent locals merely because the runtime reuses one map.

Define lookup/shadowing explicitly, for example:

```text
current local scope
→ parent scope(s), only if the domain allows lexical inheritance
→ conversation/global dialogue memory
→ external/domain read model
```

Save/Load/JIP serializes the active scope/call stack using stable `DefinitionId`, return `Node/Transition` IDs, scope version and the semantic local values required for resume. Do not save one flattened local map, `TObjectPtr` frames, or runtime array indices. Resolve/migrate every frame before making the restored top frame active.

Tests cover same-name variable shadowing, multi-level SubDialogue, save inside the deepest child, return/cancel policy, missing-frame migration, and resumed external awaits.

### ScopeKey

Pick scope deliberately:

- Player;
- Party;
- shared interaction instance;
- NPC-owned conversation;
- World/Shard event.

Do not fall back to a process-global singleton when multiple players or simultaneous conversations can exist.

## 10. Replication plumbing is not Authority architecture

DlgSystem's current `UDlgContext` demonstrates replicated-UObject plumbing:

- it supports networking;
- it registers `Dialogue` and serialized participant UObject refs;
- client `OnRep` reconstructs the participant-name map.

But current source does not establish a full authoritative conversation protocol:

- no generic Server RPC command path was found;
- no `HasAuthority` gate was found in dialogue choice handling;
- active node/revision/choice state is not generally replicated as a canonical conversation snapshot;
- SpeechSequence contains an explicit replication TODO/hack;
- global memory contains an explicit multiplayer-friendliness TODO.

Therefore:

> “This UObject replicates” does not mean “this gameplay system is server-authoritative.”

### Production network contract

Authority owns `ConversationInstance`.

Client sends intent only:

```text
ConversationInstanceId
ExpectedRevision
StableChoiceId
optional client presentation context
```

Authority validates:

- caller is a participant / authorized controller;
- conversation still exists;
- revision matches or can be safely reconciled;
- current NodeGuid matches expected semantic state;
- choice belongs to current node;
- choice is visible/allowed under canonical conditions;
- distance/interaction/session permission if required;
- no conflicting transition already committed;
- any external domain transaction can commit.

Authority increments Revision on accepted semantic transition.

## 11. Snapshot-first JIP and reconnect

A client joining late must not need the historical event stream to reconstruct a dialogue.

Send a normalized snapshot first:

```text
ConversationInstanceId
Revision
DialogueDefinitionId
CurrentNodeGuid
SpeakerRoleId
current line/presentation descriptor
available choices {ChoiceId, display projection}
participant presentation bindings
conversation status
```

Then subscribe to deltas/events.

Delta receiver rules:

- drop older revision;
- ignore exact duplicate idempotently;
- detect revision gap and request resync;
- never apply a transition to a different ConversationInstanceId;
- never let a late voice/animation callback advance canonical state.

Dedicated server logic must not depend on widgets, audio completion, animation notify, face animation, or camera events to finish a gameplay transition.

## 12. Conversation memory must be explicitly scoped

DlgSystem's `FDlgMemory` singleton is valuable migration evidence but not a multiplayer ownership model.

Production scopes may include:

```text
PlayerDialogueMemory[StablePlayerId]
PartyDialogueMemory[StablePartyId]
WorldDialogueMemory[WorldInstanceId]
ConversationLocalMemory[ConversationInstanceId]
```

The same DialogueDefinition may therefore have different visited/history state for different players.

### Memory taxonomy

Separate:

- current conversation-local state;
- long-term per-player narrative history;
- party/shared history;
- world facts;
- presentation history such as “subtitle already animated”.

Do not put all of them in one static map.

## 13. Legacy index fallback is a migration bridge, not a steady-state design

DlgSystem's `FDlgHistory` intentionally supports both visited node indices and GUIDs so old saves remain readable after GUID support was introduced.

That is a good migration pattern:

```text
read legacy representation
      ↓
use explicit compatibility predicate
      ↓
resolve to new semantic identity when safe
      ↓
write new schema on next save
```

But do not keep generating new index-only saves.

For LGF-style production systems:

- old schema reader may accept NodeIndex;
- migration resolves it using the historical definition/version if possible;
- current schema stores NodeGuid/ChoiceId;
- ambiguous mapping fails loudly or follows an explicit fallback policy.

## 14. Dialogue asset version and game-save version are separate

DlgSystem carries an extensive custom object version history for dialogue asset migrations. Player save compatibility is a different concern.

Maintain separate layers:

```text
Dialogue Asset CustomVersion
    = authored/runtime definition serialization changes

Conversation Save SchemaVersion
    = active instances, histories, bindings, revisions

Content Migration Map
    = old semantic IDs -> new semantic IDs
```

Do not use one integer to represent all three.

### Content migration cases

Test at least:

- node renamed;
- node moved/reordered;
- node split into two;
- two nodes merged;
- edge/choice removed;
- choice semantics changed;
- participant role renamed;
- dialogue asset moved/renamed;
- missing optional/DLC content;
- old active conversation points at removed node.

Define deterministic recovery:

- redirect to replacement node;
- resume at semantic checkpoint;
- restart conversation;
- abort with a structured reason.

Never silently interpret the same old numeric index against a new compiled graph.

## 15. Localization identity is its own ABI

Keep three identities distinct:

```text
SemanticLineId / NodeGuid / ChoiceId
FText Namespace + Key
Current rendered/transformed text
```

DlgSystem's localization helper preserves `FText` namespace/key when stable localization keys are enabled and generates a new key only when persistence is unsafe.

Production rules:

- translated visible text is never a network/save/analytics identifier;
- editing source text should not unnecessarily churn localization key;
- moving an asset/package must have a localization namespace migration policy;
- duplicate key collisions are detected during content validation;
- runtime text arguments do not change semantic line identity.

## 16. Dynamic text arguments are presentation-time reads

DlgSystem extracts `{Argument}` fields and resolves them through the participant/context, then uses `FText::Format`.

Treat this as projection logic.

Dynamic text arguments may read:

- player display name;
- gender/pronoun form;
- numeric read model;
- relationship label;
- localized item/quest display name.

They must not mutate authoritative state.

If dynamic values require reflection or expensive domain traversal, resolve/capture them when a line projection is produced rather than every UI frame.

## 17. Blueprint/serialized enum ordinals are ABI

DlgSystem includes enum-order compatibility comments and long-running serialization evolution. General rule:

- do not insert a new serialized/Blueprint-authored enum value in the middle unless migration is explicit;
- append values when ordinal stability matters;
- or assign explicit numeric values and still test old assets;
- preserve redirects for renamed Blueprint functions/nodes/properties where necessary.

Treat authored Blueprint data as external serialized input, not “just code.”

## 18. World participant scans are convenience paths, not hot-path discovery

DlgSystem's default-start helper can scan world Actors implementing the participant interface and explicitly warns not to do that every frame.

Production runtime should prefer:

- explicit participant bindings from interaction/session authority;
- indexed registries by StableAgentId / ParticipantRole;
- subsystem registration on spawn/despawn;
- weak handles / generation-aware resolve.

Avoid:

```text
Start conversation
→ scan all world actors
→ choose first matching participant name
```

in large multiplayer worlds.

Duplicate participant names must be a hard ambiguity, not “pick one.”

## 19. Asset loading and dialogue definition lookup

Do not `LoadAllDialoguesIntoMemory()` as a default production startup strategy for a large ARPG.

Prefer:

- PrimaryAsset/AssetManager or project registry;
- stable DialogueDefinitionId -> soft path;
- async load before interaction commit;
- cache hot definitions;
- unload/cull when policy allows;
- revalidate Conversation request after async completion.

No synchronous dialogue asset discovery/load belongs in per-frame interaction scans.

## 20. Quest integration boundary

Dialogue and Quest are adjacent domains, not one mutable object graph.

Preferred relationship:

```text
Quest Authority ──read model──> Dialogue condition
Dialogue choice ──typed request──> Quest Authority
Quest state delta ───────────────> Dialogue/UI projection
```

Dialogue may:

- query whether a quest is available/live/resolved;
- request accept/advance/abandon;
- return a semantic dialogue outcome to a quest objective;
- display quest-derived text.

Dialogue must not:

- edit quest manager internal maps;
- grant quest rewards directly;
- fabricate Objective progress;
- bypass Quest condition/hold/reward ledgers.

Use stable correlation IDs when one conversation transition and one quest command form a business operation.

## 21. Inventory / GAS / progression boundary

Same principle:

```text
Dialogue asks
Domain validates and mutates
Dialogue observes result
```

Examples:

- “Pay 100 gold” -> Inventory/Economy transaction;
- “learn spell” -> Ability grant owner;
- “heal target” -> GAS semantic action/effect request;
- “unlock door” -> WorldState/interaction authority.

Dialogue graph owns narrative routing, not every game's source of truth.

## 22. StateTree / AI integration boundary

Dialogue should not replace an AI brain.

A conversation can request scoped presentation/behavior intents:

```text
FaceParticipant
HoldPosition
DisableCombatTemporarily
EnterSocialState
PlayGesture
```

StateTree / AI decision owner remains lifecycle owner.

Use scoped tokens/handles:

- acquire on conversation start/node entry;
- include ConversationInstanceId and generation;
- release on transition/end/cancel/avatar switch;
- ignore late completion after release.

Do not let dialogue node completion permanently mutate AI task internals by pointer.

## 23. Conversation and replaceable Avatar

For games with respawn, transformation, possession, mounts, or disguise:

```text
Stable Agent / PlayerState identity
         owns long-lived gameplay truth
Current Avatar / Pawn
         owns temporary body/presentation
ConversationInstance
         binds semantic participant -> stable agent
```

On avatar generation change:

1. freeze or continue semantic conversation according to design;
2. invalidate old presentation callbacks;
3. unbind old mesh/camera/face/audio target;
4. resolve current avatar adapter;
5. reapply participant presentation role;
6. project current line/choices from canonical ConversationInstance;
7. do not replay authoritative node-enter business events merely to refresh presentation.

## 24. Conversation side-effect ordering

A choice can involve both external transaction and dialogue transition.

Define one of these explicitly:

### Validate external command before advance

```text
validate conversation choice
→ execute domain transaction
→ if success, commit dialogue transition
```

Use when domain mutation is required to make the choice valid.

### Reserve then commit

```text
validate
→ reserve external resource
→ commit conversation transition
→ commit external transaction
→ rollback reservation on failure
```

Use when stronger cross-domain atomicity is required.

Never:

```text
advance dialogue
→ maybe domain transaction fails
→ UI already shows next irreversible state
```

without a documented compensating model.

## 25. Read model for UI and presentation

UI should consume a stable presentation DTO, not poke mutable graph nodes.

Example:

```text
FConversationView
  ConversationInstanceId
  Revision
  CurrentNodeGuid
  SpeakerRoleId
  SpeakerDisplayData
  LineSemanticId
  LocalizedLine
  VoiceAssetRef
  Choices[]
      ChoiceId
      LocalizedText
      bEnabled / BlockReason presentation
```

The authoritative system may keep more internal data; UI receives only what it needs.

### Snapshot + delta

- opening dialogue UI: fetch current view snapshot;
- subsequent changes: apply revisioned deltas or replace snapshot;
- widget recreation: re-fetch current snapshot;
- JIP/reconnect: snapshot first;
- stale widget command: rejected by revision.

## 26. Enter events and save/resume

Saving a conversation is a **continuation contract**, not just a cursor snapshot. Tests should save/load from every latent or nested state (choice input, wait timer, async domain command, sub-dialogue/call stack, sequence cursor if semantic) and prove the next transition is identical after migration/rebind. Hidden runtime state is either serialized by stable identity or documented as deterministically reconstructible.

DlgSystem's resume API exposes `bFireEnterEvents`, correctly revealing a hard policy question.

Every side-effectful node entry must define replay semantics:

- `ReplayNever` — reward/transaction/business command already committed;
- `ReplayPresentationOnly` — rebuild subtitle/camera/pose;
- `ReplayIdempotent` — safe with semantic idempotency key;
- `ReplayAlways` — deliberately repeatable behavior.

Do not use a single global boolean for all event types in a large production game.

## 27. Local vs long-term history

DlgSystem distinguishes per-context visited history from global dialogue history for entry restrictions.

Production version should make scope explicit:

```text
ConversationLocal
PlayerPersistent
PartyPersistent
WorldPersistent
Account/Profile (only if design requires)
```

An authored “Only Once” restriction must declare *once per what*.

Avoid ambiguous “global” in networked games.

## 28. Determinism and selector/random nodes

If a selector/random dialogue node affects business semantics:

- Authority chooses;
- persist the selected semantic NodeGuid/ChoiceId when needed;
- use explicit random stream/seed if reproducibility matters;
- do not let each client independently pick a random branch.

For purely cosmetic local bark variation, local random choice may be acceptable when it cannot alter canonical gameplay state.

## 29. Import/export round-trip contract

DlgSystem has JSON/config IO plus editor human-readable/Twine tooling. A production narrative pipeline should treat external text formats as versioned authored inputs.

Round trip must preserve or explicitly migrate:

- DialogueDefinitionId / DialogueGuid;
- NodeGuid;
- ChoiceId/EdgeId;
- participant role IDs;
- semantic event/condition IDs;
- localization namespace/key or a deterministic reconstruction contract;
- content schema version.

Reject imports that silently regenerate stable IDs for already-shipped content.

### CI checks

Add content checks for:

- duplicate DialogueGuid;
- missing/duplicate NodeGuid;
- missing/duplicate ChoiceId;
- dangling destination;
- unknown participant role;
- missing localization identity;
- invalid command descriptor;
- unknown condition descriptor;
- stale compiled data;
- unresolved migration redirect.

## 30. Search/debug tooling should expose semantic identity

DlgSystem's editor search can include Dialogue/Node GUIDs, which is a strong production practice.

Debug output for a live conversation should include:

```text
ConversationInstanceId
ScopeKey
DialogueDefinitionId
CurrentNodeGuid
Revision
Participant bindings
Visible ChoiceIds
pending domain command IDs
last transition reason
```

Do not report only human-readable node text; translated text may be ambiguous and change across builds.

## 31. Testing matrix

DlgSystem includes IO round-trip test infrastructure, but the visible IO automation test is disabled by default and current source does not provide evidence of a full authoritative multiplayer suite.

A production dialogue system needs separate tests for:

### Definition/content

- compile graph -> runtime definition;
- GUID uniqueness;
- edge target resolution;
- localization key stability;
- import/export round trip;
- custom version migration.

### Runtime

- condition visibility;
- node entry restrictions;
- local/persistent history;
- selector behavior;
- enter-event idempotency;
- save/resume at each supported node type.

### Network

- Listen Host choice;
- Remote Autonomous client request;
- unauthorized client request;
- stale revision;
- duplicate request;
- simultaneous choice race;
- Dedicated Server with no UI/audio;
- JIP snapshot;
- reconnect snapshot;
- packet loss/reordering;
- avatar replacement during line/choice;
- participant actor destroyed/recreated.

### Cross-domain

- quest accept/advance failure;
- inventory payment success/failure;
- GAS command reject/cancel;
- StateTree social token cancellation;
- server rollback/structured failure.

## 32. Performance checklist

Do not optimize conversation systems blindly, but avoid obvious high-frequency debt:

- no all-world participant scans each frame;
- no load-all-dialogues in gameplay hot path;
- no reflection variable lookup every UI frame for unchanged text;
- no repeated rebuilding of the full available-choice set if dependencies have not changed;
- no repeated sync asset load on each line;
- cache compiled ID -> index maps;
- use event/fact subscriptions to re-evaluate conditional choices when relevant state changes;
- profile localization/text formatting if bark/subtitle volume is high.

## 33. Anti-pattern ledger from DlgSystem

Useful source evidence that must **not** be copied as production doctrine:

1. `FDlgMemory` is a process-global singleton and source itself questions multiplayer friendliness.
2. `UDlgContext` replicates Dialogue and serialized participant refs but does not form a complete Authority protocol.
3. SpeechSequence contains a replication TODO/hack for actual sub-index state.
4. choice API uses visible option index without stable edge/choice identity.
5. generic event system can reflectively mutate arbitrary participant class variables/functions.
6. condition callback API cannot enforce purity.
7. default participant discovery scans world Actors and is explicitly not for per-frame use.
8. IO automation test is disabled by default.

Keep these in reviews as risk detectors.

## 34. Decision table: retain, adapt, reject

| DlgSystem mechanism | Production verdict | SkillForge transformation |
|---|---|---|
| Editor graph -> compiled runtime nodes | Retain | Keep authoring/runtime boundary |
| DialogueGuid + NodeGuid | Retain | Stable semantic save/content identity |
| NodeIndex | Adapt | Hot lookup only after stable-ID resolve |
| Participant interface | Adapt | Split semantic role/stable agent from ephemeral UObject adapter |
| FText namespace/key handling | Retain | Keep separate from semantic line identity |
| Text arguments | Adapt | Projection-time pure reads; avoid hot reflection |
| Resume by NodeGuid | Retain | Add schema/content migration and substate |
| Visited index fallback | Adapt | Explicit legacy migration bridge only |
| Global FDlgMemory | Reject as multiplayer truth | Scope by Player/Party/World/Conversation |
| Replicated UDlgContext refs | Adapt | Add Authority ConversationInstance, revision, choice protocol |
| Option index as command | Reject | Stable ChoiceId + revision |
| Reflective mutation event | Reject for core domains | Typed Authority domain command |
| World participant scan | Adapt | Convenience/editor/small SP only; registry for production |
| IO/Twine/human-readable pipeline | Retain/adapt | Preserve stable IDs/localization identities + CI roundtrip |

## 35. Code-review questions

When reviewing dialogue code, ask:

1. What is the stable ConversationInstanceId?
2. What is the dialogue definition identity?
3. What survives asset/node/line text rename?
4. Is current node saved by GUID or by array index?
5. Does every network-visible choice have stable identity?
6. Does the client send choice intent or authoritative outcome?
7. Is there a revision/generation fence?
8. Are conditions pure?
9. Which domain owns each event side effect?
10. Can reconnect/JIP rebuild from a snapshot without event replay?
11. How are player/party/world histories scoped?
12. What happens when the current participant Pawn is replaced?
13. Are localization keys preserved independently of text?
14. Can a Dedicated Server progress with no UI/audio/animation?
15. What happens when active content is removed in a patch?
16. Can imports silently regenerate stable IDs?
17. Are enter events replay-safe after save/load?
18. Are test cases covering stale/duplicate/racing choice requests?

## 36. Minimum production contract

A dialogue implementation is not production-ready until all of these are explicit:

- compiled runtime definition;
- stable Dialogue/Node/Choice identities;
- participant semantic role binding;
- canonical ConversationInstance;
- scoped memory ownership;
- pure condition reads;
- typed Authority side-effect commands;
- revisioned choice protocol;
- snapshot-first JIP/reconnect;
- localization identity contract;
- save schema + definition custom version + content migration;
- avatar-rebind generation fencing;
- cross-domain Quest/Inventory/GAS/AI boundaries;
- CI content validation and runtime/network tests.

DlgSystem provides strong evidence for the authoring, GUID, localization, adapter, resume, and tooling portions of this contract. SkillForge intentionally supplies the missing Authority, scoped-memory, stable-choice, JIP, and cross-domain production boundaries.
