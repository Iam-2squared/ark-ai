# Run408 — Query-hash epoch, original registry binding and mixed-DAG crash prefixes

Scope: **disconnected local-first synthetic fixtures only** on Draft PR #8.
No live ToolBackend, model inference, external clock/issuer, user approval,
device/sensor capture, notification, Candidate build or paid action is enabled.

## Package A — Memory v1 snapshot query hashing

- Source: `src/ark/memory/coherent_snapshot_review.py`.
- Regression: `tests/test_memory_snapshot_query_hash_epoch_run408.py` (4 cases).
- Prior hazard: the content-free witness's query SHA-256 was computed inline
  inside payload construction. An injected digest callback could reflectively
  mutate the original request, backing Path or previously hydrated record; a
  later JSON callback could restore it before the next integrity check.
- Change: precompute `query_digest` and immediately check request/source,
  scope and all record epochs **before any later metadata/JSON serialization**.
- Negative fixtures: query-hash callback retargets request, source identity, or
  hydrated row; a separate JSON callback would conceal the drift if reached.
  The regression requires rejection *before* that restoration callback.
- Positive fixture: an unchanged snapshot witness remains deterministic.
- Boundary: no Memory v1 table/index/trigger/schema/API change. The witness
  is local continuity metadata, not privacy consent or origin attestation.

## Package B — Synthetic mock binding before the first durable transition

- Source: `src/ark/agency/synthetic_mock_action_cycle_review.py`.
- Regression: `tests/test_mock_original_registry_binding_run408.py` (4 cases).
- Prior hazard: two consistent but forged registry `BoundAction` returns
  could retain their own internally matching `call` and `registration`
  while not referring to the caller's original ToolCall or the registry's
  installed ToolRegistration. Later receipt validation would reject only
  **after** the Planner's durable RUNNING transition.
- Change: require the exact BoundAction type, original `call` object,
  installed registration identity, and unchanged registry revision before
  journal RUNNING. This catches lookalike-but-distinct call/registration,
  foreign revision, and duck-typed return.
- Negative fixtures require zero durable journal transitions, zero occurrence
  reservations, zero audit rows and zero backend calls.
- Boundary: this is not authenticated authorization or a real action proof;
  even an accepted synthetic mock result has `external_outcome_known=False`.

## Package C — Every synthetic crash prefix in a mixed multi-WRITE DAG

- Regression: `tests/test_synthetic_multiwrite_fault_prefix_matrix_run408.py`
  (5 parameterized cases).
- Independent WRITE may reach **synthetic** SUCCEEDED while another WRITE
  stops after RUNNING, reservation, pre-action audit, link, or mock marker.
  A READ bridge and dependent WRITE remain held behind that UNKNOWN root.
- Reopen all four independently committed SQLite files; retain the original
  Planner, occurrence, audit and audit-link witnesses. Require exact retained
  evidence, UNKNOWN non-replay and no external backend invocation for every
  injected boundary. The test never simulates real external success.
- Required distinctions: durable occurrence count varies by crash phase;
  audit and link rows appear only after their actual commit boundary.
  No cross-SQLite atomicity is inferred.

## Package D — Partial history erasure across four SQLite stores

- Regression: `tests/test_synthetic_four_store_partial_prefix_erasure_run408.py`
  (4 parameterized cases).
- Start with two *nonempty* independently committed synthetic WRITE histories.
  Clone the four closed SQLite files into a fresh, disposable test directory.
  First prove the full clone exactly matches all four retained witnesses.
- Delete **one row only in the disposable copy** from, respectively,
  Planner events, occurrence reservations, ActionAudit events or linked
  occurrence/audit events. The independently retained pre-erasure witness
  must force rejection, even though the other stores still contain valid
  histories and both WRITEs remain locally ambiguous.
- The untouched original fixtures must still pass exact retained review.
  Neither partial erasure detection nor local hash agreement attests to
  atomicity across files, external outcomes, authentication or replay rights.

## Evidence and non-claims

- Work-basis before Run408 implementation: Run407 checkpoint
  `ac557ccd5b0608ec31fac3116347e85789c2f994`
  (CI #940 / run `40152571536` independently observed SUCCESS).
- Package source commits:
  `208b383a9487c32ca074eac8221b41a611482427` (Memory),
  `14f05b0b4f9dd06632447daa9bf9dae9cf690d22` (Mock).
- Regression commits:
  `e0e5b8aa6a56fd0a088eccef7285d71a0b8bb67e` (crash matrix),
  `8b0d315b8fb323b6ba6d3d41ca686dcdc7c1db14` (Memory),
  `d84d75eee3e09a898473ce42e2a6bc419a31d551` (Mock),
  `ced693e3912a4002b033aef90672043fda62f973` (partial erasure).
- **Exact-head CI results must be checked separately** before claiming
  all-six GREEN. In-progress or queued status is not a PASS.
- FROZEN V1/V2/Local UI/Launcher evidence, Memory v1 schema, ActionAudit
  v1 schema, V3 Contract 1 and protected V2 final evaluation are unchanged.
  V3 PR #5 remains independently gated Draft/NOT_PASSED.
- No authenticated user issuer/consent, trusted OS/external clock, live
  result receipts, global four-DB snapshot, signed identity, side-effect
  exactly-once guarantee or automatic UNKNOWN replay is established.

## Prioritized next plan

1. Verify the **exact final code+regression HEAD** on Ubuntu/Windows
   Python 3.11–3.13 with Ruff and pytest, correct any actual failure through
   ordinary fresh-HEAD Contents writes, and preserve failed-run evidence.
2. Expand retained witness diagnosis for cross-DB concurrent updates, erased
   prefixes and dependent terminal states; do not infer global atomicity.
3. Continue Memory row/event CAS and expiry-race fixtures, privacy-safe
   Personal Context revocation/scope custody, scheduler/observation contracts.
4. Develop optional, deny-by-default issuer/clock audit-before-action
   contracts, with all real dispatch and notification still disconnected.
5. Keep V3 path/identity/reproducibility approval gates free-only and
   preserve PR #5 Draft/unmerged/NOT_PASSED pending explicit authorization.
