# Run517 — disconnected READ journal, restart graph and fixture-to-journal custody

Recorded: 2026-11-01T01:48:11.214Z UTC ordinary runtime clock (not a trusted timing or authorization witness).

## Source and test exact heads

- Repository `Iam-2squared/ark-ai`; PR #8 `research/jarvis-foundations` remains Draft/unmerged, work-basis previous checkpoint HEAD `95d1c1682d01a4244df1ad8fb71fa2b858db73ce`.
- **Final Run517 source+test HEAD:** `2ceaf41277c40292b3ba999170448ad0858f6849` (earlier Agency-only source+test HEAD `d5b43480af79326426ad79ae556feb5027dff321` is predecessor evidence, not final)..
- **Package A — local SQLite journal open/create safety**: source `src/ark/agency/disconnected_read_journal.py` at commit `4bf1cd4c6aad0c2e388bae701399339fc2b9e958`, blob `a082df59cadc9a9576165c1556c1425203473a13`; new `tests/test_read_journal_atomic_open_create_run517.py` at `de0b5adc1ec1c9e5ccd5a2084f1d3fa45fcabd77`, blob `b5a39265b94dd000de7c5f00582575f2cede6f29`. Failed create closes the acquired connection without deleting the incomplete file; existing DB open now checks marker, schema and hash chain inside one SQLite BEGIN/COMMIT snapshot. A concurrent WAL writer fixture tests the snapshot distinction. **3 authored pytest cases**, including two parameter expansions.
- **Package B — started READ ancestry consistency**: source `src/ark/agency/disconnected_read_recovery_schedule.py` at `c23b3feb7c6aa043dfff8e506e9ad7cde8094bd0`, blob `6b5f498304cedaa8fa0ae92b6c7b302dac94cd53`; `tests/test_read_recovery_started_dependency_run517.py` at `c118e71776b38f2e576403e73fccfd205a339b5a`, blob `4864f4c6337e92620acc1195c1d7ea5c2106fd9c`. Mock FAILED/RUNNING/UNKNOWN children with an unresolved prerequisite now fail closed instead of acquiring apparently valid recovery dispositions; NOT_STARTED descendants still get HOLD/WAIT diagnostics and completed ancestors remain non-authorizing. **19 authored pytest cases** (12 reject + 3 completed + 4 pending).
- **Package C — post-append fixture carrier custody**: source `src/ark/agency/disconnected_read_receipt_bridge.py` at `2791f6ea0cb7ce0239dae7908e4a2970fb8f3f82`, blob `59b9594c1044aef7689d09752a851109a11f6ae7`; `tests/test_read_bridge_postcommit_custody_run517.py` at `d5b43480af79326426ad79ae556feb5027dff321`, blob `34868990b6c56cc38e7133e7cd1d4891d51f4fa3`. Original synthetic request/result/binding/receipt identity is rechecked after local journal append callbacks. If input changes after actual SQLite COMMIT, bridge reports uncertainty and **never retries or claims rollback**. A returned wrong-count witness is rejected. **4 authored pytest cases** (3 carrier targets + 1 wrong-count fixture).

- **Package D — Memory retained-row report final-denial custody**: source `src/ark/memory/sqlite_retained_row_delta_review.py` at commit `0ebf8717d7e352048ff3e2c62c89211cfff8cc79`, blob `0c68f57a4fb4182a1c0f2c1c04f7e1e6c008a000`; test `tests/test_memory_row_delta_last_denial_run517.py` at `2ceaf41277c40292b3ba999170448ad0858f6849`, blob `b45b3466c77c29917604b8208bca1f8417f5f6bf`. The local row-delta review rechecks exact report counts, digest carrier and all denied capabilities after a false-valued callback; detects reflected digest/count changes and earlier authority flag changes without accessing or exposing private Memory contents. **5 authored pytest cases** (4 denial variants + 1 inert positive).

**31 new pytest cases** are authored across PR #8, not an independent local PASS count.

## Evidence at documentation preparation

- Prior Run516 source [41258581825](https://github.com/Iam-2squared/ark-ai/actions/runs/41258581825) and checkpoint [41258999110](https://github.com/Iam-2squared/ark-ai/actions/runs/41258999110) each completed six jobs successfully; **they do not validate Run517 edits**.
- [Run517 Agency-only predecessor CI 41262541096](https://github.com/Iam-2squared/ark-ai/actions/runs/41262541096) had jobs IN PROGRESS when sampled, but precedes Package D. [Final PR #8 source/test CI 41262669072](https://github.com/Iam-2squared/ark-ai/actions/runs/41262669072) at exact HEAD `2ceaf41277c40292b3ba999170448ad0858f6849` was QUEUED when first observed; full matrix GREEN is NOT claimed here. Any later CI failure requires an exact-head inspection and minimal semantics-preserving fix.
- Local full-checkout pytest/Ruff and physical-PC/GPU verification: **NOT PERFORMED**. Synthetic SQLite receipts and caller-supplied hashes do not independently prove past writer, trusted time, real Tool dispatch, correct external effects or cross-process custody.

## Boundaries and next steps

- No actual ToolBackend/OS action, external service, model training, paid GPU/API, protected V2 evaluation, real Candidate, promotion, automatic unknown WRITE replay, main merge or destructive data operation.
- Frozen Agency contract blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9` and Memory contract blob `b6e93821ecd69270a7634aceb20775dc36e9953c` remain unchanged. V1/V2/Local UI/Launcher frozen evidence unaffected.
- NEXT: establish exact-head CI for all jobs; continue registry-bound READ provenance + restart-safe observation without external dispatch; verify durable Memory CAS/event prefix, UNKNOWN WRITE manual triage, trusted-clock audit-before-action and Scheduler occurrence uniqueness before any real executor integration.
- Overall **ARK/JARVIS NOT_PASSED**; every module remains isolated/reversible.
