# Quest / Objective Runtime Patterns

Use this reference when a UE C++ task involves quest definitions, objectives, quest-step routing, save/restore, quest event buses, quest journals, shared quests, dedicated server support, or authoring-graph compilation.

This reference distills production-oriented rules from `TheGeebus/SimpleQuest@46978ad2c81ba90f21836e7c468141523dedb95d` (SimpleQuest 0.8.1, 2026-09-14) and integrates them with the existing SkillForge FlowGraph, Authority, networking, persistence, and UI contracts.

## 1. Version and evidence gate

SimpleQuest 0.8.1 is a current-to-target sample for UE 5.7 work:

- current `main` commit: `46978ad2c81ba90f21836e7c468141523dedb95d`;
- the commit tree is `daf658bd6c86f54ca024d76e58a9a81908635617` — do not confuse tree SHA with commit SHA;
- README explicitly targets Unreal Engine 5.6–5.8;
- `SimpleQuest.uplugin` is 0.8.1 and separates Runtime, UncookedOnly and Editor modules;
- StateTree / GameplayStateTree are plugin dependencies;
- the repository is active and the pinned commit is the 0.8.1 merge.

Even for a current project, apply the normal evidence ladder:

1. README claim;
2. descriptor / Build.cs / module boundary;
3. active header/cpp path;
4. automated tests;
5. target-project UBT / PIE / Dedicated / JIP verification.

Do not promote README claims to production rules when the active runtime path differs.

## 2. Authoring graph and runtime definition are different products

A visual quest graph is an authoring surface, not the runtime state machine.

Preferred pipeline:

```text
UEdGraph / editor nodes
        ↓ compile / validate
runtime quest definition
        ↓
QuestlineId / ContentGuid / ObjectiveGuid
entry routes / outcome routes
conditions / rewards / objective refs
        ↓
Authority quest runtime
```

The Shipping runtime should not need to traverse `UEdGraph`, editor pins, node coordinates, graph widgets, or uncooked editor objects.

SimpleQuest demonstrates this strongly:

- `UQuestlineGraph` owns editor graph data but also stores compiler output;
- `CompiledNodes` is the runtime tag-to-node registry;
- `EntryNodeTags` is compiler-generated entry routing;
- compiled aliases preserve linked-questline perspectives;
- `CompiledSourceHash` detects stale compiler output;
- linked questline content is inlined at compile time;
- questline-level rewards are flattened into runtime-reachable compiled data.

### Production rule

When introducing a quest authoring graph:

- compile authoring objects into a compact runtime definition;
- validate all semantic references before cook;
- fail cook/CI on duplicate IDs, missing objective targets, invalid outcomes, illegal links, or stale compiled data;
- keep Runtime modules independent of Editor/UncookedOnly modules;
- use soft asset references only where runtime loading is genuinely required.

### Compile-time validation checklist

At minimum validate:

- unique QuestlineId / QuestId;
- stable ContentGuid / ObjectiveGuid uniqueness;
- every objective reference resolves;
- every entry / outcome route resolves;
- named outcomes are unique within their semantic scope;
- no illegal linked-graph recursion/cycle;
- reward definitions are valid;
- condition types are valid for the target build;
- compiled source hash/version matches authoring source;
- editor display names are not used as persistence IDs.

## 3. Stable semantic identity is not a display label

Quest authoring has many names that designers must be free to change:

- graph asset name;
- display title;
- objective display name;
- event label;
- pin label;
- description;
- editor comment.

These are not durable identity.

Use stable identities such as:

```text
QuestlineId
QuestTag / QuestId
QuestContentGuid
ObjectiveGuid
PathIdentity / OutcomeTag
QuestInstanceId (runtime)
```

SimpleQuest's `UQuestObjective` has a persistent `ObjectiveGuid`; `FQuestStep` carries `SourceNodeGuid`; compiled questline nodes preserve contextual identity; questline `DisplayName` is explicitly presentation-only while `QuestlineID` forms the semantic namespace.

### Rename rule

A designer rename should:

1. update editor presentation;
2. reconstruct affected pins/references if necessary;
3. preserve stable semantic GUID / ID;
4. preserve save compatibility;
5. preserve analytics and routing identity.

If the designer is changing semantics rather than a label, use an explicit migration / redirect / tombstone, not silent GUID reuse.

### Copy / duplicate rule

Copying a quest node is not the same as aliasing it.

