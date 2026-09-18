# DlgSystem Distillation Validation — R15

Date: 2026-09-14

## Research boundary

- Repository: `NotYetGames/DlgSystem`
- Default branch: `master`
- Pinned commit: `d705231216bd64558d437b87a57928689b1e7fef`
- Commit date: 2026-06-22
- Commit tree: `cac042505f4d32364bfadad2a15a2b8ddfa1f7e3`
- Plugin version: 18.0.8
- Source compatibility evidence: README supports UE 5.6/5.7/5.8; adjacent current commits include UE 5.8 support and UE 5.7 include compatibility.
- License: MIT (`LICENSE.txt`).

## TDD semantic gap

R14 baseline dialogue-specific gap probe covered 14 contracts:

1. participant semantic identity;
2. ConversationInstance/revision;
3. stable ChoiceId;
4. dialogue memory scope;
5. participant query/command split;
6. localization identity;
7. stable resume;
8. dialogue Authority;
9. JIP snapshot;
10. Quest↔Dialogue boundary;
11. StateTree↔Dialogue boundary;
12. replaceable-Avatar participant rebind;
13. import/export stable identity;
14. dialogue asset/save/content version split.

RED result: 13/14 absent from R14 formal references; localization had generic `FText` guidance but lacked dialogue namespace/key/semantic identity contract.

GREEN semantic probe after R15 formal references: **14/14 PASS**.

## New formal content

- `skills/skillforge-ue-cpp/references/dialogue-runtime-patterns.md` — 984 lines.
- `skills/skillforge-lgf/references/dialogue-conversation-contracts.md` — 782 lines.
- `docs/project-distillations/dlgsystem.md` — 1237 lines.

Behavior cases after R15:

- UE C++: 101 cases, last `CPP-101`.
- LGF: 63 cases, last `LGF-63`.

New behavior cases:

- CPP-93 participant semantic identity;
- CPP-94 ConversationInstance save/resume;
- CPP-95 stable ChoiceId;
- CPP-96 Authority/revision/JIP;
- CPP-97 explicit memory scope;
- CPP-98 condition/event domain command boundary;
- CPP-99 localization semantic identity;
- CPP-100 content version/import roundtrip;
- CPP-101 replication plumbing is not Authority;
- LGF-59 stable participant / Avatar rebind;
- LGF-60 Conversation Authority/read model/JIP;
- LGF-61 Quest↔Dialogue boundary;
- LGF-62 StateTree↔Dialogue scoped AI intent;
- LGF-63 save/resume/content migration.

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

### Targeted validator regression

Six selected `ValidateSkillsTests` cases were run:

- portable package from unrelated directory;
- standalone relative resources;
- main file line budget;
- inline/reference links;
- eval JSON arrays;
- behavior expectations / fixture paths.

Final fresh result: **6/6 PASS** in 12.686s.

### LGF workspace inspector

Command:

```text
python -m unittest discover -v skills/skillforge-lgf/tests
```

Result: **10/10 PASS**.

### JSON parse

Final repository JSON parse after adding R15 validation artifacts: **46/46 PASS**.

### Full validator suite attempt

Command:

```text
python -m unittest -v tests.test_validate_skills
```

Bounded at 220 seconds. The first 12 displayed tests were `ok`; execution budget expired while running:

```text
test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names
```

No assertion failure was shown before timeout. Therefore the full suite is **not claimed as complete or passing**.

The active slow test was then isolated on both trees:

- R15 working tree: **1/1 PASS**, unittest 9.842s, wall 10.46s.
- untouched R14 baseline snapshot: **1/1 PASS**, unittest 9.716s, wall 10.38s.

This supports classifying the full-suite stop as an existing slow-suite/runtime-budget behavior rather than evidence of an R15-specific assertion regression. It does not replace a completed full-suite run.

## Diff boundary

Before adding delivery metadata, R14 baseline → R15 formal content diff was 3 added + 5 changed + 0 deleted.

Final fresh diff after adding this validation record and changed-files manifest:

- added: 5 files;
- changed: 5 files;
- deleted: 0 files;
- total R15 paths: 10.

The manifest excludes its own hash to avoid recursive self-reference; the changes ZIP includes the manifest itself.

## DlgSystem evidence constraints preserved

R15 explicitly does **not** promote the following source mechanisms into production doctrine:

- process-global `FDlgMemory` as multiplayer truth;
- visible option index as network/save semantic identity;
- replicated Dialogue/Participant UObject references as a complete Authority protocol;
- SpeechSequence's current replicated-index workaround as a production substate model;
- reflective dialogue events as a safe mutation path for Quest/Inventory/GAS/world truth;
- world participant scans or load-all-dialogues as gameplay hot-path patterns.

## Not executed

This R15 distillation did not execute or prove:

- DlgSystem UE5.7 UBT;
- Unreal Editor opening/compiling a real Dlg graph;
- DlgSystem's disabled IO Automation test;
- PIE multiplayer;
- Listen Server gameplay test;
- Dedicated Server dialogue progression;
- JIP/reconnect;
- lag/loss/reordering/race testing;
- Localization gather/cook;
- Twine/human-readable roundtrip;
- performance profiling;
- integration into the user's live LGF repository.

Any of those require separate target-project evidence.


## Final fresh pre-package verification

After the validation record/manifest were present, the repository was verified again:

- dialogue semantic probe: **14/14 PASS**;
- self-contained validator: **6 skills, 0 errors, 6 standalone copies**;
- targeted validator: **6/6 PASS**;
- LGF inspector: **10/10 PASS**;
- JSON: **46/46 PASS**;
- behavior counts: **UE C++ 101 (CPP-101), LGF 63 (LGF-63)**;
- final baseline diff: **5 added + 5 changed + 0 deleted**.

Test execution generated Python cache files; they are cleanup artifacts and are removed before packaging.
