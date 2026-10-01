# ARK AI Project Status

**LATEST**

Saved at: **2026-10-01 15:20:00 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `26451d0782d905ce0c4bfa52e742670f2799352d`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

Supersedes the prior canonical checkpoint saved at 2026-09-30 02:10:49 JST.

## Current state

V1/V2/Local UI/Launcher evidence remains frozen and unchanged. PR #5 remains Draft/unmerged under its frozen V3 Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. At the work-basis HEAD, PR #8 is open, Draft, mergeable, **86 commits ahead / 0 behind** `main`.

## New work this session

- Direct GitHub connector verification succeeded through the normal Contents path: commit `26451d0782d905ce0c4bfa52e742670f2799352d` hardened `PlanGraph` ingress to require a tuple of exact `PlanStep` values, closing the previously documented duck-typed mutable-topology entry point. No bypass path was used.
- CI #236 / run `36824969232` started for that exact source-write commit and is **IN PROGRESS** at this checkpoint; no GREEN claim is made yet.

- Saved commit `5651ef2588d3e52cbed3c90feaf94c72a9ce8ca1` updates the Foundation Gap Matrix from exact prior HEAD `6e0539078a6dd0005003a6733050e3faf0c8e6c0`.
- Planner tracking now records two source gaps verified from current code: `PlanGraph` accepts non-`PlanStep` duck-typed inputs whose dependency topology can later mutate, and explicit `CANCELLED`/`BLOCKED` terminal states do not propagate blocking to pending descendants. The safe package is exact `PlanStep` ingress plus non-success-terminal descendant propagation and focused regressions.
- Permission tracking now records that the public gate does not exact-type-check `ToolSpec`/`ToolCall`/grant/token inputs before effect branching. An isolated source-equivalent check reproduced a type-confused WRITE spec with string `"write"` bypassing the in-memory one-shot branch; an exact-type/non-consuming-grant prototype rejected it while preserving normal one-shot replay denial.
- Action Audit tracking now records that arbitrary caller-provided `outcome` text can persist sensitive plaintext even though raw ToolCall arguments are excluded. New writes need a bounded content-free outcome domain while any necessary legacy reader compatibility remains explicit.
- PR #5 was re-read at exact head `d6d4c1954a85fc716b1c593ac55c85417912418f`. Free-only review confirms the preflight authorization packet is not runtime-consumed; its `packet_sha256` hashes packet content before that field is inserted, nested sections are shallow-copied, `load_snapshot()` accepts duplicate JSON keys, and authorization/preflight output checks do not reject symlinked parent directories. A follow-up documentation write for these findings was rejected and therefore is not repository evidence.
- The Planner source patch attempt and a Memory hardening-plan follow-up were also rejected by the normal Contents safety path. No alternate write path was used.

## Tests / CI / evidence

- Exact work-basis CI run `36790110870`: **SUCCESS, 6/6 GREEN** across Windows/Ubuntu and Python 3.11-3.13.
- Job IDs: Ubuntu 3.12 `110140753467`; Windows 3.11 `110140753653`; Ubuntu 3.13 `110140753663`; Windows 3.13 `110140753682`; Ubuntu 3.11 `110140753706`; Windows 3.12 `110140753745`.
- `main...research/jarvis-foundations` at the work-basis HEAD: **86 ahead / 0 behind**.
- Isolated checks reproduced mutable duck-typed Planner topology (`ready=["read"]` becoming `["read","write"]` after external dependency mutation), cancelled-root descendants remaining PENDING with no ready path, the PermissionGate type-confusion bypass, and strict JSON duplicate-key rejection semantics.
- Prototype/source-ready findings remain non-repository implementation evidence until source/tests are saved and exact-head CI is GREEN.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence, V3 Contract semantics, protected evaluation state, Candidate state, PR #5 Draft/unmerged state, and `main` remain unchanged. No paid/external compute, real training, Candidate generation, promotion, protected-evaluation opening, new credentials, destructive action, physical-PC action, or main merge occurred.

## Blockers / authorization boundaries

Normal executable-source/test writes have been intermittently rejected by the GitHub safety path; however, the direct source-write verification at `26451d0782d905ce0c4bfa52e742670f2799352d` succeeded normally in this session. During this session a documentation-only Gap Matrix update was accepted normally, while the Planner source patch and later documentation updates were rejected. No raw Git object/ref, force-push, alternate hidden route, or other safeguard-circumvention path was used.

PR #5 still requires explicit authorization before external compute or real Candidate work. Free guard closure remains limited to local validation/approval-binding/path/integrity work.

## Next plan / 今後の方針

1. Add focused Planner regression coverage for exact `PlanStep` ingress, then continue non-success terminal descendant propagation only through the normal Contents path.
2. Implement Memory exact-scope/API validation, semantic schema and persisted row/event integrity, serialized writer ordering, trusted-clock rollback protection, coherent read snapshot ordering, and revision/expiry-bound purge.
3. Harden Action Audit v1 bootstrap/schema/row/timestamp handling and constrain new-write outcomes to a bounded content-free domain.
4. Land immutable ToolRegistry source/tests, then exact-type PermissionGate/non-consuming grant validation.
5. Add registry-bound durable one-shot authorization + execution occurrence, occurrence-bound Audit v2, and mock-only audit-before-action executor.
6. Continue planner recovery, startup readiness, Personal Context, proactive scheduler, and fixture-only multimodal foundations.
7. Continue PR #5 strict JSON, reviewed approval artifact binding, output-parent/symlink safety, local identity verification, and durable one-attempt consumption without external compute or protected evaluation.
