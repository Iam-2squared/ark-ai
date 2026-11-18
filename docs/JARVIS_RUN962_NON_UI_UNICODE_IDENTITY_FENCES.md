# ARK AI Run962 — Unicode format-control identity fences (non-UI, free-only)

Work basis: `44ddda2276e81cee648720117e6990324cf5ca9b` (Run961 canonical checkpoint).
Report written: 2026-11-18T08:01:22.368+00:00 (UTC; report timestamp, not a trusted authorization/expiry clock).
Branch/PR: `research/jarvis-foundations` / Draft PR #8. ARK/JARVIS **NOT_PASSED**.

## Rationale

ASCII C0/DEL rejection is insufficient for human-readable tool, permission, plan and
observation fixture identifiers. U+0085 and U+2028/U+2029 are alternate line
separators; U+061C, U+200E/U+200F, U+202A–U+202E and U+2066–U+2069
are directional formatting controls. Those code points may visually reorder
or split a logged identifier without changing its hashed byte sequence.
This run rejects exactly those 15 format code points at opt-in admission
boundaries, **not** all Unicode text.

## NEW coherent packages (3 independently scoped components)

1. **Registry + PermissionGate synthetic regression**: Source
   [`bcb5299d`](https://github.com/Iam-2squared/ark-ai/commit/bcb5299d714b001a14b91b3efefc6cde3e3dea7a)
   rejects the format set in the opt-in `_text` boundary before registry hash,
   backend descriptor inspection, or registered scope binding. Test
   [`38336233`](https://github.com/Iam-2squared/ark-ai/commit/38336233d58196849cd6ff70942b60f7d989708c)
   authors **79 parametrized cases**: 45 registration fields, 30 resolve/bind
   scopes, 3 non-consumption of an unrelated process-local WRITE one-shot,
   1 valid multilingual identifier. Mock backend is never executed.
2. **Planner optional PlanGraph ingress**: Source
   [`620cf817`](https://github.com/Iam-2squared/ark-ai/commit/620cf81797d98dd5c117dac8433ab686e60e4950)
   refuses the same format set before DAG topology or request digest.
   Test [`d4a55565`](https://github.com/Iam-2squared/ark-ai/commit/d4a5556522aa48d3e6c08e9db2951a8ee03a738d)
   authors **78 cases**: five graph fields × 15 controls, two reflected
   post-init substitutions, and one valid multilingual graph. Frozen
   `PlanStep`/`ToolCall` dataclasses and journal contracts unchanged.
3. **Disconnected synthetic Observation fixture**: Source
   [`f51ccb9f`](https://github.com/Iam-2squared/ark-ai/commit/f51ccb9fc6e9d8d1823eace1e366ff94e34a82c4)
   refuses format-bearing optional source/privacy labels before the synthetic
   payload hash. Test [`40a5655f`](https://github.com/Iam-2squared/ark-ai/commit/40a5655f18a1cf3d8106b0f7f9694c2ed35fbe9e)
   authors **31 cases**: 15 controls × two labels, plus a valid multilingual
   fixture. The direct, frozen `ObservationEnvelope` v1 constructor remains
   unchanged; there is no camera, microphone, file or network adapter.

Total: **188 cases authored, not yet claimed passed at the checkpoint HEAD**.

## CI evidence and correction

- Run961 prior checkpoint `44ddda22`: [CI #44254482936](https://github.com/Iam-2squared/ark-ai/actions/runs/44254482936)
  had six completed GREEN Windows/Ubuntu × Python 3.11–3.13 jobs at Run962 preflight.
  This validates **only** Run961.
- Early source/test states: [#44261575095](https://github.com/Iam-2squared/ark-ai/actions/runs/44261575095),
  [#44261874008](https://github.com/Iam-2squared/ark-ai/actions/runs/44261874008) and
  [#44262171100](https://github.com/Iam-2squared/ark-ai/actions/runs/44262171100)
  all completed **FAIL** due to Ruff I001 whitespace after the new test import groups.
  This was a test-only formatting issue, not evidence of a functional behavior failure.
- Minimal test-only corrections:
  [registry `ae68f01b`](https://github.com/Iam-2squared/ark-ai/commit/ae68f01bd4ee2720cd6970d9431947535a3aa504),
  [Planner `94cb2bb2`](https://github.com/Iam-2squared/ark-ai/commit/94cb2bb2532a52330e5e2e3daaaae8f7472cdc9d),
  [Observation `f8d79213`](https://github.com/Iam-2squared/ark-ai/commit/f8d79213e733074336aff2ec7ce663901f1f5e6f);
  no test semantics, source protections or frozen contracts were loosened.
- Corrected exact HEAD `f8d79213e733074336aff2ec7ce663901f1f5e6f`:
  [CI #44263010547](https://github.com/Iam-2squared/ark-ai/actions/runs/44263010547)
  was **IN PROGRESS 0/6 complete** at the evidence sampling. Do not claim GREEN
  until all six exact-SHA jobs finish; no duplicate workflow was manually run.
  Full local pytest not performed.

## Boundaries, limitations and next lanes

Strict zero-new-cost and no-new-UI. Draft #5 remains protected/unmerged;
Draft #9 is paused/unmerged and untouched; main and V1/V2/Local UI/Launcher
frozen evidence unchanged. No protected V2 final evaluation, real Candidate,
training/weights, paid API/GPU, external credential, live tool, captured media,
consent claim, human-review inference, irreversible operation, forced Git write,
or main merge. Local SHA-256 and process-local one-shots do **not** establish
independent audit custody, trusted time or exactly-once external effects.

Next: 1) certify the *exact latest* Windows/Ubuntu × 3.11–3.13 CI result,
repair any failure via ordinary Content writes; 2) independently audit Memory
WAL/SHM cold last-close and event/row integrity; 3) Planner COMMIT-UNKNOWN
quarantine and exact registry-bound authorization/audit preaction, with only a
disconnected/mock executor after lower-level exact-head GREEN; 4) privacy-safe
Personal Context, Proactive occurrence, Observation synthetic provenance and
V3 free-only gates. Overall **ARK/JARVIS NOT_PASSED**.
