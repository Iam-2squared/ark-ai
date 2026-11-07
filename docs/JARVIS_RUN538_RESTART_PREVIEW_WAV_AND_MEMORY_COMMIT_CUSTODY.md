# Run538 — Detached Scheduler Preview, WAV Format, and Memory COMMIT Ambiguity

**Scope:** PR #8 Draft, local/synthetic and free-only. This note is source-grounded engineering evidence, **not a PASS, user approval, trusted clock, consent, external action, or completed physical-computer demonstration**. No frozen V1/V2/Memory/Planner contract is changed.

## 1. Scheduler preview digest rederivation

In `src/ark/offline_schedule_resume_review.py`, the restart bridge already independently rederived the policy-bound next occurrence, deadline, and due classification, but accepted any syntactically valid 64-character preview fingerprint from the replaceable preview callback. A forged exact-class `DisconnectedDuePreview` could therefore supply correct visible fields and an unrelated digest. The new bridge independently encodes the retained policy, cursor, caller-asserted clock, expected state, occurrence ID, and deadline using the original `ARK-disconnected-schedule-preview-v1` domain. It refuses a mismatched SHA-256.

The bridge also pins the preview result's original field carriers and authority descriptors, checking them after quarantine-inspection callbacks and after the final returned review's false-only authority getters. The detached quarantine ledger remains a separate read. No clock source is authenticated; neither notifications nor ToolBackend operations run.

**Writes:** source `151fcefbafeae03182cbc643ae790b1d394cb134`, seven authored test variants `119c7d1725a49003b7e8feea8cb66f677559c965` in `tests/test_offline_schedule_resume_preview_digest_run538.py`. Tests cover real NOT_DUE/DUE/EXPIRED classification, forged syntactically valid digests, in-flight quarantine callback mutation, and post-denial preview tampering.

## 2. WAV callback format independent header check

In `src/ark/offline_wave_energy_pipeline.py`, the original inspector verifies WAV structure, but a replaceable callback could return a matching WAV SHA and false sample rate while retaining enough other fields to alter resampling. The pipeline now checks the pinned source's 44-byte canonical `fmt(16) + data` header independently, including PCM format, sample rate, channels, bits, byte rate, complete data length/pad, frame count, and duration fraction. It refuses inconsistent exact-class callback reports before normalization. This is a memory-only WAV fixture operation; no microphone, speech recognition, identity proof, storage, or audio disclosure.

**Writes:** source `1b6bbb64b6260c36c5b4c110a9965e8506e95ddb`; explicit binary-header expression correction `cc1de6d2e14f4172e70d1793968daf2e5ceb811b`; nine authored test variants `490d5d439205c5598016210bd5e51c3612d256ad` in `tests/test_offline_wave_header_binding_run538.py`; and Ruff F841 unused-variable-only correction `24c282ee48af6763e3667371703dd30b5812273d`. Tests cover four ordinary WAV header variants and five forged callback fields.

## 3. Memory generation CAS: post-COMMIT remains manual-only

`tests/test_memory_generation_postcommit_manual_run538.py` (three authored variants at `c4e35f83d11c25168b790a3ca569fff6eaa1edd1`) simulates a callback after the inner `sqlite3.Connection` transaction has committed but before an opt-in CAS call returns. A reflected change to source content, metadata, or expiry must raise and **must not** be treated as evidence that SQLite rolled back. Reopening the same local DB demonstrates exactly one persisted update event and the prior generation token cannot replay. Read-only `review_memory_generation_cas_outcome` can report one matching update without attributing it to the caller or granting a retry.

This package adds tests, not a replacement for Memory v1 write APIs, a distributed exactly-once guarantee, authenticated SQLite provenance, trusted clock, or consent.

## Verification and blockers

The ordinary CI matrix is six Linux/Windows Python 3.11/3.12/3.13 jobs. GitHub Actions results belong to **exact commit HEADs**, not a prior successful commit or this technical note by implication. Earlier PR #8 CI failed while an unused `frame_width` alias remained; source fix `24c282ee48af6763e3667371703dd30b5812273d` removes that line without weakening checks. Independently check the latest CI before claiming GREEN. Tests above are **authored parameter-expanded cases, not a local pytest execution count**. Local `git ls-remote` was unavailable due GitHub DNS failure in the container.

No real microphone, scheduled action, external API/GPU, Candidate generation, paid service, destructive data operation, protected V2 final evaluation, or main merge was invoked. PR #8 stays Draft and unmerged. Additional integration requires verified immutable registry identity, PermissionGate authority, trusted clock, durable cross-store receipts, and human review where specified.

## Next technical priorities

1. Exact-head CI, and semantics-preserving minimal corrections for any genuine failures.
2. Memory CAS post-COMMIT ambiguous state, durable event-row witness, and consent/retention policy independent from caller clock.
3. Planner FAILED/BLOCKED archive+READ journal coherent recovery, with UNKNOWN WRITE manually quarantined.
4. Scheduler trusted-clock audit-before-action and restart occurrence fences; privacy-safe Personal Context; explicit fixture-only observation diagnostics.
