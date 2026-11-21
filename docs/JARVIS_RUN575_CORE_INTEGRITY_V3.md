# Run575 — Four free-only non-UI integrity work packages

**Scope:** Draft PR #8 `research/jarvis-foundations` and separate Draft PR #5
`research/v3-learning-evaluation`. No UI/frontend changes. PR #9 and main
remain untouched. These patches do not claim live action authority, training
readiness, model improvement, or JARVIS completion.

## 1. Memory expiry candidate event-clock ordering

- Source `src/ark/memory/expiry_candidate_preview.py` at
  `6a8b6f2c0b321167eaab7cbff6b52d1f4204ce9f` checks nondecreasing local
  `occurred_at_ms` **across every event of each candidate's lifecycle**.
  Previously a current row could match the last event while an intermediate
  event clock moved backward, including an old delete/recreate epoch.
- Tests `tests/test_memory_expiry_event_clock_run575.py`, final correction
  `4a5cbba1e349aedd6d7d3d9e159d5cf629adb92e`, cover two update
  positions, a deleted/recreated source, and valid equal-clock recurrence.
- Applies to both selected and overflow candidate rows without changing
  Memory v1 schema, real purge semantics, or authorization. A local timestamp
  ordering check does **not** authenticate a clock or historical writer.

## 2. Planner registered READ recovery parent/child continuity

- Source `src/ark/agency/disconnected_recovered_registered_read_join.py`
  at `050f8a9e31a645f92ad12d7335f8ef91351dfdce` now independently
  recalculates the registered child digest after all false-only denial
  callbacks, before recording the child in the parent join.
- `tests/test_recovered_registered_child_postdenial_run575.py` at
  `5f98bc5768c731757f35937eb58d1dab6d93f9a1` adds two mutating-denial
  probes and two inert success/failure regressions. All fixtures are local
  and have an explicitly forbidden backend.
- A deterministic local receipt hash is **not** ToolRegistry permission,
  proof of an external READ, exactly-once effect, or replay authorization.

## 3. Proactive attention: second privacy veto check

- Source `src/ark/offline_attention_revocation_review.py` at
  `58cf6fe2aa2089cf9b6fbeaa224404b69995251e` does a second retained
  ledger continuity read *after* a nonvetoed, synthetic attention preview.
  If the ledger changed during the preview, the earlier REVIEW_ONLY
  conclusion is rejected rather than reported as current.
- `tests/test_attention_privacy_final_veto_run575.py` at
  `63cd87ce30b5c62adf6153a9cc0e292e70081179` injects a local marker
  at the second SQLite read for same and foreign scopes, and covers the
  unchanged success path.
- The two reads are **not** atomic across stores, cannot rule out a revocation
  after final inspection, and are not real consent, notification, trusted
  clock, or personal data disclosure approval.

## 4. V3 passive snapshot transition authority definition

- On PR #5, `src/ark/learning/offline_readiness_transition.py` at
  `64ff7b3136403142ee02b278f4edafda5ac71245` pins the original
  passive result type and all false-only denial descriptors **at import**.
  Replaced descriptors are refused before snapshot shape processing.
- `tests/v3/test_passive_transition_original_denials_run575.py` at
  `5ce98ebe00cbd8f220c6124fc672e577f0fff284` adds eight
  flag-substitution cases, one class-substitution case and an inert template
  regression. It does not access a GPU or open the V2 protected evaluation.
- The V3 contract, data/model identities, human review, financial
  authorization, official PASS status, Candidate and exports are unchanged.

## Evidence status and restrictions

- Last completed **prior** PR #8 checkpoint on
  `e1e65a4013805b3c912981104dea90b6ba098df7`:
  [Actions #41593576568](https://github.com/Iam-2squared/ark-ai/actions/runs/41593576568)
  **SUCCESS 6/6**, checked directly.
- Post-package PR #8 source/test CI:
  [#41598689036](https://github.com/Iam-2squared/ark-ai/actions/runs/41598689036),
  **QUEUED** at initial sample, **not** a GREEN claim.
- PR #5 latest source/test CI:
  [#41598916980](https://github.com/Iam-2squared/ark-ai/actions/runs/41598916980),
  **QUEUED** at initial sample, **not** a GREEN claim.
- These are **21 newly authored parameter-expanded pytest cases**:
  Memory 4, Planner 4, Privacy 3, V3 10. None is counted as an independent local PASS.
- Frozen PR #8 Memory contract blob `b6e93821ecd69270a7634aceb20775dc36e9953c`;
  Planner contract `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`;
  PR #5 V3 contract `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`.
- No paid/external GPU/compute/API, Candidate or weights, protected V2
  opening, credentials, physical-PC action, real ToolBackend dispatch,
  automatic permission/promotion, irreversible effects or main merge.

**Next:** Verify exact-head six-job CI for both PRs; fix only observed
failures. Continue non-UI Memory lifetime/expiry/CAS and Planner recovered
READ/FAILED/BLOCKED isolation; privacy and V3 local-only authorization guards.
All claims remain **NOT_PASSED** until their specified evidence gates succeed.