- duplicate authored node -> normally generate a new content/objective GUID;
- linked/inlined placement -> retain canonical source identity plus explicit placement/context identity;
- reparent/relink -> migration must state whether old save identities redirect or become obsolete.

## 4. Quest domain CQRS: writer and reader are separate contracts

A mature quest system benefits from an explicit command/query split.

```text
Request / command
      ↓
Authority Quest Manager
      ↓ sole writer
canonical quest/domain state
      ↓
Quest State / Journal read model
      ↓
UI / markers / dialogue / telemetry
```

SimpleQuest documents this directly:

- `UQuestManagerSubsystem` is the opaque orchestrator and sole writer;
- `UQuestStateSubsystem` is the public read-side registry;
- write access to state is friend-controlled;
- adopter-facing request methods live outside manager internals;
- state queries are pure and do not require manager mutation.

### Why this matters

Do not let UI or quest consumers depend on:

- `LoadedNodeInstances`;
- internal cascade maps;
- transient objective UObjects;
- manager-specific delegate internals;
- mutable manager containers.

Instead expose stable read DTOs for:

- quest phase;
- objective progress;
- blockers / prerequisites;
- tracking state;
- entry / outcome history;
- display data;
- stable quest identity;
- current revision / generation where networking needs it.

The writer can evolve without rewriting every UI and gameplay consumer.

## 5. Runtime Objective objects are behavior/lifecycle objects, not persistence identity

An Objective UObject can be useful when it owns:

- signal subscriptions;
- runtime behavior;
- blueprint extension points;
- local progress logic;
- activation / completion / failure hooks.

But the UObject pointer is not the long-term identity.

SimpleQuest's objective contract includes:

- stable `ObjectiveGuid`;
- explicit active/completed/failed/frozen state;
- progress API;
- progress snapshot / restore;
- signal subsystem binding;
- manager binding;
- cleanup on destruction.

Production split:

```text
Objective definition / descriptor
          +
ObjectiveGuid / ContentGuid
          ↓
runtime Objective UObject
          ↓
progress snapshot / canonical quest state
```

The runtime UObject may be destroyed and rebuilt after:

- travel;
- save/load;
- JIP;
- quest graph reload;
- avatar replacement;
- dedicated/client read-model rebuild.

The saved quest does not care which UObject instance happened to exist before the transition.

## 6. Event-driven objective progression

Objectives should not all Tick the world.

Prefer:

```text
Combat / Inventory / World / Interaction domain
                ↓ typed event/fact
Signal bus / explicit subscription
                ↓
QuestInstanceId + ObjectiveGuid binding
                ↓
Objective consumes event
                ↓
Authority progress commit
```

Examples:

- kill objective -> Combat kill ledger/event;
- collect objective -> Inventory canonical count or delta;
- reach objective -> authoritative overlap/zone fact;
- equip objective -> Equipment state change;
- world event objective -> WorldState fact;
- dialogue objective -> dialogue result event.

### Subscription lifecycle

Every objective subscription needs:

- stable quest/objective identity;
- exact listener handle or equivalent owner registration;
- explicit activation point;
- explicit deactivation / destroy cleanup;
- runtime generation where stale callbacks are possible;
- safe no-op for late callbacks after quest teardown.

## 7. Live event versus durable state

Not every event can be reconstructed after a listener arrives.

Distinguish:

### Durable/current state

Examples:

- quest is Enabled;
- quest is Live;
- quest is Completed;
- objective count is 7/10;
- prerequisite fact is true;
- quest is tracked.

A late subscriber can catch up from a state snapshot.

### Transient event

Examples:

- progress pulse animation;
- refusal feedback;
- transient audio cue;
- one interaction attempt.

These can legitimately have no catch-up.

SimpleQuest's `UQuestObserverComponent` explicitly differentiates catch-up-capable lifecycle state from transient events and defers registration until the tick after BeginPlay so the owning actor can finish initialization before synthetic/current events arrive.

### Late-registration rule

```text
register listener
→ owner fully initialized
→ read canonical/current quest state
→ synthesize only catch-up-capable state events
→ begin live delta/event consumption
```

Do not require unbounded historical event replay just so a UI/objective can discover current truth.

## 8. Event deduplication must be a declared contract

Complex quest systems can route one domain signal to the same objective through multiple paths:

- step-level QuestEvent routing;
- objective-specific signal bindings;
- parent-tag hierarchical delivery;
- canonical tag + alias perspective;
- JIP catch-up followed by a live event;
- network retry.

Define dedupe identity explicitly, for example:

