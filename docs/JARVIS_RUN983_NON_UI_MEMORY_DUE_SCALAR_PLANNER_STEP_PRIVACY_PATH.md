# ARK AI Run983 — Non-UI Memory due-page scalar admission, Planner step labels, Context revocation source paths

**Work basis:** `1236de889f62659d7009a34c2b125acf2c99452b` (Run982 canonical checkpoint). **Source/test result before this report:** `1cb0977d60c7837c6d31f6669793765eed201ccf` on `research/jarvis-foundations`, Draft PR #8. **Overall JARVIS NOT_PASSED.** This is local-only, synthetic/disconnected work and not an approval or real-world action.

## New coherent packages

1. **Memory — coherent expiry scalar SQL admission.** [Production source](https://github.com/Iam-2squared/ark-ai/commit/09d85c23653e32dc85b5464319378bc18a67f00a) adds a pre-`SELECT *` SQL filter for chosen due-page scalar types, identifier/digest lengths, timestamps and revision, alongside the existing private content/metadata/source budget. The predicates run in the SAME snapshot on the SAME limited due-page; no schema or existing expiry mutation contract changes. [Tests](https://github.com/Iam-2squared/ark-ai/commit/d05f9b45a372ac19e51e112a4779ed580d617547): **6 authored cases** (five oversized SQLite BLOB identity/scalar corruption variants and one valid scoped preview with an unrelated corrupt scope). Existing tests preserved. A selected corrupt scalar must be rejected before Python full-row hydration, but this is not a complete malicious-SQLite/open-file custody proof.
2. **Planner — disconnected restart identifier admission.** [Production source](https://github.com/Iam-2squared/ark-ai/commit/88b539782fbcaedbdceb648bf930a889f3641088) refuses ASCII/C1, bidi/invisible Unicode and formatting delimiters in local restart step labels before dict hashing, sorting, comparison or the cross-source reviewers, while preserving ordinary UTF-8/CJK labels. [Tests](https://github.com/Iam-2squared/ark-ai/commit/7d2547236d6e605fd7b08a84c240240c242d490f): **29 authored parametrized cases** (7 markers × four input carriers plus one multilingual acceptance). No change to frozen Planner identity schema or execution eligibility, no real backend or automatic WRITE replay.
3. **Personal Context — privacy veto SQLite path source preflight.** [Production source](https://github.com/Iam-2squared/ark-ai/commit/26be21c1ce67490befde9c041febd5edcf506ce9) refuses lexical parent traversal and checks the absolute ancestor chain for link aliases before revocation SQLite opens. [Tests and import cleanup](https://github.com/Iam-2squared/ark-ai/commit/1cb0977d60c7837c6d31f6669793765eed201ccf) (first tests commit `76472af2447e40f5d3f900ed56e86e6560cc45f3`): **5 authored cases** (absolute/relative parent traversal × existing flag, and normal relative local fixture). The preflight remains raceable: not atomic dirfd/open-handle custody and not deletion, user consent, or erasure proof.

**Total: 3 meaningful isolated non-UI packages; 40 newly authored test cases.** All writes used normal GitHub Contents API; no force push, raw Git-object writes, overriding safeguards, unauthorized services or extra workflow dispatch. These are authored tests, not yet certified PASS on the newest HEAD.

## CI and evidence

- **Previous exact checkpoint HEAD** `1236de889f62659d7009a34c2b125acf2c99452b`: [#44447458824](https://github.com/Iam-2squared/ark-ai/actions/runs/44447458824), **6/6 GREEN**, Windows/Ubuntu × Python 3.11–3.13, independently read from GitHub Actions in this invocation.
- Memory source/test: [#44453305702](https://github.com/Iam-2squared/ark-ai/actions/runs/44453305702) and [#44453363632](https://github.com/Iam-2squared/ark-ai/actions/runs/44453363632), **IN PROGRESS** at last check.
- Planner source/test: [#44453555068](https://github.com/Iam-2squared/ark-ai/actions/runs/44453555068) **IN PROGRESS**, [#44453595181](https://github.com/Iam-2squared/ark-ai/actions/runs/44453595181) **IN PROGRESS** at last check.
- Privacy source/test: [#44453899012](https://github.com/Iam-2squared/ark-ai/actions/runs/44453899012), [#44453933821](https://github.com/Iam-2squared/ark-ai/actions/runs/44453933821), [#44453958830](https://github.com/Iam-2squared/ark-ai/actions/runs/44453958830) **QUEUED** at last check.
- A report or checkpoint commit may trigger a *newer* run. Latest source/test and checkpoint exact-head **6/6 GREEN remain unconfirmed**; no local full pytest or actual device GGUF/PC gate was performed.

## Preserved boundaries

main `7a843f17eb96ed13d66f23b58b06406b3002e405`; gated PR #5 Draft `805b377697472268db02650a89c7a94b1c5337c8`; UI-paused PR #9 Draft `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` — unchanged. Frozen V1/V2/Local UI/Launcher evidence and Memory v1, ToolCall/PlanStep v1, Observation Envelope v1 and protected evaluation/Candidate boundaries remain untouched. No paid services, external GPU, training, real Candidate adapter/weight generation, automatic promotion, protected V2 final opening, actual action/tool dispatch, physical-PC work, irreversible erasure or main merge.

## Next plan / 今後の方針

1. Confirm latest exact-head CI on all 6 jobs; repair any actual failures via normal permitted API, keeping CI-independent non-UI progress active.
2. Memory WAL/SHM alias/open races, CAS generation ABA, expiry/event coherent snapshots, COMMIT-UNKNOWN manual-only no-retry triage.
3. Planner restart terminal states and registry-bound PermissionGate, durable one-shot authorization, trusted-clock pre-action audit; mock-only integration after lower-level exact-head GREEN.
4. Personal Context consent/retention/revocation, proactive occurrence replay and observation fixtures; free V3 path/identity/reproducibility guards. **UI stays PAUSED.**
