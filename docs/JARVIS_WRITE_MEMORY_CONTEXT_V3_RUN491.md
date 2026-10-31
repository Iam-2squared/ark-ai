# ARK AI — Run491 detached foundation evidence

> Status: local-only source/test work, **NOT_PASSED** as an integrated JARVIS. No external action, user consent, trusted time, model training, Candidate promotion, or protected V2 evaluation is demonstrated.

## Exact starting basis and work packages

Initial Run491 branch basis was the verified Run490 checkpoint `e1ae5e350d1c90c21f994687a1d14fc68bc72ca1` (Draft PR #8). Independent Draft PR #5 began at source/test HEAD `7cebbbbd3e0915028a1aa447b0baf7511df8a49e`. Both PRs remain unmerged; no main changes were requested.

1. **V3 lineage lint regression fix** (Draft PR #5). `src/ark/learning/lineage.py` changed only the presentation of the existing `non-symlink file` error message into a multiline `ValueError`, preserving the exact original message and all path/hash checks. The prior full six-job CI #1734 failed at Ruff E501 in `lineage.py:111`. Normal GitHub Contents update yielded source HEAD `7d3d1fe69e5d8e550ea444510c793395047d99f7`. [CI #1740 / 41151476912](https://github.com/Iam-2squared/ark-ai/actions/runs/41151476912) subsequently completed **six of six success** on Ubuntu/Windows and Python 3.11/3.12/3.13.
2. **Planner durable WRITE reservation path/carrier custody** (Draft PR #8). `src/ark/agency/disconnected_write_slot_ledger.py`: preserve the exact SQLite path object across startup, read-only `inspect` and `reserve_many`; retain exact witness field carriers and inert authority across re-entrant SQLite callbacks. Source HEAD `2ba4b0473a1d9e1d3c100d75d63833179bbb2ce2`, tests HEAD `d08be0f17fffd4f9f19ad0ac57a5261f895a49fa`; three new focused tests in `tests/test_write_slot_custody_run491.py`. Rebound same-text paths, reflectively replaced equal-value witness hashes and path swaps before SQLite INSERT must fail closed. A WRITE reservation never authorizes dispatch or replay.
3. **Memory independent witness startup and CAS authority** (Draft PR #8). `src/ark/memory/disconnected_witness_ledger.py`: reject startup path rebind across SQLite review; re-check retained witness and all denied-authority properties on every append CAS callback boundary, before INSERT/COMMIT. Source HEAD `59cf9917ce7342261590a83484ee030297070cc9`, tests HEAD `f9c5a0074efd1f3af7e83f4e6d6c21c86ecc9268`; two new focused tests in `tests/test_memory_witness_authority_drift_run491.py`. Exact witness custody does not independently authenticate its writer or protect against complete SQLite+retained-tip rollback.
4. **Personal Context replay witness fail closed** (Draft PR #8). `src/ark/personal_context_replay_ledger.py`: read-only restart validates the returned witness exact class, shape and negative authority; `witness()` checks it before and after the read transaction, and startup checks exact path-object preservation. Source HEAD `fcb020eb941eb5a1269257495ff4dcf292463b96`; three new focused tests in `tests/test_context_replay_readonly_authority_run491.py` at tests HEAD `416504daed39d35cebd59da3f4d13deb79f5ad02`. Hashed context request identities remain linkable and no consent, retention, disclosure or tool permission is inferred.

## CI, scope, and reproducibility

- V3 **exact source** `7d3d1fe69e5d8e550ea444510c793395047d99f7`: six of six GitHub Actions jobs GREEN, run ID `41151476912`. Prior failure #1734 was Ruff line length, not proof of failing artifact safety semantics.
- PR #8 exact latest **source/test** at the time of authoring this report: `416504daed39d35cebd59da3f4d13deb79f5ad02`; latest CI should be checked independently against that SHA. Earlier source runs **must not be counted** as final-head GREEN.
- Focused local reproduction, when source checkout is available: `python -m pytest -q tests/test_write_slot_custody_run491.py tests/test_memory_witness_authority_drift_run491.py tests/test_context_replay_readonly_authority_run491.py`; `ruff check .`; then all configured six CI matrix jobs.
- Eight new test functions. These are disconnected fixtures; no real ToolBackend, UI permission, microphone, external clock, notifications, network effects or Candidate bytes.
- Independent local full pytest/Ruff were not verified this run; this environment's direct `git ls-remote` could not resolve `github.com`. GitHub connector reads and Actions are distinct evidence sources.

## Maintained boundaries and future work

Frozen Memory v1 and Agency contract modules, V1/V2/Local UI/Launcher evidence, V3 Contract 1, provenance/contamination/reproducibility and protected evaluation boundaries were not edited by these packages. Draft PR #5 remains explicitly **NOT_PASSED**, unmerged, and cannot run real Candidate/preflight/weight generation or open protected V2 evaluation without the appropriate authorization. No paid/external GPU, paid API/service, credentials or account connection, destructive operation, main merge, or external WRITE action was initiated.

These guards protect specific local Python/SQLite carrier assumptions, not against an adversarial operating system, independently authenticated storage writer, a rollback of both file and retained state, a trusted clock, consent freshness, or true exactly-once external effects. Unknown or in-flight WRITEs remain quarantined and never automatically replay.

**Next:** confirm exact PR #8 six-job CI; repair any concrete failure without relaxing invariants; follow with isolated durable Memory CAS and manual Planner UNKNOWN WRITE reconciliation, trusted-clock audit-before-action, scheduler and privacy lifecycle work, and free-only V3 identity/authorization/reproducibility validation.
