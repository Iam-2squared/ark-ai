# ARK AI Run843 — Non-UI restart identity admission and Memory verifier custody

**Work basis (exact GitHub PR #8 HEAD):** `8cb65a85796171b542e2796ce5273730e6727c9e`, after confirming [six-job GREEN CI #43404956402](https://github.com/Iam-2squared/ark-ai/actions/runs/43404956402). Scope: free-only, disconnected, reversible, no UI, no real action or Candidate.

## New work saved through the normal GitHub Contents API

1. **Proactive offline recurrence input bounds** — source [`68451ed1`](https://github.com/Iam-2squared/ark-ai/commit/68451ed159480fa8550fa21be5299c55c4dc1239), tests [`058d1fc1`](https://github.com/Iam-2squared/ark-ai/commit/058d1fc12fa69df49cd77f4e06e93c61b6dc80c7). The policy SHA must be exactly 64 characters and the retained `slot_` cursor exactly 69 characters **before regex**, so oversized restart labels cannot reach digest pattern matching. Nine authored parameterized cases (eight invalid forms, one exact positive); not nine independently established PASS. This remains a caller-clock preview, never notification, consent or tool authority.
2. **Registry-bound inert WRITE identity bounds** — source [`be693fef`](https://github.com/Iam-2squared/ark-ai/commit/be693fef40f6949027a1fa9b541508eee055c1ef), tests [`2fe063bc`](https://github.com/Iam-2squared/ark-ai/commit/2fe063bca68217df93e7de7d0b49735ebf57416f). Reject occurrence IDs not exactly `occ_` + 64 hex **before** Registry access; require exactly `act_` + 64 hex before `bind`, and exactly `bound_` + 64 hex before digest use. Eight authored cases (seven invalid and one positive). Existing ToolRegistry binding identity and backend nonexecution retained. The output is **not** an authenticated approval or a write permit.
3. **Memory expiry restart module identity custody** — source [`ed6abd23`](https://github.com/Iam-2squared/ark-ai/commit/ed6abd23349040951099029fc82ca055c7686bc1), tests [`fa8dbda0`](https://github.com/Iam-2squared/ark-ai/commit/fa8dbda07a55ab7e9bb267b1c0e77f0d39a321cb). Pin `hashlib`, `json` and `cohort_module` module objects **before** accessing potentially executable replaced attributes. Pin protocol domain/pattern by identity. Three synthetic hostile-module getter regressions require zero getter calls. It remains a content-free, caller-supplied, cross-scope non-atomic, *no automatic purge* review.

**Total: 3 packages / 20 authored test cases.** No full local pytest/Ruff, no PC GGUF inference or external tool invocation. Source/test correctness on the exact final HEAD remains dependent on GitHub CI. No duplicate manual workflow run started.

## CI evidence (separate source/test HEADs)

- Last fully observed before this run: [#43404956402](https://github.com/Iam-2squared/ark-ai/actions/runs/43404956402), SHA `8cb65a85796171b542e2796ce5273730e6727c9e`, **6/6 GREEN** on Windows/Ubuntu × Python 3.11–3.13.
- Proactive tests: [#43411602255](https://github.com/Iam-2squared/ark-ai/actions/runs/43411602255), SHA `058d1fc12fa69df49cd77f4e06e93c61b6dc80c7`, initially IN PROGRESS.
- Registry tests: [#43411725617](https://github.com/Iam-2squared/ark-ai/actions/runs/43411725617), SHA `2fe063bca68217df93e7de7d0b49735ebf57416f`, initially QUEUED.
- Memory tests: [#43411933699](https://github.com/Iam-2squared/ark-ai/actions/runs/43411933699), SHA `fa8dbda07a55ab7e9bb267b1c0e77f0d39a321cb`, initially QUEUED. These are time-scoped observations; later verification is required.
- Final report/checkpoint commits trigger ordinary automatic PR CI. Do not claim GREEN without job inspection of their exact SHAs.

## Unchanged gates and next work

ARK/JARVIS remains **NOT_PASSED**. Frozen V1/V2/Local UI/Launcher evidence and protected final-eval contracts remain untouched. [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) and paused [Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) remain unmerged; no new UI/frontend work. No paid/external GPU/API or potentially billable action, Candidate creation/promotion, human-approval fabrication, trusted-clock attribution, real ToolBackend execution, physical-PC action, destructive operation or main merge.

Next: (1) exact final-head Windows/Linux CI and minimal fixes only if genuinely failing; (2) disposable Memory/ActionAudit WAL/SHM sidecar lifecycle and restart ambiguity diagnostics; (3) Memory COMMIT-UNKNOWN isolation and Planner persisted UNKNOWN recovery; (4) immutable Registry/PermissionGate/audit-before-action plus disconnected Mock-only integration after dependency exact-head GREEN; (5) privacy, proactive, observation and V3 free-only guards in independent non-UI lanes.
