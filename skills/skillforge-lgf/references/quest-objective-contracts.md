# LGF Quest / Objective Contracts

Use this reference when LGameplayFramework adds or integrates questlines, objective progress, quest journals, quest givers, shared/world quests, quest rewards, quest save/load, or a graph-based quest authoring tool.

This contract extends the generic [Quest / World Flow 编排](quest-world-flow-orchestration.md) rules with domain-specific lessons distilled from `TheGeebus/SimpleQuest@46978ad2c81ba90f21836e7c468141523dedb95d` (0.8.1, UE 5.6–5.8 target range).

## 1. LGF quest architecture

Use this ownership split:

```text
Quest Authoring Graph
        ↓ compile
Quest Definition DTO
        ↓
LQuestAuthority / Quest Manager
        ↓ sole writer
Quest Canonical State + Reward Ledger
        ↓
Quest Read Model / Journal Projection
        ↓
UI / Markers / Dialogue / Telemetry
```

External domains remain authoritative for their own state:

```text
Combat -> kill/damage truth
Inventory -> item/currency truth
Progression -> XP/unlock truth
WorldState -> world fact truth
GAS -> ability/effect truth
Mover -> movement truth
```

The quest system coordinates these domains. It does not replace them.

## 2. Quest scope is explicit and Avatar-independent

LGF already separates stable owner from replaceable Avatar. Quests must follow the same rule.

```text
Player scope -> StablePlayerId / AgentId
Party scope  -> StablePartyId
World scope  -> StableWorld/Shard identity
Shared scope -> explicit SharedQuestScopeId
```

Then:

```text
ScopeKey + QuestDefinitionId -> QuestInstanceId
```

Never use current:

- Pawn;
- Character;
- mount actor;
- AIController;
- PlayerController UObject pointer;

as the sole durable quest identity.

### Transform / absorb / mount

When the player:

- absorbs an NPC;
- transforms into another NPC;
- becomes a prop;
- mounts a pet;
- changes Pawn due to respawn;

only runtime interaction bindings change.

Quest state continues under the stable player/agent identity.

Old Avatar callbacks carry AvatarGeneration and cannot mutate current quest state after replacement.

## 3. Runtime quest definition is compiled data

Do not execute the editor graph in Shipping.

Compile:

```text
QuestlineId
ContentGuid
ObjectiveGuid
Entry routes
Named OutcomeTag / PathIdentity
Step conditions
Objective references
Reward definitions
Display metadata refs
Linked quest placements / aliases
```

into a runtime definition that can be loaded without editor modules.

Keep editor graph layout and pin widgets outside Runtime.

### LGF content ID rule

Use IDs that survive asset/display renames.

Recommended shape:

```text
QuestDefinitionId / QuestTag
QuestContentGuid
ObjectiveGuid
SemanticOutcomeId
SemanticRewardId
```

If designer-facing labels change, these IDs do not.

## 4. QuestDefinition and QuestInstance are separate

```text
QuestDefinition
= immutable/data-driven authored content

QuestInstance
= owner/scope-specific runtime state
```

A definition may be active for:

- player A;
- player B;
- party C;
- world event D;

at the same time without sharing mutable progress accidentally.

## 5. Manager is sole writer; Journal/State is the public reader

LGF should not expose mutable quest manager internals to UI or other modules.

Command side:

```text
StartQuestRequest
AbandonQuestRequest
AdvanceQuestRequest
TrackQuestRequest
RetryQuestRequest
```

Read side:

```text
GetQuestPhase
GetQuestObjectives
GetQuestProgress
GetQuestBlockers
GetTrackedQuests
GetQuestDisplayData
GetOutcomeHistory
```

The UI receives stable DTO/projection data, not `UQuestObjective*` as long-term truth.

## 6. Client request is intent, never truth

Client can ask:

```text
Accept quest X
Advance using choice Y
Track quest X
Abandon quest X
```

Authority resolves:

