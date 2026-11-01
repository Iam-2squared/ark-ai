# Run540 — local Memory CAS postwrite integrity and Planner failure archive final custody

**Scope:** free-only, deterministic/disconnected. This record is not approval for real tool dispatch, trusted time, user consent, privacy erasure, automatic retry, or protected V2 evaluation.

## Work basis and saved code

- Initial PR #8 work basis: `27b3cfcdc090144927e696eae5243b9868f1cd7b`.
- Planner failure archive source: `a04a3689517a18e940833a8ca5147df794d969ec`; tests: `d61fb13485b29521ab8d6badbd770596605a2a3e`.
- Memory opt-in generation CAS source: `551d49e4ce8a95dd45d7e4661f9fa30cf33fa0a0`; tests: `0556ef4ee4153cf58b56f831925fcf06d9b2845f` (the last source/test HEAD).
- All updates used normal GitHub Contents operations on `research/jarvis-foundations`; there was no protected schema or main-branch write.

## Concrete invariants

1. `generation_fenced_memory_update` already begins an SQLite `BEGIN IMMEDIATE`, checks generation token, retained event chain, and bounded, non-extending retention. Its postwrite check now **also** demands exactly the intended content, decoded metadata, expiry, and update timestamp from the same transaction. A test-only replacement for the SQLite event hook changes metadata or expiry after the SQL UPDATE but before COMMIT. The code rejects and the same transaction rolls back both row and event. This does not repair the original frozen `SQLiteMemoryStore.put` contract, attribute external caller identity, or authorize replay after an ambiguous COMMIT.
2. `review_disconnected_failure_archive` now pins the hypothetical terminal receipt's field identities, final witness fields, and the class denial-property descriptors before its final file read. After the read, it rejects changed fields (including new equal-valued carrier objects), terminal counts, a swapped False-only permission property, or a True property. The saved JSON is create-only, bounded, synthetic and contains no actual executor results. A complete restart never automatically replays UNKNOWN WRITE.
3. Newly authored cases: **3** Memory postwrite cases (one valid path, two reentrant row edits), **7** Planner final-read cases (one valid path, six late mutations). **10 newly authored parametrized pytest variants in total**, not proof of 10 separately executed standalone PASS cases. CI must be assessed by exact commit before any GREEN claim.

## Evidence boundaries

- Previous Run539 PR #8 checkpoint HEAD `27b3cfcdc090144927e696eae5243b9868f1cd7b` was 6/6 GREEN as separately inspected in this invocation at GitHub Actions run [41348836165](https://github.com/Iam-2squared/ark-ai/actions/runs/41348836165), but this cannot prove the newer source.
- Initial current source/test HEAD `0556ef4ee4153cf58b56f831925fcf06d9b2845f`: [Actions 41353949482](https://github.com/Iam-2squared/ark-ai/actions/runs/41353949482), all six jobs **IN PROGRESS at first checked snapshot**, not declared GREEN here.
- This note creates a new documentation-only HEAD and may launch its own normal free public repository CPU workflow; that run is a different exact HEAD and requires a separate read.
- No independently executed full local pytest or Ruff checkout was performed. GitHub Actions runs the existing public repository Linux/Windows x Python 3.11–3.13 CPU matrix.

## Deferred integration

An unknown post-COMMIT outcome remains manual-only; a matching row cannot prove who wrote it. Planner terminal receipts and registered READ evidence live in separate stores and never establish cross-store atomicity or real ToolBackend outcomes. Subsequent work should integrate failure archive and registered READ identity under a non-executing shared read protocol, validate consent/retention and occurrence replay independently, and preserve all frozen contracts. PR #5/#8 remain Draft/unmerged; ARK/JARVIS overall NOT_PASSED.


## Run540 continuation — Scheduler quarantine authority epoch

- Independent third foundation lane: `src/ark/offline_schedule_resume_review.py` source commit `66c44c1f1eb3482437e8eba684e8c83de75f16c5`; `tests/test_schedule_resume_quarantine_denial_epoch_run540.py` commit `0c5a46082f4621ad1b4c4484442c17202464f40f`.
- The restart review pins the class descriptor of `QuarantineWitness.independently_authenticated` before the first ledger inspection and checks it plus exact False on **every** one of the three retained-prefix observations. A later inspection cannot silently install a different False-only or True getter, or mutate that witness's own count/hash carriers during the getter. This is isolated from real timers, OS trusted clocks, notifications and ToolBackend dispatch.
- **6 additional newly authored parametrized cases**: one normal three-read due preview and five injected permission-property rebind cases after the first, second or third read. The combined **PR #8 new cases in this Run540 note are 16** (10 earlier plus 6 Scheduler); this is a count of authored cases, **not** standalone pytest success. PR #5 independently adds 14 V3 cases, for **30 authored cases across four lanes**.
- Source/test HEAD for this continuation: `0c5a46082f4621ad1b4c4484442c17202464f40f`. Its own exact-head CI must be checked after completion. A green result on the earlier PR #8 source/test HEAD does not imply this later Scheduler HEAD is green.
