# Run872 — Non-UI bounded SQLite bootstrap and detached schema capture

Reporting observation (UTC, not trusted action clock): 2026-11-14T12:50:00.593Z. ARK/JARVIS **NOT_PASSED**.
Branch: `research/jarvis-foundations`; Draft PR #8 remains an isolated,
unmerged core workstream. This report concerns **synthetic, disconnected**
SQLite fixtures; no actual permission grant, approval, effect or user data.

## Work basis and source changes

Initial invocation HEAD: `a3d687ad888138dc63d4da3d0fc9321a278188f0`.
Prior checkpoint CI [#43594513344](https://github.com/Iam-2squared/ark-ai/actions/runs/43594513344):
all six Ubuntu/Windows × Python 3.11–3.13 jobs **GREEN**, confirmed per-job.

1. **Disconnected Memory witness constructor:**
   `dbc27c2d8ffcf48d8cc3ae1cd4fe7cf1350af032` changes the
   `sqlite_master` create-only empty-catalog test from unbounded tuple
   materialization to `SELECT 1 ... LIMIT 1`, **within the existing
   BEGIN IMMEDIATE** transaction. Any planted foreign table/view still denies
   initialization. `35cb78111d9e53755e5a4a32c1b8c3296e796091` adds
   three new synthetic tests: bounded exact SQL probe, post-path-preflight
   TABLE injection and VIEW injection. Existing DDL, CAS, event history
   and owner scopes were not changed.
2. **Detached SQLite schema seal:**
   `b62e9ab02fef9e980a379b2d73c59c6cc9e96acd` changes the
   `PRAGMA database_list` admission from `tuple(...)` to
   `fetchmany(2)`. Only a single main database is accepted, so a
   two-row upper read is sufficient; rejected attached databases remain
   attached and an idle caller connection is left idle.
   `c774d3ae2cacbad879e9d02e2d5becd707d36e01` adds three
   new synthetic cases: 1, 2 and 3 attached databases, denial on
   both capture and review, explicit detach and subsequent revalidation.
3. **CI semantics-preserving correction:**
   Intermediate [#43596366738](https://github.com/Iam-2squared/ark-ai/actions/runs/43596366738)
   failed all six on **Ruff E501**, a 101-character Memory witness line.
   `f1800295b96e9318fd292665e03017eba48e5569` wraps the identical
   boolean expression without relaxing any admission checks.
   The latest source+test CI is
   [#43596487033](https://github.com/Iam-2squared/ark-ai/actions/runs/43596487033);
   its final six-job outcome must be checked independently, not inferred.

**Validation scope:** six new test cases authored. The four changed
files were reread from the actual branch; none has a line over 100 characters.
Local disposable SQLite smoke verified blank/TABLE/VIEW existence probe and
the ability to attach/detach three in-memory databases while query_only
remains enabled. No complete local pytest, Ruff, physical-PC, GGUF,
external writer identity, WAL custody, rollback resistance or real executor
test has been claimed. Exact-HEAD six-job CI is a separate gate.

## Independent core integration boundary audit

A read-only review of `agency/registry.py`, `agency/policy.py`,
`agency/disconnected_write_slot_ledger.py` and
`agency/disconnected_atomic_preaction_ledger.py` confirms the critical
separation of local mock authority from trusted real effects:

- ToolRegistry's immutable revision/binding and PermissionGate's exact
  capability/scope gate alone do **not** establish durable identity, consent
  or trusted-clock approval. The direct PermissionGate token set is process
  local and must never be mistaken for restart-safe authorization.
- The disconnected WRITE Slot Ledger serializes **synthetic** reservations;
  the atomic intent/audit fixture commits two local SQLite records together.
  Neither proves exactly-once external side effects or a user-authorized
  one-shot token. Cross-store atomicity is still unresolved.
- Safest integration order: exact-head GREEN on each lower-level gate,
  separate retained approval/occurrence custody and audit-before-action
  evidence, restart UNKNOWN quarantine, then a **disconnected mock**
  executor only. Do not bridge an external executor or open the protected
  V2 evaluation here.

No frozen V1/V2/Local UI/Launcher contracts/evidence modified. PR #5 is
Draft/unmerged under its explicit gate; UI PR #9 remains Draft/unmerged
and **no frontend/UI work was performed**. No training/Candidate generation
or promotion, new credentials, paid compute/service, real tool side effects,
or main merge.

## Next plan / 今後の方針

1. Confirm run #43596487033 and exact latest checkpoint SHA across all six
   platforms; address any actual failure through the normal GitHub Contents API.
2. Investigate Memory/ActionAudit final-WAL/SHM-client-close and
   COMMIT-UNKNOWN in independent disposable processes; never blind-retry.
3. Verify Planner durable UNKNOWN/manual recovery and Memory coherent CAS,
   expiry and retained witness alignment.
4. Advance Personal Context revocation/expiry, proactive/observation back-end
   fixtures independent of any in-flight Planner/Memory CI.
5. Only after prerequisites GREEN, connect registry-bound exact PermissionGate,
   retained occurrence/audit and a disconnected mock executor in isolation.
