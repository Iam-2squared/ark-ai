# Run535 — local Memory, Scheduler, and registered Planner archive custody

This record covers three isolated, disconnected, free-only JARVIS foundation packages on Draft PR #8, starting from work-basis commit `49b3e7a7fe1b050f18dce2227fb28c67477637cc`. No frozen Memory schema/API, Planner contract, main, V1/V2/Local UI/Launcher evidence, ToolBackend dispatch, live notification, trusted-clock attestation or external model/compute path was changed.

## 1. Memory generation CAS — retention cannot grow implicitly

`src/ark/memory/generation_fenced_cas.py` adds a strict check **inside its existing `BEGIN IMMEDIATE` generation-fenced update**, after the exact row/event witness and clock checks but before row/event mutation. If a row has a finite expiry, a replacement expiry of `None` or a later deadline now fails with `MemoryGenerationCASRejected`. The same deadline or a shorter *future* deadline is allowed. An initially unbounded record may stay unbounded or acquire a finite future deadline.

A generation/revision token is neither an authenticated consent statement nor a retention extension permission. This check deliberately offers no override; an independently verified retention policy/PermissionGate must be designed before a future relaxation. Frozen legacy `SQLiteMemoryStore.put/delete` remain unchanged, so this is **only** an opt-in CAS protection, not a claim that all Memory writes enforce the rule.

`tests/test_memory_generation_cas_retention_fence_run535.py`: eight parametrized pytest cases including rejection with no extra durable event and retained lifetime on a failed extension.

## 2. Scheduler synthetic quarantine — restart time floor

`src/ark/offline_schedule_resume_review.py` now brackets a **read-only SQLite lookup** of the most recently quarantined slot's persisted `observed_ms` with full ledger witness inspections. If the caller-supplied preview time predates that timestamp, the restart preview rejects it; a genesis ledger has no prior floor. Corrupted/missing tail values or SQLite errors reject rather than manufacturing a due state.

`tests/test_offline_schedule_resume_clock_floor_run535.py`: ten cases for one/two historical quarantines, equality and regression boundaries, and genesis. The time comparison detects internal inconsistency only. Caller wall clock is untrusted, ledger times are not independently authenticated, and no scheduled occurrence is executed, replayed or notified.

## 3. Planner durable mock archive + registered READ set join

`src/ark/agency/disconnected_registered_archive_bridge.py` is a **read-only joining diagnostic** for an already persisted, independently SHA-pinned mock cycle file and the complete registered READ receipt set of the exact same bounded DAG plan/schedule. It invokes existing archive and ToolRegistry/PermissionGate/SQLite receipt verifiers, independently compares plan/schedule/step count, constructs a domain-separated joined SHA-256 of the matching evidence, and repeats source reviews after all deny-only result callbacks.

`tests/test_registered_cycle_archive_bridge_run535.py`: nine cases covering success without backend calls, mismatched independent hashes/evidence/time, file and SQLite tampering, and a reflectively modified denial result.

**Limitations:** separate SQLite and file reads are not an atomic cross-store snapshot. Local SHA-256 checks cannot authenticate writers or human intent. No tool dispatch, real outcome proof, dependency completion authority, WRITE, automatic replay or UNKNOWN WRITE recovery permission is produced. An ambiguous persisted transaction remains manual-only.

## Tests and open gates

**27 newly authored pytest cases** across the three PR #8 packages (8 + 10 + 9), not 27 independently executed standalone local PASS. GitHub Actions runs six standard Python/OS matrix jobs; use exact head/run IDs when stating CI. The early scheduler test source CI was rejected for Ruff import order in `test_offline_schedule_resume_clock_floor_run535.py` and the import-only correction was saved at `b5fb9273a7e8a68495cfe87e8d901232f026838c`. Do not represent prior failed runs as passed.

PR #8 stays Draft/unmerged; no paid API, remote GPU, protected V2 evaluation, Candidate generation, consent/license decision, real external action, destructive cleanup, or automatic promotion. Future integration requires exact-head CI, trustworthy audit-before-action and explicit user approval for the restricted boundaries.

## Next

Confirm exact-head CI on the corrected sources, inspect any failed job and fix without reducing rejection boundaries. Extend independent persistence/recovery evidence for Planner and retention/clock policy only on free synthetic fixtures. Keep live ToolBackend, payment, protected evaluation and main integration separate.
