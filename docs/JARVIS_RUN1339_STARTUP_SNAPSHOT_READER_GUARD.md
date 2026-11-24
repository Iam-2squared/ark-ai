# ARK Run1339 — Public startup snapshot reader guard

## Exact basis

- Parent package: Draft PR #518, branch `research/run1338-startup-snapshot-method-custody-20261125`.
- Exact parent HEAD: `9d531b38f9e943401956c27e60379b40dbdec58e`.
- This child adds the direct-reader enforcement missing from the parent package.
- New branch: `research/run1339-startup-reader-integrity-guard-20261125`.

## Finding and correction

Run1338 pins the import-original `StartupSnapshot._assert_integrity`, `state`, and `root_blockers` methods in the central guard. A direct call to the original `state()` or `root_blockers()` method still reached `self._assert_integrity()` before invoking that guard. If the integrity method had been replaced, the public reader could dispatch through the replacement without first checking the pinned identity.

Both public readers now call `_assert_original_startup_constructors()` before dispatching through `_assert_integrity()`. Regression tests replace the integrity method and verify that neither reader invokes the substituted callback.

## Evidence boundary

Synthetic readiness graph only. No live startup, dispatch, notification, hardware, credentials, external service, paid compute, Candidate, protected V2 evaluation, frozen-contract change, destructive action, UI work or main merge. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.
