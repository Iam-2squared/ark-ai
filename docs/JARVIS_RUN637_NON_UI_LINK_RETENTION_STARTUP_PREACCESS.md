# ARK Run637 — Non-UI durable link and preaccess custody

**Work basis:** Draft PR #8 `research/jarvis-foundations` at `5e68652f945365b11abc2d0cdd9e31933f0c256e`. At invocation start its [CI #42049901812](https://github.com/Iam-2squared/ark-ai/actions/runs/42049901812) completed **6/6 GREEN** on Ubuntu/Windows × Python 3.11–3.13. The V1/V2/Local UI/Launcher freeze, V3 Contract 1, PR #5, PR #9 and `main` were not modified.

## NEW 1 — Synthetic mock WRITE sidecar and terminal audit consistency

- `src/ark/agency/synthetic_mock_action_cycle_review.py`: [commit `3ee62d1b3d45cad57c7b9f21832a32764f7c34bc`](https://github.com/Iam-2squared/ark-ai/commit/3ee62d1b3d45cad57c7b9f21832a32764f7c34bc).
- `tests/test_mock_cycle_link_readback_run637.py`: [commit `e16e0a98bf83ce8cf88fe2ff43e0664960925734`](https://github.com/Iam-2squared/ark-ai/commit/e16e0a98bf83ce8cf88fe2ff43e0664960925734). **6 parameterized cases authored**, NOT locally proven PASS.
- When an optional sidecar is configured, retain its pre-append witness; require the exact linked occurrence/audit receipt and **one newly persisted** sidecar row and matching tail hash before terminal success. After terminal journal readback, require the pre-action audit row still exists with its original fields and the sidecar remains consistent. Do not trust a forged callback receipt or a journal SUCCEEDED row when other SQLite evidence has drifted.
- A synthetic post-terminal rejection is **COMMIT-UNKNOWN/manual review**, not a rollback claim. Backend calls and automatic replay remain forbidden.

## NEW 2 — Privacy retention constructor/field preaccess

- `src/ark/personal_context_retention_review.py`: [commit `187ef9a468135536bcdd84ee246a0507a6588826`](https://github.com/Iam-2squared/ark-ai/commit/187ef9a468135536bcdd84ee246a0507a6588826).
- `tests/test_retention_original_contract_preaccess_run637.py`: [commit `fb11580264cf7af85326e1ecd31077e3fc50b7e7`](https://github.com/Iam-2squared/ark-ai/commit/fb11580264cf7af85326e1ecd31077e3fc50b7e7). **9 authored cases**.
- Pin original `SyntheticRetentionItem` and `SyntheticRetentionInventory` dataclass constructors, slots and getter hooks, plus original denial-only descriptors, **before private SQLite reads** and again at construction. Verify hostile replacements are never invoked or used to disclose personal content. Retention inventory remains diagnostic; no erasure, consent or authorization is granted.

## NEW 3 — Detached startup report original-result guard

- `src/ark/disconnected_local_readiness.py`: [commit `cf3656a08f8cd35c42352ef4cc3663f01ec70b66`](https://github.com/Iam-2squared/ark-ai/commit/cf3656a08f8cd35c42352ef4cc3663f01ec70b66).
- `tests/test_startup_report_constructor_preaccess_run637.py`: [commit `2b3718570b743376d468897f4022684b9301a5c6`](https://github.com/Iam-2squared/ark-ai/commit/2b3718570b743376d468897f4022684b9301a5c6). **3 authored cases**.
- Require import-original startup report initializer and field slots before any schema callback. Keep readiness strictly read-only, query-only and non-dispatching; other existing startup pregetter fault fixtures remain in place.

## Validation, blockers and scope

- **18 new test cases authored total** (6+9+3); this is not a pytest PASS claim.
- Automated CI is started by ordinary Contents commits, **no duplicate manual dispatch**. At last read, exact source/test CI for mock [#42059095817](https://github.com/Iam-2squared/ark-ai/actions/runs/42059095817), privacy [#42059741091](https://github.com/Iam-2squared/ark-ai/actions/runs/42059741091) were **IN PROGRESS** and startup [#42060147188](https://github.com/Iam-2squared/ark-ai/actions/runs/42060147188) **QUEUED**. The latest exact HEAD is **NOT yet six-job GREEN-verified**. Inspect logged failures and fix through ordinary guarded Contents writes; no fabricated local pytest/Ruff evidence. An attempted local `git ls-remote` failed GitHub DNS resolution, so there is no local checkout test result.
- Separate journal, occurrence, audit and link SQLite databases have **no cross-DB atomicity**, no independently authenticated history, no trusted clock, no human consent, no actual external-effect attestation and no exactly-once production executor. Post-COMMIT ambiguity always requires manual inspection. These checks narrow callback/missing-row vulnerabilities, not the unresolved architecture/approval gap.
- Zero paid services, APIs, GPU, training, Candidate/weight generation, external dispatch or physical-PC actions. Draft PRs #5/#8/#9 stay unmerged; UI development PAUSED, PR #9 untouched, `main` and all frozen evidence/contract boundaries unchanged. **ARK/JARVIS/V3 NOT_PASSED**.

## Next plan / 今後の方針

1. Verify latest exact-head six-platform CI and inspect any actual failing job logs; minimal semantics-preserving corrections only, non-conflicting lanes during CI.
2. Audit/cross-process interleaving around terminal journal, audit and sidecar links without claiming cross-DB atomicity. Preserve UNKNOWN and never automatically retry.
3. Extend Memory generation CAS/event consistency and Planner restart recovery; proceed to registry-bound PermissionGate and disconnected audit-before-action integration only after lower-level exact-head GREEN evidence.
4. Continue privacy-safe Personal Context, proactive/observation back-end contracts and zero-cost V3 approval/identity/path guard reviews. No UI, spending, protected evaluation or promotion.