```text
QuestInstanceId
+ ObjectiveGuid
+ OriginatingEventID / DamageId / ItemTxnId
+ dispatch generation
```

Default behavior for progress-affecting signals should be at-most-once per objective per stable event identity unless the objective explicitly opts into multi-delivery.

Do not infer dedupe from UObject pointer equality or the event's display name.

## 9. Lifecycle event enums are public compatibility surfaces

SimpleQuest deliberately keeps two event shapes:

- a wide bitmask for subscription/exposure configuration;
- a single-value Blueprint-friendly arrival enum.

It also appends new enum values rather than inserting them mid-list because authored Blueprint switch values may already rely on ordinal stability.

General rule:

- serialized / Blueprint-authored enums are compatibility surfaces;
- append where practical;
- avoid renumbering old values;
- separate bitmask configuration from single-value runtime identity when their reflection/storage requirements differ;
- write explicit conversion helpers and tests.

## 10. Named outcomes beat boolean branch explosion

Quest completion is rarely just success/fail.

Prefer stable semantic outcomes:

```text
Outcome.Victory
Outcome.Spared
Outcome.Bribe
Outcome.TimedOut
Outcome.Failed
```

rather than:

```text
bSucceeded
bFailed
bSpared
bBribed
...
```

### OutcomeTag versus PathIdentity

These are not always the same thing.

- `OutcomeTag` says **what semantic result occurred**.
- `PathIdentity` says **which authored route produced it**.

Two different paths can both produce `Outcome.Victory` while prerequisites or analytics may need to know which route was used.

Save/history can therefore store both.

### Authority rule

A client must not be able to send an arbitrary outcome tag and skip the quest graph.

On advance, Authority revalidates:

- quest instance / owner scope;
- current step;
- expected revision/generation;
- objectives complete;
- conditions satisfied;
- holds allow advancement;
- requested outcome/path is valid from this node;
- reward/route has not already committed.

## 11. Quest Conditions are pure predicates

A prerequisite/condition is a query, not a command.

```text
Condition(Context, Facts) -> Satisfied / Blocker / Reason
```

Condition evaluation must not:

- remove an item;
- spend currency;
- grant reward;
- apply GameplayEffect;
- mutate quest state;
- spawn gameplay actors;
- claim a SmartObject.

Why:

- conditions may be evaluated for UI previews;
- enablement watches may reevaluate repeatedly;
- catch-up may reevaluate;
- server validation may reevaluate after network delay;
- editor/debug tooling may inspect conditions.

A side-effectful predicate creates duplicates and TOCTOU bugs.

If the operation must consume a key/item, do:

```text
read condition
→ request command
→ Authority revalidates
→ domain transaction consumes resource
→ quest commit
```

## 12. Conditions are Authority gates even when UI predicts them

Client-side mirrored conditions are useful for:

- showing locked quest;
- displaying reason text;
- enabling/disabling a button;
- local responsiveness.

They are not permission.

The server must re-evaluate against canonical:

- player/party/world facts;
- quest phase;
- inventory/equipment state;
- level/progression;
- block state;
- current revision.

Never trust `Client says condition passed`.

## 13. Advancement holds are scoped resources, not booleans

Async presentation may need to pause quest auto-advance:

- dialogue;
- cinematic;
- voiced line;
- scripted world transition;
- multiplayer vote;
- reward selection UI.

Do not use one `bPauseQuestAdvance`.

Use scoped holds:

```text
HoldA = HoldQuestAdvancement(QuestTag, Reason.Audio)
HoldB = HoldQuestAdvancement(QuestTag, Reason.Cinematic)

Release(HoldA) -> still held by B
Release(HoldB) -> cascade may resume
```

SimpleQuest explicitly supports exact/ancestor quest holds, required reason labels, release handles, active-reason inspection, and only resumes after the last applicable hold clears.

### Authority timing

The hold must exist before the Authority cascade executes.

A client cannot safely observe `Completed` and only then decide to place a server hold—the server may already have advanced.

If client UX requires a hold, request/reserve it before the completion transition.

### Save/load policy

Decide explicitly whether pacing holds survive save/load.

SimpleQuest intentionally releases all advancement holds before snapshot capture: pacing is transient and should not restore a save that appears permanently stuck.

Another project may choose differently, but it must be a deliberate schema rule.

## 14. Holds park semantic work, not raw pointers

When a cascade is held, store enough stable context to revalidate later:

- QuestInstanceId / QuestTag;
- source ContentGuid;
- outcome/path identity;
- originating event identity;
- revision / generation;
- inherited activation data required by the route.

