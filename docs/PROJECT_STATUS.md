# ARK AI Project Status

**LATEST**

Saved at: **2026-10-01 22:45:29 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `5fb916ddb9b36f02267c85af7e155924dc28a7cc`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

Supersedes the prior canonical checkpoint saved at 2026-10-01 15:20:00 JST.

## Current state

V1/V2/Local UI/Launcher evidence remains frozen and unchanged. PR #5 remains Draft/unmerged under its frozen V3 Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. At the work-basis HEAD, PR #8 is open, Draft, mergeable, **93 commits ahead / 0 behind** `main`.

## New work this session

- Saved commit `5fb916ddb9b36f02267c85af7e155924dc28a7cc` refreshed `docs/JARVIS_FOUNDATION_GAP_MATRIX.md` from exact current source and PR #5 review state.
- Planner tracking now records that exact outer `PlanStep` ingress is already landed, while nested `ToolCall`, transition `step_id`, identity-bearing text fields, and JSON object keys still need exact-type closure. A `str` subclass can alter equality/hash behavior while canonical JSON serializes its underlying bytes, so policy/dictionary identity can diverge from hashed request bytes.
- Memory tracking now records exact `MemoryWrite` / `MemoryQuery` / `MemoryScope` ingress plus single-field-snapshot requirements. Current repeated attribute reads permit a mutable duck-typed request to split deterministic ID inputs from persisted/returned scope/source within one logical operation.
- PR #5 tracking now records shared strict duplicate-key JSON requirements, all-local path/byte validation before runtime import, all-entry learning-tree symlink rejection, reviewed approval consumption, and a durable one-attempt ledger so a crashed full Candidate run cannot become silently retryable before Candidate output exists.
- A normal executable-source update for `src/ark/agency/contracts.py` was rejected by the GitHub/OpenAI write safety path. Follow-up V3 and Memory documentation writes were also rejected. No raw Git object/ref, force-push, alternate branch, or hidden write route was used.
- Read-only review reconfirmed Action Audit repeated `ToolCall` attribute reads can let a mutable duck-typed call produce a persisted identity different from the returned event identity; the v1 hardening target remains exact `ToolCall` ingress and one canonical field snapshot used for validation, persistence, and return.

## Tests / CI / evidence

- Exact work-basis CI #239 / run `36870806818`: **IN PROGRESS** at this checkpoint.
- Five jobs are GREEN: Windows 3.11 `110397764340`, Ubuntu 3.13 `110397764445`, Windows 3.13 `110397764489`, Ubuntu 3.12 `110397764501`, Ubuntu 3.11 `110397764583`.
- Windows 3.12 job `110397764018` is **IN PROGRESS**; no exact-head GREEN claim is made yet.
- Previous exact-head CI #238 / run `36831525164` was **SUCCESS, 6/6 GREEN** at `a8a97123d4a4738385fc04f75b5f705448132f75`.
- `main...research/jarvis-foundations` at the work-basis HEAD: **93 ahead / 0 behind**.
- PR #8 has no submitted reviews or review threads at this checkpoint.
- Source-equivalent checks reproduced identity-bearing `str` subclass divergence: dictionary lookup can alias a canonical tool name while canonical JSON serializes the subclass's underlying different text. These checks remain prototype evidence until source/tests land and exact-head CI is GREEN.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence, V3 Contract semantics, protected evaluation state, Candidate state, PR #5 Draft/unmerged state, and `main` remain unchanged. No paid/external compute, real training, Candidate generation, promotion, protected-evaluation opening, new credentials, destructive action, physical-PC action, or main merge occurred.

## Blockers / authorization boundaries

Normal executable-source/test writes remain intermittently rejected by the safety path. This session successfully saved one documentation-only Gap Matrix commit through the normal Contents API, then later source/docs updates were rejected. No safeguard-circumvention route was used.

PR #5 still requires explicit authorization before external compute or real Candidate work. Free closure remains limited to local validation, reviewed-approval binding, path/identity integrity, and durable attempt-accounting work.

## Next plan / 今後の方針

1. Through the normal Contents path only, harden agency identity text/JSON-key primitives, exact nested `ToolCall`, exact transition step IDs, and FAILED/CANCELLED/BLOCKED descendant propagation with focused regressions.
2. Implement Memory exact request/scope ingress, one immutable request snapshot, semantic schema/row/event integrity, serialized CAS writers, trusted-clock ordering, coherent reads, and revision/expiry-bound purge.
3. Harden Action Audit v1 with exact `ToolCall`, canonical one-time field snapshot, bounded content-free outcomes, exact schema/row validation, writer locking, and trusted-clock monotonicity.
4. Land immutable ToolRegistry source/tests, then exact-type PermissionGate with non-consuming grant validation.
5. Add registry-bound durable one-shot authorization + execution occurrence, occurrence-bound Audit v2, and disconnected/mock audit-before-action executor.
6. Continue planner recovery, startup readiness, Personal Context, proactive scheduler, and fixture-only multimodal foundations.
7. Continue PR #5 free-only strict JSON, all-local-before-runtime ordering, code-tree symlink rejection, deep-detached reviewed approvals, and durable one-attempt consumption. Do not start external compute or protected evaluation.
