# ARK Run464 — detached SQLite sidecar custody and cross-plan WRITE alias rejection

**Status:** isolated, reversible, synthetic/free-only foundation work. Complete JARVIS **NOT_PASSED**.
**Branch:** `research/jarvis-foundations`; Draft PR #8 remains open and unmerged.
**PR #5:** Draft/open/unmerged; V3 training and evaluation gates remain closed.
**Exact work-basis HEAD (entry):** `a689fd0c7d266c392dd7078263ecadf642c6a704`.
**Final source/test HEAD:** `593c95e0d311f42121618a09c6d9eba690a22c20`.
**Observed local inspection:** 2026-10-27 08:53–08:56 JST; ordinary container wall clock, **not** a trusted time or commit attestation.

## Package A — POSIX descriptor-relative SQLite sidecar fixture inventory

- New source: `src/ark/disconnected_sqlite_sidecar_custody.py`, Git Blob `36d2d22ad15272ec97323fe84c0a24d764ef6c66`, source commit `06265726a008e8c5587eca73ea2bf419399f5467`.
- New regression: `tests/test_disconnected_sqlite_sidecar_custody_run464.py`, Git Blob `1cc311cfa01559576860666e365e314bba197de9`, test commit `b567a5c522ad61463270d36d9fe6a03310d4b83d`.
- Uses POSIX dir-fd-relative `O_DIRECTORY` / `O_NOFOLLOW` directory traversal and file opens to inspect the **synthetic** main SQLite file and optional `-wal`, `-shm`, `-journal` sidecars. Keeps parent/file handles during intra-pass name and metadata recheck. Double snapshots must agree. Regular file, one-link, exact path and 64 MiB metadata budget requirements fail closed. Returns only SHA-256 fingerprints and sidecar presence indicators, never row data or bytes.
- Synthetic tests cover absent/present/modified/removed sidecars, unchanged-byte main file substitution, symlinks and hardlinks on main/sidecar/ancestors, directory retargeting, FIFO/directory rejection, byte budget, missing main and unsupported-platform denial. **30 local pytest PASS** on POSIX Python 3.13.5.
- The module is **POSIX-only** and explicitly rejects unsupported OS descriptor APIs; the Windows CI source/test file skips POSIX-only tests, not proof of Windows custody. No Windows reparse/junction safety claim.
- Even retained descriptors and two snapshots do **not** prove SQLite WAL snapshot atomicity, historical rollback, independently controlled witness custody, filesystem or path safety after return, trusted clock, user consent, privacy release or real Tool execution. No live SQLite connection is opened or mutated.

## Package B — fail-closed synthetic cross-plan WRITE reservation overlap

- New source: `src/ark/agency/disconnected_reservation_overlap.py`, Git Blob `301c8fd86006f7ef432f2e8da8751deb7ae6f258`, source commit `1fb74c32101d0289a796dc5aae27d1f36aa8e22a`.
- New regression: `tests/test_disconnected_reservation_overlap_run464.py`, Git Blob `80195332e6d15b58c352e95d0804ea345025e7b2`, test commit `593c95e0d311f42121618a09c6d9eba690a22c20`.
- Reviews up to 16 distinct claimed plans, each with up to 24 synthetic WRITE claims. Rejects repeated reservation IDs **between or within plans**, duplicate plan identities even at changed revision, per-plan duplicate steps, malformed exact-type/revision/enum/identity fields, and carrier mutations during hashing. Hash-bound result counts claimed PENDING/RUNNING/UNKNOWN but exposes no plan/step/slot identifier in default representations. **30 local pytest PASS**.
- Unlike the existing per-plan `disconnected_write_recovery_fence.py`, this fixture review detects collisions in an entire **supplied** multi-plan set. An incomplete, forged or concurrently stale set is not authenticated or independently complete. It does not persist uniqueness, grant write permission, reconcile external effects or replay UNKNOWN outcomes.

## Tests, hashes and queued CI

- Standalone local Python **3.13.5** and pytest **9.0.2**, only the four new files in an isolated test package: **60 PASSED** (30 + 30). Python 3.11 AST grammar parse **PASS**, `compileall` **PASS**, changed source/test lines <=100 chars.
- Additional *uncommitted diagnostic probes*, not extra saved pytest: **1,200** deterministic cross-plan sets (900 distinct accepted; 300 synthetic collision cases rejected) and **150** sidecar creation/change detections rejected.
- GitHub Contents re-reads at exact final source/test HEAD independently matched all four expected Git Blob SHAs. No source/test writes used raw objects, force pushes, hidden protection bypass or merge.
- GitHub Actions natural PR-triggered run #1426 / `40422510551` (first source), #1427 / `40422626606` (first tests), #1428 / `40422714091` (second source), final source/test **#1429 / `40422796206`** (HEAD `593c95e0d311f42121618a09c6d9eba690a22c20`): **QUEUED** at inspection. These are not PASS.
- The older #1251 / `40246006387` has Ubuntu failure and three Windows pytest jobs IN PROGRESS on its **older** code head. Actions sample: **173 QUEUED / 7 IN PROGRESS** before these new source commits. No manual dispatch, retry, cancellation, runner upgrade or billable action. Full-repository pytest/Ruff, Python 3.11/3.12 execution, Windows/Linux six-cell CI on the new HEAD **NOT VERIFIED**. Local git checkout still unavailable because github.com DNS cannot resolve in the container.

## Frozen boundaries and integration blockers

No modifications to frozen V1/V2/Local UI/Launcher evidence, Memory V1 schema, ActionAudit V1, V3 Contract 1, protected V2 final evaluation, contamination/provenance/regression/reproducibility. PR #5 and #8 remain Draft and unmerged. No paid/external GPU compute, subscription/API, credential, new connection, real user data, actual autonomous scheduler, Tool backend, microphone/camera, actual Candidate/weight, promotion, irreversible operation or main merge.

Do **not** integrate these detached checks into production Memory/Planner/SQLite/Tool execution until their dependencies have matching exact-HEAD GREEN and a reviewed design for WAL/sidecar custody, trusted clock, provenance, durable global CAS, audit-before-action and user authorization.

## Next plan / 今後の方針

1. Let existing CI progress naturally. Investigate proven latest-HEAD Linux/Windows failures and the historical Windows pytest bottleneck; do not duplicate workflows or weaken assertion semantics.
2. On the free-only isolated track, test POSIX handle/sidecar changes under interleaving and define Windows handle/reparse-safe alternative; do not claim one path check prevents TOCTOU or proves SQLite transaction integrity.
3. Extend true durable Memory row/event/CAS/expiry snapshot and Planner restart UNKNOWN-WRITE quarantine with exact-head test evidence. Cross-plan review is only a diagnostic; a durable occurrence uniqueness constraint must be transactional and independently attested.
4. Keep registry-bound identity, exact-type PermissionGate, trusted-clock pre-action audit, Personal Context privacy and V3 path/identity guards separate until integration gates are GREEN. All spending/Candidate/protected evaluation/merge gates remain closed.
