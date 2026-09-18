# RockInventory R3 distillation validation

Date: 2026-09-14
Pinned source: `brokenrockstudios/RockInventory@be30b5a4a64c5707efde45c705a2e7011d9834d0`
License observed in repository metadata: MIT.

## Scope

Third project distillation on top of the existing R2 SkillForge workspace. The round is intentionally limited to item value semantics, stable handles, FastArray item/slot separation, typed runtime state, replicated UObject escape hatches, nested inventory ownership, multiplayer transactions, server revalidation, and hot-path resource/query performance.

## TDD evidence

RED semantic probe before Skill edits reported missing coverage for:

- index+generation stable handles;
- free-list slot reuse;
- typed ItemState layer;
- MutationKey/passkey write control;
- nested-inventory cycle/depth contract;
- server clamp/revalidation for drop parameters.

GREEN probe after edits reports `MISSING: none`.

## Added behavior cases

- UE C++: CPP-12 through CPP-17.
- LGF: LGF-18.

## Verification

- `python scripts/validate_skills.py --self-contained` -> 6 skills, 0 errors, 6 standalone copies valid.
- Selected validator tests -> 6/6 passed.
- LGF workspace inspector tests -> 10/10 passed.
- JSON parse -> 35 files valid.
- UE C++ behavior cases -> 17 total, last CPP-17.
- LGF behavior cases -> 18 total, last LGF-18.
- Full root validator suite was attempted twice and exceeded the command timeout. Verbose output stopped while running `test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names`.
- That exact test passes when run alone in both the current R3 workspace and the pre-R3 snapshot. This is recorded as suite-duration/runner limitation, not as evidence that the entire root suite passed.

## Source-risk preservation

The Skill text keeps the following RockInventory areas as experimental/incomplete evidence rather than production recommendations:

- transaction prediction/reconciliation and undo TODOs/stubs;
- a Move undo assertion/parameter-flow path that requires upstream review;
- NestedInventory ownership/multiplayer TODOs;
- client-provided drop offset/impulse that still need server bounds;
- runtime synchronous loads in several paths;
- unprofiled O(N) reverse lookups/cache candidates.
