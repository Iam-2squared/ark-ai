# Run600 — READ receipt and synthetic WRITE cross-store custody (non-UI)

**Branch:** Draft PR #8, `research/jarvis-foundations`. **Invocation work-basis:** `2aa16eb1438b326f610fd6039a01ed1217322f47` (Run599 checkpoint). This document describes reversible, offline source/test changes. It does not change a frozen contract, attest a real operation, grant permission, or confer a roadmap PASS.

## Package A — original READ-cycle receipt authority before any getter

- Source `src/ark/agency/disconnected_read_cycle.py`, commit `b559fad7a4023142afbd4c1a44478694035f42a1`. Regression `tests/test_read_cycle_original_denial_descriptors_run600.py`, commit `817028d5fc3622ddfb264eb1aa670a98fb15da22`. **9 authored parametrized cases**, not local pytest PASS.
- Pin import-time class identity and four deny-only descriptors of `DisconnectedReadCycleReceipt`: `dispatch_authorized`, `external_result_verified`, `automatic_replay_authorized`, and `authenticated_clock_or_consent`. A substituted property returning exactly `False` is still not the original implementation. Checks run before the first callback, before constructing a result, before inspecting final result getters and again before return. Static class-dictionary inspection does **not execute** a hostile replacement property.
- Fixtures test all four flags both preinstalled and installed after a successful preflight, and one normal two-wave READ simulation. A mock backend must never execute; the caller's PlanGraph stays PENDING and no one-shot WRITE token is consumed.
- Limit: an in-process descriptor identity is not authenticated executable code, user consent, a trusted clock, an externally verified action or durable cross-process custody.

## Package B — durable synthetic WRITE result and reservation/audit carrier epochs

- Source `src/ark/agency/synthetic_mock_action_cycle_review.py`, commit `a04a8a0a5c7bb3856dde39fc4c7b131053977478`. Regression `tests/test_mock_cycle_original_receipt_custody_run600.py`, commit `d242ee936cc78527633706ea9abd6c488da589e0`. **9 authored parametrized cases**, not local pytest PASS.
- Independently pin the three false-only `SyntheticMockCycleReceipt` class properties at import and refuse preinstalled/late substitutes without calling their getters. Validate the final result's exact class, original field objects and False-only flags.
- Across separately committed Planner RUNNING, occurrence reservation and audit-before-mock steps, recheck the *original field carriers* of the returned reservation and audit event, not merely equal tuple values. A synthetic callback replacing `occurrence_id` or `request_id` with a distinct value-equal string must leave the journal RUNNING/unknown, never silently report success. The tests also cover normal no-backend, single-use progression and receipt denial.
- Limit: a returned exception after the Planner/occurrence/audit COMMIT does not imply rollback. The independent SQLite stores are not one atomic transaction. They do not prove an external action, independent authorization, trusted time, exactly-once side effects or human approval. Never automatically replay an uncertain WRITE. No real registered backend invocation is possible in this lane.

## CI and evidence sampled before this document

- Previously verified **exact-head GREEN:** [CI #41781977843](https://github.com/Iam-2squared/ark-ai/actions/runs/41781977843) on `2aa16eb1438b326f610fd6039a01ed1217322f47`, Ubuntu/Windows Python 3.11, 3.12, 3.13, all six completed-success. This predates all Run600 edits.
- New ordinary, automatically triggered workflows (not manually rerun): [#41788052336](https://github.com/Iam-2squared/ark-ai/actions/runs/41788052336) (`b559fad7...` source), [#41788100080](https://github.com/Iam-2squared/ark-ai/actions/runs/41788100080) (`817028d5...` READ tests), [#41788362624](https://github.com/Iam-2squared/ark-ai/actions/runs/41788362624) (`a04a8a0...` source), [#41788454470](https://github.com/Iam-2squared/ark-ai/actions/runs/41788454470) (`d242ee9...` WRITE tests). All four were **IN PROGRESS** at the sampled read. Their latest-head six-job result was **NOT YET VERIFIED**. Document/checkpoint commits will each trigger additional normal CI; do not fabricate later run IDs.
- `18` cases means **authored pytest parameter-expanded definitions** (9 + 9), not locally executed PASS counts.

## Boundaries and next plan / 今後の方針

1. Verify exact-head six-job CI; inspect real failing job logs and make only minimal semantics-preserving repairs through permitted GitHub Contents API. Avoid duplicate equivalent workflows.
2. Once prerequisite HEAD is GREEN, independently review the retained READ-cycle receipt recheck against equal-False denial substitutions across callbacks; keep no-backend isolation.
3. Continue Memory generation/CAS post-COMMIT ambiguity reconciliation and mixed Planner FAILED/BLOCKED/RUNNING recovery with manual-only uncertain WRITE triage.
4. Only then connect permission/occurrence/audit-before-action mock lanes after their exact-head evidence, without enabling real actions. Continue safe Personal Context consent revocation, proactive and Observation backend fixtures, and free-only V3 guard reviews. UI remains paused.

**Protected:** PR #5 Draft/unmerged and its V3 gate; PR #8 Draft/unmerged; PR #9 Draft/unmerged, UI development completely PAUSED; V1/V2/Local UI/Launcher frozen evidence untouched; no main merge, GPU, billable service, physical-PC action, credential, protected V2 final evaluation, real Candidate or backend. ARK/JARVIS/V3 remain **NOT_PASSED**.
