# ARK AI — Run691 non-UI: scoped CAS, Planner evidence, audit isolation and Observation lineage

**Work basis:** `9529db791b93d11f7064ad89230980213bf90c00` (Run690 checkpoint), Draft PR #8 `research/jarvis-foundations`. **Only local disconnected/synthetic lanes; no new UI/frontend development.** This note records source/test changes and does not attest JARVIS completion, consent, trusted time, actual READ/WRITE execution, real provenance or any Candidate gate.

## A — UTF-8 scope identity in opt-in generation CAS

Production `src/ark/memory/generation_fenced_cas.py` at commit `e12f8cb8602e55eb2a096e2a2ad493d05d003c6d` adds `_require_bounded_scope`, rejecting ill-formed Unicode and identity components above **256 UTF-8 bytes**, before hashing/SQLite observation or generation-CAS update. The frozen Memory v1 `MemoryScope` and put/delete schema/contracts remain unchanged. `src/ark/memory/generation_cas_outcome_review.py` at `e53ba4281943fc188a4516fbfaa79abde54f9f11` uses the same opt-in validation and translates invalid scope into manual-review rejection before private SQLite reads. `tests/test_memory_generation_utf8_scope_run691.py` commit `6fec09f8704840b97a662606b2ce6aef2e2f390e` adds **10** parametrized cases: four observation denials, four post-construction write-scope tampering denials, one manual outcome no-read denial, one valid 256-byte scope update. These do not grant permission or automatic retries.

## B — Planner step-specific READ custody

`tests/test_planner_read_bundle_cross_step_tamper_run691.py` commit `7a84302df5158006b180e0909ef836063cacb035` adds **seven** synthetic diamond DAG cases: swapped link/review, duplicate pair, overwritten step/registry/link digest/READ tip/request correlation. Each must be denied after recovery while the untouched fixture evidence still reviews as **deny-only**. The mock backend must remain uncalled. No real result provenance is established.

## C — Synthetic occurrence-to-audit request isolation

`tests/test_synthetic_audit_cross_action_restart_run691.py` commit `ac9dce015b31d7189348d6ea1ab5d836c1ae333b` adds **four** local cross-store cases: wrong audit, wrong reservation, wrong registered call and early link clock. Invalid links must leave the existing SQLite prefix unchanged; a separate correctly matched request may still link after reopen. The link only diagnoses locally stored reservations and audit events: three SQLite databases are **not** one atomic transaction and a link is **not** executable authority.

## D — Observation middle-of-chain custody

`tests/test_observation_chain_midpoint_custody_run691.py` commit `3b730d7672d62ff41a1fd7b732c6802800f172a3` adds **eight** cases: repeat digest, cross-source, cross-privacy-scope, equal/regressed timestamp at the middle of a 256-envelope fixture chain, plus three valid mixed-kind chains whose local digest changes without authenticating capture, consent or dispatch.

## CI and narrow lint corrections

- Incoming Run690 canonical checkpoint HEAD `9529db791b93d11f7064ad89230980213bf90c00`: [GitHub Actions #42393278774](https://github.com/Iam-2squared/ark-ai/actions/runs/42393278774), **COMPLETED 6/6 GREEN** (Ubuntu/Windows, Python 3.11–3.13).
- Early Run691 CI [#42397606862](https://github.com/Iam-2squared/ark-ai/actions/runs/42397606862), [#42397672523](https://github.com/Iam-2squared/ark-ai/actions/runs/42397672523), [#42397802934](https://github.com/Iam-2squared/ark-ai/actions/runs/42397802934) **FAIL** due to Ruff I001 import-order findings; this was not a semantic/test PASS. Normal GitHub Contents API fixes: outcome import `148f8eacfc7b103887f7cf94e88797b882f6868f`; Planner test import `51767359f6217b4da88a224a2ec97e5887e80f96`. **No production gate or test assertion was weakened.**
- At report preparation, corrected-source CI [#42397991661](https://github.com/Iam-2squared/ark-ai/actions/runs/42397991661) **IN PROGRESS** and Observation package CI [#42398147862](https://github.com/Iam-2squared/ark-ai/actions/runs/42398147862) **QUEUED**. An additional report/checkpoint HEAD will have its own CI; ancestor statuses cannot be credited to it.

## Unchanged fences and next plan

`main` base `7a843f17eb96ed13d66f23b58b06406b3002e405`; Draft PR #5 V3 HEAD `805b377697472268db02650a89c7a94b1c5337c8`; Draft PR #9 UI HEAD `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`: **not written, not merged**. Frozen V1/V2/Local UI/Launcher contracts and evidence untouched, protected V2 evaluation unopened. No paid API/service, external compute/GPU, new credentials/account connection, real Candidate/training/promotion, hardware action, real backend execution, destructive mutation, force/raw-Git bypass or main merge.

Next: verify exact resulting six-job CI; repair any real failures without loosening safety. Then prioritize generation-CAS ambiguous COMMIT-UNKNOWN review/retention, Planner terminal recovery and independent READ receipts, registry-bound one-time mock authorization/audit custody, and local-first privacy/scheduler/Observation source contracts. **ARK/JARVIS/V3 NOT_PASSED.**

## Follow-up failure diagnosis and narrow semantic corrections

Exact-head [CI #42397991661](https://github.com/Iam-2squared/ark-ai/actions/runs/42397991661) on earlier lint-corrected commit `51767359f6217b4da88a224a2ec97e5887e80f96` exposed **4 FAIL / 10,504 PASS / 1 SKIP on Ubuntu Python 3.11**, not a green result. Three older `test_memory_cas_outcome_preaccess_run673.py` cases expected source-specific rejection and received a combined scope/source diagnostic; `3a4c3264decee4c288733f59e2418ac8a5659ce6` restored **two precise, still fail-closed** diagnostic paths and new scope test expectation was aligned at `6ac8b3c1be27be9890aaf7c80aeec24161f0e23c`.

The fourth failure revealed a boundary in the detached Planner receipt design: a **syntactically canonical** but independently substituted SHA-256 journal tip cannot be authenticated by an I/O-free cross-journal join, so claiming that arbitrary valid hex substitution would be refused was incorrect. `cf0308aeac5acaebd24fa2d2a09b9ca09bdf72aa` requires canonical 64-hex journal tip *shape* at the individual review boundary; `390057cb461466a368bc672f70fdd9085d05f760` instead probes a demonstrably noncanonical tip. **This does not establish persisted journal-tip provenance, exact-head cross-database atomicity, or real execution.** Further authenticated custody would require an independent durable witness and a separately reviewed integration design, not a fabricated assertion.

The corrected source and tests are being checked by independent per-HEAD CI. At this addendum's initial preparation the [#42398428829](https://github.com/Iam-2squared/ark-ai/actions/runs/42398428829) corrected test HEAD was QUEUED, and its all-six platform verdict was **NOT YET VERIFIED**. No duplicate CI was dispatched. Earlier failing runs remain recorded as failures.
