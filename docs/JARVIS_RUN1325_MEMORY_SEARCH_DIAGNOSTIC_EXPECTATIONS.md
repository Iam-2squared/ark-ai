# ARK Run1325 — Memory search diagnostic expectation correction

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`, work-basis `77d3b2f50d258bb3694afc0d03830e0d44644961`.
- Source package: Draft PR #499, branch `research/run1319-memory-query-preaccess-20261125`, exact parent child HEAD `caa79962b775b6e1ceca39e38606545e5e0de9f4`.
- Failed exact-head CI: run [45464002019](https://github.com/Iam-2squared/ark-ai/actions/runs/45464002019); observed Ubuntu/Python 3.12 job `138693894588` reported six stale diagnostic-message assertions, with 19,632 tests passed and 1 skipped in that job.

## Finding and correction

Run1319 moved the complete Memory query-epoch check to before SQLite open and consistently renamed its phase diagnostics from “during clock” to “during read”. Existing synthetic reflection tests in Run364 and Run366 still asserted the former wording. The observed failures were assertion-message mismatches; the checks still rejected the retargeted query/scope.

This child branch changes only those two test expectations to the current “during read” diagnostic. It does not change the Memory implementation, query semantics, callback ordering, SQLite behavior, schema, DDL, retention or frozen contracts.

## Evidence boundary

The original Run1319 pre-SQLite rejection behavior remains the subject of fresh exact-head validation. The failed run remains recorded as FAIL; its evidence does not transfer to this correction. No local test run or new PASS is claimed here. Synthetic local tests only; no live data, paid service, Candidate, protected V2 evaluation, credentials, hardware, UI work or main merge.
