# Run762 — Non-UI atomic pre-action fixture, Memory ingress and registry binding

Date: 2026-11-10 JST. Branch `research/jarvis-foundations`, Draft PR #8.
Initial work-basis HEAD: `280cba70cf9fb7b19378a7d8f8532d1f66147efa`
(Run761, CI #42795412676 **COMPLETED SUCCESS 6/6**).
This document is non-normative implementation evidence, **not a PASS gate**.

## NEW — three independent packages (all FREE-ONLY)

1. **Single-store disconnected atomic intent and audit.**
   - `src/ark/agency/disconnected_atomic_preaction_ledger.py`
     ([source commit e2068c77](https://github.com/Iam-2squared/ark-ai/commit/e2068c77849cdde0b9d25def10c562d7bcb3e683)).
     An opt-in, separate local SQLite fixture reserves one digest-only occurrence
     and its pre-action audit in the **same BEGIN IMMEDIATE transaction**,
     subject to caller-retained count/tip CAS. Readback rejects missing,
     duplicated, edited or orphaned audit rows and schema drift.
     Input paths refuse links/unsafe sidecars on preflight; local path checks
     are not atomic protection against rename races. Evidence digests are local,
     **not independently authenticated**.
   - `tests/test_atomic_preaction_single_store_run762.py`
     ([test commit 87070e0d](https://github.com/Iam-2squared/ark-ai/commit/87070e0d43ee1f2a6414c101bebb9a9605fd8f53)):
     10 parameterized cases for create/reopen, exact CAS, row/audit tampering,
     real child-process uncommitted rollback, COMMIT-UNKNOWN manual readback,
     independent-process race and denied authority. No ToolBackend is exposed.
   - A 6/6 CI failure at old source/test HEAD #42802418996 identified **Ruff B904**
     (a missing-ledger rejection inside `except FileNotFoundError`).
     Corrected to explicit `raise ... from None` at
     [a7a33851](https://github.com/Iam-2squared/ark-ai/commit/a7a33851d7bcee12354035248e1877bcdd78a4f2).
     Earlier CI failure is not considered a source PASS.

2. **Memory write ingress revalidation after reflective modification.**
   - `tests/test_memory_write_revalidated_ingress_run762.py`
     ([417faace](https://github.com/Iam-2squared/ark-ai/commit/417faace4f4610db38e25ff080bd9bd5a8b93aea)),
     14 cases for originally valid frozen MemoryWrite/MemoryScope values
     subsequently changed to blank, subclass, excessive or invalid text,
     metadata or expiry. Requires *zero* durable event writes on invalid ingress.
   - `src/ark/memory/sqlite_store.py`
     ([b8f62d00](https://github.com/Iam-2squared/ark-ai/commit/b8f62d0027fb6ab60f630a41e7d68ceeaca841bc))
     now revalidates the original v1 scope/write constraints and an exact
     UTF-8 text snapshot **before** identifier hashing, clock or SQLite open.
     No table/schema migration, expiry policy modification, UI or frozen
     contract change. This narrows an actual ingress weakness; it does
     **not** make hostile in-process code, filesystem paths or a clock trusted.

3. **Registry-bound synthetic WRITE identity.**
   - `src/ark/agency/disconnected_atomic_registry_bridge.py`
     ([84563c0a](https://github.com/Iam-2squared/ark-ai/commit/84563c0ac6839584f3d1369445fd9f51f47c397d))
     is a separate, non-dispatching bridge deriving an inert claim from an
     exact ToolRegistry/ToolCall WRITE binding. READ registrations and
     malformed occurrence IDs are rejected. A request digest cannot substitute
     for independently reviewed approval or ownership.
   - `tests/test_atomic_preaction_registered_bridge_run762.py`
     ([83f68adb](https://github.com/Iam-2squared/ark-ai/commit/83f68adb0fe5ee8fadad2fd36521e373ad639995)),
     6 cases; no backend may execute, no WRITE grant appears in the
     snapshot, mutated/patched registry method is refused.

**New cases:** 30 pytest parameterizations in three test modules, subject to
exact-head CI verification; this is not a claim of 30 PASS.

## Limitations / integration hold

- **One SQLite DB** makes its *own intent + audit rows* atomic, but existing
  Memory, Planner, occurrence, audit, privacy, proactive and READ journals
  remain **separate stores**. No distributed transaction or external atomicity.
- A successful SQLite COMMIT followed by lost response is **COMMIT-UNKNOWN**;
  the retained witness may be stale, and local DB readback cannot authenticate
  a separate issuer. No automatic retries or promotion to real execution.
- The bridge derives registry action identity but has **no signed actor,
  trusted approval issuer, authenticated clock, consent proof, or independent
  custody**. No actual backend, notification, sensor or network call.
- Not a production execution feature: `AtomicPreactionSnapshot` has only
  deny-only flags and the ledger exposes **no** `execute()` method.
- The user-paused frontend PR #9, gated V3 PR #5, main, frozen V1/V2/Local UI/
  Launcher evidence, and protected evaluation boundary remain unchanged.
  No billable compute, paid service, physical PC action or main merge.

## CI discipline and next plan

- Verified pre-change basis: #42795412676 on `280cba70...` =
  completed **6/6 GREEN**.
- #42802418996 on `87070e0d...` = **6/6 FAIL**, Ruff B904; 
  #42802806550 on `b8f62d00...` = **6/6 FAIL** from the same issue.
  Both are old source HEADs; normal Contents API fix saved at `a7a33851...`.
- Source/test and checkpoint-result CI at later HEADs must be separately
  verified. Do not infer a later PASS from earlier results, invent run IDs or
  fire duplicate workflow dispatches.

Priorities: (1) establish latest exact-head Windows/Ubuntu × 3.11–3.13 CI,
repair real failures with minimum semantics-preserving changes;
(2) strengthen independent retained high-water and Memory CAS/ABA/
COMMIT-UNKNOWN evidence;
(3) specify a reviewed cross-store startup quarantine / manual resolution
protocol *before* any execution coupling;
(4) continue privacy-safe Personal Context, Planner persisted recovery,
observation and FREE-ONLY V3 path/identity guards on independent non-UI lanes.
