# ARK AI / Run755 — CI repair, actual local Memory lifecycle, redaction source custody

**Scope:** FREE-ONLY, NON-UI, synthetic/local fixtures on Draft PR #8.
**Initial exact work-basis HEAD:** `4a386adfad7f640dee525b69ec340edb20ba982c` (Run754).
**Source/test work-basis HEAD:** `286e4ebef576c6014dd067b66afa6f44f2e3b674`.
This file is an evidence note, NOT a PASS certificate, externally trusted time, actor identity, consent, or permission to execute.

## 1. CI log-driven Planner READ denial test repair

At old Run754 exact HEAD, [CI #42746892069](https://github.com/Iam-2squared/ark-ai/actions/runs/42746892069) was completed **FAIL 6/6**.
Actual Ubuntu Python 3.11 job log: **8 failed, 12,360 passed, 1 skipped**. The eight failures in
`tests/test_detached_read_recovery_preinstalled_denials_run552.py` had an **earlier fail-closed**
error `READ source descriptor changed` where an old test expected `carrier changed`.
There was no unexpected backend dispatch: the test's injected scheduling callback was never invoked.
The strict source-descriptor preflight remains intact.

- Normal-path test change `e030ad37e63f50862e32a8ef76131e93761f7e53` permits either
  earlier source-descriptor refusal or later carrier refusal, retaining `assert not invoked`.
- A literal `\\n` was inadvertently written into the test source rather than a line break.
  [CI #42751256788](https://github.com/Iam-2squared/ark-ai/actions/runs/42751256788),
  [CI #42751670503](https://github.com/Iam-2squared/ark-ai/actions/runs/42751670503), and
  [CI #42752062189](https://github.com/Iam-2squared/ark-ai/actions/runs/42752062189)
  all **FAIL 6/6 on Ruff pre-pytest**; the actual logs identify the malformed line.
- `286e4ebef576c6014dd067b66afa6f44f2e3b674` repairs that newline through
  the normal Contents API. No safety gate was weakened. The latest subsequent CI result
  must be checked separately.

## 2. Real SQLite lifecycle integration (6 parameterized test cases)

`tests/test_memory_cas_expiry_lifecycle_run755.py`, commit
`6c90c9ea450dea4cc856ae1bdafd876eeb36306c`.

Tests use temporary actual SQLite WAL/transaction behavior rather than mock results:
(1) scoped Memory v1 create; (2) generation-fenced CAS update with shorter expiry;
(3) a distinct scope and owner that share the same source label; (4) close/reopen through
an independent handle, rehydrate both rows, and expire only the target; (5) verify event
order and revisions across the restart; (6) reject clearing/lengthening finite expiry,
an expired generation's mutation, and stale token replay after purge.

These are test expectations on **synthetic temporary data**, not claims of currently
completed cross-platform PASS. Deletion is limited to the ephemeral test database.
Event history remains locally mutable; CAS tokens are not human consent or provenance.

## 3. Local redaction grammar/domain/byte-budget custody (15 test cases)

`src/ark/offline_context_redaction.py`, source commits
`c93bf28223f6e9375f871ca07ab88fc228b30c05` and
`14328cb262132eafd5f60e22b8e6d6ed44e188d6`.
`tests/test_offline_redaction_source_protocol_run755.py`, commit
`472daa39637b554131fd033a5ac7fcdd736ea064`.

Redaction now checks the import-original SHA/label regex identities, result-hash domain,
and exact text/span budgets. The preflight is at function ingress **before** any
potentially substituted pattern evaluates owner/scope/source metadata; later
source/result epoch checks remain. The new tests cover malicious matcher identity
without invocation, altered or boolean budgets, an altered domain, both complete and
partial masking, and a clean non-authorizing full-mask result.

This is local fail-closed callback integrity, **not** a Python sandbox, PII detector,
verified erasure, authenticated consent or an export grant. Existing frozen
Memory v1, V2, Local UI and Launcher contracts are unchanged.

## 4. Read-only V3 guard review, no training

Draft PR #5 remains at `805b377697472268db02650a89c7a94b1c5337c8`.
The control packet distinguishes preflight from full-training consent; the PR body
documents missing immutable upstream revision/materialized model and tokenizer bytes,
human-approved 120/30 dataset, exact runtime and llama.cpp identities, explicit
user JPY ceiling and provider billing-cap evidence. These blockers are preserved.
No external GPU, local physical GPU, Candidate weights, protected V2 evaluation or
auto-promotion was run. PR #9/UI remains untouched.

## 5. Evidence limitations and next work

At the last pre-report read, [CI #42752237805](https://github.com/Iam-2squared/ark-ai/actions/runs/42752237805)
for source/test HEAD `286e4ebef576c6014dd067b66afa6f44f2e3b674` was **IN PROGRESS**.
Earlier three CI runs are **known FAIL** on the malformed Ruff line and cannot serve
as a result for the repaired source. Report and checkpoint commits each create a
different SHA; latest exact-head 6/6 GREEN is unproven until confirmed.
No local full pytest or physical-PC GGUF evidence was generated.

1. Obtain the exact new run's six-platform result. If it fails, inspect the actual
   failing job log, apply the smallest normal Contents API fix, then continue independent lanes.
2. Extend actual-memory expiry/ABA and COMMIT-UNKNOWN readback only after this layer is green.
3. Keep Planner uncertain WRITE quarantine, exact PermissionGate, audit-before-action,
   and disconnected mock execution distinct until lower layers are verified.
4. Maintain PR #5 and paused PR #9 as Draft/unmerged. No paid resource, secrets,
   irreversible real effects, Candidate authorization or protected evaluation.

**Overall: ARK/JARVIS/V3 NOT_PASSED.**
