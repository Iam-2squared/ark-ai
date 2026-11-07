# ARK AI — Run676: all-SUCCEEDED Planner READ evidence and independent Memory expiry boundaries

**Scope:** FREE-ONLY, **NON-UI**, Draft PR #8 (`research/jarvis-foundations`). This work is disconnected/mock-only, no actual ToolBackend, external service, GPU, protected evaluation, human approval, or main merge. Source/test work-basis HEAD before this report: `a32e8e3d7ea699686b235b28ddae07ad9822708e`. Report authored `2026-11-07T02:53:00.626Z` UTC (system clock, **not** authenticated audit/consent time).

## Package A — Planner registered synthetic READ evidence bundle

- New opt-in source: `src/ark/agency/disconnected_planner_success_bundle_review.py`, source commit `6c9fb6a545ca645298892796c51bdd14e9df7958`.
- New regression file: `tests/test_planner_succeeded_read_bundle_run676.py`, commit `7fa354228f0ea9f0006f2901187dd6efe3e893c5`.
- A recovered synthetic Planner DAG can label multiple steps `succeeded`. The previous single-step `review_synthetic_succeeded_read_correlation` checks the target and requires its dependencies to have `succeeded` status, but does **not** by itself demand a separately reviewed read receipt for each successful ancestor. **The new bundle requires evidence for every succeeded step**, with unique step and fixture request identities, consistent ToolRegistry revision, exact local receipt/result link, and dependency-closed successes.
- Evidence order is canonicalized by step ID; accidental duplicate, omitted, mismatched, or extra evidence is rejected. For pending descendants, only the succeeded ancestor may appear in the diagnostic; no plan execution is unlocked.
- A SHA-256 bundle receipt binds topology/status and each per-step correlation digest. Its four authority flags are hardcoded `False`: external execution unproven, WRITE/dispatch/replay forbidden. This is an opt-in review, **not an attachment to the normal recovery projection**; the existing normal projection continues to reject `succeeded` states.
- Tests cover a two-step dependency with two independent detached registered fixture READs; reversed input ordering; missing ancestor or successor, duplicated step or fixture, wrong step, cross-revision link, malformed pair, pending descendant, and result-class denial tampering. A backend stub throws if invoked.

**Remaining architecture gap:** two SQLite journals have no shared atomic commit/provenance or trusted receipt-signing authority. A bundle digest cannot authenticate historical actor identity, a real result, clock, consent, or effects. Actual Planner recovery/Tool execution must remain closed.

## Package B — independent SQLite Memory retention/CAS cases

- `tests/test_memory_independent_expiry_cas_run676.py`, commit `a32e8e3d7ea699686b235b28ddae07ad9822708e`.
- Two independent local SQLiteMemoryStore handles exercise finite expiry **extension and clearing denial**, exact expiry-timestamp rejection, post-expiry rejection, regressed local-clock rejection, and durable no-new-event assertions.
- A competing writer shortening retention makes a stale CAS token unusable for overwriting or extending it; the post-COMMIT ambiguity reviewer may observe the new row but still cannot attribute the write or permit automatic retry.
- Independent namespace writes do not corrupt the exact-row generation; a CAS token cannot be applied to a different namespace. These are **local regression claims only**; a caller-supplied clock is not trusted and none of the tests grants retention or erasure authority.
- The frozen Memory V1 schema, public put/delete semantics and historical evidence remain unchanged.

## Package C — synthetic Proactive policy UTF-8 ingress hardening

- Source `src/ark/proactive_synthetic_review.py`, commit `27476fce9fe3de719bd8ecb49fd263d5d9cbbd6c`: the four policy identity labels now require strict, encodable UTF-8 and **at most 512 encoded bytes**, not just 512 Python characters. Surrogate text or multibyte overflow is rejected before hashed policy identity or local SQLite preparation.
- Tests `tests/test_proactive_policy_utf8_byte_budget_run676.py`, commit `1c60412a731fb1d4797db4d8a70d288bdef8695f`, **26 authored parameter cases**: four policy fields × four invalid Unicode/byte cases; four fields × two valid UTF-8 boundary cases; two late reflective mutations rejected before a patched SQLite connector may open. No notification, recurring service, proactive action, user permission or trusted-clock proof was added.

## Package D — private retention result-accessor preflight

- Source `src/ark/personal_context_retention_recheck_review.py`, commit `035f54077f9611ba49a16751d75ce3db99b4e9d4`: the local privacy inventory recheck now pins import-original output slot descriptors and inherited lookup hooks using noninvoking class-dictionary inspection **before** any private Memory/revocation projection. Existing original False-only authority-denial checks remain intact, as do four independent local observations and their documented non-atomic limitation.
- Tests `tests/test_retention_recheck_preaccess_slots_run676.py`, commit `f652e5bd58d256a1b6bfaeee0a7939b8416c5f77`, **10 authored cases** (seven result slot descriptors + two attribute hooks + unchanged non-authorizing receipt). A prohibited private-projector spy and substituted accessor spy must both remain uncalled on invalid original-class identity.
- Existing post-constructor tamper diagnostics were preserved; this deliberately does not declare class-level monkeypatch defense to be a sandbox, human consent, erasure proof or durable clock.

**Total NEW authored cases this run: 55** = Planner 11 + Memory 8 + Proactive 26 + Personal Context 10. Four independent coherent non-UI packages; changes were made only by normal GitHub Contents source/test writes with fresh PR HEAD reads. Frozen contracts were not edited.

## Verification and limits

- **Baseline preceding this run:** canonical prior checkpoint HEAD `dad98d16bef1a82840fb6f2dbd39d9738daf0d04` and Actions [#42326423285](https://github.com/Iam-2squared/ark-ai/actions/runs/42326423285): **COMPLETED GREEN 6/6**, individually retrieved, Windows/Ubuntu × Python 3.11–3.13.
- The four source/test packages were saved using the normal GitHub Contents write route. Their **exact-head CI outcomes remain to be verified**; neither new suite nor new code is being called GREEN merely because the earlier baseline passed.
- No protected/frozen tests, candidate weights, model identities, paid training, credentials, local physical PC, or main merge were invoked.
- PR #5 V3 and PR #9 UI remain Draft/unmerged. The November 3 **UI development pause** remains in force.

## Next plan / 今後の方針

1. Inspect exact-head CI for both packages. On failure, fix only real source/test defects using ordinary permitted writes, without relaxing any guard. Do not overlap incompatible changes onto the same in-flight code path.
2. Harden per-step bundle against substituted imported correlation callbacks and in-place reflective input/result mutation after exact-head evidence. Add deterministic negative tests; no dispatch.
3. Continue Memory COMMIT-UNKNOWN writer attribution denial, WAL/ABA/retention clock safety and Personal Context revocation invariants.
4. Only after independent lower-layer GREEN, design mock-only Planner/ToolRegistry/PermissionGate/occurrence/audit bridge. Do not claim exactly-once external effects or an authorized recovery without an independent trusted authority.
