# ARK AI — Run703 non-UI core / 2026-11-08 JST

> **DRAFT / NOT_PASSED.** Free-only, local and disconnected fixture work.
> No UI/frontend work, paid/external GPU/API call, actual Candidate training,
> protected V2 evaluation, real tool dispatch, user-account connection,
> physical-PC action, frozen-contract modification, or main merge.

## Verified starting point and bounded change set

- Repo: `Iam-2squared/ark-ai`; branch `research/jarvis-foundations`;
  [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) remains
  OPEN / Draft / unmerged.
- **Initial exact work-basis HEAD:** `e7ff4d7fc8489a761cffc3b31e643c5d34c4e22d`
  (Run702 checkpoint). Latest pre-report HEAD after three ordinary Contents
  API commits: `697522bb52afa645ca350e18e08f66cc3783a883`. No force push or raw Git-object writes.
- PR #5 at `805b377697472268db02650a89c7a94b1c5337c8` is an
  independently gated Draft; UI PR #9 at
  `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` is an untouched
  Draft. `main` remained `7a843f17eb96ed13d66f23b58b06406b3002e405`
  at invocation inspection; frozen V1/V2/Local UI/Launcher evidence unchanged.
- Four coherent packages: actual CI failure repaired, Planner mixed-terminal
  restart classification **20 new cases**, proactive retained-history
  substitution **3 new cases**, and PermissionGate registered WRITE token
  non-consumption **11 new cases**. **34** newly authored cases total, not a
  claim that the latest six platform jobs passed.

## A — Fix real multi-platform audit continuity CI failure

[Prior Run702 CI #42444652179](https://github.com/Iam-2squared/ark-ai/actions/runs/42444652179)
actually completed **6/6 FAIL**. Ubuntu Python 3.11 and Windows Python 3.12
job logs both singled out existing
`tests/test_synthetic_recovery_link_review_run375.py::test_linked_audit_event_deletion_is_rejected`.
The new Audit v1 append-only SQLite AUTOINCREMENT high-water correctly
refuses an erased tail **before** the later synthetic four-ledger link reviewer
can report a missing linked event. The old test expected the later
`SyntheticRecoveryRejected` and therefore failed on the earlier
`ActionAuditSchemaError("audit append-only high-water mismatch")`.

[Test-only fix `de0afc72`](https://github.com/Iam-2squared/ark-ai/commit/de0afc72feaa43695083194d38f01aabf18c8abf)
requires the actual early, fail-closed diagnostic. No Audit schema,
high-water enforcement, authorization, write implementation, or frozen
contract changed. [Fix-head CI #42448039012](https://github.com/Iam-2squared/ark-ai/actions/runs/42448039012)
was running; it is NOT evidence of final HEAD 6/6 GREEN.

## B — Planner fan-in restart terminal/uncertainty matrix

[Test-only `b425c837`](https://github.com/Iam-2squared/ark-ai/commit/b425c837afe853f3f72e52c1d62dccda3bf6214b)
adds `tests/test_read_recovery_fanin_terminal_matrix_run703.py`, **20**
parameterized cases:

- Five root states feeding a two-parent join, descendant and independent
  sibling: pending waits; FAILED terminally holds descendants;
  RUNNING/UNKNOWN quarantine; SUCCEEDED remains unverified.
- Two mixed FAILED/UNCERTAIN fan-ins ensure terminal failure dominates
  uncertainty without laundering sibling states.
- Twelve combinations of an already-started child after any unresolved
  parent must reject contradictory recovered histories.
- All-success fan-in still has **no dispatch, replay or external outcome
  verification authority**.

Inputs are synthetic and no model, backend, physical hardware, network or
real user data is accessed. [CI #42448151947](https://github.com/Iam-2squared/ark-ai/actions/runs/42448151947)
was still running at first check.

## C — Proactive restart retained-history substitution

[Test-only `697522bb`](https://github.com/Iam-2squared/ark-ai/commit/697522bb52afa645ca350e18e08f66cc3783a883)
adds `tests/test_proactive_retained_count_substitution_run703.py`:
**3** first/middle/last synthetic occurrence-deletion fixtures.
A separate SQLite connection deletes one historical marker. A new valid
synthetic preparation replaces it so **row count remains unchanged**.
The restarted caller's externally retained older digest must expose the
history replacement and refuse a further preparation. No notification
authorization is granted, even on the new local receipt.

This demonstrates the limit of local row counts: retained evidence must
actually be kept separately by the caller. Neither test establishes
authenticated provenance, trusted clock, consent or real scheduler service.
[CI #42448217889](https://github.com/Iam-2squared/ark-ai/actions/runs/42448217889)
was IN PROGRESS at first check.

## D — Registered WRITE permission denials never spend a local token

[Test-only `1e900ad2`](https://github.com/Iam-2squared/ark-ai/commit/1e900ad24b2b4d7b7624c097842dfc981c0c39ef)
adds `tests/test_registered_write_denial_token_nonspend_run703.py`:
**11** cases covering six invalid exact-type/bounds clocks, three
expired/mismatched capability grants, and two rejected token request/expiry
values. Each checks that a valid subsequent local registered WRITE
authorization can consume that same still-unused token only once, without
calling the mock backend. This is an in-process fixture gate, NOT durable
consent, execution authority or trusted-time proof.
[CI #42448400091](https://github.com/Iam-2squared/ark-ai/actions/runs/42448400091)
was QUEUED/IN PROGRESS at first evidence inspection.

## CI accuracy, hard stops, and next plan

- **Known earlier failure:** #42444652179 was 6/6 FAIL and its one
  distinct observed failure is corrected in commit `de0afc72`.
- **New CI:** #42448039012, #42448151947, #42448217889 and
  #42448400091 were IN PROGRESS / QUEUED at evidence preparation. Do not promote any partial
  Ubuntu/Windows result to final exact-head six-job GREEN. This document
  and the canonical status checkpoint each create their own HEAD.
- Zero-cost/free-only: no paid/potentially billable compute, no external GPU,
  no paid model APIs, no Candidate/adapter/weight generation or promotion,
  no protected V2 evaluation opening, no secrets, credentials, account
  connections, irreversible operation, real tool effects or main merge.
  PR #5/#8/#9 remain Draft/unmerged; **UI paused**.

### Prioritized next plan / 今後の方針

1. Confirm final exact-head six-job CI; inspect real failure logs and make
   the minimal semantics-preserving correction if required.
2. Extend Memory CAS/ABA/COMMIT-UNKNOWN and local WAL/coherent-snapshot
   consistency, without automatic retry of uncertain writes.
3. Advance persisted Planner step-specific READ receipts, correct
   RUNNING/UNKNOWN recovery, immutable ToolRegistry/exact-type PermissionGate,
   and restart-safe disconnected audit-before-action occurrence fences.
4. Continue privacy-safe Personal Context, proactive local dedup/state,
   Observation fixture contracts, and passive V3 authorization/provenance
   guard audits while keeping all frozen/pay/physical boundaries closed.
