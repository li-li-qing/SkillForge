# AyaDogGames GameplayFramework R4 distillation validation

Date: 2026-09-14  
Pinned source: `AyaDogGames/GameplayFramework@9379a85a0ff9d1b29dc22828ef3ed881b4635cf0`  
License observed in repository metadata: Apache-2.0.

## Scope

Fourth project distillation on top of the R3 SkillForge workspace. The round is intentionally focused on framework composition: persistent PlayerState state versus replaceable Pawn applied state, reversible GAS grants, FastArray inventory/loadout identity, client mutation authorization, re-entrant mutation boundaries, Enhanced Input -> InputTag -> GAS routing, CommonUI/UI projection, and server-side AI director layering.

README identifies UE 5.7 while repository `CLAUDE.md` identifies UE 5.8 and the `.uplugin` does not pin EngineVersion. The Skill records this as unresolved documentation conflict rather than selecting one version without build evidence.

## TDD evidence

RED semantic probe before reusable-reference edits reported missing coverage for all of:

- `copy-empty-handle` grant registry failure;
- `operation-specific default-deny` client mutation authorization;
- `persistent owner vs replaceable avatar` lifecycle;
- `construct fully -> publish once` entry publication;
- `InputTag -> AbilitySpecHandle` hot-path indexing;
- UI `same domain command` for mouse and gameplay input.

GREEN semantic probe after edits reports no missing contract.

## Added behavior cases

- UE C++: CPP-18 through CPP-23.
- LGF: LGF-19 through LGF-20.
- UI Design: UI-04.

## Verification

- `python scripts/validate_skills.py --self-contained` -> 6 skills, 0 errors, 6 standalone copies valid.
- Selected validator tests -> 6/6 passed.
- LGF workspace inspector tests -> 10/10 passed.
- JSON parse -> 36 files valid.
- UE C++ behavior cases -> 23 total, last CPP-23.
- LGF behavior cases -> 20 total, last LGF-20.
- UI behavior cases -> 4 total, last UI-04.
- Full root validator suite was attempted with a 180 second budget. Verbose output showed 13 tests completing successfully through `test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names`; the run was still executing the next test when the runner budget was exhausted. The residual process was terminated.
- The test active at that point, `test_link_cannot_escape_to_existing_repository_file`, passes when run alone (1/1, about 1.2 s). Therefore the full suite is recorded as **not completed due to aggregate runtime**, not as fully passed and not as a demonstrated regression.

## Source-risk preservation

The Skill text explicitly preserves the following as risks/anti-patterns rather than recommendations:

- ASC AbilitySet handle registry copies an empty handle before the local handle is filled;
- generic client `Server_AddItem` has no acquisition-source authorization contract;
- generic client item-stat writes use broad parent-tag permission with only limited protected leaves;
- runtime `TryLoad` / `LoadSynchronous` remains in inventory/equipment/drop/hotbar paths;
- ability input performs a full activatable-spec scan for Pressed/Held/Released;
- AI spawner periodically scans world actors and currently does not consume Weight/SpawnCost as a real budget/selection system;
- Save subsystem is synchronous, whole-world/ActorName oriented, and explicitly single-player in one player-save loop;
- README and repository agent documentation disagree on the UE minor version.

## Packaging boundary

This round does not delete files. Only project-distillation documentation, the three relevant Skills (UE C++, LGF, UI Design), and their behavior cases/references are changed. Existing unrelated SkillForge work is left byte-for-byte as in the R3 baseline except for those listed paths.
