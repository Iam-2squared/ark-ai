# Run879 — Proactive v0 bootstrap regression: six-platform fail-closed repair

## Scope / evidence

- Target: `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8); baseline checkpoint HEAD `a493b60c3c7dc8142cf209f0e4a2c39b6ab17aed`.
- Exact baseline [CI #43629239918](https://github.com/Iam-2squared/ark-ai/actions/runs/43629239918) completed **FAIL 6/6** (Windows/Ubuntu; Python 3.11, 3.12, 3.13). Independently inspected Ubuntu 3.11 and Windows 3.11 job logs: both reported **415 failed**, dominated by normal proactive callers failing at fresh SQLite initialization. This is **not** a latest-head GREEN claim.
- The common trace: `SyntheticProactiveLedger.__init__` → `version == 0` → `_objects(conn)` → `SyntheticTriggerRejected("trigger fixture schema changed")`. No real scheduler, notification, model inference or tool action occurred.
- Pre-Run878 legitimate empty SQLite catalog has **zero** rows. Run878 bounded `_objects` correctly requires **exactly two** schema entries for a *versioned* trigger ledger, but the constructor mistakenly reused that versioned check **before** its first table creation. All fresh stores were therefore rejected. Previously passing proactive tests cascaded into failures in observation/startup consumers. The versioned catalog/quick-check/row validation remained the intended strict gate.
  
## Source fix

Normal GitHub Contents API updated **only** `src/ark/proactive_synthetic_review.py` from baseline file blob `ed7aa31cf7959df78fadf03cac6400d2bcfb9f83` to `f4462dd19787d9b24c65aed525ab5dbbbda10dc5`, commit `ab0b1116d0fe35a7568125fc5465249e021588c5`.

For `PRAGMA user_version == 0` only, the constructor now issues `SELECT 1 FROM sqlite_master LIMIT 1`. It admits **only the empty catalog**, refuses any foreign object with the historic `unversioned trigger fixture is not empty` error, then creates the table and sets version 1. The unchanged `_validate` still demands the exact versioned schema (count 2, DDL-byte budget 4096, exact original DDL, bounded `quick_check` and stored-row checks). Unexpected, malformed, or partially initialized catalogs are not auto-repaired. The SQLite transaction/rollback boundary is unchanged.

This is a targeted lifecycle-ordering fix; it does **not** weaken alias/sidecar rejection or authorize any execution. Previous tests exercise fresh creation and re-open; explicit additional bootstrap-specific tests may follow after the in-flight source CI is resolved, not stacked onto the same validating path.

## Verification and limitations

- Fix commit [CI #43633846086](https://github.com/Iam-2squared/ark-ai/actions/runs/43633846086) was **IN PROGRESS** when first inspected. Do not infer the result from the source review. Recheck exact HEAD and all six individual jobs before claiming GREEN.
- Connected GitHub plugin was used via normal per-path contents update with current blob SHA and a re-read of PR HEAD. No force push, raw Git objects, merge or workflow rerun.
- No local checkout/pytest/Ruff: container could not resolve github.com. No physical PC/GGUF/GPU checks.
- Historical intermittent Privacy Revocation competing-process loser and Windows WAL/SHM last-close `link_count=0` remain **root-cause UNKNOWN**; this bootstrap fix is not a race repair and must not become justification for relaxing fail-closed path checks.
- Frozen V1/V2/Local UI/Launcher contracts, protected V2 evaluation and Draft PR #5 remain untouched; Draft PR #9/UI remain paused and untouched. All work stays offline, reversible and zero-new-cost.

## Follow-up

1. Check CI #43633846086 on exact source commit and any subsequent doc/checkpoint HEAD; minimally repair any real failure without weakening admission.
2. Add dedicated first-bootstrap positive/foreign-catalog/restart regressions only after that path's CI result is established; preserve strict older tests.
3. In an independent lane, characterize WAL last-close and Privacy Revocation rejection categories without relaxing identity, replay or COMMIT-UNKNOWN fences.
4. Continue durable Planner/Memory recovery and registry-bound permission-to-mock integration only on exact-head validated foundations.