- stable caller identity;
- quest scope;
- QuestInstanceId;
- current phase;
- expected revision;
- current step;
- conditions;
- blockers;
- objective completion;
- advancement holds;
- valid outcome/path;
- reward idempotency state.

Only then does it commit.

Never accept:

```text
Client: Objective is complete
Client: Give me Victory outcome
Client: Add 100 progress
```

without domain evidence / server revalidation.

## 7. Objective progress comes from domain facts/events

Examples:

### Kill objective

```text
Combat Authority
→ KillEvent(DamageId, KillerStableId, VictimStableId, Tags)
→ Quest binding
→ ObjectiveGuid progress
```

### Collect objective

Prefer current inventory truth where possible:

```text
Inventory snapshot/count
→ compare required DefinitionId/quantity
```

A pickup event alone can be wrong after consuming, trading, destroying, rollback, or save/load.

### Reach objective

```text
Authority zone/trigger
→ stable ZoneId fact
→ quest objective
```

### Equipment objective

```text
Equipment canonical state delta
→ stable Item/Slot semantics
```

## 8. Objective subscription lifecycle

Every objective runtime binding stores:

```text
QuestInstanceId
ObjectiveGuid
QuestRevision / ObjectiveGeneration
subscription handle(s)
```

Lifecycle:

```text
Activate
→ register exact listeners
→ authoritative/current-state catch-up
→ consume live signals
→ Complete/Fail/Deactivate
→ unregister exact listeners
```

Save/load rebuilds listeners. It never restores old delegate handles.

## 9. Catch-up is state reconstruction, not history replay

A late-created Objective/UI needs current truth.

Examples:

- collect 10 items: query current Inventory count;
- quest completed: read completed state/history;
- prereq satisfied: read WorldState;
- tracked quest: read tracking state.

Do not replay every old pickup/kill event just to reconstruct the current number.

For genuinely event-counting objectives that cannot derive current state, persist their own objective progress snapshot keyed by ObjectiveGuid.

## 10. Dedupe repeated progress events

Use stable event IDs from the owning domain:

```text
Kill -> DamageId / KillId
Inventory -> TransactionId
Craft -> CraftOperationId
Dialogue -> DialogueResolutionId
World Event -> EventInstanceId
```

Consume with:

```text
QuestInstanceId + ObjectiveGuid + DomainEventId
```

or an equivalent dedupe ledger/window.

This prevents duplicate progress caused by:

- network retry;
- multiple tag aliases;
- step event route + objective binding;
- JIP catch-up followed by delayed live event;
- repeated GameplayMessage.

## 11. Conditions are pure read gates

LGF Quest Conditions must not mutate domains.

Good:

```text
HasItem(DefinitionId, 1)
PlayerLevel >= 20
WorldFact.BossDead
Quest X resolved with Outcome Y
PartySize >= 3
```

Bad:

```text
Condition checks key -> removes key
Condition checks mana -> spends mana
Condition checks faction -> grants reputation
```

Command path revalidates condition immediately before the write/consume transaction.

## 12. Named outcomes and path identity

Use semantic outcomes such as:

```text
Quest.Outcome.Completed
Quest.Outcome.Spared
Quest.Outcome.Betrayed
Quest.Outcome.TimedOut
```

Do not grow one bool per ending.

Keep `PathIdentity` when authored path matters independently from semantic outcome.

```text
Outcome = Spared
Path = TalkDownBoss
```

can be different from:

```text
Outcome = Spared
Path = BribeGuard
```

Future prerequisite logic can query either level intentionally.

## 13. Advancement holds compose with handles

Quest pacing is not one boolean.

Use:

```text
HoldHandle Hold(QuestScope, Reason, Policy)
Release(HoldHandle)
```

Reasons might be:

```text
Dialogue
Cinematic
RewardChoice
PartyVote
Streaming
WorldTransition
```

Only the final applicable hold release allows cascade.

### Important authority rule

A client cannot wait to see a replicated completion then place the hold; that is already after server advancement may have run.

Reserve/request the hold before the authoritative transition.

### Teardown

