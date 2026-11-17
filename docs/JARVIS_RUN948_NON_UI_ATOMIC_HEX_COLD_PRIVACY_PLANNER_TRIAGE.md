# Run948 — offline atomic-claim CI repair and cold multi-store privacy quarantine

**Scope:** Draft PR #8 `research/jarvis-foundations`, synthetic/local/non-UI only.
**Work basis:** `e535c92ded919e5c64c33cc399b7db5f4d5548b7` (Run947 checkpoint).
This report is not a frozen contract, model evaluation, user consent, trusted clock,
external backend attestation, approval, promotion, or PASS evidence.

## Observed failure and narrow repair

The latest Run947 checkpoint workflow
[44131640642](https://github.com/Iam-2squared/ark-ai/actions/runs/44131640642)
completed **FAIL 6/6**. The Ubuntu Python 3.11 job
`134210015475` reported **3 failed, 17168 passed, 1 skipped**. Windows Python
3.11 job `134210016164` showed the same case taxonomy. All three failures came
from `tests/test_atomic_unknown_four_commit_prefix_run947.py`: test fixture
`_claim("z")` produces `occ_zz...`, `bound_zz...` and `zz...` hashes, but
`AtomicIntentClaim` explicitly requires lowercase hexadecimal `[0-9a-f]`.
This is a **test fixture** bug, not evidence of a production COMMIT-UNKNOWN
classifier defect.

Commit `4a445f8f9d0e635f382e30b82666685f8764ad03` changes exactly three
unrecorded test claims from `"z"` to valid-but-unrecorded `"e"`. The
expected local review states `ADVANCED_OTHER` and `UNCHANGED`, and all
assertions denying dispatch/replay/effect/custody, are unchanged. No grammar,
audit, identity, action or permission validation was relaxed.

## Independent disconnected integration regression

Commit `6600a9b7f6f9e9ebfa396dc6ab7897d5410c461a` adds
`tests/test_disconnected_privacy_planner_unknown_triage_run948.py` with
**3 parametrized cases**, varying which synthetic local record appears first:
privacy veto, Planner RUNNING journal transition, or pre-action intent row.

For each ordering, a fresh-handle read-only recovery reviews:
- a Planner `RUNNING` step as **ambiguous**, never a replay/dispatch grant;
- a locally recorded pre-action claim as `LOCALLY_RECORDED`, **not**
  independently authenticated effect, approval, custody or replay authority;
- a private scoped Memory entry against a durable revocation veto, which
  **still blocks context use and deletion authorization** despite the other two
  local records. The veto remains reconstructable through a cold SQLite reopen,
  and synthetic private content must not appear in diagnostic representations.

This is **not** a common snapshot across Planner, pre-action, Memory and
revocation databases, nor does sequential rechecking close a race after the
last read. No real tool backend, actual notification, external action, device,
Candidate or protected evaluator was invoked. These three new cases remain
unverified until exact-HEAD CI is completed.

## Exact-HEAD CI evidence and outstanding verification

- Previous `e535c92d` workflow **44131640642 FAIL 6/6** as diagnosed above.
- Repair HEAD `4a445f8f`: workflow
  [44139933211](https://github.com/Iam-2squared/ark-ai/actions/runs/44139933211)
  was **IN PROGRESS** when sampled.
- New three-store/privileged-denial test HEAD `6600a9b7`: workflow
  [44140420880](https://github.com/Iam-2squared/ark-ai/actions/runs/44140420880)
  was **IN PROGRESS** when sampled.
- A documentation/checkpoint write creates a later HEAD; do **not** transfer
  a GREEN result from a different HEAD. No duplicate manual CI run.
- No local full-suite run or owner's physical Windows GGUF test was performed.

## Source-backed trust and free-only boundaries

`docs/AGENCY_EXECUTION_CONTRACT.md` requires one-shot authorization and
audit-before-action *before* executing a registered WRITE, with UNKNOWN
outcomes quarantined. A Planner RUNNING row is not permission; a local
pre-action row is not proof of an external effect; a local synthetic privacy
veto is not proof of erasure. `docs/V3_FREE_GUARD_REVIEW.md` continues to
identify preflight identity cross-binding and canonical export-path safety
as precompute guard work; this invocation neither changed the protected V3
branch nor opened those evaluation/training lanes.

Frozen V1/V2/Local UI/Launcher, Contract #1, PR #5 approval gates and all
protected evaluation evidence remain unchanged. PR #9 stays Draft/untouched
and new UI work remains PAUSED. No paid/external compute, secrets, account
connection, real Candidate/weight production, protected V2 evaluation,
promotion, physical-PC action, actual backend execution, destructive
mutation, human approval fabrication or main merge.

## Next plan / 今後の方針

1. Confirm newest exact-HEAD Windows/Ubuntu Python 3.11–3.13 CI 6/6;
   inspect actual failing job logs before a semantics-preserving correction.
2. Deepen Memory WAL/SHM last-close and generation-CAS event alignment,
   especially corruption and ABA under cold readers, without frozen API edits.
3. Examine Planner/registered WRITE/occurrence durable recovery under
   ambiguous crash boundaries. Keep local diagnostics fail-closed and manual-only.
4. Continue privacy revocation and proactive/observation back-end fixture work,
   plus offline V3 approval/path/identity guards; no external operations.

**Overall ARK/JARVIS NOT_PASSED.**
