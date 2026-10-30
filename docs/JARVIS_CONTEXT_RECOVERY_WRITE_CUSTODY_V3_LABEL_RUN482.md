# ARK AI Run482 — Context restart recovery / WRITE receipt custody / V3 label identity

**Scope:** isolated, reversible and free-only. No live Tool dispatch, private content disclosure, paid GPU/API, model training, Candidate, protected final evaluation, or main merge.

## Exact work basis

- Initial PR #8 HEAD: 13733061a2bb61a1d5a60b91582763be921a13b1.
- Final PR #8 source/test HEAD: 2100b45c2d4dea6bcb205ab6abc46ba4924933ef.
- Initial PR #5 HEAD: 21de6635404b9e277c363a5b795ca52006bcbe62.
- Final PR #5 source/test HEAD: b22f7fac3f8a6fe1d9fbcd054ceb8d8d1f14a15b.
- All source/test writes through normal GitHub Contents API; current PR HEAD reread immediately before every write. No raw Git objects, force-push or merge.

## A. Read-only Personal Context replay restart triage — 19 new authored pytest cases

New source: src/ark/personal_context_replay_recovery.py (blob 4711d9d5119eaf44499b14640985a41ee4515b70).
New tests: tests/test_personal_context_replay_recovery_run482.py (blob 94f89a271b61d6ef0c28c6e6dca5c286f3f0605f).

Compare one caller-retained history witness with a fresh local SQLite witness. Reject count rollback, same-count digest rewrite, non-exact carriers, source path/retained/observed/result mutation or forged authority. Advancing history is ADVANCED_HISTORY_UNVERIFIED, **not** proven historical prefix, independent custody, fresh consent/revocation, disclosure authorization, Tool permission, or automatic replay. No raw context content read or retained by the reviewer.

## B. Planner synthetic WRITE quarantine finding custody — 10 new authored pytest cases

Updated source: src/ark/agency/synthetic_write_quarantine_matrix_review.py (blob c0f8778333924ada05fe13358abfeddd6de410c8).
New tests: tests/test_write_quarantine_finding_custody_run482.py (blob 06495583e20bd37ae657a51edf097f4e332eafe3).

Pin exact original type, identity, reason codes and no-replay authority for **every earlier finding** throughout later callbacks. Reject substituted constructors, after-creation reflection edits, reordered result findings, or claimed dispatch/replay/outcome authority. Existing input and reason contracts unchanged. UNKNOWN WRITE remains quarantined, never automatically retried.

## C. V3 local manifest label canonicalization — 24 new authored pytest cases

Updated source on PR #5: src/ark/learning/identity.py (blob add2c7c740a2487fcf377b26d829f418326f4dcc).
New tests: tests/v3/test_identity_label_boundary_run482.py (blob 8dd52adb338b46b5b8de8dc7b35ce8ce026eada1).

Fail closed before hashing when a local file identity label is non-exact, ambiguous, absolute, drive-qualified, traversing, backslash-containing, malformed, control-containing or too long. Valid relative nested POSIX paths are retained. Not a hostile-writer-safe file descriptor snapshot or license/provenance check. No external bytes or model run.

## CI at first review and boundaries

- Prior Run481 checkpoint PR #8 #1636 / run 41078042907 — all six Ubuntu/Windows jobs SUCCESS.
- PR #8 Context latest source/test at 63f23d4e8206e97907ef49aac0a8c5c1fe4195d3: #1638 / 41083685953 IN PROGRESS on first review.
- PR #8 final Run482 source/test at 2100b45c2d4dea6bcb205ab6abc46ba4924933ef: #1642 / 41084068310 IN PROGRESS on first review.
- PR #5 final Run482 source/test at b22f7fac3f8a6fe1d9fbcd054ceb8d8d1f14a15b: #1640 / 41083841017 all six Ubuntu/Windows Python 3.11–3.13 jobs SUCCESS.
- Independent local clone/whole-repository pytest and Ruff NOT VERIFIED because local GitHub DNS is unavailable. Authored test counts are not execution evidence.
- Final CI outcomes and checkpoint-result HEAD must be read independently and recorded in the canonical PROJECT_STATUS.

Both PR #5 and #8 are Draft/unmerged. Frozen V1/V2/Local UI/Launcher, Memory/agency contracts and V3 evaluation/training gates unchanged. No trusted clock, independently authenticated writer or consent, cross-store atomicity or actual external effect verification has been proven. No Candidate/weights, paid external services, irreversible operation or human-reviewed promotion.

## Next plan

1. Verify latest exact-head CI, inspect real failure logs if necessary, and make only semantics-preserving fixes.
2. Continue Memory CAS and independently retained event witnesses; never call hash chains authenticated custody.
3. Advance Planner UNKNOWN WRITE quarantine, independent registry/permission identity, trusted-clock audit-before-action, and scheduler replay prevention in isolated synthetic lanes.
4. Advance Personal Context retention/revocation, privacy-aware startup readiness and disconnected Observation fixtures.
5. Keep V3 free-only model/path/approval/provenance guards separate; protected V2 and paid training paths remain blocked.
