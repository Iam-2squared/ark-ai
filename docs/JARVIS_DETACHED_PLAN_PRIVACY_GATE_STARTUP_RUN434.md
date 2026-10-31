# Run434 — Offline Plan-Wide Recovery Bundle, Cross-Process Privacy, Permission Race, Startup Epoch

**Classification:** isolated/reversible, disconnected synthetic engineering evidence; no frozen-contract or activation change.
**Work-basis:** PR #8 Draft at `ece577347637149b948f07b0f377a2d7313a24df`.
**Final executable/test work HEAD:** `698eab6942c4e7f35c47c2abec7e9985d0669c54`.
**Confidence:** source/test files saved; **latest exact-head CI has not completed**. No GREEN claim for Run434.

## 1. Multi-WRITE detached restart evidence — new module (+12 expanded tests)

`src/ark/agency/synthetic_plan_recovery_bundle_review.py` and `tests/test_synthetic_plan_bundle_cross_process_run434.py` introduce a bounded canonical JSON envelope for an already diagnosed `SyntheticWritePlanReview`. Each WRITE is detached through the existing per-step `archive_synthetic_recovery` local witness contract. The 4 MiB total bound, maximum 128 steps, canonical base64, exact archive digest validation, sorted unique step IDs, equal cross-step source witnesses, topology equality, and locally derived uncertain steps are checked on restore. Caller must independently retain the bundle bytes/digest. Neither SHA-256 nor the bundled SQLite histories authenticate consent or side effects.

Tests cover unchanged PENDING and RUNNING+reserved PENDING through a READ bridge, detached decoding from a separate Python interpreter without database access, six recomputed-digest malformed-bundle variants, noncanonical/oversized input and reflective bytes/digest substitutions during validation. **The new API only detaches/reopens evidence: it does not itself authorize or perform a cross-store restart, establish atomicity, or replay an action.** A future exact-head GREEN integration can connect separately reviewed store rechecks; doing so before validating this foundational bundle would be premature.

Source commit `dd9107cdab5f9e878fbd8ee11de450c4b2b1e67e`; tests `3e5e30f921fcd6ae2326fe59f1185919775228a0`.

## 2. Personal Context revocation race — independent child processes (+5)

`tests/test_privacy_cross_process_veto_projection_run434.py` commits only fixture tests to an existing API. Another Python process commits a local revocation of either of two owner-scoped namespaces (a) after a coherent Memory snapshot is prepared or (b) after the first veto check. The enclosing `review_fresh_nonrevoked_context` must reject rather than release a private context projection. An independently retained revocation prefix must recognize the appended veto after restart. No actual personal data, deletion, notification, model ingestion or consent clearance. **The acknowledged post-last-check race remains unresolved; a result never licenses live disclosure.**

Test commit `00f629580d8c1496836d291bd1d1896aafd116f5`.

## 3. PermissionGate admission race & limitation (+6)

`tests/test_permission_thread_local_boundaries_run434.py` explicitly races two threads through direct and registry-bound WRITE policy paths using a single process-local `PermissionGate` token; exactly one admission is expected, with no executor calls. A second diagnostic proves two distinct in-memory gates can independently accept the same synthetic token. **This is expected and documents why durable SQLite occurrence fencing and authenticated issuer verification are prerequisites for any external action.** No permission contract modified.

Test commit `11a3afddd0040d877a3bce254c3bb35108746183`.

## 4. Startup component original-carrier epoch (+7)

In `src/ark/startup_readiness_review.py`, the source generator and cached integrity review now check exact original `component_id`, `failure_code` and `schema_revision` carriers, not only equal string values. Tests inject equal-value but distinct string objects between generator yields and during retained snapshot identifier validation. A stable BLOCKED root still yields a DEPENDENCY_BLOCKED downstream component; the synthetic READY/BLOCKED value remains a caller claim, not actual readiness attestation.

Source `30c0a3fc3d838ca05e573c0b551ed7377ffbac2c`; tests `698eab6942c4e7f35c47c2abec7e9985d0669c54`.

## Validation and unresolved evidence

The 30 parameter-expanded tests above are **new test cases**, not 30 claimed PASSes. CI runs `#1233 / 40232620906` (bundle tests), `#1234 / 40232710447` (privacy), `#1235 / 40232827498` (permission), `#1236 / 40233167149` (startup source), and `#1237 / 40233213149` (startup tests) were **QUEUED** when inspected; none attests final HEAD GREEN. Existing Run433 source `#1229 / 40227718289`, doc `#1230 / 40227965932`, and checkpoint `#1231 / 40228196762` also remained QUEUED. Prior Run433 Observation `#1225 / 40227325547` showed only 2/6 SUCCESS, other jobs unfinished; Memory `#1227 / 40227494157` all six queued.

No local full-repository Python environment was available: the working container has no network resolution to fetch the repository, and no claim of local pytest/Ruff execution is made. Test source formatting was checked for lines above 88 characters, but that is not a Ruff result. **If CI fails, inspect actual job logs, make only semantics-preserving normal GitHub Contents edits and retain historical FAIL results; while jobs run, use independent lanes.**

Read-only nontruncated Git Tree comparison at final source/test HEAD: main `7a843f17eb96ed13d66f23b58b06406b3002e405` has 94 blobs; PR #8 has 576 blobs, **482 added, zero existing main blobs modified or deleted**. New implementation resides only in PR #8, Draft/unmerged. PR #5 remains Draft/unmerged/NOT_PASSED. Frozen V1/V2/Local UI/Launcher, Memory v1 and ActionAudit v1 DDL, and V3 Contract 1 have not been changed.

## Next isolated dependencies

1. Exact-head CI #1237 and eventual technical-document/checkpoint CI before any PASS assertion; troubleshoot failed tests using normal Contents only.
2. After bundle exact-head GREEN, integrate its detached per-step retained prefixes into a **separate** plan-wide reopened-store recheck; never infer external success from a local journal, or cross-file atomicity from four SQLite files.
3. Continue Memory cross-process CAS/expiry and privacy-revocation freshness with independent retained witnesses; preserve COMMIT outcome semantics.
4. Develop read-only issuer/clock and Observation/Scheduler interfaces only behind synthetic deny-only gates; do not activate sensors, notifications or Tool dispatch.
5. V3 PR #5 approval, exact immutable model/dataset/hardware identities, protected V2 final-evaluation opening, Candidate promotion, spending and main merges remain human-gated hard stops.

**No paid/external compute, paid API, credential, real Candidate training/weights, destructive action, device access, notifications, external ToolBackend execution, frozen contract modification, protected evaluation, or main merge was attempted.**
