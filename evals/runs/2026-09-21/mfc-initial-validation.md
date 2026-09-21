# MFC Skill First-Round Validation

Date: 2026-09-21

## Scope

Added a standalone `skillforge-mfc` platform skill to the existing SkillForge collection. The first round distills current and historical MFC evidence into portable rules rather than copying repository-specific implementations.

Pinned source set:

- `microsoft/mfcmapi@c8379e0f2673227cf0b429ba8ab31d7f7ba093bb` — 2026-09-16, current reference;
- `WinMerge/winmerge@63deba2519c0ce81b1cf459c1659ad443b9e18ea` — 2026-09-21, current large MFC application;
- `TortoiseGit/TortoiseGit@acc10fc20afe36aabc4afbc5f1af33f31acae32e` — 2026-06-27, current MFC/Shell architecture;
- `microsoft/comic-chat@48a162249484ab8d116c243e8203b0956d350c09` — 2026-07-22, archived modernization worked example;
- `Microsoft/VCSamples@9e1d4475555b76a17a3568369867f1d7b6cc6126` — 2019-11-24, archived historical MFC mechanism samples.

## Added skill surface

`skillforge-mfc` contains:

- `SKILL.md` — routing and implementation rules;
- `references/architecture-message-routing.md`;
- `references/threading-com-sta.md`;
- `references/window-lifetime-resources.md`;
- `references/dpi-layout-controls.md`;
- `references/build-testing-modernization.md`;
- `references/github-sources.md`;
- trigger and behavior eval specifications.

Primary contracts cover MFC command/message routing, object/HWND/resource lifetime, worker-to-UI handoff, COM apartment ownership, DPI/layout, owner-data/high-frequency controls, build/test/modernization, and cross-skill composition.

## Fresh structural validation

Command:

```text
python scripts/validate_skills.py --self-contained
```

Result:

```text
Validated 7 skill(s): 0 error(s); 7 standalone copies validated.
```

`skillforge-mfc/SKILL.md` is 128 lines, below the repository's 500-line main-skill budget.

## Targeted validator regression

The six repository validator tests most relevant to a newly added portable skill were run:

- portable package from an unrelated directory;
- self-contained relative-resource copy;
- main `SKILL.md` line budget;
- inline/reference link integrity;
- eval files present and JSON arrays;
- behavior expectations and fixture-path validation.

Result:

```text
Ran 6 tests in 12.742s
OK
```

## JSON parse

All non-`.git` repository JSON files were parsed after the MFC changes.

Result:

```text
53 JSON files parsed successfully.
```

## Behavior-eval status

The new trigger/behavior JSON files are **test specifications**, not evidence that a fresh isolated agent has already passed those scenarios. No RED -> GREEN model-run claim is made in this round.

## Full validator-suite status

A full `tests/test_validate_skills.py` run was attempted, but the environment time budget expired before the entire suite completed. Therefore this round does **not** claim a complete validator-unit-suite pass. The targeted six tests above completed and passed, and the actual repository self-contained validator completed with zero errors.

## Not verified

This first round did not build or run a real MFC product. It does not certify:

- any user's `.sln` or `.vcxproj`;
- x86/x64/ARM64 binaries;
- MFC static/dynamic linkage;
- COM registration or third-party automation;
- DPI behavior on physical multi-monitor systems;
- Shell extension Explorer isolation;
- UI Automation/accessibility;
- performance under a real high-frequency data source.

Those should be added as project-grounded rules and fixtures during formal development, rather than guessed into the generic MFC skill now.
