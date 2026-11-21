# Run544 — Detached WRITE Slot and Memory Witness Scalar CAS

**Scope:** opt-in, disconnected, local SQLite fixture invariants on Draft PR #8. No real action, consent, independent custody, trusted actor/clock, protected evaluation, model training, or external compute is authorized.

**Work basis:** `f88c75063366b23b7f7b37248183a0b26527e95d` (Run543 checkpoint). Source and regression-test commits were saved using ordinary GitHub Contents writes against current branch/blob state:

| Package | Source commit | Test commit | Regression coverage |
|---|---|---|---|
| Detached WRITE slot ledger | `f95ded7336768147b5365fc32573bd40afdb7b7d` | `8862c09a5a4e5e139bf4758540cf72c8dd78cf38` | 4 authored pytest functions |
| Detached Memory witness ledger | `5081abc132ded6f35d5d51cd7cda1ab1c2a9cc45` | `3d130215f598ed67129acab8239ba7060423b9e0` | 4 authored pytest functions |

## Failure class and correction

A frozen dataclass instance does **not** make its class's `__eq__` implementation immutable. Under a deliberately poisoned test process, replacing `WriteSlotLedgerWitness.__eq__` or `MemoryLedgerWitness.__eq__` with an always-True method could cause a stale independently retained synthetic witness to compare equal to a newer SQLite tip. Always-False equality could reject legitimate read-only reviews. Equality could also mask a forged in-transaction post-insert witness returned by an instrumented inspection callback.

Three comparisons in each ledger now match the already validated **actual count and chain hash primitive values** directly to a pinned caller tip or the locally computed expected append tip:

- read-only restart/inspection: reject stale retained count/hash;
- `BEGIN IMMEDIATE` append/reservation: reject stale retained count/hash before insert;
- same-transaction post-insert scan: reject inconsistent committed-intent count/hash and roll back before COMMIT.

Existing exact carrier checks, SQLite transaction behavior, schema, caps, path ancestry safeguards, and non-authorizing result flags remain unchanged. A SHA-256 chain **detects local disagreement** only; it never authenticates a writer, grants consent, or proves external exactly-once effects. A post-COMMIT exception remains ambiguous and never justifies an automatic retry.

## Deterministic regression scenarios

Both modules exercise (1) stale read + always-True equality; (2) stale write + always-True equality with unchanged persisted row count; (3) forged second in-transaction inspection with always-True equality, forcing rollback; and (4) a legitimate read/append under always-False equality. The tests are at:

- `tests/test_write_slot_scalar_custody_run544.py`
- `tests/test_memory_witness_scalar_cas_run544.py`

**Evidence status at note authoring:** eight test functions have been **authored** and source/test commits saved, not independently executed locally. Exact-commit GitHub Actions run IDs and six-job outcome must be checked separately. No PASS may be inferred from writing the tests.

## Remaining safety work

The local synthetic witnesses are caller-retained and not an authenticated custody root. Higher-level integration still requires trusted-clock audit-before-action, exact ToolRegistry+PermissionGate, durable occurrence/replay protection, COMMIT-UNKNOWN manual-only triage, memory expiry/revocation, independent privacy consent, and a disconnected startup readiness gate. Keep PR #8 Draft/unmerged until its explicit approval condition.