- exact handle release;
- duplicate release is safe;
- owner destruction releases owned holds or transfers them explicitly;
- debug view lists reason + owner + age;
- save policy explicitly says whether transient pacing survives save/load.

## 14. Reward grant is a domain transaction

Quest code describes and requests reward. Inventory/Progression/Currency system commits it.

```text
Quest completion
→ RewardCommand
  IdempotencyKey = QuestInstanceId + SemanticRewardId
→ domain Authority transaction
→ result
→ reward ledger mark
→ quest/UI event
```

If reward command retries after reconnect/load, ledger returns AlreadyApplied instead of granting twice.

For multiple rewards, define atomicity:

- all-or-nothing transaction; or
- per-reward ledger with resumable partial completion.

Never silently half-grant a reward bundle.

## 15. Snapshot format

LGF quest save should include at least:

```text
SaveSchemaVersion
QuestContent/DefinitionVersion
Quest clock if game semantics need it
ScopeKey
QuestInstanceId / QuestId
phase/current step
world/quest facts required by quest system
entry/resolution history needed by prerequisites
ObjectiveGuid -> progress snapshot
deferred activations
tracked quest state
reward ledger
soft definition IDs/paths needed to restore
```

Do not save:

```text
UQuestObjective* pointer
current Pawn pointer
AIController pointer
signal listener handle
editor graph node pointer
widget state
```

## 16. Restore ordering

Recommended:

```text
1. Parse snapshot into staging
2. Validate SaveSchemaVersion
3. Migrate schema
4. Resolve QuestDefinition/ContentVersion
5. Migrate content IDs / outcomes / objectives
6. Restore domain facts/history
7. Async-load required quest definitions
8. Register compiled definitions
9. Rebuild active/deferred QuestInstances
10. Restore ObjectiveGuid progress
11. Rebind signals
12. Rebuild Journal/read projection
13. Restore reward ledger
14. Publish one coherent revision
```

Do not broadcast every intermediate mutation to UI while restore is half complete.

## 17. Active-world load

If loading without leaving the current world:

```text
block new quest commands
→ quiesce old quest runtime
→ build staging state
→ migrate/validate
→ swap canonical state
→ destroy/unbind old runtime
→ rebuild new runtime
→ resync read model/clients
→ unblock requests
```

On failure, keep old live state or enter a deliberate safe/recovery state.

## 18. Content migration

Quest save schema can remain version 1 while a quest definition changes meaning. Therefore content migration is separate.

Maintain mappings like:

```text
OldContentGuid -> NewContentGuid
OldObjectiveGuid -> NewObjectiveGuid(s)
OldOutcomeTag -> NewOutcomeTag
OldQuestId -> NewQuestId
```

For split/merge migrations, write explicit progress transformation.

Historical fixture tests should cover at least N-1 and N-2 released saves.

## 19. Linked questline placements

When reusable quest content is embedded in multiple questlines:

- source definition has canonical identity;
- each placement has explicit placement/context identity where needed;
- UI can display contextual path;
- save resolves the exact placement without leaf-name guessing;
- progress is not accidentally shared between two placements unless explicitly designed that way.

## 20. Dedicated server and mirror

Dedicated server owns:

- lifecycle transitions;
- objectives;
- conditions;
- reward commands;
- quest scope state.

Client gets:

```text
QuestReadSnapshot(revision)
+ later QuestReadDelta(revision)
+ optional presentation events
```

Host uses the same Authority validation even when no RPC hop is needed.

## 21. JIP and reconnect

On JIP:

```text
receive canonical read snapshot
→ install revision R
→ build journal/map/dialogue projection
→ subscribe deltas > R
```

If delta sequence gaps or arrives stale:

```text
reject / request resync
```

Do not reconstruct quest state from notifications that happened before the client joined.

## 22. Quest Journal is the one UI read model

Avoid independent caches in:

- quest log;
- HUD tracker;
- map marker;
- NPC icon;
- dialogue menu.

They should query/observe the same read projection.

A journal record can contain:

