# ChronicleEngine R17 Distillation Validation

Date: 2026-09-15

## Scope

Project distilled:

```text
TodayYueC/ChronicleEngine
branch main
commit b2fb37b14b7537c30d6ebf16cf612671bd0286e9
commit date 2026-04-30T11:34:37Z
license MIT
host EngineAssociation 5.3
plugin VersionName 0.12.0-dev / Beta
```

Freshness classification: **Stable-but-old** for UE5.7/5.8 production adoption.

The repository is recent source, but the primary host baseline remains UE5.3, current HEAD is a beta development version, UE5.7 evidence is author-side smoke rather than this round's build, active editor code still uses legacy `FAssetTypeActions_Base`, and no Authority/RPC/replication/JIP implementation was found. Current Epic UE5.8 `UAssetDefinition`, UObject replication/Iris and text-localization documentation were used as target-version calibration.

## TDD / semantic RED -> GREEN

R17 added seven new behavior contracts before changing formal references:

UE C++:

- CPP-110 transient editor projection / single semantic truth;
- CPP-111 dialogue continuation frames + pending await save state;
- CPP-112 async completion AwaitId / execution generation correlation;
- CPP-113 compiled-expression cache vs dependency-revisioned result cache.

LGF:

- LGF-69 Graph Foundation projection-first option;
- LGF-70 Conversation continuation + pending await token / Avatar-generation fence;
- LGF-71 Dialogue condition dependency-revision cache.

### RED

Only the Behavior Eval JSON files were changed first. The fixed seven-condition semantic probe was then executed against the unchanged R16 formal references.

Fresh result:

```text
CPP-110 FAIL
CPP-111 FAIL
CPP-112 FAIL
CPP-113 FAIL
LGF-69 FAIL
LGF-70 FAIL
LGF-71 FAIL
SUMMARY 0/7 PASS; 7/7 MISSING
```

The failure was due to missing production contracts, not malformed eval JSON.

### GREEN

The formal references were then minimally changed:

- `skillforge-ue-cpp/references/generic-graph-authoring-patterns.md`
- `skillforge-ue-cpp/references/dialogue-runtime-patterns.md`
- `skillforge-lgf/references/graph-authoring-foundation.md`
- `skillforge-lgf/references/dialogue-conversation-contracts.md`

The same semantic probe was rerun without weakening its conditions:

```text
PASS CPP-110
PASS CPP-111
PASS CPP-112
PASS CPP-113
PASS LGF-69
PASS LGF-70
PASS LGF-71
SUMMARY 7/7 PASS; 0/7 MISSING
```

No Chronicle-specific standalone Skill was created; existing R13-R16 references were corrected or strengthened.

## Behavior totals

After R17:

```text
UE C++: 113 sequential cases, last CPP-113
LGF: 71 sequential LGF cases, last LGF-71 (74 JSON entries including three historical special-ID cases)
UI Design: unchanged; 9 JSON entries, last sequential UI-09
UE Blueprint: unchanged; 5 JSON entries, last sequential BP-04
```

## Fresh working-tree validation

### Self-contained validator

Command:

```text
python scripts/validate_skills.py --self-contained
```

Result:

```text
Validated 6 skill(s): 0 error(s); 6 standalone copies validated.
```

### Targeted validator regression

Six selected `ValidateSkillsTests` cases were run:

- portable package from unrelated directory;
- standalone relative resources;
- main file line budget;
- inline/reference links;
- eval JSON arrays;
- behavior expectations / fixture paths.

Fresh result: **6/6 PASS** in 18.265s.

### LGF Inspector tests

Command:

```text
python -m unittest discover -v skills/skillforge-lgf/tests
```

Fresh result: **10/10 PASS** in 0.014s.

### JSON parse

Before adding this validation report and changed-files manifest, repository JSON parse was **47/47 PASS**. The final tree is parsed again during package verification because the manifest adds another JSON file.

### R17 semantic probe

Fresh result: **7/7 PASS**.

## Full validator suite attempt

Command:

