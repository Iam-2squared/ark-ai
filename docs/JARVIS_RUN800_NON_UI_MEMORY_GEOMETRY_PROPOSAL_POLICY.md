# ARK Run800 — Memory retained-CAS geometry and immutable proposal policy (NON-UI / FREE-ONLY)

**Work-basis HEAD:** `beb7b4bc04356c75f7240daeb2e154a4964bc3c0` on Draft PR #8 `research/jarvis-foundations`. **Prepared:** 2026-11-12T05:52:41.274+09:00 (Asia/Tokyo wall-clock; not trusted audit timestamp, external identity, or human approval). **Overall ARK/JARVIS: NOT_PASSED.**

## Package A — reject geometrically impossible Memory generation witnesses before SQLite

- Source `src/ark/memory/retained_generation_fence.py` updated by ordinary GitHub Contents API, commit `322fa170c600550e44b4cda8027f5d093c6c3e98`.
- Regression `tests/test_memory_retained_generation_geometry_run800.py` created in `636e30256a7b4b7867a0634976b8a20e4912d5bc`: **9 parameterized test cases** (seven impossible shapes rejected before any private read, two actual multi-lifetime positive cases).
- Existing input checks already required exact scalar types, bounds and a Boolean revision-reuse marker, but a forged exact-shaped retained receipt could report zero generations with a live row, a terminal generation with too few events, or a second generation without its preceding delete. A bounded event count is not by itself a feasible historical event sequence.
- Added necessary lower bound: for zero generations, there can be no events or live row. For **G > 0** generations, at least `2*G - 1` events are needed for a live generation, plus `R - 1` updates for live revision `R`; a terminal last generation instead requires `2*G` events. These are **necessary**, not sufficient conditions; original read-only full SQLite review still decides the exact event history.
- No v1 schema, CAS API, actual Memory row, lifecycle data, consent, authorization or automatic COMMIT-UNKNOWN retry changed. These guards do not authenticate the retained receipt or prevent concurrent changes immediately after the read-only comparison.

## Package B — make the local improvement-proposal transition grammar immutable

- Source `src/ark/agency/disconnected_proposal_lifecycle.py` commit `848b7d4b6854cbc8809243226ecf05c2710e8370`.
- Regression `tests/test_disconnected_proposal_policy_custody_run800.py` commit `4d2fe8299dacb208ea5e61e534f8a04a2f57df3d`: **10 cases** (three in-place mutations, five protocol rebindings, one persisted terminal-reopen rejection, one ordinary lifecycle).
- The previous `_ALLOWED` grammar was a mutable dict, with `_ORIGINAL_ALLOWED` pointing to that same mutable object. In-place mutation could therefore broaden a terminal transition while still satisfying identity-only checks. `MappingProxyType` now owns the internal fixed mapping literal, preventing in-place additions/replacements. Genesis, ID/digest validators and event budget are also pinned at import-time in the existing protocol check.
- Accepted proposal states remain **descriptive mock lifecycle states only**. `ACCEPTED_FOR_IMPLEMENTATION` is not authenticated human review and grants no code edit, training, tool dispatch, protected evaluation or Candidate promotion. The global CAS event-store schema is unchanged; no source changes under UI branches.

## Validation / CI evidence boundaries

- Earlier [Run799 checkpoint workflow #43093515609](https://github.com/Iam-2squared/ark-ai/actions/runs/43093515609) was **IN PROGRESS** when inspected. Ubuntu 3.11 and 3.13 were GREEN; Ubuntu 3.12 pytest job `130776371290` **FAIL**, Windows 3 jobs still running. Ruff on that failing job was GREEN; concrete pytest failure text could not be retrieved from the connector at this point (log endpoint timed out / returned unavailable). **Do not claim Run799 GREEN**. Diagnose the real error before any semantics-changing repair.
- Latest known earlier completed package workflow [#43092597442](https://github.com/Iam-2squared/ark-ai/actions/runs/43092597442) **SUCCESS** at its earlier HEAD, not proof for this run.
- Newly enqueued auto-CI for source/tests: [#43098102418](https://github.com/Iam-2squared/ark-ai/actions/runs/43098102418), [#43098167443](https://github.com/Iam-2squared/ark-ai/actions/runs/43098167443), [#43098248865](https://github.com/Iam-2squared/ark-ai/actions/runs/43098248865), [#43098309544](https://github.com/Iam-2squared/ark-ai/actions/runs/43098309544); **QUEUED at inspection**, **latest exact-head 6/6 GREEN NOT VERIFIED**. No duplicate workflow manually launched; no local full pytest/Ruff or hardware/model attestation claimed.
- **Total NEW submitted tests: 19.** Test counts describe committed cases, not completed validation.

## Frozen contracts and explicit non-authorities

Frozen V1/V2/Local UI/Launcher, V3 Contract 1 and protected V2 final evaluation remain untouched. Draft PR #5 remains gated/unmerged and Draft PR #9 remains untouched/unmerged with **all new UI work paused**. This run used no new paid/potentially billable service, external GPU or model training, physical target hardware, real ToolBackend, new credential, automatic uncertain WRITE replay, Candidate generation/promotion, human approval or main merge. Local fixture digest identity is not provenance, cross-store atomicity or a trusted clock.

## Next plan / 今後の方針

1. Resolve the observed Ubuntu 3.12 Run799 pytest failure using an actual accessible job log or specific failure artifact; preserve existing fault-injection tests and do not infer it was flaky.
2. Confirm all six exact-head CI jobs for Run800; on failure, fix minimal semantics-preserving issues through normal GitHub Contents API and work another independent non-UI lane while CI runs.
3. Continue Memory event/row/expiry coherent retained review, generation ABA, and manual-only COMMIT-UNKNOWN reconciliation. Use immutable protocol inputs without expanding frozen Memory v1.
4. Connect only GREEN lower-level Planner, registry-bound PermissionGate, durable audit-before-action, occurrence replay quarantine and disconnected/mock executor boundaries. No live WRITE or automatic retry.
5. Maintain private Context/Observation/Proactive and V3 free-only guard work; preserve Draft gates and UI pause. Overall ARK/JARVIS **NOT_PASSED**.
