# Run999 — Planner/mock terminal COMMIT-UNKNOWN recovery

**Work basis:** Draft PR #22 exact head `8dd522befb15e39b805a417744dd2fc89db49331`, the isolated Planner / registry-preflight / mock-only composition branch. PR #22 remains Draft and unmerged.

## Regression scope

The new test injects an uncertain COMMIT at the Planner journal's terminal `SUCCEEDED` transition, after the disconnected mock backend has returned and its two local audit events have been appended.

Two outcomes are exercised:

1. The underlying SQLite COMMIT persists, but the caller loses its acknowledgement. Cold recovery must show `SUCCEEDED`.
2. The synthetic COMMIT failure rolls back the terminal transition. Cold recovery must show `RUNNING` as ambiguous.

In both cases the recovered step is not ready, dispatch and automatic replay remain false, and a second cycle attempt is rejected before another mock backend call. The test also verifies that the audit and occurrence fixtures are unchanged by the attempted retry.

## Boundaries

Only disposable local SQLite files and the exact in-process `MockToolBackend` are used. The test does not alter Planner DDL, transition semantics, ToolCall/PlanStep contracts, Action Audit or occurrence schemas. It does not prove cross-store atomicity, trusted time, authenticated consent, external-effect delivery, or exactly-once real-world execution.

No real ToolBackend, network, shell, device, model, notification, paid service, GPU, Candidate artifact, protected evaluation, UI/frontend code, or main merge is involved.

**Validation:** authored regression test and report only. Exact-head CI is pending after this Draft PR is opened; no PASS is claimed. Overall ARK/JARVIS remains NOT_PASSED.
