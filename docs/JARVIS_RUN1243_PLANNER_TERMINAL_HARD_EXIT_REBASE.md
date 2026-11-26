# JARVIS Run1243 — Planner terminal hard-exit regression rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `609a3cdaf7ad3b08ef90f2398378d9984bdc329d`.
- Rebased from Draft PR #424 child branch `research/run1241-planner-terminal-hard-exit`, exact child HEAD `762395a8aa8c2b142121d1a46c2d5c36c6f94340`.
- The test body is carried forward unchanged; this rebase adds no production source, schema or contract changes.
- Previous child CI [45314707305](https://github.com/Iam-2squared/ark-ai/actions/runs/45314707305) was GREEN 6/6 on its older parent and does not certify this rebased head. Fresh exact-head CI is required.

## Regression coverage

- Create a synthetic DAG with a root, one dependent step and one independent step.
- Persist the root's RUNNING transition.
- In a spawned process, persist the terminal FAILED transition and call `os._exit` immediately after native SQLite COMMIT, before Python cleanup or receipt return.
- Recover through a fresh `PlannerJournal` instance and require root FAILED, dependent BLOCKED, independent PENDING, exact revisions and the two-event append-only prefix.
- Verify SQLite quick-check, no ambiguous RUNNING step after the durable terminal commit, no automatic replay/dispatch authority, and no raw ToolCall argument persistence.

## Evidence boundary

Synthetic local process-exit evidence only. It is not a power-loss/fsync certification, filesystem durability guarantee, trusted-clock proof, execution authorization, backend dispatch or exactly-once external-effect claim. The fixture does not invoke a ToolBackend or use live personal data.

No production source, schema, frozen contract, V1/V2 evidence, UI/frontend branch or protected evaluation is changed. No paid/external compute, Candidate generation/promotion, credentials, hardware, destructive operation or main merge is performed. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.
