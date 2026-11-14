# ARK JARVIS Foundation — Run431 Fault Matrix

**Scope:** three isolated, reversible, no-cost hardening packages on Draft PR #8.
This evidence is **not** a completion, operational readiness, consent,
trusted clock, external outcome, or automatic WRITE-retry authorization.
Sources and tests operate only on disconnected synthetic / disposable SQLite.

## 1. Last Planner recovery is a callback, not a trusted observation

- Source: `src/ark/agency/synthetic_write_plan_recovery_review.py` at
  `44e5774dfd440e6525d2e25105f3211c8489ad4d`.
- Regression: `tests/test_plan_final_journal_recheck_epoch_run431.py` at
  `82fcc97d886a2336fc122d25242b79ee9e57a31b`.
- Fault: after two per-step snapshots and the final repeat per-step witness,
  a final `journal.recover()` callback rewrites an earlier step's state,
  rewrites a retained digest to a distinct equal-valued string, or retargets
  the original caller's ToolCall/dependency tuple while returning a still
  value-equal baseline.
- Guard: compare the repeat result first, then independently recheck caller
  topology / retained witnesses and all prior review objects **after** the
  last journal recovery. Require exact final plan/tail result types and
  baseline equality. An unmodified RUNNING WRITE still quarantines its
  descendant WRITE through a READ/plan dependency.
- This diagnoses uncertainty; no dispatch is enabled.

## 2. Memory event audit queries preserve original scope identity

- Source: `src/ark/memory/sqlite_store.py` at
  `7023a5f290300eecc6a84f798ad9dd0b06a3d7bd`.
- Regression: `tests/test_memory_events_original_scope_epoch_run431.py` at
  `8ddc336ca20e5d4f554788ee624e72bb9300ce12`.
- Fault: a reflected-frozen `MemoryScope.owner_id` or `namespace` is
  replaced with an equal-text, **different object** on SQLite open, schema
  validation, or event materialization. Value-only checks used to miss this.
- Guard: compare both original caller carrier identities and pinned values
  at the existing read boundaries, including each materialized event.
- Preserves Memory v1 SQL schema, query semantics, ordered create/update
  events, and isolation between different owners; no external privacy
  deletion is performed.

## 3. Post-COMMIT occurrence receipt is not permission

- Source: `src/ark/agency/durable_occurrence_review.py` at
  `e8c5329b6d06a7a487138cc4e014d8da44654695`.
- Regression: `tests/test_occurrence_postcommit_receipt_epoch_run431.py` at
  `71f7262f253fe97ad7fafdaf830095102c7c9d65`.
- Fault: after SQLite has committed a one-time synthetic WRITE reservation,
  a replaced receipt constructor returns an unexpected type, changes the
  request identity, replaces the bound action ID with equal text, or
  reflectively changes the original token/source.
- Guard: preserve the exact original inert receipt class and all five
  return-field carrier identities; verify original inputs again after
  constructing the receipt. A rejected post-COMMIT result **does not**
  roll back the already durable one-shot reservation. Reusing its token
  remains blocked across the fixture store.
- No authenticated issuer, trusted timestamp, external execution or
  exactly-once external outcome can be inferred.

## Verification and boundaries

Initial work basis: Run430 checkpoint
`e4882eee17ffcca5ea629b65cbda142d2ebddce7` (CI #1204 / 40213762744,
all six completed SUCCESS, checked at this invocation's opening). New
Python tests add 5 + 7 + 6 = **18 parameter-expanded cases** across three
independent areas. These counts describe submitted regressions, not passes.

The repository's normal pull-request workflow is triggered by ordinary
GitHub Contents commits. At initial inspection, Run431 source/test workflow
#1205–#1210 was **in progress / queued**; their exact-head results must be
checked separately. Never propagate an earlier HEAD's GREEN to a later one,
and never relabel an actual FAILED historical run as GREEN.

Frozen V1/V2/Local UI/Launcher evidence; Memory v1 and ActionAudit v1 SQL
contracts; V3 Contract 1 and protected evaluation boundaries remain untouched.
PR #5 remains gated Draft / NOT_PASSED; PR #8 remains Draft and unmerged.
No weights/adapter generation, Candidate promotion, paid/external compute,
new credentials, actual hardware access, live sensor/notification service,
personal-data deletion or main merge was performed.

## Next investigations

1. Read exact source/test and checkpoint CI failures (if any); fix the minimum
   validated defect via normal Contents writes, preserving the first failure.
2. Test reservation/result recovery under independent process restarts and
   SQLite partial-history loss, always holding UNKNOWN/RUNNING/reserved
   PENDING WRITEs from automatic replay.
3. Expand Memory cross-process CAS + expiry + event-query coherent epochs;
   do not infer atomicity across distinct SQLite databases.
4. Advance deny-only issuer/clock and Personal Context revocation/retention
   contracts without granting real permissions or shipping private data.