```text
QuestId / QuestInstanceId
scope
phase
DisplayData reference
objective summaries
progress
blockers
tracking
latest outcome
revision
```

UI never mutates these structures directly.

## 23. Quest Giver is a presentation/interaction role

A quest giver NPC is not the quest's owner.

The actor can disappear, transform, die, respawn, or be represented by Mass at distance.

Persist:

```text
QuestId
Giver semantic role / StableAgentId if required by design
```

not the runtime actor pointer.

At interaction time resolve current representation and revalidate availability.

## 24. Mass integration

Remote Mass agents should not each own a full quest graph runtime by default.

Use Mass/world facts to represent:

- giver availability summary;
- quest marker presentation;
- coarse narrative state;
- world event participation.

Promotion to Full LGF Avatar rebinds interaction/presentation to the same durable quest state.

## 25. StateTree integration

StateTree owns AI decision, not quest truth.

Quest can send a typed scripted intent/override such as:

```text
EscortTarget
GoToQuestLocation
WaitForDialogue
PlayQuestInteraction
```

StateTree decides/executes the agent action under priority/generation rules.

Quest completion waits for an authoritative result event, not for a Blueprint node to assume the AI did it.

## 26. GAS integration

A Quest can request:

```text
Activate semantic ability
Apply quest-related effect via Authority service
Wait for typed result
```

but it does not own PredictionKey/TargetData/ability internals.

If quest progress depends on combat, consume canonical Combat/GAS result events with stable identities.

## 27. Inventory integration

Collect/turn-in quests need two distinct semantics:

### Possession objective

"Have 10 herbs" -> query current inventory count.

### Acquisition objective

"Collect 10 herbs over time" -> persist objective counter keyed by stable inventory transaction/event IDs.

Do not accidentally use pickup count for a possession requirement or vice versa.

Turn-in:

```text
Authority checks quantity
→ inventory transaction reserves/removes items
→ only on success advance quest
```

## 28. Objective state versus quest phase

Do not derive the entire Quest phase from one Objective UObject.

Quest phase can include:

```text
Unknown
PendingPrereq
Offerable
Enabled
Live
Blocked
Resolved
Deactivated
```

Objective state is subordinate:

```text
Inactive
Active
Completed
Failed
Frozen
```

Keep these state machines separate so a quest can block/hold/retry without corrupting objective history.

## 29. Debugging requirements

LGF quest debugger should expose:

- stable owner/scope key;
- QuestDefinitionId / QuestInstanceId;
- compiled content source/version/hash;
- current phase;
- current content/step GUID;
- objective GUID + state + progress;
- subscriptions / last event ID;
- blockers / conditions;
- active advancement holds + reasons;
- deferred activations;
- outcome/path history;
- reward ledger;
- mirror revision / JIP state.

Use stable IDs in logs so reports survive asset/presentation renames.

## 30. Release acceptance matrix

Before shipping a quest framework change, test:

```text
Standalone
Listen Host
Remote Client
Dedicated Server
JIP
Reconnect
Travel
Respawn
Avatar transform
Mount/Dismount
Save/Load cold
Save/Load active-world
Objective late registration
Duplicate event
Quest/Event display rename
Objective GUID migration
Linked questline duplicated placement
Multiple named outcomes
Multiple holds
Reward retry
Inventory turn-in rollback
DLC/missing definition
Historical save fixture
```

## 31. Default LGF recommendation

For LGF, adopt the **architecture contracts**, not necessarily the SimpleQuest plugin as a hard framework dependency.

Recommended layering:

```text
LGF Quest Domain
  ├─ Definition compiler / data
  ├─ Authority manager
  ├─ stable state store
  ├─ objective runtime adapters
  ├─ journal/read model
  ├─ save/migration
  └─ adapters
       ├─ Combat
       ├─ Inventory
       ├─ GAS
       ├─ WorldState
       ├─ StateTree
       └─ Mass/Avatar
```

If SimpleQuest is integrated directly, keep it behind an adapter so LGF public contracts remain stable when the external plugin evolves.
