# Run517 — V3 detached paired-comparison exact JSON type audit

Recorded UTC: 2026-11-01T01:45:27.793Z (ordinary runtime wall clock; not trusted time).

## Precise free-only change

- PR #5 remains Draft and unmerged at source+test HEAD `bdb4d13e701818ffdce1130522409e832cdb2be6` based on Run516 docs HEAD `b38970f5a58142861e391bc1edfaeab65e37884b`.
- `src/ark/learning/detached_comparison_recheck.py` updated at commit `1d8a8a59b8d6fb842e0bc18808cda5de985230e5`, blob `4840ed633b922eb6d9466e230db54341948ca977`.
- `tests/v3/test_detached_comparison_exact_types_run517.py` added at `bdb4d13e701818ffdce1130522409e832cdb2be6`, blob `01c4880b65179990bb68d189ecf40d46a1a472f3`.
- The independent synthetic comparison verifier now requires recursively identical builtin JSON node types for every field of the comparator callback's output. Python equality aliases (e.g. `True == 1`, `1.0 == 1`), tuple/list substitutions and dict subclasses can no longer pass merely because their values compare equal. Reject-only; no benchmark scoring, new permissions, source artifact generation or frozen evaluation.
- Eight authored pytest cases (seven parameter expansions and one positive invariant) use synthetic reports only. No local GPU/model, paid API or real Candidate.

## Evidence and limits

- [Exact source+test CI 41262204659](https://github.com/Iam-2squared/ark-ai/actions/runs/41262204659): six GitHub Actions jobs completed successfully (Ubuntu/Windows x Python 3.11, 3.12, 3.13), checked after tests committed.
- Independent local full-checkout pytest/Ruff NOT PERFORMED. CI does not prove runtime model identities, data review, a provider cost cap, human consent or reproducibility.
- Frozen V3 contract blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` unchanged; protected V2 final evaluation unopened. No real Candidate training/weights, no paid external GPU/API, no automatic promotion, and no main merge.
- All changes isolated/reversible. V3 and full ARK/JARVIS remain NOT_PASSED.

## Next plan

Continue offline data/revision/file-byte identity guards and audit denial-only retained reports. Defer any real Candidate, external compute or protected evaluation until explicit separate authorization and immutable inputs, source rights, verified human reviews, reproducibility and spend hard-stops.
