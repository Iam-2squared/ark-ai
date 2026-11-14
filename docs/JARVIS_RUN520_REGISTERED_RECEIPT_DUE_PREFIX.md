# Run520 — Registered READ SQLite reconciliation and due-prefix terminal integrity

**Draft PR #8 / `research/jarvis-foundations`.** Work basis: previous checkpoint HEAD `1a8718c8f2c49e7c35d82e3a7c39ed4a6b2328e2`. Final combined source+test HEAD before this documentation: `c02aae319b1c72ab07830fb8f319ca1df29347f8`. No main merge and no frozen Agency/Memory/V1/V2/Local UI/Launcher contract change.

## Package A — persisted registered READ/link inspection, 18 new tests

- `src/ark/agency/disconnected_registered_receipt_review.py` added at `b2fb77e1fb0888befbd318938d9993cfa6a22d9b`. It accepts the prior independent local `RegisteredFixtureLink`, a caller-retained `ReadJournalWitness`, the immutable registry/grant/fixture inputs and the already-opened `DisconnectedReadJournal`.
- Before and after one read-only SQLite snapshot it recomputes the registry/grant/fixture correlation and verifies exact untrusted `act_` and `req_` namespaces. Within **one** `BEGIN`/snapshot it checks the entire v1 receipt chain and the exact target row. Caller witness count+tip must match that snapshot. No duplicate append or automatic retry is attempted.
- The link is **not** stored in journal schema v1. The caller must retain it and the witness separately; hash matching proves neither external Tool execution, authenticated historical provenance, independently trusted time, consent, replay rights nor external result identity.
- `tests/test_registered_receipt_restart_review_run520.py` added at `5890fe2995b11125a3f2d35df96b16205e36163c`, with 18 parametrized cases for reopen and same-snapshot checks, forged linkage, stale counts, edited/deleted SQLite rows, wrong or expired scope, WRITE substitution, reflected carrier mutation, and denial-only outputs. [Source+test CI 41274238791](https://github.com/Iam-2squared/ark-ai/actions/runs/41274238791) was IN PROGRESS when this evidence was prepared; partial GREEN does not validate final HEAD.

## Package B — synthetic Scheduler due-prefix final denial, 9 new tests

- `src/ark/agency/disconnected_due_prefix_review.py` tightened at `49781e368213f82069b11898b1166a314f5ef45e`. Its previously validated local receipt now rechecks **all** status/count/digest fields after the last false-valued authority getter and after final retained-source checks.
- This closes an integrity gap where an injected `automatic_replay_authorized` property could return False while replacing `status`, `previous_count` or `current_count` on a frozen dataclass after the first field comparison.
- `tests/test_due_prefix_final_fields_run520.py` added at the final source+test HEAD above: 9 cases, including six late report mutations and retained witness drift. The ledger is a synthetic local SQLite fixture; **no** notification, trusted time, scheduling, ToolBackend, WRITE, erasure or replay is authorized.
- [Final combined source+test CI 41274431370](https://github.com/Iam-2squared/ark-ai/actions/runs/41274431370) was IN PROGRESS at document preparation. Do not inherit earlier branch CI success; require 6/6 for this exact head.

## Boundaries / next steps

These are disconnected, reversible, free-only controls. No paid/external compute, Candidate training, V2 protected evaluation, real Tool READ/WRITE or action execution, credentials, physical-PC operation, destructive data change, model promotion or main merge. Independently retained hashes are not authenticated and cannot establish cross-process consent, externally completed effects, trusted clock, storage rollback immunity or cross-store atomicity.

After exact-head CI succeeds, extend mock Planner DAG → registered READ → persisted journal correlation under a **restart-safe read-only** interface. Then address durable UNKNOWN WRITE manual triage, Memory CAS/event/prefix custody, trusted-clock audit/occurrence fencing, Scheduler deduplication and Personal Context privacy revocation without opening effects.
