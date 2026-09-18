# GenericGraph R16 Distillation Validation

Date: 2026-09-14

## Scope

Project distilled:

```text
jinyuliao/GenericGraph
commit f9b8fe3de6bc2ef39ee771658ac4a8bf48c2e078
commit date 2023-07-15
tree 373cc9d89894a05b8204714370fd7972c87b3387
license MIT
```

Freshness classification: **Historical architecture sample**.

Reason: default branch last explicit engine migration is UE5.1; README still describes a UE4 plugin; no target UE5.7/5.8 branch/tag evidence was found. Current UE5.8 official API evidence was separately used to calibrate editor entry points such as `UAssetDefinition`, ToolMenus and current EdGraph/Schema APIs.

## TDD / semantic RED → GREEN

R16 planned thirteen previously missing contracts:

1. `UAssetDefinition` / modern editor API freshness gate;
2. `EdgeStableId`;
3. rootless strongly-connected component handling;
4. parallel edge policy;
5. compiler last-known-good behavior;
6. canonical edge records / derived adjacency;
7. copy/paste stable-ID policy;
8. scalable context menu / node discovery;
9. rejection of a gameplay-owning `UniversalGraphRuntime`;
10. per-domain `DomainSchema` / topology policy;
11. GraphEditor/Slate/UnrealEd runtime boundary;
12. `CompiledRevision` / live-session fence;
13. structured diagnostic `FixHint`.

Baseline probe against R15 formal UE C++ and LGF skill references: **0/13 covered, 13/13 missing**.

After R16 formal references were written, the same probe produced: **13/13 PASS**.

## Added behavior cases

UE C++:

- CPP-102 GenericGraph freshness / modern editor API gate;
- CPP-103 authoring → compiled artifact + stable identity;
- CPP-104 schema / topology validation contract;
- CPP-105 cycle-safe traversal + rootless SCC;
- CPP-106 EdgeStableId + parallel-edge semantics;
- CPP-107 canonical edge list + derived adjacency;
- CPP-108 copy/duplicate/diff/migration identity policy;
- CPP-109 editor scalability / layout / discovery.

LGF:

- LGF-64 shared graph authoring, not shared gameplay runtime truth;
- LGF-65 compiled stable IDs + content migration;
- LGF-66 per-domain graph topology policy;
- LGF-67 Graph Editor / Runtime module boundary;
- LGF-68 live graph revision / session safety.

Behavior totals before packaging:

```text
UE C++: 109, last CPP-109
LGF: 68, last LGF-68
UI Design: 9, last UI-09
UE Blueprint: 5, last BP-04
```

## Fresh repository verification

### Self-contained validator

Command:

```text
python scripts/validate_skills.py --self-contained
```

Fresh result:

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

Fresh result: **6/6 PASS** in 12.597s.

### LGF workspace inspector

Command:

```text
python -m unittest discover -v skills/skillforge-lgf/tests
```

Fresh result: **10/10 PASS**.

### JSON parse

Before adding this validation manifest, repository JSON parse result: **46/46 PASS**.

The final verification after the manifest is generated is recorded below separately.

## Full validator suite attempt

Command:

```text
python -m unittest -v tests.test_validate_skills
```

The run was bounded to about 220 seconds. The first **16 displayed tests were `ok`**. Execution budget expired while running:

```text
test_name_constraints_and_directory_match
```

No assertion failure was displayed before timeout. Therefore the full validator suite is **not claimed as complete or passing**.

The active slow test was then run in isolation on both trees:

```text
R16 working tree: 1/1 PASS; unittest 6.238s; wall 6.88s
R15 untouched baseline: 1/1 PASS; unittest 6.068s; wall 6.81s
```

This provides no evidence of an R16-specific regression in that test, but it does not replace a completed full-suite run.

## Diff boundary before validation artifacts

R15 → R16 content diff before adding this validation report/manifest:

```text
added: 3
changed: 9
deleted: 0
```

Added:

