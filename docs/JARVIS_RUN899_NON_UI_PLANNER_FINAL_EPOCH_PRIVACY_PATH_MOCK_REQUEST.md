# ARK AI Run899 — Non-UI Planner final epoch, Privacy path admission and Mock READ request custody

**Observed at (Asia/Tokyo/JST): 2026-11-16T00:55:10.839+09:00** (ordinary wall clock only, NOT a trusted authorization or evidence clock). **Overall ARK/JARVIS NOT_PASSED**. Work is isolated on `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), unmerged. [Protected Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), paused [UI Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9), main and frozen V1/V2/Local UI/Launcher/evaluation evidence remain unchanged.

**Initial work-basis HEAD:** `f68c95484c28dcfc481beebbdb1854525db66b0e`. **Complete source/test HEAD:** `8276528c281465c33c9b808ac0648755320236ee`. **Three source+test packages, 12 authored regression cases**; not an exact-head CI PASS claim.

## Package A — Planner transition final-copy epoch

[Source `a1f831b6`](https://github.com/Iam-2squared/ark-ai/commit/a1f831b6202b1a7933c74e1991c60c51c5739527) pins the committed `PlanGraph` status epoch before detaching the final return value. A valid nested transition during the final `replace()` callback advances the graph coherently but invalidates the older receipt. The outer call now refuses the obsolete receipt, without rolling back either published transition or granting replay. [4 authored test cases `adbd2095`](https://github.com/Iam-2squared/ark-ai/commit/adbd2095d3bc178ba7d9182ac5ff9c5592bafb20) cover same-step, independent-step, terminal BLOCKED cascade, and normal detached success. Only synthetic in-memory steps are exercised.

## Package B — Synthetic Privacy veto SQLite path ingress

[Source `48e939e1`](https://github.com/Iam-2squared/ark-ai/commit/48e939e1de6514f8183f83ddc0750f87d1b9b5aa) checks exact local absolute paths for NUL, malformed UTF-8 and encoded-byte budget including `-journal` BEFORE `lstat` or SQLite. [4 authored test cases `db23ba5f`](https://github.com/Iam-2squared/ark-ai/commit/db23ba5f3ebd189a26a382d31ddb59c1f180b275) exercise NUL, unpaired surrogate, overbudget multibyte paths and a normal restart-read control. This is lexical fail-closed checking, not atomic file-handle custody or consent verification. Windows WAL/SHM last-close races remain unresolved; missing markers never grant permission.

## Package C — Disconnected/mock READ request identity epoch

[Source `ab7c8f13`](https://github.com/Iam-2squared/ark-ai/commit/ab7c8f13cc9d068cf7fc24b3c8fa53e4417ec115) pins the fixture's original request-field descriptors and request-ID/operation/canonical-JSON carrier identities throughout the existing bridge phase checks. A mutable reflected request can no longer silently retarget input while the enclosing binding remains unchanged. [4 authored test cases `8276528c`](https://github.com/Iam-2squared/ark-ai/commit/8276528c281465c33c9b808ac0648755320236ee) cover mutation during identity derivation, equal-text ID replacement, rebound private-argument descriptor and valid inert mock READ. No real registered backend, external tool, authenticated consent or WRITE is executed.

## Exact-head CI evidence

Run898 starting HEAD `f68c9548...` [CI #43726822439](https://github.com/Iam-2squared/ark-ai/actions/runs/43726822439) **GREEN 6/6**, Windows/Ubuntu × Python 3.11–3.13, verified prior to changes. It is not evidence for the Run899 code.

| Run | HEAD | Status when observed |
|---|---|---|
| [#43732296200](https://github.com/Iam-2squared/ark-ai/actions/runs/43732296200) | `8276528c2814` | QUEUED |
| [#43732238786](https://github.com/Iam-2squared/ark-ai/actions/runs/43732238786) | `ab7c8f13cc9d` | QUEUED |
| [#43731997221](https://github.com/Iam-2squared/ark-ai/actions/runs/43731997221) | `db23ba5f3ebd` | IN_PROGRESS |
| [#43731949865](https://github.com/Iam-2squared/ark-ai/actions/runs/43731949865) | `48e939e1de65` | IN_PROGRESS |
| [#43731853647](https://github.com/Iam-2squared/ark-ai/actions/runs/43731853647) | `adbd2095d3bc` | IN_PROGRESS |
| [#43731811651](https://github.com/Iam-2squared/ark-ai/actions/runs/43731811651) | `a1f831b6202b` | IN_PROGRESS |

All final-head six jobs must pass before any GREEN claim. CI automatically runs per PR push; no equivalent manual dispatch.

## Safety boundary and Next plan / 今後の方針

No new UI/frontend source/tests/integration, paid or potentially billable compute/API/GPU, credentials, protected V2 evaluation, V3 Candidate/adapter generation/promotion, real tool dispatch, personal context export, destructive action, physical-PC step, or approval-gated main merge. These changes do not prove trusted clocks, independently retained permission, filesystem atomicity, model provenance, or exactly-once execution. PRs #5/#8/#9 remain Draft.

1. Establish exact-head Windows/Ubuntu six-job CI; fix any real failure minimally through normal Contents API while other modules are reviewed.
2. Continue isolated Windows SQLite WAL/SHM last-close diagnostic, distinguishing durable winning veto from a refusing loser without treating a winning row as consent.
3. Deepen Planner cold UNKNOWN quarantine, Memory CAS/event/expiry snapshot coherence and cross-process integrity.
4. After lower-level exact-head GREEN, integrate registry-bound exact-type PermissionGate, durable pre-action audit and disconnected READ receipts. Never replay COMMIT-UNKNOWN.
5. Continue Personal Context privacy retention, proactive/Observation back-end fixtures and detached free-only V3 guard reviews, with no frozen gate crossing.
