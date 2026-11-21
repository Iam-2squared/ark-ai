# Run418 — disconnected post-COMMIT and final-witness continuity

This engineering note records **source, regression and safety scope**, not
training PASS, signed timestamp, permission, live execution or human approval.

## Exact work basis and gates

- Opening PR #8 head was `797eb1675c68cb02b56cb66e1e21ca267014d6ec`
  (Run417 five-package document; CI **#1069 / 40179116377 SUCCESS**).
- Working branch `research/jarvis-foundations`, **Draft PR #8**, no main merge.
- Independent PR #5 remains Draft/unmerged/NOT_PASSED. Frozen V1/V2/Local
  UI/Launcher and V3 contracts, Memory v1 and ActionAudit v1 DDL untouched.
- All fixtures use disposable local SQLite, caller-supplied clock, inert
  registry/Planner. No ToolBackend, paid GPU, API, PC, media, notification,
  Candidate, authorization, consent, deletion or external side effect.

## Five source+regression packages (45 parametrized pytest cases)

### A — Memory DELETE and expired purge after SQLite COMMIT (+12)

Source `src/ark/memory/sqlite_store.py` at
`f2e05414295c055eb35fe4fb758086d1d88f4b9e`.
Test `tests/test_memory_delete_purge_commit_fence_run418.py` at
`1633c107b0020b6c2f6c1957ddd91edcf5c1cae4`.

Bind original caller owner/namespace and SQLite path identities before
transaction. After the SQLite context manager has successfully committed,
reject a clean DELETE/purge return if the source or caller scope was modified
or replaced by an equal-valued carrier. The late diagnostic **cannot undo an
already committed deletion or its content-free event**. Tests inspect the
durable row/event pair directly after injected post-COMMIT drift and verify
normal single-operation success. Neither deletion authorization nor a
replay-safe retry is inferred.

### B — Retention inventory first/last hash boundaries (+10)

Source `src/ark/personal_context_retention_review.py` at
`df72763298325c330c3542121acfba23d60728f8`.
Test `tests/test_retention_first_hash_and_final_result_run418.py` at
`2178e0420807908c487f5d6fd8f9d3217f906643`.

Pin owner/namespace exact carriers and both independent local SQLite
sources **before the first scope hash**, then recheck them after that callback.
Also reject row/scope/source retargeting during the final inventory
SHA-256/hexdigest or frozen-result constructor. Return remains content-free,
read-only, non-authoritative. Cross-store privacy veto and Memory reads are
still **not atomic**; current time and consent remain untrusted.

### C — Plan-wide recovery output construction (+5)

Source `src/ark/agency/synthetic_write_plan_recovery_review.py` at
`836969694bc54a648b41e3f8ac4be94affb79ddd`.
Test `tests/test_plan_recovery_final_result_epoch_run418.py` at
`d11793fc8e67c67db8e212087cd6e45d66bc64f4`.

After constructing the returned frozen plan-wide review, recheck original
Planner/Registry/SQLite-source inputs and all per-WRITE witness carriers.
Reject equal-valued replacements of the final step tuple, uncertain-WRITE
tuple or topology digest and reflective changes to earlier reviews. RUNNING
and reserved-PENDING writes remain uncertain; diagnostics never authorize
automatic replay, real tool dispatch or a fabricated external outcome.

### D — Synthetic clock constructed witness across generator completion (+7)

Source `src/ark/agency/synthetic_clock_sequence_review.py` at
`ee35f3a5dde14d073ca07689aa7b52aef6f0bd78`.
Test `tests/test_clock_constructed_result_generator_epoch_run418.py` at
`317732d41d33d5daf739ec81c16b902235d35cb1`.

Pin the *locally constructed* clock result's fields and exact text carriers.
A malicious iterable can reflectively alter the result when yielding a next
sample or during final StopIteration/finally; both now reject. Caller-provided
clock origin is not authenticated or signed, and no permission is produced.

### E — Observation-to-trigger bounded ingress and result custody (+11)

Source `src/ark/proactive_observation_lineage_fence_review.py` at
`9e0e352424a462520df981c33a95273490bd0970`.
Test `tests/test_observation_trigger_budget_and_final_result_run418.py` at
`d0033f24626c9060167a86785b24daa3af6fc9bf`.

Standalone untrusted source identifiers must be exact, nonblank, valid UTF-8
and at most 1024 characters, matching the existing ObservationEnvelope budget.
The correlation entry rejects more than 256 envelopes and unbounded selection
IDs **before** invoking the costly lineage or SQLite reviewers. After the
diagnostic result is constructed, check original envelope, trigger receipt,
retained-policy inputs and exact output digest/ID carriers once more. These
constraints do not establish source authenticity, notification readiness,
human consent or external action authority.

## CI precision and known limits

- Auto-triggered package test commits:
  - Memory `1633c107b0020b6c2f6c1957ddd91edcf5c1cae4`:
    **#1071 / 40179847950**.
  - Retention `2178e0420807908c487f5d6fd8f9d3217f906643`:
    **#1073 / 40179975244**.
  - Planner `d11793fc8e67c67db8e212087cd6e45d66bc64f4`:
    **#1075 / 40180078670**.
  - Clock `317732d41d33d5daf739ec81c16b902235d35cb1`:
    **#1077 / 40180189276**.
  - Observation `d0033f24626c9060167a86785b24daa3af6fc9bf`:
    **#1080 / 40180530603**.
- At the next sampled runs list, #1071 completed SUCCESS six jobs and
  #1075 was FAIL due to a Windows 3.12 existing frozen Local UI
  `tests/ui/test_server.py::test_cross_origin_reads_and_writes_rejected[headers2]`
  `ConnectionAbortedError [WinError 10053]`; Ubuntu 3.11/3.12/3.13 and
  Windows 3.11/3.13 succeeded. The local server was not changed.
  #1073/#1077 and final #1080 were not yet whole-matrix verified.
  **Do not infer GREEN for a later HEAD from any prior success.**
- Expected baseline: Run417 documented Run416's 2349 plus 52 = 2401;
  adding 45 cases suggests **2446**, which is a calculation, **not a test
  pass claim** until the exact-head pytest and all six CI jobs confirm it.
- All changes stay within their distinct modules. No new workflow was
  manually dispatched and failed CI must remain in history.

## Next plan / 今後の方針

1. Check #1071/#1073/#1075/#1077 **at their exact HEADs**; read failing job
   logs and fix only the narrow defect by normal Contents writes, switching
   independent lanes while checks execute. Do not duplicate workflow runs.
2. Expand multi-WRITE retained-PENDING / UNKNOWN crash-recovery with partial
   independent SQLite history loss and audit-before-action ordering.
3. Develop Memory CAS/expiry coherent read and Personal Context privacy
   retention/consent-review diagnostics without v1 DDL changes or real erase.
4. Continue offline Registry/Issuer/clock, startup readiness,
   Observation/Scheduler fixture interfaces and V3 free-only path/provenance
   and reproducibility gates.
5. Keep **real dispatch, hardware/media access, external exactly-once,
   trained Candidate and main merge disabled** pending their distinct human
   authorization and externally verifiable integration evidence.
