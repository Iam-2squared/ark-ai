# ARK AI — Run823: Memory SQLite sidecar safety forensics (non-UI, free-only)

## Scope and governing result

- Work basis: `de2f59e449eb1bac14f293a32be9677aa918a961` (Run822 latest checkpoint).
- Work branch: `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), **UNMERGED**. Do not modify Draft PR #5 or paused UI Draft PR #9.
- Overall ARK/JARVIS remains **NOT_PASSED**. No real memory erasure, tool action, protected evaluation, Candidate generation/promotion, physical PC or GPU action, and no paid service.
- This report is diagnostic evidence only: a local pathname stat is neither filesystem-descriptor custody nor proof of authenticated history, multi-process atomicity or privacy consent.

## Confirmed latest-checkpoint failure and actual traceback

[Run822 checkpoint CI #43252974470](https://github.com/Iam-2squared/ark-ai/actions/runs/43252974470) completed with FAILURE. Ubuntu Python 3.12 job `131303524907` reported **1 failed, 14338 passed, 1 skipped**. The failure was in `tests/test_memory_cross_process_create_race_run435.py::test_concurrent_memory_initial_create_is_single_cas_per_identity[separate-owner-expected1]`. One of two independent children raised `MemorySchemaError: memory SQLite sidecar path is not a single regular file`; the other child's put succeeded with `CREATED`.

The logs do **not** establish which SQLite suffix, file kind, link count, transient unlink/replacement, filesystem state, or exact synchronization point caused the refusal. The sibling's success does not prove the failing child's sidecar was safe. A process-local `_BOOTSTRAP_LOCK` is not a cross-process synchronization primitive. **No automatic retry** and no weakening of symlink, hardlink, orphan or nonregular sidecar denial is justified.

## Package A — Preserve fail-closed sidecar refusal; add privacy-safe evidence

- [Source `74cbb871`](https://github.com/Iam-2squared/ark-ai/commit/74cbb8716931190a1505916ce954a6122085b927): `src/ark/memory/sqlite_store.py` reports only `suffix`, octal `file_type` and integer `link_count` alongside the existing denial. Never emits a database pathname, private row or owner. It still refuses before SQLite opening for any nonregular sidecar or `st_nlink != 1`. No path preflight, lock, CAS, transaction or schema semantics changed.
- [Test `e9096ec7`](https://github.com/Iam-2squared/ark-ai/commit/e9096ec7a45dcd5ca1d5fcba079ec6ccb5712f6f): 9 combinations of `-wal/-shm/-journal` with disposable symlink/directory/hardlink, plus accepted regular and rejected orphan sidecar cases = **11 new regression cases authored**. The checks assert no private path/name appears and no files were mutated. No original private database is opened.
- [Lint-only correction `e0d0ea64`](https://github.com/Iam-2squared/ark-ai/commit/e0d0ea649180325386ae5b241abdd72ed16315db): prior [CI #43262916256](https://github.com/Iam-2squared/ark-ai/actions/runs/43262916256) failed Ruff `E501` due to one 103-character test assertion line, with six jobs failing early. The correction is line wrapping only; no test predicate or production safety check was changed.

## Package B — Bounded, disposable cross-process observation harness

- [Script `fffcc569`](https://github.com/Iam-2squared/ark-ai/commit/fffcc56907ce5065956107344800564ba3a6577a): `scripts/diagnose_memory_sidecar_startup.py` initializes one disposable SQLite Memory store then overlaps two fresh Python child interpreters (not the parent's in-process lock). Both workers hold after initialization until a shared release file allows concurrent CAS writes. Accepts `--mode same-identity|separate-owner` and `--iterations` bounded 1–30 (default 4). Child outputs are limited to local status, optional sidecar suffix/type/link count or generic exception class; stderr is never exported. Results contain aggregate status counts and anonymized sidecar metadata only.
- Intended manual reproduction (not executed here against the actual repository checkout): `python scripts/diagnose_memory_sidecar_startup.py --iterations 12 --mode separate-owner`, optionally repeat with `--mode same-identity`. Only automatically created temporary directories are touched. A nonzero exit means at least one attempt did not meet the expected outcomes; **do not use this as an authority to retry an unsafe SQLite open**.
- The script was syntax-checked as a locally authored standalone Python copy; this does **not** constitute an imported `ark.memory` runtime test or real multi-process reproduction. Its GitHub CI result is the actual validation authority.

## CI / pending evidence

- [Run822 corrected source HEAD #43251602443](https://github.com/Iam-2squared/ark-ai/actions/runs/43251602443) and [report HEAD #43252678514](https://github.com/Iam-2squared/ark-ai/actions/runs/43252678514): completed SUCCESS before the failed Run822 checkpoint, not proof of the later head.
- [Run822 checkpoint #43252974470](https://github.com/Iam-2squared/ark-ai/actions/runs/43252974470): FAILURE, real SQLite cross-process sidecar refusal on Ubuntu 3.12.
- [Source diagnostics CI #43262840182](https://github.com/Iam-2squared/ark-ai/actions/runs/43262840182): last observed IN PROGRESS.
- [New test initial CI #43262916256](https://github.com/Iam-2squared/ark-ai/actions/runs/43262916256): FAILURE, Ruff E501, corrected without weakening.
- [Corrected 11-case tests CI #43263317952](https://github.com/Iam-2squared/ark-ai/actions/runs/43263317952): last observed IN PROGRESS.
- [Standalone script CI #43263443699](https://github.com/Iam-2squared/ark-ai/actions/runs/43263443699): last observed IN PROGRESS.
- These are **not** a declaration of exact-head six-job GREEN. The report and later checkpoint commits create their own CI runs. Inspect actual job logs on any FAIL, and never duplicate equivalent runs.

## Next plan / 今後の方針

1. Inspect actual script/test/diagnostics CI jobs and source HEAD. If failed, apply the smallest semantics-preserving fix. Do not claim a partial CI result as GREEN.
2. Use disposable multi-process evidence to distinguish genuine aliases from a benign SQLite sidecar lifecycle transition; preserve exact path denials until independent, reproducible evidence supports a narrowly scoped change. Never silence failure or add unsafe generic retries.
3. Resume Memory CAS/ABA and COMMIT-UNKNOWN recovery, Planner durable UNKNOWN quarantine and authorization audit-before-action/registry-bound mock integration only on relevant proven foundations.
4. Keep privacy-safe Personal Context, proactive state, observation fixture adapters and free V3 path/identity/approval guards isolated and reversible. Draft PR #5/#8/#9 remain unmerged; UI stays paused.

**No paid/external compute, protected V2 opening, Candidate action, real tool dispatch, frozen contract changes, credentials or main merge. Overall NOT_PASSED.**
