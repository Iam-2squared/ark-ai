# Run851 — Non-UI SQLite sidecar path custody and exact-head CI recovery

**Work basis:** `2deb4a12fb9a28cbd764e3def70b590f3ca16af8` (Run850 checkpoint); branch `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). **All work is offline, reversible, free-only; overall ARK/JARVIS remains NOT_PASSED.**

## 1. CI failure correction: coherent Memory snapshot

[Prior exact-head CI #43457126299](https://github.com/Iam-2squared/ark-ai/actions/runs/43457126299) **FAIL 6/6** (Ubuntu/Windows × Python 3.11–3.13) after successful Ruff and during pytest. Inspected Ubuntu 3.12 job `131994086263` (1 failed, 15115 passed, 1 skipped) and Windows 3.12 `131994086325` (1 failed, 15026 passed, 90 skipped). Both showed the same **existing test diagnostic mismatch**, not a failure of the fail-closed result: `test_hash_callback_cannot_replace_report_constructor_before_use` expected `invalid retained witness`, whereas the earlier pre-access pin correctly rejects the substituted `hashlib.sha256` with `coherent Memory digest implementation or domain changed`. The injected callback did not execute.

[Test-only correction `f859f2a6`](https://github.com/Iam-2squared/ark-ai/commit/f859f2a6f8f81882fcef09c547594b481521f65e) updates that **one diagnostic assertion** to the observed earlier rejection. No production Memory implementation, rejection condition, frozen evidence or protected evaluation was changed. Full CI on the fixed HEAD must be checked; an earlier PASS cannot be promoted to a later HEAD.

## 2. Detached WRITE slot ledger: WAL/SHM/journal custody

[Source `7faeba0b`](https://github.com/Iam-2squared/ark-ai/commit/7faeba0ba2fed0f6ccec75536e410210c2e95b98) updates `src/ark/agency/disconnected_write_slot_ledger.py` `_check_path` to reject:
- Orphaned `-wal`, `-shm` or `-journal` pathnames when a new synthetic ledger would be created.
- Non-regular, symbolic or multiply linked sidecar pathnames when an existing ledger would be inspected or reserved.
- New-ledger bootstrap with any pre-existing sidecar path, before SQLite opens.

The existing regular-file and ancestor checks remain. [13 authored parameterized regression cases `ed8862a9`](https://github.com/Iam-2squared/ark-ai/commit/ed8862a9956181a81f00673374cc05ea455e4eed) cover 3 sidecar suffixes × directory/orphan/hardlink/symlink, plus a positive reservation/reopen. Host features unsupported for hardlinks/symlinks may explicitly SKIP. All paths use disposable pytest fixtures.

## 3. Detached proactive due ledger: WAL/SHM/journal custody

[Source `af516efe`](https://github.com/Iam-2squared/ark-ai/commit/af516efe624cfd871e205e91b49a5abe3c2e92df) updates `src/ark/agency/disconnected_due_reservation.py`: bound local fixture path length to 4096 characters before filesystem operations; inspect main DB via `lstat` to deny missing/aliased/non-regular files; reject orphan, non-regular, symlinked or multiply linked WAL/SHM/journal pathnames before SQLite opens. Preserve read-only restart and all existing no-actual-notification denial flags.

[14 authored regression cases `2349ca91`](https://github.com/Iam-2squared/ark-ai/commit/2349ca9188973b0111b275f001c2170c6f844a9d) cover three sidecar suffixes × four unsafe sidecar types, overlong path, and valid reservation/restart. No real reminder is scheduled or sent.

**Important limits:** these are best-effort pathname preflights, **not** race-free held-fd custody, independent attestation, authenticated consent, trusted clock or exactly-once external effects. A SQLite last-close can remove the SHM pathname without malice; do not weaken no-follow/single-link policy or treat ambiguous post-COMMIT state as rolled back. CI runs and authored test counts are not proof of all-environment PASS.

## Remaining integration gates

V1/V2/Local UI/Launcher frozen contracts/evidence unchanged. PR #5 is protected Draft/unmerged. UI PR #9 stays paused Draft/unmerged and untouched. No paid external compute/API, Candidate generation/promotion, protected evaluation opening, real hardware/microphone/camera, real ToolBackend execution, credential connection, destructive operation or main merge.

1. Confirm exact-HEAD six-matrix CI, inspect each failing job and fix only the minimum non-weakening regression.
2. Continue disposable independent-process Memory/ActionAudit/WAL last-close diagnosis; do not auto-retry COMMIT-UNKNOWN.
3. Strengthen Memory coherent CAS/expiry/event highwater, Planner durable terminal/UNKNOWN quarantine, immutable registry/policy identity and persistent audit-before-mock-action in separate reversible lanes.
4. Reconcile concurrency and process-crash evidence before claiming restart-safe exactly-once authorization, trusted action or JARVIS completion.
