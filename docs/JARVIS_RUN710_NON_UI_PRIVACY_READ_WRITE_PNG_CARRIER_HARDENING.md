# ARK AI — Run710 NON-UI evidence / 2026-11-08 JST

**Status: FREE-ONLY, disconnected/mock-only, NOT_PASSED.** This document records four independent, reversible source/test work packages. It does not grant access to real tools, audio/video devices, private contexts, GPU compute, Candidate training, protected evaluation or external effects.

- **Work-basis branch/PR:** `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). **Initial exact HEAD:** `fb51f8e3596c2828d87ec9394940f052716a90a0`. **Pre-report HEAD:** `0079b0a6af1d66e1a101ec84dd40035fcc522ba9`. The final checkpoint-result HEAD must be read independently after the subsequent single `docs/PROJECT_STATUS.md` write.
- **Recorded at:** `2026-11-08T19:51:41+09:00` (administrative connector runtime wall-clock only, **not trusted clock / authenticated attestation**).

## A. Privacy retention — real CI failure recovery

The previous exact checkpoint [CI #42468758347](https://github.com/Iam-2squared/ark-ai/actions/runs/42468758347) completed **FAIL across all six** Ubuntu/Windows Python 3.11–3.13 jobs. Ubuntu 3.11 recorded **12 failed, 11,042 passed, 1 skipped**; Windows 3.11 recorded **12 failed, 10,983 passed, 60 skipped**. All 12 failures were `tests/test_retention_recheck_result_custody_run423.py` legacy expectations. New fail-closed `SyntheticRetentionRecheck.__init__` pre-access custody rejects with `original denial implementation` before any private inventory read, whereas older tests expected 4 reads and downstream mutated-field diagnostics.

[Commit `5fe95d1`](https://github.com/Iam-2squared/ark-ai/commit/5fe95d121384c579d23eb94daa9df6a51bd24626) updates the existing 12 parametrizations to require rejection before private inventory projection and before hostile constructor invocation. No production privacy check or authority semantics were weakened. CI [#42472512909](https://github.com/Iam-2squared/ark-ai/actions/runs/42472512909) had Ubuntu 3/3 GREEN, Windows 3/3 **IN PROGRESS** at this report's preceding inspection, not 6/6 final GREEN.

## B. Planner detached READ journal pre-access

[Source `c7d196d`](https://github.com/Iam-2squared/ark-ai/commit/c7d196dc487d2e4dbdcf127b47866a23bdbb0747) corrects the evaluation order in `DisconnectedReadJournal.recover_receipts`: `_check_witness(retained)` must check import-original dataclass field descriptors and lookup hooks **before** reading `retained.count` or `retained.tip_sha256`. The former order allowed executable substituted getters to run before validation. [Tests `50cea40`](https://github.com/Iam-2squared/ark-ai/commit/50cea40d25a1c518b3c8acf28851c4f8c76d39c5) add 5 isolated Python-process cases: count/tip slot, lookup, constructor hook and deny-only descriptor. A closed synthetic handle makes preaccess ordering explicit. No real READ backend or action replay.

## C. Durable WRITE slot receipt pre-access

[Source `522c478`](https://github.com/Iam-2squared/ark-ai/commit/522c478ef5972f5b29a544e0d242e7cd0fc0d060) extends `_require_original_constructors` to bind original `WriteSlotReservationReceipt` field slots and getter/new hooks. An untrusted descriptor can otherwise execute at receipt inspection after SQLite reservation COMMIT; fail-closed validation now precedes the reservation. [Tests `89c3426`](https://github.com/Iam-2squared/ark-ai/commit/89c3426cc886da989936f66e203518579c84aa54) add 4 subprocess hostilities and 1 healthy non-authorizing reservation. A locally unique slot **does not** establish consent, a trusted clock, registry authority or exactly-once external effects.

## D. Observation PNG privacy/provenance carriers

[Source `738c7e0`](https://github.com/Iam-2squared/ark-ai/commit/738c7e0006ef76b7796aa0f8be322d6241d8030b) pins import-original `OfflinePngRequest` fields/constructor/lookup hooks **before reading sensitive synthetic PNG bytes** and `OfflinePngInventory` fields/constructor/lookup hooks before emitting a result. The request check is repeated before and after validation callbacks (including CRC). [Tests `0079b0a`](https://github.com/Iam-2squared/ark-ai/commit/0079b0a6af1d66e1a101ec84dd40035fcc522ba9) add 7 interpreter-isolated cases for preinstalled request/result slot, lookup and constructor substitutions and a CRC callback-injected request replacement. This is still metadata-only PNG framing review, **not** pixel verification, consent or camera provenance.

## Verification limits and next plan

**New tests authored: 17** (5 READ + 5 WRITE + 7 PNG) plus **12 corrected existing privacy parametrizations**. The new source/tests have been saved through the ordinary GitHub Contents API. No local repository-wide pytest/Ruff execution, full six-environment GREEN, paid compute, physical-PC verification, real model or human-review result is claimed. Distinguish the prior last confirmed six-job GREEN [#42464738344](https://github.com/Iam-2squared/ark-ai/actions/runs/42464738344) on a prior HEAD from incomplete Run710 CI. Do not duplicate CI runs; inspect actual job failures and apply the smallest preserving fix.

1. Check all six jobs for the final exact HEAD, especially Windows subprocess isolation, test collection, Ruff and injected descriptor diagnostics. If a failure occurs, correct without weakening fail-closed ordering; meanwhile investigate independent Memory/Planner recovery lanes.
2. Continue Memory generation-CAS/ABA and COMMIT-UNKNOWN manual-only triage, Planner durable READ terminal evidence, immutable registry-bound authorization, audit-before-action and deterministic disconnected/mock execution. Integration requires exact-head GREEN lower-layer evidence.
3. Keep PR #5 V3 approval/training protected, PR #8 foundations Draft, PR #9 completed UI foundation untouched/Draft. No UI/frontend development; frozen V1/V2/Local UI/Launcher boundaries preserved; no main merge or authorization crossing.

**Boundary summary:** no new paid/possibly billable service, external GPU, credentials, irreversible action, external dispatch, automatic replay, Candidate generation/promotion, V2 final gate opening, protected contract changes or fabricated hashes/identities/evidence. ARK/JARVIS/V3 remain **NOT_PASSED**.
