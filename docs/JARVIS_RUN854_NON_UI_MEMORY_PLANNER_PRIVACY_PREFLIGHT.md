# ARK AI Run854 — non-UI Memory / Planner recovery / Personal Context SQLite ingress

Work basis: `0a55e7433887b323831909f8467a4947e74ee0e7` (Run853 checkpoint), whose exact-head [GitHub Actions CI #43487043887](https://github.com/Iam-2squared/ark-ai/actions/runs/43487043887) completed GREEN on Windows/Ubuntu × Python 3.11/3.12/3.13 (all six jobs). **Run854 work is separate, not covered by that older-head green evidence.**

This record covers only disposable/local synthetic SQLite fixtures and reversible code/test changes on Draft PR #8. V1/V2/Local UI/Launcher frozen evidence and PR #5/#9 untouched. No external compute, paid API, secrets, protected evaluation, Candidate work, UI work, main merge, real dispatch, real approval or hardware action.

## Work package 1 — coherent Memory SQL preflight before private row hydration

Source: [`e62155c1`](https://github.com/Iam-2squared/ark-ai/commit/e62155c1a2bcfa4152e259086c5af5caad4ff102). Tests: [`09c02ad2`](https://github.com/Iam-2squared/ark-ai/commit/09c02ad262a130e15120ba03c36bca2388367caa), `tests/test_memory_coherent_sqlite_ingress_run854.py` (10 authored cases).

`sqlite_retained_coherent_review.review_retained_coherent_memory` now executes relational row/event COUNT bounds and a SQLite-native storage-class/identifier-width preflight before asking `_record` to materialize any private row, in the SAME existing read transaction as the retained prefix/lifecycle/WAL reconciliation. This catches malformed data even when it belongs to another owner, before copying that owner's private content into the Python process. Limits are compatible with existing MemoryWrite identity/content budgets; the permissive metadata JSON upper bound is an ingress resource ceiling, **not a substitute** for canonical JSON/schema verification by `_record`. No v1 schema mutation, cryptographic attestation, auto-repair or Memory disclosure authority.

New tests cover BLOB/overlong identities/content/metadata in a foreign owner's row, both row/event scan limits, and healthy unchanged denial-only replay. In tests the `_record` boundary is intentionally made forbidden to assert **early refusal**, not to prove a production no-read guarantee against malicious SQLite or cross-process races.

## Work package 2 — Planner recovery path and sidecar custody

Source: [`1e55e665`](https://github.com/Iam-2squared/ark-ai/commit/1e55e665dd2c1bc168ac61b4cf4094519b7f09e6). Tests: [`ff6efc5a`](https://github.com/Iam-2squared/ark-ai/commit/ff6efc5a3afe14a6318e524ebc8ecf0642d3e38d), `tests/test_planner_recovery_sqlite_sidecars_run854.py` (18 authored cases).

Found a concrete read-path inconsistency: `SyntheticPlanJournal.recover` built a read-only `Path.resolve()` URI without calling the existing journal path admission, while append/initialization called that guard. Recovery now refuses post-initialization main-file symlinks and unsafe parent paths before constructing a SQLite connection. The shared guard additionally rejects over-4096-character paths and unexpected/orphaned `-wal`, `-shm`, `-journal` files that are not singly linked regular files, for initialization, recovery and append.

Tests cover unsafe directories, symlinks/hardlinks and orphaned sidecars before connector callbacks, plus legitimate unchanged recovery. This is **best-effort lexical preflight, not atomic descriptor-held pathname custody**, so race-to-open, WAL/SHM final-connection-close unlink behavior, and independent actor provenance remain unresolved. Recovered RUNNING is still UNKNOWN; automatic replay and tool dispatch stay denied.

## Work package 3 — privacy-safe durable request replay preflight

Source: [`540b77b7`](https://github.com/Iam-2squared/ark-ai/commit/540b77b74050920f5a65999f526e9821874516e6). Tests: [`f9c8f547`](https://github.com/Iam-2squared/ark-ai/commit/f9c8f5477984154a952d396197ff98b069b461db), `tests/test_personal_context_replay_sqlite_preflight_run854.py` (8 authored cases).

`DisconnectedContextReplayLedger._inspect` now checks SQL COUNT <= 512 and exact text/storage classes for the `ctxreq_` +64 SHA request ID and four 64-character digests before Python row decoding and hash callbacks. This is inside the current transaction and applies to startup, witness, retained-prefix checks and reserve readbacks. Tests use only hash-only synthetic bindings and malformed disposable rows; none grants disclosure, consent, revocation freshness, notification, or execution.

## Evidence status and explicit blockers

- **36 authored regression cases total** across three independent packages. Authored ≠ PASS; no full local Ruff/pytest or physical-PC GGUF validation was performed in this run.
- GitHub automatic CI after commits is in flight, NOT confirmed GREEN at this document's composition. The newest source+test HEAD is `f9c8f5477984154a952d396197ff98b069b461db`, [CI #43496430949](https://github.com/Iam-2squared/ark-ai/actions/runs/43496430949) **QUEUED** at last observed time. Earlier source/test heads have different in-flight jobs and must not be substituted for latest HEAD evidence.
- All new tests/source are in Draft PR #8; explicit gates remain. Reproduction on real user Windows/GGUF hardware remains unavailable.
- SQLite sidecar/rename races, final close on SHM link count, independent durable consent/clock/provenance and exactly-once external effects remain **NOT PASSED**. Local SQLite hashes are not independently retained attestation. Never auto-retry COMMIT-UNKNOWN.
- The Personal Context record count budget and Memory metadata upper bound are pre-hydration resource gates; all existing format, canonicality, scope, lifecycle and identity checks remain independently required.

## Next plan / 今後の方針

1. Check latest exact-head CI Windows/Ubuntu six jobs; if FAIL, inspect actual Ruff/pytest failures, perform minimal semantics-preserving repair without relaxing rejection, then work on independent modules while CI runs.
2. Investigate Memory/ActionAudit WAL/SHM last-close descriptor/link-count behavior on disposable databases; do not accept unsafe unlinked held descriptors merely because normal SQLite cleanup caused it.
3. Strengthen Memory COMMIT-UNKNOWN retained row/event recovery and Planner restart persistent UNKNOWN/quarantine under competing writers, with explicit CAS and append highwater checks.
4. Only after exact-head prerequisites GREEN, connect ToolRegistry, exact-type PermissionGate, persistent occurrence/replay and audit-before-action to **disconnected Mock**, never real dispatch.
5. Continue privacy-safe Personal Context, proactive scheduler/observation fixtures and free-only V3 guard reviews. All frozen contracts/evidence, protected evaluation, Candidate promotion and UI development remain unchanged/blocked.
