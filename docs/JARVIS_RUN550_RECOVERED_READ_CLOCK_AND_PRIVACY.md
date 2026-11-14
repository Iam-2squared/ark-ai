# Run550 — Recovered READ registry join, generation event clock floor and privacy denial custody

**Scope:** Isolated, reversible, disconnected foundations on PR #8 (Draft/unmerged). The changes below use local synthetic inputs and never dispatch a real ToolBackend, claim external outcomes, authenticate user consent, or authorize retry, WRITE, model training or paid compute.

## 1. READ recovery ↔ ToolRegistry ↔ SQLite reconciliation

- Source `src/ark/agency/disconnected_recovered_registered_read_join.py` saved at `2009c5cf7ccc6446c4892c0d347ef2ac1f91afb8`. New opt-in deny-only report joins the recovered mock DAG and retained common-request SQLite READ receipt tip to matching registered READ step identities (distinct `act_` action and `req_` fixture), verifying each child's canonical digest and the Registry/PermissionGate-bound fixture review. Only `SUCCEEDED` steps require registered receipts; `FAILED`, `NOT_STARTED`, `RUNNING` or `UNKNOWN` steps cannot be silently treated as executed.
- Regression cases in `tests/test_recovered_registered_read_join_run550.py`, commit `ab204dba81b7daf45b2e14feb472fc11785b9d8c`, cover full/partial/empty-success graphs, missing/duplicate/reversed registered evidence, invalid result/operation, stale retained plan or journal, expired and invalid clock inputs, same-request binding, changed SQLite rows, forged child digests, late reentrant mutation and false-authority flags.
- Lower-level Reader/Registry witnesses are separately verified; their equality is **not** cross-store atomicity, a historical signed actor, independent consent, real tool execution, or an exactly-once effect claim.
- At documentation preparation, exact test-head [CI 41401799686](https://github.com/Iam-2squared/ark-ai/actions/runs/41401799686) had Ubuntu 3/3 GREEN and Windows pending; do not represent incomplete exact-head CI as 6/6 GREEN. Further hardening: explicitly require recovered journal request identity to equal the DAG plan request identity before treating the joined report as coherent.

## 2. Memory ABA diagnostic event-clock continuity

- Source `src/ark/memory/cas_generation_review.py` commit `b101a0e6ea59b450dbeb93d573abf0453f87d916` now rejects a decreasing local `occurred_at_ms` anywhere in a generation history. It matches the nondecreasing event-clock condition already enforced by opt-in generation-fenced CAS observations. This is not trusted clock attestation or change to frozen Memory v1 contracts or storage schema.
- Regression file `tests/test_memory_generation_clock_floor_run550.py` commit `7e6474d1d640d7a12eb05c423d4ab4f3dc93c5ba` covers backdated final updates even with matching row timestamp, backdated intermediate events, delete/recreate rollback, and valid same-clock events.
- Exact test-head [CI 41402266701](https://github.com/Iam-2squared/ark-ai/actions/runs/41402266701) had Ubuntu 3/3 GREEN and Windows pending at preparation.

## 3. Privacy-safe retention inventory denial descriptors

- Source `src/ark/personal_context_retention_review.py` commit `d0c65d2aed5c2dde8b26c38ddf7eddcd6e7b862c` pins original class-level `erasure_completed`, `deletion_authorized`, and `context_use_authorized` descriptors before any caller-generated report; a dynamically replaced False-valued getter cannot become a trusted authority baseline. The final review compares the exact original descriptors as well as content-minimized result fields.
- Regression file `tests/test_retention_denial_descriptor_custody_run550.py` commit `a68dbfcc0e2c768a7ced253bba5afeea4fff16b3` covers all three prior false-only descriptor substitutions, two chained substitutions and an unaffected normal private inventory.
- Exact test-head [CI 41402691483](https://github.com/Iam-2squared/ark-ai/actions/runs/41402691483) was running at preparation. This review never deletes data or claims GDPR/forensic erasure.

**Evidence classification:** newly *authored, parameter-expanded* test cases are not independent local pytest PASS counts. Only individual finished GitHub jobs support cross-platform CI statements. The execution environment's wall clock, fixture hashes, synthetic identities, SQLite tips and local denied-property checks provide no external provenance or user authorization.

## Next plan / 今後の方針

1. Close every outstanding source/test CI on its exact HEAD, inspect any failing job logs, apply only semantics-preserving changes via the normal GitHub Contents API and never force-push.
2. After the initial join's exact-head CI is GREEN, require exact plan-request ↔ recovered-journal-request binding with synthetic mismatch regression tests; independently inspect recovered step result scope, registry identity and retained custody.
3. Continue Planner FAILED/BLOCKED persistence, COMMIT-UNKNOWN manual Memory reconciliation, restart-safe occurrence uniqueness and trusted-clock audit-before-action. No automatic retries or live execution.
4. Maintain frozen Memory/Planner/V3 contracts, V1/V2/Local UI/Launcher evidence, Draft PR #5/#8 gates, protected V2 final evaluation, and all user-approval and free-only boundaries.


## Run550 follow-on — Cross-plan recovered request binding

The initial join's exact test-head [CI 41401799686](https://github.com/Iam-2squared/ark-ai/actions/runs/41401799686) subsequently completed **6/6 GREEN** across Windows/Ubuntu Python 3.11–3.13. Its isolated review revealed a remaining local-custody gap: an otherwise valid registered receipt could be correlated with an unrelated DAG plan's `req_` request, since steps and operations were identical and the two independently valid plans had distinct plan IDs.

- Source `src/ark/agency/disconnected_recovered_registered_read_join.py` at `424d644c8a4a7d0a4d6503d2ef004b6d5f275e7a` now requires the recovered journal's `request_id` to exactly match the detached plan's `request_id` before accepting the report.
- `tests/test_recovered_registered_read_join_run550.py` appended **two parameter-expanded cross-plan replay rejection cases** at `139d5dbea1f1a8434e92fae1fca9b72919666a38` for complete and partially failed recovery. The joining tool still cannot dispatch or attribute real-world execution.
- Later exact-head [CI 41403083913](https://github.com/Iam-2squared/ark-ai/actions/runs/41403083913) was **QUEUED** when this addendum was prepared. Do not infer its GREEN outcome from the earlier successful initial-head CI.

This is local-only identity continuity, not a proof of actor authenticity, transactional read across databases, trusted time or permission to retry.
