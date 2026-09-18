# FlowGraph R13 Distillation Validation

- Date: 2026-09-14
- Round: R13
- Topic: MothCocoon/FlowGraph -> Quest / World Event / Graph Runtime / Save ABI
- R12 baseline: `/mnt/data/skillforge_r13_baseline/SkillForge`
- R13 worktree: `/mnt/data/skillforge_r13_work/SkillForge`

## Source anchors

### Latest design anchor

- Repository: `MothCocoon/FlowGraph`
- Branch: `5.x`
- Commit: `c616a5d2afa8124cb7c1d66b1071fd499f2be7db`
- Commit date: 2026-08-31
- License: MIT
- Plugin descriptor: Flow 2.4, runtime/editor/debugger modules, no pinned EngineVersion.
- Release evidence: 2.4 is in works and is the first UE5.9 release.

### LGF target-compatible anchor

- Tag: `v2.3-5.7`
- Commit: `8211b25999068407cb7b40b8c97e18b52d4832ca`
- Reason: LGF current target is UE5.7; latest 5.x is already a UE5.9 development line.

## Freshness result

Classification:

```text
Latest FlowGraph source: Current source / next-engine branch
Flow 2.3-5.7: Current-to-LGF-target compatibility anchor
2.4-only API: future-version evidence, not direct UE5.7 production API
```

New freshness lesson: a maintained plugin can require both a latest design anchor and a target-engine tag. Serialized graph assets can also require staged migration/resave, independently of C++ API compatibility.

## Source areas reviewed

- `Flow.uplugin`
- `README.md`
- `docs/Releases/Version23.md`
- `docs/Releases/Version24.md`
- `docs/Features/SaveGameSupport.md`
- `docs/Features/SignalModes.md`
- `UFlowAsset`
- `UFlowNode`
- `UFlowSubsystem`
- `UFlowComponent`
- `UFlowNode_SubGraph`
- `FlowSave.h`
- `FFlowDeferredTransitionScope`
- `EFlowNodeState / EFlowFinishPolicy / EFlowSignalMode / EFlowNetMode`

## RED

Behavior cases were added before production references:

- CPP-76..CPP-83
- LGF-49..LGF-53

A semantic probe against the R12 formal references checked 13 intended contracts:

1. graph template vs runtime instance;
2. Flow FinishPolicy / Complete vs Abort latent cleanup;
3. deferred transition / execution gate / ordering;
4. persistent NodeId save ABI;
5. SubGraph lifecycle owner + synchronous-load boundary;
6. active-world staging restore;
7. canonical quest state vs transient notify;
8. narrative orchestration domain fit + debugging;
9. stable quest owner vs replaceable Avatar;
10. typed graph domain command + idempotency;
11. durable quest snapshot + event/JIP projection;
12. shipped quest graph migration;
13. FlowGraph / StateTree / Mass / Avatar separation.

Result before GREEN:

```text
RED missing 13/13
```

## GREEN implementation

Added:

- `skills/skillforge-ue-cpp/references/flow-graph-runtime-patterns.md`
- `skills/skillforge-lgf/references/quest-world-flow-orchestration.md`
- `docs/project-distillations/flowgraph.md`

Updated:

- UE C++ SKILL reference index
- LGF SKILL reference index
- UE C++ behavior cases
- LGF behavior cases
- external-project freshness guidance
- LGF external-project mapping
- distillation index
- research log
- implementation progress

GREEN semantic probe result:

```text
13/13 contracts covered
```

## Main accepted mechanisms

- FlowAsset definition/template separated from per-owner runtime instance.
- Node stable ID becomes save ABI once serialized in shipped saves.
- Latent node lifecycle owns its delegate/timer/async/domain resources.
- Complete/Keep differs from Abort/Cancel.
- Deferred transition scope is a reentrancy boundary; per-graph ordering does not imply a strict global FIFO across graphs.
- Parent SubGraph node owns child graph instance lifecycle.
- Soft asset pointer does not prove runtime async loading.
- Save/load needs project schema and graph-definition versioning around the graph serializer.
- Pass-through/tombstone/redirect is preferable to deleting persisted node IDs.
- Replicated notify events are projection/delivery, not durable quest truth or JIP snapshot.
- Graph orchestration issues typed domain commands into existing Authority services.
- FlowGraph belongs to sparse authored Quest/World/Narrative orchestration, not per-Mass-agent hot decision loops.

## Explicit reject / adapt findings

- Do not copy Flow 2.4/UE5.9-only APIs into LGF UE5.7 without adapter/backport verification.
- Do not use transient object names, Actor names or World names as the only Quest identity.
- Do not let client-only Flow execute canonical reward/inventory/damage state.
- Do not treat `TSoftObjectPtr` as proof of asynchronous activation; current SubGraph create path still contains synchronous loading.
- Do not remove or repurpose shipped persisted NodeGuid without migration.
- Do not rely on Flow notify history to reconstruct late-join quest state.
- Do not create one UObject FlowGraph brain per low-fidelity Mass NPC by default.

## Fresh verification

### Self-contained skill validator

Command:

```text
python scripts/validate_skills.py --self-contained
```

Result:

```text
Validated 6 skill(s): 0 error(s); 6 standalone copies validated.
```

### Targeted validator tests

Fresh targeted run:

```text
6/6 PASS
```

Covered:

- standalone resource copy;
- SKILL main-file line budget;
- inline/reference links;
- link escape protection;
- local absolute path portability;
- behavior expectations/fixture paths.

### LGF inspector

```text
10/10 PASS
```

### JSON

Before this report/manifest addition:

```text
43 JSON files parsed, 0 errors
```

Behavior counts after R13 cases:

```text
UE C++: 83, last CPP-83
LGF: 53, last LGF-53
UI Design: 9, last UI-09
UE Blueprint: 5, last BP-04
```

### Full validator suite

Attempted:

```text
python -m unittest -v tests.test_validate_skills
```

Tool budget: 220 seconds.

Observed before timeout:

```text
12 tests reported ok
then test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names was still running when the outer tool timed out
```

This is recorded as **full suite incomplete**, not a failure and not a full pass.

The active slow test was then run independently:

```text
R13 worktree: 1/1 PASS, ~9.39 s test time
R12 baseline: 1/1 PASS, ~9.08 s test time
```

No evidence indicates R13 introduced that historical full-suite timeout behavior.

## Diff review before validation artifacts

R12 -> R13 content diff before adding this validation file and manifest:

```text
added:   3
changed: 9
removed: 0
```

Added:

- `docs/project-distillations/flowgraph.md`
- `skills/skillforge-lgf/references/quest-world-flow-orchestration.md`
- `skills/skillforge-ue-cpp/references/flow-graph-runtime-patterns.md`

Key line-ending check:

- `skills/skillforge-lgf/SKILL.md` remained CRLF like the baseline.

## Not verified in Unreal runtime

This round did not execute:

- FlowGraph UE5.7 UBT;
- FlowGraph UE5.9 UBT;
- packaged game;
- LGF dependency integration;
- PIE Host/Remote;
- Dedicated Server;
- JIP/reconnect/packet loss;
- active-world save/load;
- historical save migration;
- world-partition travel;
- AssetManager preload integration;
- 100/1000 active quest graph performance benchmark.

Therefore R13 is a **fixed-source research + Skill architecture contract** result, not runtime production certification.
