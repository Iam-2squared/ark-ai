# ARK AI — Run569 Detached Attention Restart and Observation Integration

**Scope:** three independent, reversible, zero-cost, deny-only source/test work packages on Draft PR #8. This note is documentation of real source changes, not a PASS declaration or authenticated execution proof. All times, surface markers, transcript coverage, retained hashes and policy decisions are *synthetic caller fixtures*.

## Package A — retained proactive attention prefix

- Added `src/ark/attention_retained_prefix_review.py`: read-only prior-vs-current bounded attention history reconciliation, exact append-only prefix check and retained history SHA-256 agreement, caller time monotonicity, import-pinned upstream/output denial properties, reentrant input/result carrier integrity, and versioned evidence digest. Requires the previous digest to be independently retained to be useful. Identical copied marker values are acceptable, but missing/reordered/rewritten prefix markers are rejected.
- Added `tests/test_attention_retained_prefix_run569.py`: **25 authored parameter-expanded cases**, including same/append, removal/reordering, SHA forgery, clock types/regression, duplicated/future occurrence, equal-value marker copy, forged False authority, replaced dependency, and hash-callback drift.
- Classification is **`UNCHANGED`** or **`APPEND_ONLY`**. Neither classification permits a new notification, replay or append. This does **not** prove actual historical custody, independent identity or actual clock trust. In particular, a caller could manufacture a new consistent prior+current pair.

## Package B — detached transcript coverage → attention

- Added `src/ark/offline_coverage_attention_join.py`: composes caller-provided local transcript-frame coverage accounting with a *recomputed* detached attention budget. Checks exact types, bounded frame counts and gap identity, floor-divided ppm accuracy, retained coverage SHA equality, original deny-only properties and reentrant receipt integrity. A configurable `required_coverage_ppm` can turn otherwise `REVIEW_ONLY` into **`INSUFFICIENT_COVERAGE_HOLD`**. Duplicate, cooldown and budget holds are never upgraded. Binds source and attention receipt SHA into a separate versioned output digest.
- Added `tests/test_coverage_attention_join_run569.py`: **29 authored parameter-expanded cases**, including threshold boundaries, duplicate/cooldown precedence, forged frame accounting, invalid types, retained-SHA mismatch, False-only authority spoofing and in-flight mutation.
- This is a **synthetic metadata gate, NOT camera/microphone processing, ASR quality validation, consent, a verified sensor identity, notification scheduling or ToolBackend dispatch**. Since the upstream coverage instance is caller-provided and is not reconstructed from independently preserved raw fixtures at this join, its claimed SHA is not evidence of an authenticated measurement.

## Package C — bounded text chunks → offline lexical search

- Added `src/ark/offline_chunk_index_bridge.py` and `tests/test_offline_chunk_index_bridge_run569.py` (**27 authored parameter-expanded cases**). This connects the existing local UTF-8 chunk bundle verifier with the detached lexical index, deriving deterministic `doc_[0-9a-f]{16}` identifiers per complete chunk and returning only chunk positions, scores and digests — **no text, snippet, actual Memory read, file write or model call**. It explicitly rejects more than 32 chunks instead of silently truncating a source, and uses exact per-call owner/scope and full expected membership.
- Requires caller-retained bundle SHA agreement, reconstructs and verifies every chunk, pins the original verifier/index and deny-only result types, validates normalized UTF-8 query byte budgets and exact query SHA before search, rechecks source and nested result-hit epochs after callbacks and binds all returned identifiers into a versioned local evidence digest.
- These hashes are deterministic consistency evidence only, not authenticated ownership, revocation or consent. It cannot promote an offline lexical hit to tool permission, disclose private text, or infer new model capability. The join is reversible, independent of scheduler or training, and remains explicitly disconnected.

## Validation and restrictions

- Run568's exact checkpoint HEAD `9b2eeed4da98621e531aabf30509579118f86d11` has [CI #41556589374](https://github.com/Iam-2squared/ark-ai/actions/runs/41556589374) **SUCCESS 6/6**.
- All writes in this run use the normal GitHub Contents API. The first new coverage-join source CI [#41561767379](https://github.com/Iam-2squared/ark-ai/actions/runs/41561767379) found Ruff E501 on one 101-character assignment; the assignment has been wrapped in a normal source fix. A separately reviewed unit helper confused omitted/explicit `None` retained digests, and an invalid-clock fixture accidentally reached the helper before the target; both have been corrected in ordinary test updates. New tests are **authored** and the final combined **exact-HEAD six-job GREEN is not yet claimed** in this note.
- Frozen `src/ark/memory/contracts.py`, `src/ark/agency/contracts.py`, and PR #5 `docs/v3/CONTRACT.md` were read separately and remain at the recorded blob SHAs `b6e93821ecd69270a7634aceb20775dc36e9953c`, `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`, `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`. No V2 protected final gate, Candidate, GPU, real backend, external expense, privacy disclosure, irreversible action, promotion or main merge.
- Draft PR #5 and PR #8 remain isolated; **ARK/JARVIS/V3 NOT_PASSED**. More meaningful integration requires independently pinned source provenance, live revocation/freshness, a trusted clock, durable append/occurrence leases, and audit-before-any-action authorization. All such capabilities remain out of scope for these components.

## Next

Verify the exact latest source+test and checkpoint CIs across Ubuntu/Windows Python 3.11–3.13; fix failures from logs using normal writes. Continue restart-safe Planner and READ recovery, Memory CAS/expiry/manual unknown-COMMIT reconciliation, trusted-clock occurrence integrity, consent revocation and privacy-safe observation fixtures without live hardware or paid services.
