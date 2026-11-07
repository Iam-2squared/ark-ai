# ARK AI — Run693: preaccess Memory identity, synthetic occurrence count and privacy-veto digest

**Scope:** FREE-ONLY, non-UI, opt-in/disconnected safety foundations. Work basis: Run692 checkpoint HEAD `2d844a69d10fdeb1f2da88509ed8488fbddc207c`. Target: Draft PR #8 / `research/jarvis-foundations`, never main, PR #5 or paused UI PR #9.

## Package A — Memory generation observation first-hash epoch

`observe_memory_generation_for_cas()` pinned the scope owner, namespace and SQLite path only **after** its first deterministic identity hash. A reentrant hash callback could replace these caller-owned references, even with equal-valued new objects, and have the replacement treated as the observation's starting epoch. This is unsafe custody of a potentially private read, not an authenticated-hash attack.

The opt-in observation now captures original scope/path references, constructs its `stable()` check, and checks that original epoch **both before and after** `deterministic_memory_id()`, before opening SQLite. The frozen Memory v1 put/delete API, schema and CAS persistence semantics are unchanged.

- Source commit: `b0285beb5cac3d176502554a082f1858e9ab9c3e` (`src/ark/memory/generation_fenced_cas.py`).
- Tests: `1853a751f81386705b454bff3bb1f947eeebd6e2` (`tests/test_memory_generation_initial_hash_epoch_run693.py`), **7** parametrized cases: owner/namespace/path × value-equal vs changed replacement, and unchanged valid read-only token. Private connection callbacks must not run on a rejected identity. No real Memory contents are used.
- Limits: local identity-hash callbacks are not independently authenticated provenance or consent. An unchanged digest does not authorize an external action.

## Package B — synthetic occurrence count source/read custody

`SyntheticOccurrenceStore.count_synthetic()` originally checked source identity only after completing its SQLite count query. A reentrant `Path.resolve()` or `sqlite3.connect()` callback could silently replace the synthetic ledger's source prior to a private schema read. The reader now fences its original Path object before/after resolution, URI construction, handle creation, BEGIN, validation, SELECT and commit.

- Source commit: `20aac1e49e1d9881f8a6fee5674fe76a46567f6b` (`src/ark/agency/durable_occurrence_review.py`).
- Tests: `3f9ff483c3b6d88838ff153aee760e7d2be178a1` (`tests/test_synthetic_occurrence_count_source_epoch_run693.py`), **5** cases: path resolve equal/different retarget must not open SQLite; connection callback equal/different retarget must not validate private rows; valid fresh/reopened ledger count remains zero.
- Limits: this read-only count is not a trusted clock, durable approval, actual tool execution, or cross-store atomicity proof. SQLite handle identity and filesystem owner are not globally authenticated.

## Package C — privacy-veto continuity hash implementation custody

`review_revocation_continuity()` previously trusted a dynamically replaceable local `_hash`, `hashlib.sha256` or `json.dumps`. A forged hash function could make false witness-prefix equality look locally coherent. The read-only checker now pins the import-time implementations and rejects substitution **before reading retained witness fields or revocation SQLite**.

- Source commit: `826edc2cc96b9d9ea6b2f7f03633b00a53f3759c` (`src/ark/personal_context_revocation_continuity_review.py`).
- Tests: `17e9718a077c16c7e8ff05f23d70a2629b69ad3e`; import order correction `4636b117c1808117e46b24b63fc0015ecfe64015` (`tests/test_personal_context_revocation_digest_identity_run693.py`), **5** cases: replaced local hash, SHA-256, JSON serializer, JSON module all deny before private reads, plus valid restart-safe retained-prefix review.
- Limits: revocation history digests are **local, untrusted** evidence. They do not prove comprehensive deletion, external consent or a tamper-resistant source. Two separate SQLite stores cannot supply an atomic global privacy snapshot.

## Test / CI provenance and independent boundaries

**17 new case instances** across three new test modules; **three production modules** hardened. Read-only baseline verified: Run692 exact checkpoint HEAD [CI #42403850627](https://github.com/Iam-2squared/ark-ai/actions/runs/42403850627) **6/6 GREEN** (Ubuntu/Windows × Python 3.11–3.13). Run693 source/test ancestor evidence must be inspected per exact HEAD; an in-progress or older green result is **not** evidence that this final report or checkpoint HEAD passed.

No network/backend execution, paid compute, Candidate generation/training, protected V2 evaluation, UI/frontend modification, credentials, physical-PC action, promotion, destructive operation, frozen contract change or main merge. PR #5/#8/#9 remain Draft/unmerged at work start, with explicit user gates preserved. ARK/JARVIS/V3 **NOT_PASSED**.

## Next plan / 今後の方針

1. Verify exact Run693 HEAD CI, inspect actual failure logs if any, and fix only the minimal test/source contract mismatch by ordinary GitHub Contents updates.
2. Strengthen independent durable custody for Planner step-level READ receipts and UNKNOWN WRITE restart quarantine. A local digest is not external execution evidence.
3. Continue Memory COMMIT-UNKNOWN manual-only review, CAS/ABA/WAL/expiry coherence and Personal Context revocation read-before-disclosure checks.
4. Extend disconnected ToolRegistry/PermissionGate and audit-before-action recovery, Observation/proactive backend fixtures, and free V3 path/approval/identity guards. Maintain no-new-UI and no-paid-compute boundaries.
