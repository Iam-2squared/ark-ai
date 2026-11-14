# ARK AI Run857 — private revocation preflight, encoded SQLite paths and offline observation identity

**Work basis:** `research/jarvis-foundations` at `4a55338955c515f407e17d2581821b54ed4a3ef7` (Draft PR #8). **Overall ARK/JARVIS:** NOT_PASSED. This is isolated, offline, synthetic non-UI groundwork. No paid compute, training, Candidate, real tool call, protected evaluation, or main merge.

## Package 1 — SQL-first privacy-veto row/schema admission

- [Source `71b78ceb`](https://github.com/Iam-2squared/ark-ai/commit/71b78ceb63e01e660a213dc2b0121fe1dd51e57c) updates `src/ark/personal_context_revocation_review.py` without changing the existing revocation schema or grant semantics.
- For the exact two-object SQLite schema, the validator first checks SQL-side object count and aggregate DDL-byte budget (4096), *before* fetching `sqlite_master.sql` into Python. Full exact-DDL equivalence and `PRAGMA quick_check` remain required.
- Within the caller's existing writer/read transaction, SQL next checks row count (maximum 10,000), digest storage class `TEXT` and exact 64-byte width, timestamp storage class `INTEGER` and nonnegative SQLite range, *before* fetching scope digests into Python. Full lowercase SHA regex and integer checks remain required afterwards. The validator may still reject valid-looking but untrusted or rolled-back data.
- [Seven-case fixture suite `a93695ff`](https://github.com/Iam-2squared/ark-ai/commit/a93695ff16e798a5196a99a13306295c4a3b1f5a) uses disposable SQLite files, rejecting malformed text/BLOB digests, BLOB/negative timestamps, 10,001 rows, and an additional SQL view. Special `sqlite3.Connection` subclasses make any row/DDL hydration before preflight fail; a valid veto remains denial-only.

## Package 2 — POSIX filesystem-encoded lexical admission

- [Source `35818a54`](https://github.com/Iam-2squared/ark-ai/commit/35818a546a51c0e268970488d2777562fd906833) measures `os.fsencode(path)` bytes, including the longest `-journal` suffix, instead of only Python Unicode code points; `os.fsencode` identity is pinned before invoking it on the path.
- [Three-case fixture suite `1264a5e7`](https://github.com/Iam-2squared/ark-ai/commit/1264a5e72cd48573f77c36233e5be58a610dd85f) checks oversized multibyte leaf/ancestor paths are rejected before descriptor inventory and that a normal exact Path remains accepted.
- This is lexical admission, not open-to-use source custody, proof of WAL transaction coherence or replay authorization. A pathname check is still subject to outside filesystem changes.

## Package 3 — observation digest ingestion

- [Source `391c5202`](https://github.com/Iam-2squared/ark-ai/commit/391c52021e02664f0d12c7c7a3a60b8e597f0937) enforces exact 64-character digest shape before regular-expression matching, and rejects a replaced regex module/function before invoking a callback with a caller's observation digest.
- [Six-case fixture suite `b0173fa2`](https://github.com/Iam-2squared/ark-ai/commit/b0173fa2c2df65c650932f473401dafcca915f11) covers oversized, wrong-type and replaced matcher ingress, plus a valid deterministic synthetic observation ID.
- No microphone/camera, ASR, source attestation, consent, disclosure permission, streaming, or physical machine activity is enabled.

## Package 4 — bounded Planner crash-replay schema admission

- [Source `ff805358`](https://github.com/Iam-2squared/ark-ai/commit/ff805358cbe8d83cbaf8275dbe79e3e68e720e4d) adds SQL-side schema object count (exactly two) and DDL-byte budget (4096) inside the existing replay/append transaction, before Python `sqlite_master` hydration. Exact DDL comparison and `quick_check` remain mandatory.
- [Three-case fixture suite `b2709e01`](https://github.com/Iam-2squared/ark-ai/commit/b2709e01e939d1d863564ce3262b50c23202cd1c) checks the unchanged canonical schema plus extra-view and oversized-name rejection before the DDL-hydration callback. No recovered RUNNING/UNKNOWN step acquires replay or dispatch authority.

## In-run CI failure repair (not a new PASS)

- Ubuntu Python 3.12 [run #43521945930](https://github.com/Iam-2squared/ark-ai/actions/runs/43521945930) reported **FAIL** in `tests/test_personal_context_revocation_run373.py::test_valid_shape_but_rewritten_digest_refused`. The newly earlier SQL denial was correct, but its message dropped the established `row integrity` substring expected by a legacy regression.
- [Diagnostic-only fix `713e4808`](https://github.com/Iam-2squared/ark-ai/commit/713e4808a3c171206becd7d7751517740fc5cea1) restores the legacy substring while retaining `revocation row preflight` for the new tests. No predicate, budget, transaction boundary or denial semantics was weakened. Later exact-HEAD CI is **not yet confirmed GREEN**.

## Verification and limits

- **Last prior HEAD with completed exact CI:** `4a55338955c515f407e17d2581821b54ed4a3ef7`, [Actions run #43514612444](https://github.com/Iam-2squared/ark-ai/actions/runs/43514612444): Windows/Ubuntu × Python 3.11–3.13 **GREEN 6/6**. This evidence does *not* apply to the new changes.
- New-source CI [#43521945930](https://github.com/Iam-2squared/ark-ai/actions/runs/43521945930) and sidecar-test CI [#43522101203](https://github.com/Iam-2squared/ark-ai/actions/runs/43522101203) were **IN PROGRESS** at observation. Privacy-tests CI [#43522175028](https://github.com/Iam-2squared/ark-ai/actions/runs/43522175028) and observation-tests CI [#43522367710](https://github.com/Iam-2squared/ark-ai/actions/runs/43522367710) were **QUEUED**, no conclusion. **19 newly authored cases (including Planner), not 19 confirmed PASS.**
- Disposable in-memory `sqlite3` preflight arithmetic was exercised locally for valid text, invalid width, BLOB and negative time. Full repository pytest/Ruff, real-model hardware, authenticated provenance and cross-store atomicity were not measured here. CI on the *final* checkpoint HEAD requires independent confirmation.
- No frozen V1/V2/Local UI/Launcher contracts or evidence, PR #5, PR #9, protected evaluation, real candidate weights or credentials were modified. PRs #5/#8/#9 remain Draft and unmerged as observed at work basis.

## Remaining risks / handoff

Priority: confirm all six CI jobs for the exact newest HEAD and repair concrete failures without relaxing the fail-closed rules; investigate Memory/ActionAudit SQLite WAL/SHM final-close/open-to-use races with disposable stores; preserve COMMIT-UNKNOWN and Planner recovered RUNNING as quarantined UNKNOWN; validate retained privacy-veto continuity and independent provenance; then combine lower-level GREEN-backed ToolRegistry, PermissionGate, occurrence ledger, trusted audit-before-action and disconnected Mock Executor without enabling effects. Restart-safe exactly-once authorization/effects, cross-store coherent snapshots and physical-machine gates remain **NOT_PASSED**.
