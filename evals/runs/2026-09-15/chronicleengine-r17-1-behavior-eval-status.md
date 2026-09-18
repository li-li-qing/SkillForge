# ChronicleEngine R17.1 Behavior Eval Execution Status

Date: 2026-09-15

## Verdict

Fresh-context Behavior RED→GREEN is **not executed in this harness**. The available tool surface can edit/run repository files but does not expose an isolated subagent/model runner. R17's previous `0/7 -> 7/7` result is therefore correctly reclassified as a **semantic Reference coverage probe**, not as model behavior evidence. No raw answer is fabricated to close this gap.

## Cases frozen for execution

Existing R17 cases, unchanged:

- CPP-110..CPP-113
- LGF-69..LGF-71

R17.1 cases, added RED-first:

- CPP-114 durable semantic ID: no Runtime/PostLoad random repair
- CPP-115 nested Dialogue local scope/call frame
- LGF-72 LGF Conversation nested local scope Save/JIP

The executable prompt/expectation packet is `chronicleengine-r17-1-behavior-eval-packet.json`. It deliberately marks baseline raw answer, forward raw answer and independent judgment as `pending`.

## What was executed here

A deterministic semantic coverage probe was executed for the three new contracts:

```text
RED before formal Reference edits
CPP-114 FAIL
CPP-115 FAIL
LGF-72 FAIL
SUMMARY 0/3 PASS; 3/3 MISSING

GREEN after formal Reference edits
CPP-114 PASS
CPP-115 PASS
LGF-72 PASS
SUMMARY 3/3 PASS; 0/3 MISSING
```

This proves the formal References gained the intended contracts. It does **not** prove an Agent changes behavior.

## Required closure gate

Before claiming full Skill TDD closure for CPP-110..115 / LGF-69..72, a Codex/Agent environment with fresh-context execution must produce and retain:

1. baseline raw response per case;
2. forward raw response per case;
3. expectations revealed only after each raw response is frozen;
4. per-expectation judgment with concrete answer evidence;
5. model/settings/tool-surface record and any loaded references.

Until then the behavior improvement remains **未证明**, while the structural/semantic Skill changes may still be validated independently.
