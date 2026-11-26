# ARK AI Run966 — non-UI guard-vector custody and persisted atomic type fences

**Scope:** detached/mock-only ARK core work in Draft PR #8, zero new spending. No live tool execution, external GPU/API, model training, Candidate promotion, protected V2 evaluation, new credentials, physical PC or UI changes. Frozen V1/V2/Local UI/Launcher and controlling contracts/evidence remain unchanged.

## Dependency-aware work packages

1. **Memory ambiguous-COMMIT diagnostic** [`acbd2d2b`](https://github.com/Iam-2squared/ark-ai/commit/acbd2d2b8fc1116c37f83dbbf766740ee73fbd68): the independent global high-water check now selects **at most two** `sqlite_sequence` rows. One exact sequence marker is required; zero/duplicate/invalid markers still deny reconciliation. This bounds Python hydration of a potentially forged local SQLite catalog without altering Memory v1 or granting automatic retry.
2. **Planner disconnected READ recovery** [`82897ec9`](https://github.com/Iam-2squared/ark-ai/commit/82897ec99a8997c9b6e177ae1fda7249038ff3da): pin import-time tuples for result hooks, decision/schedule field names, and the three denial-property names. Shrinking or rebinding a guard vector now rejects *before* any caller-owned READ history or output getter is trusted. `READY_MOCK_ONLY` remains non-executable.
3. **V3 detached packet review** [`7c03c401`](https://github.com/Iam-2squared/ark-ai/commit/7c03c401f265334cfd9d5f1e57571c8aab541db7): pin result fields, denial names, and class hooks so a truncated iteration cannot bypass validation of a forged offline V3 report. No Candidate, GPU probing or protected test.
4. **Atomic audit regression matrix** [`3c5f2e52`](https://github.com/Iam-2squared/ark-ai/commit/3c5f2e528ccc9b987664303d5f4ecbd1b2607b27): **18 new parametrized cases** (6 persisted identity/digest columns × BLOB, INTEGER, oversized TEXT) in disposable local SQLite. Expect cold reopen, retained inspection, and next reservation to deny, with the corrupt committed rows unchanged. This is an authored regression suite; no synthetic digest provides independent custody.
5. **Personal Context replay recovery** [`8a26959f`](https://github.com/Iam-2squared/ark-ai/commit/8a26959f70cbbeeca55926a3cf54f6c9651cec43): pin result field/hook/denial vectors and ledger access-hook vector before reading linkable replay metadata. A shorter or substituted tuple cannot suppress fail-closed checks. Does not authorize context disclosure or privacy consent.

## Why the change matters

Earlier code compared descriptor names to their originals using `zip(..., strict=True)`, but the original *vector itself* was not always fixed. A locally rebound, shortened vector could omit protected fields while the remaining comparisons appeared valid. Import-time vector identity preflight closes that bypass in these **opt-in** reviewers. This is process-local defensive programming, **not** isolation from arbitrary untrusted Python code and **not** proof of external authorization.

The Memory `sqlite_sequence` two-row probe is a read amplification bound, not an independent append-only evidence witness. SQLite file edits can still undermine provenance; ambiguous commits stay manual-only.

## Validation and follow-up

- Prior Run965 checkpoint HEAD `74476ecccd989f8e2342f3df607ec56fb88ccaa3`: [CI #44279894502](https://github.com/Iam-2squared/ark-ai/actions/runs/44279894502), **6/6 SUCCESS**.
- Run966 Memory source `acbd2d2b`: [CI #44288708384](https://github.com/Iam-2squared/ark-ai/actions/runs/44288708384), **IN PROGRESS** at initial sample.
- Planner source `82897ec9`: [CI #44288851068](https://github.com/Iam-2squared/ark-ai/actions/runs/44288851068), **IN PROGRESS** at initial sample.
- V3 source `7c03c401`: [CI #44288930807](https://github.com/Iam-2squared/ark-ai/actions/runs/44288930807), **IN PROGRESS** at initial sample.
- Atomic audit tests `3c5f2e52`: [CI #44289056941](https://github.com/Iam-2squared/ark-ai/actions/runs/44289056941), **QUEUED** at initial sample.
- Personal Context `8a26959f`: CI not yet sampled in this report.

**Do not conflate source-commit CI with newer checkpoint CI.** Subsequent exact-HEAD regression tests should exercise guard-vector truncation and constructor/getter nonexecution. If any job FAILS, review the exact logs, fix through the ordinary GitHub Contents path, and switch independent lanes while CI runs. No workflow reruns are necessary merely to poll progress.

## Next plan / 今後の方針

1. Confirm the exact current HEAD's six Windows/Ubuntu x Python 3.11–3.13 jobs and repair only proven failures.
2. Add focused guard-vector truncation/nonexecution regressions after independent source CI; expand Memory ambiguous-COMMIT, WAL/SHM and CAS/ABA coherence without touching frozen Memory v1.
3. Continue Planner terminal/UNKNOWN recovery and exact ToolRegistry/PermissionGate/audit-before-action integration with a disconnected executor only.
4. Advance privacy-safe Personal Context and Proactive occurrence/replay, Observation fixtures, and V3 zero-cost packet identity/reproducibility fences.

**ARK/JARVIS NOT_PASSED.**
