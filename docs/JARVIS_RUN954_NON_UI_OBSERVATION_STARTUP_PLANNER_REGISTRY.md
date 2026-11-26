# ARK AI Run954 — Non-UI core: frozen Observation compatibility, startup diagnostics, Planner fan-in, registry scope

**Work basis:** Draft PR #8 research/jarvis-foundations commit 838c88e89f695cbdc42b540869e70f563bdb2b6a. **Latest source/test HEAD before report:** 6456c0cb67bc627260393e1f948c8532347edddd. All changes on PR #8 only; main, PR #5, paused UI PR #9 untouched. **ARK/JARVIS NOT_PASSED**. No paid compute, real tools, live capture, owner PC or training.

## Four packages — 45 authored test cases

1. **Observation frozen-v1 compatibility audit, 8 tests.** Initial direct-envelope NUL rejection (f3c1c152) and new regression (c64587b4) conflicted with old tests explicitly preserving the frozen direct ObservationEnvelope NUL-as-distinct-JSON identity. Ubuntu Python 3.11 CI #44202357551 found **39 failed, 17,243 passed, 1 skipped** on erroneous intermediate HEAD. Repaired normally: direct Observation source restored to **exact prior blob** 10c3b6e1d9f4635394e44dfa8893d3a5b9fccb30 at fd602a7b; compatibility regression updated at 6456c0cb to require legacy direct NUL JSON identity and separately reject NUL in the opt-in fixture adapter. Old tests preserved and no frozen contract change persists. **Await postrepair CI.**
2. **Startup readiness diagnostic control characters, 24 tests.** Source 58f42232 adds ASCII C0/DEL refusal (including CR, LF and TAB) to the optional disconnected readiness label check. New regression d0e7c80c: 5 controls × 4 identity fields, three reflectively mutated label cases, one valid Unicode dependency-blocking graph. No startup or action permission.
3. **Planner cold fan-in propagation, 4 tests.** Regression 51afcef8 examines FAILED/CANCELLED of either upstream root, other-root success, cold SQLite recovery, durable BLOCKED join/child and automatic-replay denial. No backend execution.
4. **ToolRegistry optional scope identity, 9 tests.** Source a8499ffb preflights NUL and invalid UTF-8 scopes immediately before registry binding; regression 9e7296d5 covers READ/WRITE, resolve/bind, reflected scope, valid Japanese UTF-8 and zero backend calls. Frozen ToolCall v1 and valid deterministic registry vector remain unchanged; identity is not authorization.

## Evidence sampled 2026-11-18 08:59:41 JST

- Initial checkpoint HEAD 838c88e8 [CI #44195426596](https://github.com/Iam-2squared/ark-ai/actions/runs/44195426596): **GREEN 6/6** (Windows/Ubuntu × Python 3.11–3.13).
- Intermediate erroneous Observation HEAD f3c1c15 [CI #44202357551](https://github.com/Iam-2squared/ark-ai/actions/runs/44202357551): Ubuntu 3.11 **FAIL** (39 conflicts with frozen legacy direct NUL semantics); repaired by restoring original source bytes.
- Startup [CI #44202908752](https://github.com/Iam-2squared/ark-ai/actions/runs/44202908752): **IN PROGRESS**, Planner [CI #44203122329](https://github.com/Iam-2squared/ark-ai/actions/runs/44203122329): **IN PROGRESS**, Registry [CI #44203520638](https://github.com/Iam-2squared/ark-ai/actions/runs/44203520638): **QUEUED** at sample; those earlier heads may inherit the intermediate Observation fault.
- Observation original-source restoration [CI #44203913323](https://github.com/Iam-2squared/ark-ai/actions/runs/44203913323): **QUEUED**, compatible new tests [CI #44204003407](https://github.com/Iam-2squared/ark-ai/actions/runs/44204003407): **QUEUED** at sample.
- **Latest source/test exact-HEAD six-job GREEN not verified.** Additional report/checkpoint writes will launch automatic CI, no duplicate manual workflow requests.

## Safety limits and next actions

Direct ObservationEnvelope NUL behavior is frozen; native NUL veto belongs only in optional disconnected fixture ingress. Frozen V1/V2/Local UI/Launcher evidence, protected V2 final-evaluation, V3 Contract #1, contamination/provenance/reproducibility and explicit approval gates unchanged. PR #5/#8/#9 Draft/unmerged; UI paused. No paid/external compute, Candidate generation/promotion, protected evaluation, real ToolBackend, human approval fabrication, actual private-data release/erasure or main merge. Local hash witnesses and SQLite journals do not authenticate issuer, consent, trusted time, external action, cross-store atomicity or external exactly-once outcomes.

**Next plan:** confirm postrepair exact-HEAD CI and narrowly fix any genuine defect; advance Memory WAL/SHM CAS/ABA and coherent expiry; integrate Planner COMMIT-UNKNOWN, immutable ToolRegistry, exact PermissionGate and audit-before-action only under disconnected mock; then continue Personal Context privacy, proactive occurrence, observation fixture adapters and free-only V3 guards. UI remains paused; **ARK/JARVIS NOT_PASSED**.
