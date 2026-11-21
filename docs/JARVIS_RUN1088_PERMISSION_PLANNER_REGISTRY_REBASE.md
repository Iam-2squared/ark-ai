# Run1088 — Rebase PermissionGate, immutable PlanGraph and registry preflight

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `073d08ca19dfc67de7dd8da6ce3956bbefc3974b`.
- Common parent for source packages: `916aae6c6578086fee5e83c77c23375712676c90`.
- Compare evidence: the parent delta from the common parent consists only of two `docs/PROJECT_STATUS.md` commits; no source/test paths changed.
- Child branch: `research/run1088-permission-planner-registry-rebase`.

## Reapplied packages

1. **PermissionGate state custody** from PR #212: exact local state/registry binding and one-shot grant/token invariants, with the associated carrier, concurrency and spend-lock regressions.
2. **Immutable PlanGraph status** from PR #214: immutable status publication and staged direct/cascading transition publication, preserving existing terminal propagation semantics.
3. **Read-only Planner ToolRegistry preflight** from PR #216: bind exact PlanStep ToolCalls to an immutable registry revision; capture topology/status digests, ready step IDs and per-step action identities; reject unknown/mismatched tools and method/epoch drift.

The preflight returns only a local consistency fingerprint. It does not mutate PlanGraph, advance a cursor, persist Planner state, invoke PermissionGate, call ActionAudit, grant permission, dispatch, or execute a backend.

## Exact-head source evidence carried forward

- PR #212 exact head `a460543c6130030342051eff8cf42a9bb49aa966`, CI run [44948075522](https://github.com/Iam-2squared/ark-ai/actions/runs/44948075522), GREEN 6/6.
- PR #214 exact head `9307993e5928ab90ac370a811ffe32c579a5128a`, CI run [44948194900](https://github.com/Iam-2squared/ark-ai/actions/runs/44948194900), GREEN 6/6.
- PR #216 exact head `cc7967ec89ae24d8b1f5a05da9f9d93491d96d68`, CI run [44948927136](https://github.com/Iam-2squared/ark-ai/actions/runs/44948927136), GREEN 6/6.

These results apply only to the original child heads. This rebase requires its own fresh exact-head Windows/Linux × Python 3.11–3.13 CI; no prior result transfers.

## Limits

These remain local consistency and in-process mutation controls, not a Python sandbox, authenticated registry provenance, remote backend attestation, restart-safe durable authorization, trusted consent, or proof of external effects. The registry preflight is read-only and disconnected.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, real ToolBackend dispatch, credentials, physical hardware action, UI/frontend work, or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