On release:

1. resolve current quest instance;
2. verify it is still at the expected phase/revision;
3. verify route is still valid;
4. execute or discard.

Do not park a lambda capturing a transient Node UObject by reference and execute it later without revalidation.

## 15. Snapshot should persist domain state, not runtime object topology

SimpleQuest's `FSimpleQuestSaveSnapshot` is a useful domain-oriented example. It stores:

- `Version` schema version;
- quest play-time domain;
- WorldState facts;
- quest resolution history;
- quest entry history;
- soft paths for graphs involved;
- deferred activations keyed by persistent content GUID;
- objective state keyed by persistent placement/content GUID.

It explicitly does not store derived lookup indices; those rebuild on apply.

This is preferable to serializing runtime UObject pointers or an editor graph.

### Save principles

Persist:

```text
SchemaVersion
Stable quest/content/objective IDs
Canonical facts / histories
Objective progress
Deferred semantic intent
Required definition soft IDs
```

Rebuild:

```text
runtime objective UObjects
subscriptions
parallel lookup indices
manager maps
UI journal projection
client mirror
```

## 16. Schema version and content-definition version remain separate

`FSimpleQuestSaveSnapshot::Version` handles snapshot schema changes.

That does not replace the R13 requirement for content/definition migration.

You still need a separate notion of quest definition/content version when released content changes semantics:

- objective split/merge;
- step reordering;
- outcome rename;
- content GUID redirect;
- linked questline moved;
- DLC removed;
- reward changed.

Think of:

```text
SaveSchemaVersion = how bytes/fields are shaped
QuestDefinitionVersion = what those fields mean in this authored quest
```

## 17. Deferred activation is first-class saved runtime intent

An important quest-specific lesson is that not all meaningful runtime state is a boolean fact.

If a node is waiting on a prerequisite at save time, restoring only facts and completed history can lose the future wake-up behavior.

Persist stable deferred intent:

```text
ContentGuid -> activation context
```

On restore:

- resolve current definition node by GUID;
- re-run activation/gate logic;
- if condition now passes, proceed;
- otherwise resubscribe / remain deferred.

Do not serialize the old listener/delegate handle.

## 18. Runtime graph restoration should be self-describing

A quest snapshot can keep soft definition paths/IDs for graphs that were participating at capture time.

This lets restore say:

```text
snapshot
→ async-load required definitions
→ apply facts/history
→ register runtime definitions
→ rebuild live objectives/deferred activations
```

rather than requiring the calling game to manually remember which quest graph assets were alive.

Still validate soft paths against allowed content and target version; a save must not become an arbitrary asset-loader command channel.

## 19. Player / shared / world quest scope is part of identity

Quest state must declare its scope.

Typical forms:

```text
Player quest   -> StablePlayerId + QuestId
Party quest    -> StablePartyId + QuestId
World quest    -> World/Shard identity + QuestId
Shared quest   -> explicit shared scope key
```

Do not infer scope from current Pawn or PlayerController pointer.

When a player:

- respawns;
- transforms;
- mounts;
- changes Pawn;
- reconnects;

quest identity should remain the same.

## 20. Dedicated server is the canonical writer

A quest framework claiming multiplayer support should not require visual actors, UI, or client graph callbacks to finish gameplay state.

Authority path:

```text
Client intent
→ server request endpoint
→ resolve stable player / quest scope
→ current-state validation
→ canonical manager mutation
→ read model/mirror update
→ replicated snapshot/delta/event projection
```

Client graph/UI can present the result but does not create the truth.

### Server request validation

For start/abandon/advance/retry/resume:

- validate player ownership/permission;
- resolve known quest;
- validate phase;
- validate expected step/revision;
- validate conditions/blockers;
- validate outcome/path;
- validate hold state;
- enforce idempotency;
- only then mutate.

RPC existence is not validation.

## 21. JIP / reconnect uses snapshot first, event second

The read model must be reconstructible without replaying every historical event.

```text
JIP client
→ canonical quest snapshot / mirror
→ build journal/markers/dialogue availability
→ establish revision cursor
→ consume later delta/events
```

Events carry enough identity to reject:

- duplicate;
- stale;
- wrong player scope;
- wrong quest generation;
- previous avatar callbacks.

## 22. Journal / UI is a projection

UI should query a single stable read model, not maintain independent hidden quest state in each widget.

The read model should expose DTO-like information such as:

- QuestId;
- display metadata;
- phase;
- current objective summaries;
- progress;
- blockers;
- tracked flag;
- latest outcome / history when relevant;
- revision.

Then:

```text
Journal
Map Marker
NPC Quest Icon
Dialogue availability
HUD tracker
```

all derive from the same canonical read-side model.

## 23. Outcome/event payload should carry provenance

Complex quest events benefit from provenance:

- Instigator;
- origin tag;
- origin chain;
- originating event ID;
- canonical quest tag;
- matched delivery channel;
- content/node info;
- path/outcome.

This lets hierarchical/tag-routed systems distinguish:

```text
what actually happened
```

from:

```text
why this subscriber received it
```

Do not replace stable provenance with the last Actor pointer seen by a widget.

## 24. Aliases and linked placements need canonical identity

When linked questlines are inlined or exposed under multiple graph perspectives:

- canonical content identity remains stable;
- aliases represent placement/context;
- a runtime node can publish on multiple semantic channels without becoming multiple business instances;
- save/progress uses the canonical content/placement identity defined by the compiler contract.

Avoid leaf-name-only lookup; it collides when the same linked content appears more than once.

## 25. Rewards are external domain transactions

A quest definition may describe rewards, but reward truth belongs to the domain that owns the resource.

Pattern:

```text
Quest resolves outcome
→ resolve reward definitions
→ Reward Command(IdempotencyKey)
→ Inventory/Currency/Progression Authority transaction
→ success/reject
→ ledger commit
→ quest projection/event
```

Use an idempotency key such as:

```text
QuestInstanceId + SemanticRewardId
```

or equivalent stable grant identity.

Retry/save/load/reconnect must not duplicate reward grants.

## 26. Editor rename/reconstruct must preserve runtime ABI

Editor code should react to mutable authoring properties:

- event name;
- outcome name;
- objective reference;
- linked questline;
- pin configuration.

When these change:

- reconstruct affected pins;
- update compiler references;
- invalidate compiled source hash;
- validate missing old routes;
- preserve stable GUIDs unless the semantic object is actually replaced.

The editor representation can change shape without silently changing persisted business identity.

## 27. Performance rules

Quest systems are usually low-frequency orchestration systems. Keep them that way.

Avoid:

- Objective Tick polling inventory/combat/world every frame;
- full graph traversal on every signal;
- non-exact hierarchical tag scans in hot loops;
- repeated sync asset load on interaction;
- rebuilding every journal DTO for one progress delta;
- client and server independently executing all quest orchestration.

Prefer:

- signal-driven subscriptions;
- indexed QuestId / GUID maps;
- cached compiled routes;
- async definition preload;
- incremental read-model projection;
- LOD/budget only if quest/event counts become genuinely large.

## 28. Debugging contract

A useful quest debug surface should show:

```text
Quest scope / owner key
QuestId / QuestInstanceId
Definition/content version
Current phase
Current step/content GUID
Objective GUID + progress
Condition/blocker summary
Pending/deferred activation
Active advancement holds + reasons
Last originating event ID
Outcome/path history
Read-model revision
Reward ledger status
```

Without stable IDs and provenance, a graph debugger becomes a collection of pretty node highlights that cannot explain production desyncs.

## 29. Minimum validation matrix

For a production quest feature, test at least:

- standalone;
- Listen Host;
- remote client;
- Dedicated Server;
- JIP;
- reconnect;
- respawn / Pawn replacement;
- transformation / mount;
- save/load before objective completes;
- save/load while prerequisite-deferred;
- save/load after completion but before presentation finishes;
- late observer registration;
- duplicate signal delivery;
- quest event rename;
- objective display rename;
- content GUID migration;
- named outcome change;
- multiple concurrent advancement holds;
- client retry / duplicate request;
- reward transaction retry;
- missing/DLC quest definition;
- historical save migration.

## 30. Review questions

Before approving a quest runtime change, answer:

1. What is the stable quest instance identity?
2. What is the stable content/objective identity?
3. What is authoring-only presentation?
4. Who is the sole writer?
5. What can clients request versus decide?
6. What state is durable and what event is transient?
7. What catches up a late listener?
8. What dedupes repeated domain events?
9. What is the named outcome/path identity?
10. How do concurrent pacing holds compose?
11. What survives save/load?
12. What is rebuilt after restore?
13. How is definition migration distinguished from snapshot schema migration?
14. What is the reward idempotency key?
15. What proves the runtime works on Dedicated/JIP rather than only PIE standalone?
