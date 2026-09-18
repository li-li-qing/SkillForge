# R14 SimpleQuest Distillation Validation

Date: 2026-09-14

## Scope

Baseline: SkillForge FlowGraph R13.

Research target:

- `TheGeebus/SimpleQuest`
- default branch `main`
- commit `46978ad2c81ba90f21836e7c468141523dedb95d`
- commit tree `daf658bd6c86f54ca024d76e58a9a81908635617`
- SimpleQuest 0.8.1
- MIT
- README target UE 5.6–5.8

Important evidence correction: the tree SHA was initially at risk of being treated as a commit SHA. R14 records commit and tree independently; all source evidence is pinned to the commit.

## TDD boundary

Added behavior cases before writing the new formal references:

- UE C++ `CPP-84` through `CPP-92`
- LGF `LGF-54` through `LGF-58`

RED semantic probe against the R13 formal references:

```text
13/14 contracts missing
1/14 only partially touched by R13's generic Authority/idempotency guidance
```

Missing SimpleQuest-specific contracts included:

- compiled authoring graph -> runtime quest definition;
- ObjectiveGuid / ContentGuid stable identity;
- Manager sole writer / StateSubsystem read-side CQRS;
- late registration catch-up and progress dedupe;
- domain-shaped quest snapshot / deferred activation;
- named outcomes plus authored PathIdentity;
- scoped advancement hold handles;
- pure Authority quest conditions;
- Dedicated/JIP mirror/read projection;
- stable Player/Shared/World quest scope;
- Journal as a unified read model.

GREEN writeback added:

- `skills/skillforge-ue-cpp/references/quest-objective-runtime-patterns.md`
- `skills/skillforge-lgf/references/quest-objective-contracts.md`
- `docs/project-distillations/simplequest.md`

GREEN semantic probe:

```text
14/14 contracts covered
```

## Key accepted mechanisms

- Editor quest graphs compile to runtime maps/arrays/definitions; Shipping does not traverse `UEdGraph`.
- Stable QuestlineId, QuestContentGuid, ObjectiveGuid, OutcomeTag and PathIdentity are separated from display names and pin labels.
- `UQuestManagerSubsystem` is the opaque sole writer; `UQuestStateSubsystem` is a public pure read-side registry.
- Objective UObjects own runtime behavior and subscriptions but not durable identity.
- Event-driven objectives replace per-objective Tick scanning.
- Durable lifecycle state supports late-registration catch-up; transient Progress/Refusal events can intentionally have no catch-up.
- Progress-affecting signals require stable domain event identity/deduplication when multiple delivery routes can converge.
- Named outcomes avoid boolean branch explosion; PathIdentity remains available when authored route identity matters.
- Quest Conditions are pure read predicates; resource consumption/reward mutation happens after Authority revalidation through the owning domain transaction.
- Advancement pacing uses scoped hold handles with reason/ownership, not one boolean.
- `FSimpleQuestSaveSnapshot` is domain-shaped and versioned: WorldFacts, resolution/entry history, ActiveGraphs, DeferredActivations and ObjectiveStates; derived indices rebuild.
- Restore rebuilds live quest/objective state without replaying normal entry/forward lifecycle transitions.
- Dedicated server owns canonical mutation; clients use requests plus mirrored/read-side state.
- Player/shared/world quest scope is stable and independent from current Pawn/avatar.
- Journal, map marker, NPC quest icon and dialogue availability derive from one quest read model.
- Rewards remain external domain transactions with stable idempotency ledger in LGF.

## Explicit reject / adapt findings

- Do not use display/event/pin names as Save identity.
- Do not use Objective array index as the only durable objective identity.
- Do not expose Quest Manager mutable internals to UI/adopters.
- Do not let clients self-report arbitrary OutcomeTag/objective progress as canonical truth.
- Do not put gameplay side effects inside prerequisite/condition evaluation.
- Do not use one `bPauseQuestAdvance` for concurrent cinematic/audio/vote pacing.
- Do not restore by starting the graph from Entry again; this can duplicate side effects/rewards.
- Do not serialize delegate handles, UObject pointers, current Pawn pointers or editor graph pointers into long-term quest saves.
- Do not treat SaveSchemaVersion as a substitute for QuestDefinition/Content migration.
- Do not assume a same-day GitHub commit is production-ready without active-code evidence and target-engine verification.

