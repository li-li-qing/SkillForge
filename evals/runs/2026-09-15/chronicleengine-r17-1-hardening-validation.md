# ChronicleEngine R17.1 Hardening Validation

Date: 2026-09-15

## Scope

R17.1 is a corrective hardening pass over the delivered R17 SkillForge tree. It does **not** distill a new GitHub project and does not start R18.

Source evidence remains pinned to:

```text
TodayYueC/ChronicleEngine
branch main
commit b2fb37b14b7537c30d6ebf16cf612671bd0286e9
commit date 2026-04-30T11:34:37Z
license MIT
host EngineAssociation 5.3
plugin VersionName 0.12.0-dev / Beta
```

R17.1 fixes four review findings:

1. projection-first Graph wording still conflicted across Graph/Dialogue references;
2. R17 semantic coverage probes had not produced fresh-context raw Behavior Eval responses;
3. Chronicle's Runtime/PostLoad random durable-GUID repair was not distilled as a rejection pattern;
4. nested SubDialogue local-variable scope was not included in continuation Save/JIP state.

## Baseline

The only R17.1 modification baseline is the delivered R17 archive:

```text
SkillForge_ChronicleEngine_R17.zip
```

No R16/R15 tree was used to regenerate R17.1 content. R16 is referenced only as the historical baseline condition required by the pending behavior-eval packet for CPP-110..113 / LGF-69..71.

## Graph contract consistency correction

The four formal references now use one conditional contract:

```text
Runtime never depends on / traverses UEdGraph.

Domain may choose:
A. Authoring Graph -> compiler -> runtime artifact
B. Canonical semantic definition <-> transient editor projection
```

A separate compiled artifact is required only when lowering, compaction, cook/security stripping, runtime layout optimization, or ABI isolation materially requires it. Projection-first still requires stable identities, whole-definition validation, migration, deterministic caches, editor-only metadata stripping and live revision fencing.

The old absolute quick-table answer `否，编译成 runtime definition` and the Dialogue-only single preferred pipeline were removed/reworded.

## New Behavior cases: RED -> GREEN semantic contract probe

Cases were added **before** formal Reference edits:

- CPP-114: durable semantic ID cannot be repaired randomly during Runtime/PostLoad;
- CPP-115: nested Dialogue locals are per-call semantic scope frames;
- LGF-72: LGF Conversation saves/restores nested local scope stack across Save/JIP/Avatar rebind.

### RED

Against the unmodified R17 formal References:

```text
CPP-114 FAIL
CPP-115 FAIL
LGF-72 FAIL
SUMMARY 0/3 PASS; 3/3 MISSING
```

### GREEN

After minimal Reference changes, the same semantic contract conditions were checked again:

```text
CPP-114 PASS
CPP-115 PASS
LGF-72 PASS
SUMMARY 3/3 PASS; 0/3 MISSING
```

This is a **Reference semantic coverage probe**, not a model Behavior Eval.

## Existing R17 Behavior evidence correction

R17's CPP-110..113 / LGF-69..71 `0/7 -> 7/7` result is retained as semantic coverage evidence only.

`evals/README.md` now explicitly forbids treating grep/anchor/reference coverage as Behavior RED/GREEN. A genuine Behavior Eval needs a fresh context, frozen raw answer before expectations are revealed, and post-freeze judgment.

This artifact-editing ChatGPT harness does not expose an isolated subagent/model-runner primitive. Therefore no raw answer was fabricated. The following remain **pending / 未证明** as model-behavior improvements:

```text
CPP-110..CPP-115
LGF-69..LGF-72
```

A reproducible packet is frozen at:

```text
evals/runs/2026-09-15/chronicleengine-r17-1-behavior-eval-packet.json
```

Execution status is recorded at:

```text
evals/runs/2026-09-15/chronicleengine-r17-1-behavior-eval-status.md
```

## R17.1 source-level findings added

### Durable ID runtime repair rejection

`UDialogueTree::PostLoad()` calls `EnsureStableGuids()`, and missing tree/node GUIDs can be filled via `FGuid::NewGuid()`.

R17.1 formalizes the boundary:

- new semantic entities may receive new IDs during controlled authoring;
- rename/move/reload/recook of the same shipped entity preserves ID;
- legacy missing IDs require Editor/commandlet/deterministic migration + resave and diagnostics;
- Shipping/Dedicated/Cook validation must not randomly repair a durable ID and continue.

### Nested local scope/call frame

Chronicle `UVariableBank` owns one flat `LocalVariables` map, while SubDialogue continuation state does not carry per-call local scopes. R17.1 therefore treats nested Dialogue local memory as semantic call-frame state:

```text
DefinitionId
Return Node/Transition stable IDs
LocalScopeFrame / LocalScopeVersion
resumable local semantic values
```

Save/Load/JIP restores the active scope stack, not one flattened local map. Avatar replacement rebinds presentation only; it does not destroy the semantic scope stack.

## Behavior totals after R17.1

```text
UE C++: 115 sequential cases, last CPP-115
LGF: 72 sequential LGF cases, last LGF-72
     75 JSON entries including three historical special-ID cases
UI Design: unchanged
UE Blueprint: unchanged
```

## Fresh working-tree validation

### Self-contained validator

```text
python scripts/validate_skills.py --self-contained
Validated 6 skill(s): 0 error(s); 6 standalone copies validated.
```

### Targeted validator regression

Six selected validator tests passed:

```text
6/6 PASS
Ran 6 tests in 19.165s
```

Covered portable unrelated-directory execution, self-contained relative resources, main-file line budget, links, eval arrays, and behavior expectation/fixture validation.

### LGF Inspector

```text
10/10 PASS
Ran 10 tests in 0.021s
```

### JSON parse

Before adding this validation report/manifest, repository JSON parse was:

```text
49/49 PASS
```

The final package is parsed again after the manifest is generated.

### Chronicle semantic coverage / consistency probe

```text
CPP-110 PASS
CPP-111 PASS
CPP-112 PASS
CPP-113 PASS
LGF-69 PASS
LGF-70 PASS
LGF-71 PASS
CPP-114 PASS
CPP-115 PASS
LGF-72 PASS
SUMMARY 10/10 PASS; 0/10 MISSING
GRAPH_CONSISTENCY PASS
```

Again, this is formal Reference coverage, not raw model behavior proof.

## Full validator suite attempt

Command:

```text
python -m unittest -v tests.test_validate_skills
```

The complete suite did not finish within the bounded run. The first 11 displayed tests were `ok`, then execution remained in:

```text
test_host_specific_tool_syntax_is_rejected
```

Therefore: **full suite 未完整运行**.

The blocking test was then run alone on both the frozen R17 baseline and R17.1 working tree:

```text
R17 baseline:  1/1 PASS; unittest 3.476s; wall 4.63s
R17.1 current: 1/1 PASS; unittest 3.694s; wall 5.13s
```

This does not replace a completed suite, but there is no R17.1-specific failure in that isolated case.

## Not verified

R17.1 did not execute:

- fresh-context raw model Behavior RED/GREEN for the 10 Chronicle-derived cases;
- ChronicleEngine UE5.3/5.7/5.8 UBT/UHT;
- Unreal Editor / Chronicle automation suite / BuildPlugin;
- PIE / Listen / Remote / Dedicated / JIP / reconnect / packet loss;
- actual nested SubDialogue Save/Load with local shadowing;
- runtime missing-GUID migration reproduction;
- late async callback race reproduction;
- localization gather/cook;
- performance benchmark;
- real LGF integration.

R17.1 is a Skill/reference hardening pass, not ChronicleEngine production certification.
