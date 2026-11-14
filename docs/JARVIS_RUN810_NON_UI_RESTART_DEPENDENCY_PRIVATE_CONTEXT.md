# Run810 — Disconnected Planner restart quarantine + private Personal Context preview delta

**Evidence timestamp:** 2026-11-12 15:03 JST (observed local wall clock; not a trusted-clock credential).  
**Initial work-basis HEAD:** `2fc5375c8d216fd5d4d3cfa873851aa5129cd5ce`.  
**Branch/PR:** `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), unmerged.  
**Protected:** Draft PR #5 and frozen V1/V2/Local UI/Launcher untouched; Draft UI PR #9 untouched, UI development paused.

## Package A — join synthetic Planner recovery with exact WRITE ancestry

- New opt-in, inert `src/ark/agency/disconnected_restart_dependency_join.py`, source commit `f33bed3761e44164b9d5b4f42a975e6466a4eee5`; corresponding `tests/test_disconnected_restart_dependency_join_run810.py` initially `5b23c68b2c307a1280a27269d050ce700387e1a5`.
- Reconciles an independently retained synthetic plan tail, replayed step IDs/states/revisions, `RUNNING`/unknown set and the separate dependency quarantine result. Validates sorted exact claims, bounded DAG, explicit WRITE transitive ancestry and every canonical HOLD reason. Results remain `dispatch_authorized=False`, `automatic_replay_authorized=False`, `external_outcome_verified=False` and `trusted_provenance_verified=False`.
- **35 new parameterized cases:** nominal WRITE+READ+RUNNING join; 29 malformed/contradictory/local-fault cases; five terminal or pending READ hold states. No real `ToolBackend`, resource execution, permission grant or SQLite write.
- First CI [#43163708178](https://github.com/Iam-2squared/ark-ai/actions/runs/43163708178) failed Ruff `I001` (test import ordering); corrected by normal source write `88cff89a39c79216c5c867c966f61532af2f3372`.
- Second CI [#43164259723](https://github.com/Iam-2squared/ark-ai/actions/runs/43164259723) revealed a production tuple-versus-field read in the new join and a malformed-tail exception that had not yet been wrapped into the public denial type; both corrected in `bd9302d797a6d8083a6bcc3853d9da4b9b16a2be`. Existing safety checks and test expectations remained intact.
- This join does **not** authenticate its supplied plan topology or the separate stored evidence; an identical digest in two caller-supplied receipts is not an independently attested graph or cross-store transaction.

## Package B — no-disclosure Personal Context preview change review

- New isolated `src/ark/personal_context_preview_delta.py` source commit `c28a2af3f7d161af4f250050c91c0143e59da156`; `tests/test_personal_context_preview_delta_run810.py` initially `c939f6a0d26fa266f1be50ef5e5e032fa6582727`.
- Checks exact two canonical local fixture preview SHA-256 receipts, fixed owner ID, sorted allowlisted scope IDs and independently retained prior digest. Compares canonical record IDs/scope digests/content hashes without returning, logging or exporting plaintext. Reports added/removed/changed/retained counts and content-free comparison digest; rejects scope migrations, invalid UTF-8, extra/duplicate JSON fields, forged count/digest and malformed receipt carriers.
- **29 new parameterized cases:** six expected change scenarios, 18 incorrect/hostile input cases, one secret-nondisclosure case, four reflected mutation cases. Returned review explicitly denies reuse, deletion, consent verification and external export.
- Intermediate CI [#43164068633](https://github.com/Iam-2squared/ark-ai/actions/runs/43164068633) found Ruff `E501` in the new test. Fixed in `82aaabf4cad44716805c827ad78f101b4bad37a3`, also repairing the surrogate fixture so it really tests lone-surrogate rejection.
- Subsequent CI #43164259723 found two mismatched diagnostic cases: repeated record IDs and oversized content were correctly rejected but classified by an earlier generic branch. Source `c97cbbb7f882a574626120084f9817ab2a2d14c7` now rejects duplicate record IDs earlier and reports the explicit private-content budget. **No invalid input is made admissible**.
- These local fixture receipts contain caller-supplied data; neither owner consent, freshness/revocation, independent custody, trusted time, cross-store isolation, or live Memory/Tool access is proven. Caller must not wire this to a live Personal Context exporter without the separate consent and privacy lifecycle gate.

## Testing evidence and provenance

- Before this invocation the exact prior checkpoint `2fc5375c8d216fd5d4d3cfa873851aa5129cd5ce` had [#43157691647](https://github.com/Iam-2squared/ark-ai/actions/runs/43157691647) **GREEN 6/6** on Ubuntu/Windows Python 3.11–3.13 (individual completed job results inspected).
- New test total **64** (35 + 29). Intermediate builds failed on concrete Ruff or pytest defects, all traced to actual logs and repaired through the normal GitHub Contents write path; no tests weakened, no force-push, no duplicate manual workflow run.
- Latest source/test fix HEAD `c97cbbb7f882a574626120084f9817ab2a2d14c7`: [#43164712185](https://github.com/Iam-2squared/ark-ai/actions/runs/43164712185), **Ubuntu Python 3.11 / 3.12 / 3.13 GREEN 3/3 at evidence read; Windows three jobs in progress**. Ubuntu 3.11 reported `13982 passed, 1 skipped`. This is **not** an assertion of 6/6 GREEN nor an exact future checkpoint result.
- Only GitHub Actions is a source of full test evidence; no local full checkout, Ruff or pytest run, real GGUF/PC performance gate, paid GPU, real Candidate generation or protected evaluation claimed.
- Normal GitHub commit ordering/current branch HEAD must be re-read before further source/test and checkpoint writes. A later checkpoint commit is assigned its own result SHA by GitHub and cannot be accurately self-referenced before it exists.

## Next plan / 今後の方針

1. Verify all six exact-HEAD CI jobs; inspect true failing job logs, apply minimal test-preserving fixes and switch to independent lanes while CI executes.
2. Before any additional joins, validate the isolated Planner recovery and dependency quarantine contracts at an exact GREEN HEAD. Extend permanent restart `UNKNOWN` isolation and zero-dispatch mock execution, then audit-before-action, ToolRegistry and PermissionGate sequencing.
3. Continue Memory CAS/ABA and `COMMIT-UNKNOWN` reconciliation, coherent expiry snapshots and privacy/erasure retention gates; keep Personal Context preview delta detached from real user data and exporter actions.
4. Continue local-only proactive/observation fixtures and free V3 numerical/identity/path gates without paid compute, V2 protected evaluation, Candidate promotion or UI work. **JARVIS completion remains NOT_PASSED.**

All result values are synthetic/non-authorizing. A diagnostic hash is **not** a cryptographic signature proving who acted, who approved, or whether external work took place.