- `docs/project-distillations/genericgraph.md`
- `skills/skillforge-lgf/references/graph-authoring-foundation.md`
- `skills/skillforge-ue-cpp/references/generic-graph-authoring-patterns.md`

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

Line-ending comparison found no CRLF/LF normalization on changed files.

## What was learned from the fixed GenericGraph source

Accepted mechanisms:

- Runtime / Editor separation direction;
- extensible Graph / Node / Edge types;
- centralized editor Schema plus node-level domain connection hook;
- explicit edge objects for transition semantics;
- authoring graph → runtime topology materialization;
- cycle checking as early editor feedback;
- layout as a separate editor service.

Rejected or strengthened mechanisms:

- UE5.1-era editor API cannot be treated as UE5.7/5.8 authority;
- runtime UObject pointers / array positions are not Save/Network identity;
- `TMap<ChildNode, Edge>` does not support parallel semantic edges;
- a single `bCanBeCyclical` is not a domain topology contract;
- root-only traversal does not cover rootless SCCs;
- cycle-enabled graphs require cycle-safe traversal in runtime/debug/layout, not only connection-time checking;
- save-time `Clear + rebuild` is weaker than staged compilation + atomic publish;
- runtime artifacts need definition/compiler version + source/content fingerprint + compiled revision;
- context-menu-wide `TObjectIterator<UClass>` discovery and unbounded O(N²) layout are not large-project defaults;
- runtime modules should not depend on UnrealEd/GraphEditor/Slate editor chains without actual runtime justification;
- legacy AssetTypeActions should be target-version compatibility code, while modern UE5.7/5.8 adapters should evaluate `UAssetDefinition` / ToolMenus.

## Not verified

This R16 round did **not** execute:

- GenericGraph UBT on UE5.7;
- GenericGraph UBT on UE5.8;
- UHT/Editor launch;
- graph create/save/copy/undo tests;
- a runtime cyclical-graph hang reproduction;
- auto-layout correctness reproduction;
- 1k/10k-node editor benchmarks;
- cook or packaged build;
- Dedicated Server;
- a real LGF integration.

Therefore R16 is a **source-level architecture and Skill contract distillation**, not a claim that the fixed GenericGraph snapshot is production-ready on UE5.7/5.8.

## Final fresh pre-package verification

After this report and the changed-files manifest were present, the repository was verified again from the final working tree:

- R16 semantic probe: **13/13 PASS**;
- self-contained validator: **6 skills, 0 errors, 6 standalone copies**;
- targeted validator regression: **6/6 PASS** in latest rerun 12.527s;
- LGF workspace inspector: **10/10 PASS**;
- repository JSON parse: **47/47 PASS**;
- behavior totals: **UE C++ 109 (CPP-109), LGF 68 (LGF-68), UI 9 (UI-09), Blueprint 5 (BP-04)**;
- final R15 → R16 diff: **5 added + 9 changed + 0 deleted**;
- Python cache artifacts after cleanup: **0**.

The final package verification additionally extracts the generated full ZIP to an unrelated directory, reruns key validation there, verifies archive CRC, and checks every changes-only archive file hash against the frozen working tree.

## Package verification

After the delivery archives were generated, the full archive was extracted into a fresh unrelated directory and verified there.

Verified on the extracted full package:

- R16 semantic probe: **13/13 PASS**;
- self-contained validator: **6 skills, 0 errors, 6 standalone copies**;
- targeted validator regression: **6/6 PASS**;
- LGF workspace inspector: **10/10 PASS**;
- JSON parse: **47/47 PASS**;
- full package file/path parity against the frozen working tree: **249/249 exact SHA-256 matches**;
- changes-only archive: **14 files, 14/14 exact SHA-256 matches**;
- ZIP CRC check: no corrupt entry;
- packaged/extracted Python cache artifacts after cleanup: **0**.

Archive SHA-256 values are intentionally reported outside this file because this validation report is itself contained in the archive; embedding the archive hash here would create a self-referential hash cycle.
