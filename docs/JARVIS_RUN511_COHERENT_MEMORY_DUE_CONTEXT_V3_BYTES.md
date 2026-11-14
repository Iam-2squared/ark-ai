# ARK AI — Run511: coherent Memory, retained offline histories and V3 byte custody

**Prepared at:** 2026-11-01T04:57:04.173+09:00 Asia/Tokyo/JST (ordinary wall clock; not trusted-clock attestation).  
**Overall:** ARK/JARVIS/V3 `NOT_PASSED`. **No real execution / GPU / training / Candidate / protected final evaluation / paid service / main merge.**

## Exact work basis and independently gated workstreams

- Initial PR #8 work-basis HEAD: `a4c82d3248a9afa4fb013ac1c349887ebef9a3da`; [PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) remains Draft/unmerged. Source/test corrective HEAD at evidence preparation: `de4e7d26d747bd3231a6aed03a3994b66281d099`.
- Initial PR #5 work-basis HEAD: `013697f18831e2625f0121d42c0c521520a39b43`; [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) remains Draft/unmerged. Final V3 source/test HEAD `20781a6c752a00a406b2543d621fe29062d1a982`.
- `main` HEAD `7a843f17eb96ed13d66f23b58b06406b3002e405`, untouched.
- Frozen Memory contract blob `b6e93821ecd69270a7634aceb20775dc36e9953c`; Agency contract blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`; V3 `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`. No edits, no frozen V2 evaluation opening.

## NEW source/test packages — 62 authored pytest parameter expansions

### 1. Memory: retained historical prefix + current row/event coherent transaction — 23 tests

- `src/ark/memory/sqlite_retained_coherent_review.py` blob `c1015d19efcd19e4a6ad10d43eaea541a6411907`.
- `tests/test_memory_retained_coherent_review_run511.py` blob `04e8c4b5a4b5d413f358fa57fc97a9f4012b05a1`.
- A **single bounded read-only SQLite transaction** checks the full current row set using the established row decoder, checks CREATE/UPDATE/DELETE/EXPIRE causality, recomputes the *old* event-prefix SHA-256 even after newer appends and compares the retained row/event alignment if no new event exists. It independently hashes current row/event state without plaintext in the result and always refuses disclosure / action / consent / writer authentication authority.
- A current append is `ADVANCED_PREFIX_UNAUTHENTICATED`; it cannot reconstruct older row bytes because frozen V1 events lack those bytes. Caller-held prefix and alignment witnesses are not independently authenticated, and an adversary who changes both witnesses and database can forge both.
- WAL-insertion race, empty genesis, multi-scope history, old-prefix rewrite, changed metadata/expiry, missing events, row corruption, exact type, no-write and reentrant source/witness drift fixtures included.
- Intermediate CI exposed a Ruff `I001` import order failure; fixed on the normal Contents API. A later CI exposed **two test diagnostic regex assertions**, not permission bypass: invalid retained event-count witness correctly refused as `invalid retained witness`, and retargeted source was already refused but its more precise message was obscured by a broad exception catch. Fixed source exception preservation and test regex without changing fail-closed semantics.

### 2. Disconnected scheduler: durable due-slot retained-prefix audit — 17 tests

- `src/ark/agency/disconnected_due_prefix_review.py` blob `8a7ce4281cd495579f29a4cb3c19ac3a94a2d6bb`.
- `tests/test_disconnected_due_retained_prefix_run511.py` blob `1935fc5ec26c248fb6dc6999e47a965dd5d8891b`.
- Validate existing synthetic due-reservation lifecycle and recompute the **first N complete original rows** inside the same SQLite read transaction, rather than treating a higher count and new local SHA as proof of an intact prefix. Detect earlier timestamp rewrite followed by legitimate append, count rollback, malformed rows, source/witness drift, result authority spoofing. No actual scheduling, reminders, trusted time, notification, replay, or OS action.
- Earlier scheduler CI was blocked by the independent Memory import error, **not** evidence of a scheduler-specific failing assertion. Later corrected PR #8 CI is the relevant validation.

### 3. Privacy-safe Personal Context: retained replay prefix — 15 tests

- `src/ark/personal_context_replay_prefix_review.py` blob `a63572c9592827caee8966737dabf851def9fda0`.
- `tests/test_personal_context_retained_replay_prefix_run511.py` blob `dd4cf7356e9a7f16905ede6f18bab4a184b76527`.
- Recheck the full local stored request hash chain, then compare the previously retained **sequence-N hash link in one read-only transaction**. Even if an attacker recalculates a locally consistent whole chain after changing an earlier owner digest, a separately retained old tip exposes the rewrite. No payload text, consent, disclosure, replay, erasure guarantee, or independently authenticated writer.
- Includes genesis, appends, re-open, forged full chain, rollback, tampered retained witness, mutation during scan and result authority denial fixtures.

### 4. V3: second independent byte pass after local identity artifact witness construction — 7 tests

- `src/ark/learning/identity_artifact_verify.py` blob `9f1169d1704d5aae8c28fdc902ab6022d29324a3`.
- `tests/v3/test_identity_artifact_second_byte_epoch_run511.py` blob `3dbef6322b30e3aa188eec419f7b3775a31fc4ef`.
- After the original bounded/read-only JSON verify and inert witness-constructor callbacks, re-open and SHA-256 the entire local bytes once more; check same-inode and full byte count. This can detect same-size content rewrites with restored mtime during a report callback. It **cannot** offer an atomic filesystem snapshot, upstream model provenance, source authenticity, protected evaluation access, GPU authorization or Candidate generation.
- Normal GitHub Actions [V3 exact source/test CI 41236023580](https://github.com/Iam-2squared/ark-ai/actions/runs/41236023580): **6/6 GREEN, workflow SUCCESS** on Ubuntu/Windows Python 3.11–3.13; earlier source-only [41235992393](https://github.com/Iam-2squared/ark-ai/actions/runs/41235992393) also SUCCESS.

## CI evidence (exact commit boundaries)

- Previous Run510 [PR #8 checkpoint CI 41231699077](https://github.com/Iam-2squared/ark-ai/actions/runs/41231699077), `a4c82d3248a9afa4fb013ac1c349887ebef9a3da`: SUCCESS, **predecessor only**, not evidence of Run511 source.
- First Memory CI [41235862616](https://github.com/Iam-2squared/ark-ai/actions/runs/41235862616) and following source/test CI [41235922350](https://github.com/Iam-2squared/ark-ai/actions/runs/41235922350): FAIL, Ruff `I001` import grouping; corrected without weakening data validation.
- Later Memory-corrected CI [41236184640](https://github.com/Iam-2squared/ark-ai/actions/runs/41236184640), HEAD `7495ccc58cf41d09477026959ec2300fc7e548f6`: Ubuntu 3.12 reported two diagnostic assertion mismatches, not an action authorization failure; corrected afterward at HEAD `de4e7d26d747bd3231a6aed03a3994b66281d099`.
- PR #8 latest corrected source/test [41236481926](https://github.com/Iam-2squared/ark-ai/actions/runs/41236481926) at `de4e7d26d747bd3231a6aed03a3994b66281d099`: **QUEUED/IN PROGRESS at evidence preparation; no claim of full six-job GREEN**. Recheck the exact run before changing status; subsequent docs/checkpoint commits produce separate CI SHA.
- Independent local pytest/Ruff: **NOT VERIFIED** due local checkout inability to resolve GitHub DNS. 62 = **authored test cases**, including decorator parameter expansion, not a claim of local test passes. All writes via the standard GitHub Contents API; no raw Git ref/object safety bypass.

## Explicit remaining boundaries

- Both PR #5 and #8 stay Draft and unmerged. Frozen V1/V2/Local UI/Launcher evidence and V2 evaluation gates untouched.
- No billable compute/API/GPU, no actual model weights/adapter training or Candidate generation, no new credentials/accounts, no physical-PC action, no destructive/irreversible action, no actual human approval/consent, no real ToolBackend, automatic UNKNOWN WRITE replay, real scheduler notification or main merge.
- Local hash witnesses are only as trustworthy as independently maintained custody. SQLite and inode rechecks cannot authenticate upstream binaries, external action truth, user consent or immutable snapshots. Separate local databases do not share one transaction.
- V3 remains blocked on verified model/tokenizer upstream + local byte provenance, actual reviewed datasets and contamination clearance, runtime/toolchain/device identities, and explicit authorization/budget. **Do not infer successful training or a V3 PASS from the free guard CI.**

## Next plan / 今後の方針

1. Confirm exact corrected PR #8 CI at `de4e7d26` in Windows/Ubuntu, Python 3.11–3.13. Fix genuine failures by the normal source/test path and preserve safety. Confirm PR #5 `20781a6c` remains 6/6 GREEN.
2. Extend Memory independent retained witness custody and coherent SQLite row/event snapshots, with verified regression fixtures for interleaved WAL writes. Treat unproven historical row content and cross-store linkage as blockers, not PASS.
3. Improve Planner persisted UNKNOWN WRITE manual-only incident review and registry-bound exact-type permission gate, trusted-clock pre-action audit, occurrence fencing, without real effect dispatch.
4. Continue scheduler restart/duplication fencing, Context revocation/privacy erasure evidence, Observation fixtures and free-only V3 reproducibility/path-identity safeguards. Preserve Draft PRs and paid/hardware/protected/merge gates.
