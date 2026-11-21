# ARK AI Run884 — Detached Personal Context, Observation and Memory byte admission

**Scope:** non-UI, disconnected/local-only source/test hardening; Draft PR #8 only. **JARVIS: NOT_PASSED.** No real tool execution, model training, protected evaluation, external device/compute, private user account connection, new service or main merge.

## Initial verified baseline

- Work-basis branch HEAD: `9000fc45a35769d5f96a175b98244ec723e31c64` (Run883 canonical status checkpoint).
- [Run883 exact-head CI #43655512248](https://github.com/Iam-2squared/ark-ai/actions/runs/43655512248): completed **GREEN, all 6 individual jobs** (Windows/Ubuntu × Python 3.11/3.12/3.13).
- [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) remained open/unmerged at start. Frozen V1/V2/Local UI/Launcher paths and protected V2 evaluation were not opened. Draft PR #5 and UI-paused Draft PR #9 are not modified.

## NEW: three independent, reversible non-UI packages

1. **Ephemeral Personal Context admission.** `src/ark/personal_context_review.py` and `tests/test_personal_context_utf8_digest_budget_run884.py`. Policy revision now requires a valid, nonempty, **at most 128 UTF-8 bytes** exact string; reflected/fabricated snapshot and Memory row SHA-256 identifiers must be exactly 64 codepoints *before* their regex matching. This does not change Memory v1 DDL, frozen data, consent, export or tool authority. **9 new synthetic parameter cases authored.** Initial source commit `ee19a11f2187cbb3b583495b536f8082aef36830`; package source/test HEAD `06658fe20bf7a284c3926715c7e2f1311bf62380`.
2. **Disconnected Observation metadata-before-digest.** `src/ark/disconnected_observation_fixture.py` and `tests/test_disconnected_fixture_metadata_preflight_run884.py`. An inert in-memory `ObservationEnvelope` with a fixed SHA-256 sentinel validates **source ID, privacy label, clock and optional parent digest before hashing** an exact-bounded 1..65,536-byte *caller-supplied synthetic* payload. The preliminary envelope is never returned or stored, and no raw payload enters metadata. A direct-function C-call profiler fixture checks that each of ten malformed-metadata cases reaches no payload hashing; an admitted case exercises one payload hash. **11 synthetic cases authored.** Initial source HEAD `88150bff1a5211b8e41dfcf884b631c938d46cf1`; package HEAD `c7cde5f2886f3c257b84c30931c5d8e10093614b`. No live camera, mic, screen or file adapter.
3. **Coherent Memory snapshot query byte ceiling.** `src/ark/memory/coherent_snapshot_review.py` and `tests/test_coherent_snapshot_search_byte_budget_run884.py`. Existing 4,096-character request query check remains; the validated UTF-8 encoding is now capped at **4,096 bytes before SQLite access**, closing the multibyte expansion gap. No Memory v1 schema, store API, CAS, expiry or persistence changes. **9 synthetic cases authored.** Initial source HEAD `478751ba354cc25bacf8565f03718d1ae1fa1f13`; complete source/test HEAD `3327add81b8222682ba26f4851f23ad2e2bbe20a`.

**Total: 29 authored test cases, NOT 29 verified passes.** GitHub compare `9000fc45...3327add81`: six normal Contents API commits, **exactly three non-UI source files and three new test files**. Local checkout/pytest/Ruff is unavailable in this execution container because public GitHub DNS resolution fails. The GitHub Actions jobs provide platform test evidence only after exact-HEAD completion.

## Exact-head CI observations at evidence writing

- [Context source CI #43659967525](https://github.com/Iam-2squared/ark-ai/actions/runs/43659967525): **IN PROGRESS** at last read.
- [Context source/test CI #43660028330](https://github.com/Iam-2squared/ark-ai/actions/runs/43660028330): **IN PROGRESS** at last read.
- [Observation source CI #43660101827](https://github.com/Iam-2squared/ark-ai/actions/runs/43660101827): **IN PROGRESS** at last read.
- [Observation completed package CI #43660179473](https://github.com/Iam-2squared/ark-ai/actions/runs/43660179473): **QUEUED** at last read.
- [Memory source CI #43660264394](https://github.com/Iam-2squared/ark-ai/actions/runs/43660264394): **QUEUED** at last read.
- [All-three source/test CI #43660310802](https://github.com/Iam-2squared/ark-ai/actions/runs/43660310802): **QUEUED** at last read. **Latest exact-head six-job GREEN is not yet established.**
- No redundant manually dispatched workflow. Report and checkpoint commits create their ordinary separate PR-triggered CI.

## Independent evidence audit: outstanding revocation concurrency

Historical [CI #43634279883](https://github.com/Iam-2squared/ark-ai/actions/runs/43634279883) Ubuntu/Python 3.12 log contains a **distinct intermittent** failure in `tests/test_privacy_revocation_cross_process_run425.py[0]`: `LOSER_REJECTION_DETAIL:'unsafe revocation SQLite sidecar'`; the other contender printed `REVOKED`, and the diagnostic read returned `durable_count_time=(1, 2000, 2000)`. Overall job: **1 failed, 15,657 passed, 1 skipped**. A durable veto witness survived, but the contender's strict loser/retry contract failed. This evidence does **not** identify the precise sidecar syscall race or prove that the bounded re-lstat mitigations later committed in Runs879–883 eliminate it. Do not relax symlink/hardlink/orphan rejection, infer consent, retry an ambiguous WRITE or declare concurrency PASS.

## Next / 今後の方針

1. Check **all six jobs** for latest complete source/test HEAD and checkpoint HEAD; investigate any failure without weakening the original rejection or identity semantics.
2. Diagnose SQLite -wal/-shm last-close and Privacy Revocation competing-process failure with restart-safe, path-classified diagnostics; preserve COMMIT-UNKNOWN quarantine.
3. Advance Memory generation/CAS/expiry coherence and Planner crash UNKNOWN/terminal propagation after exact-head green, without unapproved tool authority.
4. Connect immutable ToolRegistry, exact-type PermissionGate, occurrence and atomic audit-before-action to **disconnected Mock Executor** only after prerequisite CI/evidence.
5. Continue privacy-first Personal Context, proactive scheduling and synthetic observation/V3 free-only guards. **All UI/frontend work remains PAUSED; no paid compute, protected V2 opening, Candidate promotion, real backend dispatch or main merge.**