```text
python -m unittest -v tests.test_validate_skills
```

The suite was bounded to 220 seconds. The first **11 displayed tests were `ok`**; execution budget expired while running:

```text
test_host_specific_tool_syntax_is_rejected
```

Therefore: **full suite 未完整运行**. This report does not claim the complete validator suite passed.

The blocking test was then run in isolation on both trees:

```text
R16 uploaded baseline: 1/1 PASS; unittest 5.950s; wall 6.80s
R17 current tree:      1/1 PASS; unittest 4.602s; wall 5.42s
```

This shows no R17-specific regression in that isolated test, but it does not replace a completed full-suite run.

## Source-level Chronicle findings verified for the Skill changes

Accepted / strengthened mechanisms:

- canonical semantic definition can drive a transient editor `UEdGraph` projection;
- runtime Node/Edge lookup caches are rebuilt from canonical data;
- synchronous graph traversal has a hard 1024-step budget;
- expression parsing has a compiled AST cache;
- editor mutations use transactional ownership patterns;
- audit/import/export and automation-test sources exist.

Rejected / bounded mechanisms:

- Choice and Edge lack their own stable semantic identity;
- save/load does not serialize the SubDialogue return stack or a complete pending-await continuation;
- async completion is correlated primarily by GameplayTag, not an execution token;
- final condition results can become stale when external bindings change outside runner-owned setters;
- active runtime paths use `LoadSynchronous()` for target dialogue/voice resolution;
- editor position/breakpoint/soft-lock metadata lives in the runtime DataAsset;
- no `UPROPERTY(Replicated...)`, Server RPC, `OnRep_`, `HasAuthority` or FastArray path was found;
- editor still uses `FAssetTypeActions_Base`, which current Epic documentation treats as the legacy system replaced by `UAssetDefinition` for new asset-definition architecture.

## Baseline preservation

The only semantic baseline for R17 was the uploaded ZIP:

```text
/mnt/data/SkillForge(3).zip
SHA-256 519de24eb226d4b555b643e63f9135d36585a94cad38924496f2d49c2cc936e9
```

No R15-or-earlier cache/version was used to regenerate the project. Unrelated Skill, Codex LGF, Behavior Eval, Docs and project-distillation history files were preserved.

The uploaded baseline itself contained Python `__pycache__` / `.pyc` artifacts. They were excluded from R17 delivery because the delivery contract explicitly forbids them; this is a packaging exclusion, not a semantic Skill deletion.

## Not verified

This R17 round did **not** execute:

- ChronicleEngine UE5.3/5.7/5.8 UBT;
- UHT or Unreal Editor launch;
- Chronicle's own automation test suite;
- BuildPlugin;
- PIE;
- Listen/Remote multiplayer;
- Dedicated Server;
- JIP/reconnect/packet loss;
- nested SubDialogue save/load runtime reproduction;
- late async callback race reproduction;
- localization gather/cook;
- performance benchmark;
- real LGF integration.

Therefore this is a fixed-source architecture / Skill-contract distillation, not a production certification of ChronicleEngine on UE5.7/5.8.

## Package verification

The delivery archives were validated from a fresh unrelated extraction after the report/manifest freeze. The same gates used on the candidate package were repeated on the final named archives.

Final-package gates:

- R17 semantic probe: **7/7 PASS**;
- self-contained validator: **6 skills, 0 errors, 6 standalone copies**;
- targeted validator regression: **6/6 PASS**;
- LGF Inspector tests: **10/10 PASS**;
- JSON parse: **48/48 PASS**;
- full-package file/path SHA parity against the frozen delivery tree: **226/226 exact matches**;
- changes-only archive: **12 files, 12/12 exact SHA-256 matches**;
- ZIP CRC: **PASS** for both archives;
- archive Python cache artifacts: **0**;
- extracted delivery tree contains no shipped `.git`, `__pycache__`, or `.pyc` artifacts.

Archive SHA-256 values are reported outside this embedded validation file to avoid a self-referential hash cycle.

