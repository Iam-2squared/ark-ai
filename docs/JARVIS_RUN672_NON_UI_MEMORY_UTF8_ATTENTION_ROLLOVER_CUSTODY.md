# ARK AI — Run672 non-UI evidence: byte-bounded CAS, deny-only attention, rollover witness custody

Date: **2026-11-07 JST**. Branch: `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), **unmerged**. Initial work-basis HEAD: `164427887ad03fdc25cf2a38a881bd3e39d1ebc6`; its [CI #42302701335](https://github.com/Iam-2squared/ark-ai/actions/runs/42302701335) completed **GREEN in all six Ubuntu/Windows × Python 3.11–3.13 jobs**. That is inherited evidence, not a claim about this report's HEAD.

## Package A — Memory opt-in generation-CAS UTF-8 identity

The optional API formerly used `len(source_id) <= 512`, a character limit inherited from frozen Memory v1, without a UTF-8 byte limit. A 257-codepoint two-byte source could therefore consume 514 bytes yet enter the generation token path. `src/ark/memory/generation_fenced_cas.py` now checks the exact built-in `str`, nonblank content, original **512-character cheap pre-cap**, strict UTF-8 encoding (including rejection of unpaired surrogates), and **512-byte maximum** *before* deterministic ID generation or SQLite access. This does **not** alter `MemoryWrite`, frozen Memory v1 schema, old row storage, token format, CAS transaction, or retention/expiry gates.

Source: `63eb7a881a038d822757a493321f84b87771835c`, formatting repair `99505c60ae1e0170d480e03c574c88437af5abe2`, bounded-allocation hardening `79f87927bad60bda6c86a52b13451cac0cecb3d1`. Tests: `fa3dd694928cc9cd96fc0b625efdd2ca05f69905`, and `3a02bd4d244d235ff4b8374263599cdc05ad3b68` add **7 parameterized cases**, including exact-byte-valid ASCII and multibyte boundaries, legacy char-valid/byte-overbudget rejection, malformed Unicode, reflected write retarget, and oversized raw read refusal before SQLite. The stricter opt-in path may decline generation-CAS for existing legacy rows whose source IDs exceed 512 UTF-8 bytes; this is intentional fail-closed behavior rather than migration or silent record change.

## Package B — Proactive attention result preflight

`src/ark/proactive_attention_preview.py` now pins all five output slot descriptors plus `__new__`, `__getattribute__` and `__getattr__` at module import, rejecting substituted callbacks before JSON/hash work or creating an inert preview. It already pinned the result constructor and four deny-only authority properties. Source: `0d0a1d55ca864f1c27def3f91d5caabdd67e4624`. Tests: `d6d2343c32adb80f80b2b103a0e9e59f5f9c30af` adds **9 cases** (five output fields, three interpreter-isolated hooks, one original deny-only invariant).

**Observed CI failure and semantics-preserving resolution:** [#42307642480](https://github.com/Iam-2squared/ark-ai/actions/runs/42307642480) showed ten inherited `tests/test_attention_preview_postcallback_custody_run572.py` cases failing because their intentionally preinstalled `__getattribute__` hook is now rejected before it can capture a report. Those fixtures expected later `preview changed` and a JSON mutation. Commit `a58920e1739652756488ba1945d286e1e7db6303` changes the ten test expectations to require the **earlier** `attention source preview rejected` plus **zero captured reports, zero late JSON calls and zero mutation**, without relaxing the production guard. Historical FAIL remains real; the follow-up CI result must be checked separately.

## Package C — Observation rollover original witness contract

`src/ark/observation_rollover_review.py` now pins import-original witness type, five frozen field descriptors, `__init__`, `__post_init__`, `__new__` and Python attribute lookup hooks. Preflight runs before any retained witness field read and again at each source-epoch check, including equal-time idempotent rollover. Source `fabbbdc135ff1d4ae7b3f3a203cf6d073ca74af1`. `tests/test_observation_rollover_output_contract_run672.py` at `e07a3e8b55de31a70d51e6269ab2aba792f7b571` adds **11 cases**: five forged output slots, five isolated hook substitutions, and unchanged deterministic idempotent rollover. Tests never access a camera, microphone or live capture.

## CI provenance / current uncertainty

- Baseline [#42302701335](https://github.com/Iam-2squared/ark-ai/actions/runs/42302701335): **6/6 GREEN** at inherited exact HEAD.
- New code runs include Memory [#42307420399](https://github.com/Iam-2squared/ark-ai/actions/runs/42307420399), proactive [#42307642480](https://github.com/Iam-2squared/ark-ai/actions/runs/42307642480), proactive test [#42307726042](https://github.com/Iam-2squared/ark-ai/actions/runs/42307726042), rollover source [#42307848823](https://github.com/Iam-2squared/ark-ai/actions/runs/42307848823), rollover tests [#42307904524](https://github.com/Iam-2squared/ark-ai/actions/runs/42307904524) and inherited-test repair [#42308142222](https://github.com/Iam-2squared/ark-ai/actions/runs/42308142222). Additional automatically triggered runs can follow late fixes/report/checkpoint.
- **Do not label 27 new cases cross-platform PASS or the new exact HEAD 6/6 GREEN without all job results.** A launch, QUEUED, partial Linux GREEN, and a documentation update are not replacements for completed exact-head evidence.

## Separate read-only design audit — Planner success receipt bridge

`disconnected_planner_fence_projection.py` still **rejects recovered SUCCEEDED**, rather than fabricating a result SHA. `disconnected_write_recovery_fence.py` requires a SHA for SUCCEEDED and labels such a claim `COMPLETE_UNVERIFIED` (not real-world completion). `disconnected_registered_receipt_review.py` currently reconciles a retained `act_`/fixture `req_` link against a same-snapshot READ journal; its output is diagnostic and not dispatch authority. A future isolated bridge must bind **exact** Planner topology + step + canonical ToolCall/registry action + independent retained READ result/link + output digest, and deny WRITE success or absent/mixed witnesses. This run **does not integrate or authorize** such a bridge: no hand-waving success hash, automatic replay or broadening of prior passes.

## Preserved boundaries / next plan

All work is free-only, disconnected and reversible. V1/V2, protected final evaluation, Local UI/Launcher and their frozen contracts/evidence remain unchanged; UI PR #9 stays paused and untouched; V3 PR #5 stays Draft/unmerged; no Candidate generation/training, external GPU, paid API, credentials, physical-PC action, real backend dispatch, notification, main merge, force-push or unauthorized permission grant.

Priorities: (1) close the exact new-head CI and repair real failures via normal Contents API only; (2) continue COMMIT-UNKNOWN and CAS/expiry snapshot evidence; (3) design an independently retained, **READ-only** Planner success-result association before any integration; (4) advance auditable registry/permission/durable occurrence/mock controls and privacy lifecycle as separate free lanes.