## Fresh repository verification

### Self-contained validator

Command:

```text
python scripts/validate_skills.py --self-contained
```

Result:

```text
Validated 6 skill(s): 0 error(s); 6 standalone copies validated.
```

### Targeted validator tests

The first attempted targeted invocation used the wrong historical test class name (`SkillValidatorTests`) and therefore executed zero real tests. It is not counted as pass/fail.

The current repository class `ValidateSkillsTests` was then used.

Fresh targeted run:

```text
6/6 PASS
```

Covered:

- self-contained copied resources;
- main SKILL line budget;
- inline/reference link validity;
- repository link escape protection;
- absolute local path portability;
- behavior expectation / fixture validation.

### LGF inspector

Fresh run:

```text
10/10 PASS
```

### JSON

Before adding this validation report/manifest:

```text
44 JSON files parsed, 0 errors
```

Behavior counts after R14 behavior additions:

```text
UE C++: 92, last CPP-92
LGF: 58, last LGF-58
UI Design: 9, last UI-09
UE Blueprint: 5, last BP-04
```

### Full validator suite

Attempted:

```text
python -m unittest -v tests.test_validate_skills
```

Outer tool budget: about 220 seconds.

Observed before timeout:

```text
16 tests reported ok
then test_name_constraints_and_directory_match was the active test when the outer tool timed out
```

This is recorded as **full suite incomplete**, not a failure and not a full pass.

The active test was then run independently:

```text
R14 worktree: 1/1 PASS, 6.191 s unittest time (~6.86 s wall)
R13 baseline: 1/1 PASS, 5.687 s unittest time (~6.31 s wall)
```

No evidence indicates R14 introduced that historical full-suite timeout behavior.

## Diff review before validation artifacts

Relative to R13 baseline before adding this validation report/manifest:

```text
Added: 3
Changed: 9
Removed: 0
```

Added:

- `docs/project-distillations/simplequest.md`
- `skills/skillforge-lgf/references/quest-objective-contracts.md`
- `skills/skillforge-ue-cpp/references/quest-objective-runtime-patterns.md`

Changed:

- `docs/implementation-progress.md`
- `docs/project-distillations/README.md`
- `docs/research.md`
- `skills/skillforge-lgf/SKILL.md`
- `skills/skillforge-lgf/evals/behavior-cases.json`
- `skills/skillforge-lgf/references/external-project-patterns.md`
- `skills/skillforge-ue-cpp/SKILL.md`
- `skills/skillforge-ue-cpp/evals/behavior-cases.json`
- `skills/skillforge-ue-cpp/references/external-project-freshness-and-lyra.md`

No business/content file deletion occurred.

Line-ending check:

- LGF `SKILL.md` remained CRLF (only one logical line added).
- UE C++ `SKILL.md` remained LF.

## Formal content sizes

At pre-package verification:

```text
SimpleQuest project report: 1434 lines
UE C++ Quest runtime reference: 899 lines
LGF Quest objective reference: 777 lines
```

## Not executed

This round did **not** execute:

- SimpleQuest UE5.7 UBT/UHT;
- editor graph compilation inside UE Editor;
- packaged/cooked build;
- actual Dedicated Server + Remote Client runtime;
- JIP/reconnect runtime;
- 0.7 -> 0.8 historical save runtime migration;
- dynamic quest-pin rename editor interaction;
- reward transaction retry in LGF;
- large quest graph performance benchmark;
- direct LGF integration.

R14 therefore claims source-level distillation and SkillForge contract validation, not production integration of SimpleQuest into LGF.
