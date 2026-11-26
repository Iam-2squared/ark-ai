# ARK AI — Run477 disconnected receipt custody and preflight input binding

**Scope:** synthetic, local-only, reversible foundations. This record describes source and authored tests, not authorization or real JARVIS completion.

## Work basis and isolation

- PR #8 / `research/jarvis-foundations` work-basis checkpoint: `f0374c7947deb243f53a54fd6a2668091bb12922`.
- PR #5 / `research/v3-learning-evaluation` work-basis source/test: `7e887160853017b98373cfa88cbeeec9c7deef0a`.
- Baseline PR #8 `455407fde900085056c546041e427ddeea9b370f` CI run `41036936776` / #1571 completed SUCCESS across all six Ubuntu/Windows Python 3.11–3.13 jobs; checkpoint `f0374c7947deb243f53a54fd6a2668091bb12922` run `41037323809` / #1573 completed SUCCESS.
- All writes were through normal GitHub Contents API with PR-head re-reads; no force push, raw Git-object/ref bypass, merge or manual duplicate CI trigger.

## Package A — detached startup schema/preflight epoch

`src/ark/disconnected_local_readiness.py` blob `8aeb3fd979bf8e62ededcfc22a65b3c87f56a1f6`; `tests/test_disconnected_readiness_receipt_epochs_run477.py` blob `e82b306aa8187a6a8872d073feeacddb330583a2` (20 authored cases).

The two query-only SQLite schema probes now enforce exact receipt types, retained first-probe field identities and non-authority properties. The READ preflight receipt retains original topology, status, registry, grant fingerprint, ready-step and bound-ID tuple carriers through the second schema probe, final digest and report constructor. Any late reassignment or forged dispatch/consent/replay authority rejects startup readiness. No rows, ToolBackend or filesystem path are operated by this joining review. Two sequential read transactions do not establish atomic multi-store snapshots.

## Package B — retained Memory event chain denies authority

`src/ark/memory/synthetic_event_continuity_review.py` blob `05111cf10e5f158e01529292039686bc0ed44ac4`; `tests/test_memory_event_authority_custody_run477.py` blob `8d7a96546f89f66152233d547038c60afbc372ca` (7 cases).

Exact retained witness and every previously minted chain prefix must remain non-authorizing for deletion, Personal Context reuse and external disclosure, not merely preserve equal-valued fields. This is an in-process read-only synthetic SHA-256 continuity review. It cannot independently attest writer provenance, historical data bytes, clock trust or complete storage rollback. Memory v1 DDL is unchanged. On intermediate #1578, two older test assertions exposed a changed error string; the subsequent source correction restored the prior diagnostic without weakening refusal.

## Package C — mixed-plan UNKNOWN WRITE triage receipt denial

`src/ark/agency/disconnected_write_recovery_fence.py` blob `2063cb34e5c25050765e292b6d7f66292e15d0fa`; `tests/test_mixed_recovery_authority_receipt_run477.py` blob `7bbfba3980424b9a929aac0ddf63e0a931a00884` (6 cases).

The final exact-type `OfflineRecoveryFence` must explicitly deny dispatch, automatic replay, WRITE authorization and verified external outcome, including malicious constructor/property injection. A synthetic `UNKNOWN` WRITE remains quarantined and descendants held; `READY_MOCK_ONLY` never authorizes real execution. No externally exactly-once WRITE reconciliation or audit consent is claimed.

## Package D — V3 preflight report input epoch across callbacks

PR #5 `src/ark/learning/preflight.py` blob `64ec69a5ff5548b6b780d886951c89766c7e6866`; `tests/v3/test_preflight_report_input_epoch_run477.py` blob `50948b6900dd05566dd85d374a31f393e7f01df8` (10 cases).

`build_preflight_report` pins exact nested JSON snapshot carriers, evidence fields, measured runtime fields and exact dataclass types. The original inputs are rechecked after experiment validation, measurement binding, core hashing, dataclass materialization and canonical JSON encoding. This prevents a reentrant validation/serialization hook from producing a seemingly valid NON_CANDIDATE_PREFLIGHT report for a different mutable authorization, budget, evidence or measured-runtime epoch. It adds no authorization, GPU access or model generation. The preflight source still requires independently approved immutable identities and free-only boundaries.

The first PR #5 run #1580 failed Ruff I001 in the new test import block, and #1583 still failed I001; the final normal Contents edit removed an unnecessary post-import blank line. CI after that final edit is tracked separately in canonical `PROJECT_STATUS.md`; neither failed run may be called GREEN.

## Evidence limits and next integration gates

- All 43 synthetic pytest cases were authored/saved; no full local pytest or Ruff execution is claimed (the working container cannot resolve github.com to clone). Use exact-source-head CI results, and do not substitute a prior-green run for a later change.
- Preserve frozen V1/V2/Local UI/Launcher evidence, Memory v1 schema, protected V2 final evaluation and V3 Contract 1 / one Candidate / 120 train + 30 validation / no sweep. Both PRs stay Draft/unmerged.
- No paid or external GPU, billable APIs, subscriptions, real Candidate weights, model promotion, new credentials/accounts, real-world Tool execution, external notification, protected final-evaluation opening or main merge.
- Next priority: exact-head CI; restart-safe WRITE outcome reconciliation (unknown means no replay), immutable registry identity, trusted clock/audit-before-action, coherent Memory snapshots, and provider-side budget enforcement only with future explicit authorization.
