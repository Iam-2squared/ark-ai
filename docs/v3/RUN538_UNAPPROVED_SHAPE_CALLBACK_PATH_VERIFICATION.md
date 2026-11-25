# Run538 — Unapproved Shape Path Re-derivation, Not V3 Authorization

**Branch:** PR #5 `research/v3-learning-evaluation` (Draft / unmerged). **V3 / ARK overall NOT_PASSED.** This is disconnected read-only validation; all model, dataset, license, artifact identity, reviewer and cost fields remain *unverified unless separately established*. There is no authorized Candidate, training, preflight or protected V2 opening.

## New invariant

`src/ark/learning/offline_readiness_transition.py` previously checked the SHA-256 claimed by each exact-class shape-report callback against independently serialized snapshot bytes, but it trusted the callback's `unresolved_paths` and `invalid_shape_paths` arrays. The callback could preserve the correct snapshot digest and still invent readiness gains, hide malformed values or mislabel an alias. The new `_independent_shape_paths` rederives both category sets directly from the caller-supplied unapproved mapping, using the currently defined 25 section fields plus the tokenizer/base-revision alias, including SHA-256 syntax, 40-character revision syntax and strict numeric checks. The existing shape-report class, count, authority-denial and repeated-source checks remain in force.

This is a **second classification check**, not an artifact authenticity, approval or data provenance claim. The imported primitive shape validator is still a local deterministic implementation, not an independent trusted verifier or frozen-contract amendment. Never interpret zero unresolved paths as permission to call any runtime.

## Exact writes

- Source verification: `8ec0def6f630667836e950bf5e3260559fdb7efd`.
- Six authored parameter-expanded cases: `efefb70b986961627f0a45fe296293d5b9714644`, `tests/v3/test_passive_transition_path_auth_run538.py`.
- The first six-job CI found one test whose forged `invalid_shape_paths` overlapped the unresolved `code.git_sha`, so the pre-existing overlapping-set rejection correctly occurred before the new path-classification guard. The test fixture was changed to a non-overlapping invented path, preserving every rejection condition: `cb5a45f2676ef914a14a64557ce51210daade54b`.
- [Corrected exact-source+tests CI run 41344280935](https://github.com/Iam-2squared/ark-ai/actions/runs/41344280935) at `cb5a45f2676ef914a14a64557ce51210daade54b`: **6/6 GREEN** (individual Linux/Windows Python 3.11/3.12/3.13 jobs independently read).
- No independent local pytest/Ruff PASS claim; container `git ls-remote` could not resolve `github.com`. Six cases are **authored** cases, not separately counted local executions.

## Remaining gates

The frozen V3 Contract and Experiment 001 are unchanged. The actual model bytes, tokenizer, dataset provenance and contamination manifests, run environment/driver, converter/quantizer identity, legal/license review, cost bounds and explicit human approvals are not manufactured by syntax checks. No paid/external GPU/API, real Candidate adapter/weight generation, automatic promotion, protected V2 evaluation, or main merge was attempted. PR #5 remains Draft under the pre-paid-compute closure.

**Next:** Keep improving free-only snapshot/file/path/reviewer-packet evidence checks, address any exact-head CI failures without weakening gates, and continue independent JARVIS foundational work rather than waiting for authorization.
