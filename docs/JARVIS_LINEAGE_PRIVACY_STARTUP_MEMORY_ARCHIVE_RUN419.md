# ARK AI — Run419: lineage, private context, startup, Memory scan, recovery archive

**Scope:** `Iam-2squared/ark-ai`, isolated `research/jarvis-foundations`, Draft PR #8. Synthetic/mock-only, local-first, zero-cost. This document records engineering changes, NOT a PASS certification for JARVIS, real backend action, personal-data use, clock provenance, or human permission.

**Work-basis HEAD:** `cccce00c5d293b24850bcecd06d409d2d02bf926` (Run418 checkpoint). Verified CI #1080 / 40180530603, #1081 / 40180643128 and #1082 / 40180912480 all completed SUCCESS on all six Ubuntu/Windows Python 3.11–3.13 jobs at invocation start.

## Five independent source + test packages (37 new cases, including one intentionally skipped probe)

| Lane | Source commit | New tests / cases | Safety behavior |
|---|---|---|---|
| Observation lineage | `e2d2357fe2706715aecd72c30be64709f8fdf56c` | `tests/test_observation_lineage_phase_epoch_run419.py` at `1433da3fcf12f8b76c75144869abb5d6051e8d13` — 6 | Original envelope field carriers pinned through every parent-link, JSON, SHA-256 and resulting witness phase. Metadata-only; source hash is not attestation. |
| Personal Context reuse | `da70283d0e27d8bf67f6e2edd668ffb029f216c5` | `tests/test_context_reuse_exact_carriers_run419.py` at `af2d352a616153c47864388decfc33a5086bfea5` — 11 | Original request/policy/cached items, Memory/revocation Path carriers pinned before constructors and through result construction. No data-use consent or disclosure. |
| Startup readiness lease | `841ab26d90d97ccb45c75c9ffec04437ae51573a` | `tests/test_startup_exact_requirement_epoch_run419.py` at `ed8308e9bf4d22417257c117e42fdd7f445886b4` — 7 (one `failure_code=None` probe intentionally skipped by fixture) | Original requirement carrier pinning before reentrant shape callbacks, component value identities and post-construction check. No live startup authority. |
| Memory v1 bounded lexical search | `0bb6360e855611ba5fbc72ed79ab40302d4c8ae3` | `tests/test_memory_search_scan_budget_run419.py` at `33643c1cd0f7b572321b3f0c269dc0a7d984a849` — 8 | `fetchmany(10001)` and rejection for >10,000 scoped rows **before hydration**; bounded ranking, no Memory v1 DDL change or implicit purge. |
| Detached WRITE recovery archive | `2c6b7c1a9d66a15d54d6b404d1b3f0cdf31afeae` | `tests/test_recovery_archive_decode_epoch_run419.py` at `b31b39a53fed3d3c3adc7d73adef9f6cd4c16d5e` — 5 | Exact archive bytes/digest carrier custody across digest, decode, canonical shape checks and result; bounded fail-shut on recursive JSON instead of leaking parser exceptions. No ToolBackend invocation. |

**Test-only corrections retaining strict production checks:** observation hash fault hook originally matched a literal backslash-zero, not the actual NUL-delimited hash label; fixed at `a1022ddfe6b2fb3b6bdb86cf96add73ea5d72b70`, followed by Ruff UP034 correction at `f8bc25888970bccc0f7c8fca5e1fd58868ae433f`. Memory lexical ranking ties sort on hashed `memory_id`, not `source_id`; test expectation corrected without source semantics change at `43b28a18e5b513ddf2b1e227cb780f7b89be1127`. Recovery test unused `json` import (Ruff F401) corrected at `30f83add5cafde8ad89763825b560587e7df42fe`.

## CI and evidence fidelity

- Observation source **#1083 / 40182291953 SUCCESS all six**; following #1084 and intermediate #1085–#1088 failed due newly introduced observation test hook expectation, **not a PASS**.
- Intermediate #1089–#1091 failed Ruff UP034 in observation test. **#1092 / 40182954117** passed Ruff and then failed one new Memory test asserting incorrect source-name tie order: Ubuntu 3.13 reported **2476 passed / 1 failed / 1 skipped**.
- After source-semantic-neutral Memory test correction, **#1093 / 40183096066** at `43b28a18e5b513ddf2b1e227cb780f7b89be1127` reported Ubuntu 3.11/3.12/3.13 GREEN at inspection; Windows jobs were still completing, not yet asserted as whole-matrix GREEN.
- **#1094 / 40183232492** at archive source-only `2c6b7c1a9d66a15d54d6b404d1b3f0cdf31afeae`: Ubuntu 3.11/3.12/3.13 GREEN. Ubuntu 3.13 job `121138511717` **Ruff PASS; 2477 passed, 1 skipped**. This does **not** test the fifth archive test file.
- **#1095 / 40183403007** archive source+test failed Ruff F401 due unused test-only import, fixed at `30f83add5cafde8ad89763825b560587e7df42fe`; preserve failure evidence and confirm this new exact HEAD's six jobs rather than extrapolating.
- Test count arithmetic: Run418 `2446` + Run419 `37` = `2483` collected expected; with the explicitly skipped startup subcase expected `2482 passed, 1 skipped` **only if exact final CI reports it**. No all-six GREEN claim until independently verified on exact source/test HEAD.
- Work is a set of standalone offline diagnostic packages; no promotion, real identity, cross-SQLite transaction, external exactly-once outcome, live sensors, memory export, automatic notification, or ToolBackend effects. Repeated reads cannot close a TOCTOU window across separate SQLite files.

## Zero-cost and frozen gate protection

No paid/external compute, API, subscription, credentials, new account connection, real Candidate adapter/weights, protected V2 final evaluation, Candidate promotion, schema modifications, frozen V1/V2/Local UI/Launcher evidence changes or main merge. V3 PR #5 remains Draft/open/unmerged/NOT_PASSED under its own approval gate. PR #8 remains Draft/open/unmerged. **UNKNOWN/RUNNING or reserved-PENDING WRITE is never automatically replayable.** Synthetic hashes, local archives, fixture readiness and timestamps are not human consent or attested provenance.

## Next plan / 今後の方針

1. Verify #1093/#1094 and exact final Run419 source+tests workflow across six Ubuntu/Windows Python jobs. Preserve failed histories. If a new genuine failure emerges, smallest semantics-preserving Contents correction only; never duplicate equivalent CI.
2. Multi-WRITE recovery: retained-PENDING/UNKNOWN, partial Planner/Occurrence/ActionAudit/AuditLink history loss, concurrency and orphan pre-action audits without retry authorization.
3. Memory CAS/concurrency/expiry, coherent snapshots and privacy-aware Personal Context revocation retention; preserve Memory v1/ActionAudit v1 DDL.
4. Continue mock-only trusted-clock/issuer interface, observation fixtures and proactive scheduler readiness with no real peripherals or notifications.
5. Keep free-only V3 provenance/path/reproducibility/contamination guards and approvals frozen. Never cross paid, protected evaluation, Candidate or main-merge gates without explicit authorization.
