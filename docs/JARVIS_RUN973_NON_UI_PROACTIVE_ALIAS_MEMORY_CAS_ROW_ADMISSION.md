# ARK Run973 — Non-UI proactive witness path custody and Memory CAS row admission

**Working branch:** `research/jarvis-foundations` / Draft PR #8. **Work basis:** `573e6b70c48c7ae6fd3eb3c744aba6decdf3911f`. **Status:** source and authored regression tests saved; latest exact-head full CI not yet certified. ARK/JARVIS **NOT_PASSED**.

## Verified failure and minimal repair

Run972 checkpoint [CI 44352402823](https://github.com/Iam-2squared/ark-ai/actions/runs/44352402823) finished **FAIL in all six jobs** at Ruff I001 on `tests/test_personal_context_retention_recheck_vectors_run972.py`: `from ark import personal_context_retention_recheck_review as review` appeared below sibling imports. Fix commit [`d840a7c`](https://github.com/Iam-2squared/ark-ai/commit/d840a7cd94f4d62648d0d87ee9862283a62361d4) changes import order alone, preserving tests and all safety assertions. This is not proof that any subsequent pytest or full-matrix run passed.

## New source / test packages

1. **Proactive witness read-only SQLite path alias veto** — [source `2565e35`](https://github.com/Iam-2squared/ark-ai/commit/2565e353c86069c450026fce33748f3ee522c640) and [test `b493a81`](https://github.com/Iam-2squared/ark-ai/commit/b493a81cfb705ed23c23dbc3be8d824756a24f3b). A retained `SyntheticProactiveLedger.path` is reflectively mutable after initial safe construction. Prior readback called `Path.resolve()` then connected to a read-only SQLite URI without reapplying the ledger's path alias veto. The read-only path now invokes the original already-existing `_refuse_aliased_proactive_path` before resolve/open, pins that preflight callback identity against replacement, and requires the platform's exact `Path` class. Four authored tests exercise symlink/hardlink alias redirection, preflight substitution, executable Path subclass and stable unaliased readback. Filesystem-alias tests may SKIP on environments without native link support, never silently certify a missing alias check.
2. **Memory generation-fenced CAS pre-SELECT SQLite row admission** — [source `5fe8d18`](https://github.com/Iam-2squared/ark-ai/commit/5fe8d18fc164f2f59f9358d1f7581b9e53e13242) and [test `9b529f8`](https://github.com/Iam-2squared/ark-ai/commit/9b529f81e6cb2cda1afa332a6e73d6709ad0ab44). The optional CAS `_snapshot` selected `memories` rows with `SELECT *` before SQL-side TEXT/BLOB admission; corrupt local rows could be hydrated into Python before `_record` rejected them. It now reuses the already-verified-by-v1 mutation `_require_memory_mutation_row_hydration_admission` inside the same snapshot before row materialization. Seven authored tests cover malformed content, metadata, source, hash and revision storage classes, oversized content, and a normal Japanese-scope CAS update. No schema, original Memory v1 API, or automatic retry behavior changes.

**Total new tests authored this invocation:** 11 (4 proactive + 7 Memory). A test file saved in GitHub is not CI PASS evidence. No local hardware/model/real executor test ran.

## Precise residual limits

- Proactive path checks are **pre-open lstat checks**, not atomic directory-descriptor custody. An attacker racing filesystem renames between path admission and SQLite open is outside this proof. This review does not grant notification or occurrence/replay authorization.
- Memory row byte admission is **SQLite-side local corruption control** for the targeted memory ID. It is not proof of trusted writer identity, independent global event custody, cross-process transaction ownership, unambiguous post-COMMIT attribution, or consent.
- Neither package adds a real ToolBackend, paid compute, external service, physical-PC action, automatic WRITE retry, protected V2 final evaluation, Candidate promotion, or main merge.

## CI evidence to follow by exact source SHA

- [Ruff repair run 44362114514](https://github.com/Iam-2squared/ark-ai/actions/runs/44362114514) (`d840a7c`).
- [Proactive source run 44362633441](https://github.com/Iam-2squared/ark-ai/actions/runs/44362633441) (`2565e35`).
- [Proactive test run 44362771028](https://github.com/Iam-2squared/ark-ai/actions/runs/44362771028) (`b493a81`).
- [Memory source run 44363192338](https://github.com/Iam-2squared/ark-ai/actions/runs/44363192338) (`5fe8d18`).
- [Memory test run 44363321842](https://github.com/Iam-2squared/ark-ai/actions/runs/44363321842) (`9b529f8`).

All were **IN PROGRESS/QUEUED at last observed sample**. Do not infer success for the later source from an older GREEN run.

## Next: dependency-aware non-UI work

1. Confirm latest exact-head Windows/Ubuntu Python 3.11–3.13 CI. If FAIL, inspect job logs; fix smallest actual test/semantic fault, never waive the safety invariant.
2. Memory: WAL/SHM and CAS/ABA competing-writer restart tests, COMMIT-UNKNOWN/manual-only outcomes and event/row coherent history.
3. Planner/ToolRegistry/PermissionGate: crash recovery, original registry bindings, one-shot grants, trusted-clock audit-before-action; integrate only after exact-head GREEN.
4. Privacy-safe Personal Context and proactive occurrence/replay guards, disconnected Observation fixtures and V3 free-only reproducibility review.

Frozen V1/V2/Local UI/Launcher evidence, Memory v1, Envelope v1, PlanStep/ToolCall v1, protected V3 gates and paused Draft PR #9 remain unchanged. PR #5 stays Draft/unmerged. No new external credentials or billable services.
