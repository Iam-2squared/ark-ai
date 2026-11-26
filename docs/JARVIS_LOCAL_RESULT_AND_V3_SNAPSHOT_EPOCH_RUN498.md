# ARK disconnected result custody and V3 snapshot epochs — Run498

## Scope (synthetic, reversible, zero-cost)

This checkpoint documents implementation-level contracts, not operational
authorization or proof of end-to-end JARVIS. No new external integration,
credentials, GPU run, paid provider, live camera/microphone, or real Tool action
was introduced. All results below remain local assertions.

## Detached lexical retrieval: return-time custody

- `offline_context_search.search_offline_context` returns bounded local
  excerpts, not an authenticated personal-data or consent decision. In
  `src/ark/offline_context_search.py`, the original preview/hit types and
  exact fields are rechecked after denial-only authority getters. Getter
  callbacks that change the source row, preview digest, or nested hit are a
  rejection. `external_export_authorized`, `tool_dispatch_authorized`,
  `retention_authorized` and `consent_verified` must all be exactly False.
- `offline_text_index.search_offline_text` returns local document identifiers
  and integer scores, not snippets or independently authenticated custody.
  Result and hit carriers remain exact after the `identity_authenticated`,
  `disclosure_authorized` and `revocation_verified` getters, all of which
  must be exactly False.
- `personal_context_offline_preview.build_offline_context_preview` now
  repeats source and constructed-result epoch checks after the final
  privacy-authority getter. This closes a late reflective mutation window
  without changing its owner/scope/TTL/byte-budget rules.
- `agency_synthetic_lane_selector_review.review_disconnected_work_lanes`
  now rejects synthetic selections whose result advertises execution,
  GitHub-write, or spending permission, and rechecks the work graph/result
  following the last authority callback. A caller's `claimed_green` string
  does **not** become CI attestation, nor permission to write to GitHub.

The output shape and deterministic scoring/selection contracts remain
unchanged for ordinary inert fixtures. Reflection-based injected getters are
fault-injection tests, not a model of hostile interpreter control.

## V3 local snapshot/probe coherence (separate Draft PR #5)

`src/ark/learning/identity.py` now retains a bounded directory metadata
epoch before hashing a materialized *local* HF snapshot, then rechecks that
epoch after hashing the separately supplied chat-template probe. This catches
ordinary file replacement or membership drift between model-manifest and
probe review. The initial and final probes still cannot establish external
Hub commit identity, remote authenticity or hostile-OS writer resistance.

The test fixture contains **fake tiny bytes**, not actual model weights.
No Candidate generation or protected V2 evaluation is authorized by a
passing test or a matching local SHA.

## Regression coverage introduced

- `tests/test_offline_context_search_authority_run498.py`: 9 cases.
- `tests/test_offline_text_index_authority_run498.py`: 8 cases.
- `tests/test_personal_context_preview_final_epoch_run498.py`: 4 cases.
- `tests/test_synthetic_lane_selection_authority_run498.py`: 7 cases.
- In PR #5, `tests/v3/test_hf_probe_snapshot_epoch_run498.py`: 5 cases.

**33 new cases** in **5 independent work packages**. A new case is
not declared GREEN until its exact source/test HEAD passes the complete CI
matrix. Earlier green runs are evidence only for their respective commits.

## Integration gate: still NOT_PASSED

1. Pin an independently authenticated authority for consent, revocation,
   trusted clocks and data custody before any private-context disclosure.
2. Bind the exact registered Tool capability, explicit human approval,
   immutable occurrence identity, append-only audit and durable recovery
   before any effectful executor is considered.
3. Preserve UNKNOWN WRITE quarantine across process restarts; do not infer
   at-most-once external effects from local-only hashes or SQLite receipts.
4. Keep PR #5 Draft and blocked on actual approved dataset, immutable
   model/runtime identities, budget/billing evidence and explicit gates.
5. Keep frozen V1/V2/Local UI/Launcher plus Memory/Agency/V3 contracts intact,
   and require final-head exact-matrix GREEN before dependent integration.

No changes to frozen contracts are proposed by this report.
