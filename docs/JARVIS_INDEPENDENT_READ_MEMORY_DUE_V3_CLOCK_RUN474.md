# ARK AI Run474 — Independent READ grants, Memory event witnesses, due-slot receipts, V3 clock budgets

**Evidence observation:** 2026-10-30 16:56 JST. This is an automation working-clock observation, not independently authenticated time, consent, billing approval, or a GitHub commit timestamp.
**Scope:** Free-only, local-first, disconnected/mock or synthetic validation. No external ToolBackend dispatch, paid GPU, real Candidate, protected final V2 evaluation or main merge.

## Exact code basis and packages

- **PR #8** `research/jarvis-foundations`, final source/test HEAD `d8d7743d69d210cec05a9de7115358f52dd8c965`, Draft/open/unmerged. Work began at Run473 checkpoint `112c31d9eb7dd3444c855ff9b352f7a41e7258b9`.
- **PR #5** `research/v3-learning-evaluation`, final source/test HEAD `93352996075ccdcf001b133d6bca6d7f886a2ba5`, Draft/open/unmerged. Work began at `05e82f883ffa40c80e406db372afee2007f29ab3`.

1. **Planner READ simulation — independent preflight verification**: `src/ark/agency/disconnected_read_cycle.py` blob `238b4a2491c6cf27db7a6bd8e98780f35f2c32be`; `tests/test_disconnected_read_cycle_independent_gate_run474.py` blob `ad3ed4b4f5091f10cfbe563fa4a3212fbf331898` (7 synthetic pytest cases). A forged exact-type preflight receipt cannot skip the PermissionGate for ready READ steps, hide registered WRITE descendants, or replace a grant/fingerprint hash. The full graph's registered effect and ready grant must be independently checked each wave, without invoking any backend. A first source commit contained a wrong escaped NUL separator for the recomputed preflight digest; corrected on the ordinary Contents API path at commit `7da2af96080ad14cb6b05419d7c04d9ad4db208f` BEFORE committing new tests. Do not cite the older intermediate source commit as validating the corrected code.
2. **Memory event witness carrier/history integrity**: `src/ark/memory/synthetic_event_continuity_review.py` blob `6044e052dcb47479a806522fb0732f8ba9152621`; `tests/test_memory_event_chain_receipt_epoch_run474.py` blob `5006aa35ef5f33cb90af9853e9f183b18771a476` (5 synthetic cases). Pin original inert witness class, reject constructor-result substitution and equal-value carrier replacement, and revalidate all previously created prefix witnesses before accepting an event-chain review. No Memory v1 DDL, retention policy or live user content changed. Local hashes still require genuinely independent custody to detect coherent storage rollback.
3. **Disconnected due reservation post-COMMIT custody**: `src/ark/agency/disconnected_due_reservation.py` blob `40093179080cd8f8f403baa6c268b60e1cc9bb7a`; `tests/test_due_reservation_receipt_epoch_run474.py` blob `d368c3af0dd54200577bd0d7d2cdb7a68a0a40ed` (6 synthetic cases). Retain exact prior witness identity through SQLite callbacks, validate constructed digest witnesses and post-COMMIT inert receipt fields. A post-COMMIT diagnostic failure never asserts that a durable reservation was rolled back; no retry or external action follows.
4. **V3 local runtime budget monotonicity**: `src/ark/learning/runtime_guard.py` blob `c8a693521144f1df1706567c5cb969e5f12defa1`; `tests/v3/test_wall_time_budget_occurrence_run474.py` blob `256ad7cd6a1f1d6120756e8225aca371d8e3b841` (13 synthetic cases). Reject float-coercible non-exact clock carriers, reject a clock reading that regresses from any prior accepted reading, and make an observed timeout terminal for that budget instance. This is a soft in-process, caller-clock check, NOT a trusted clock or externally enforced spend cap.

**Total:** 4 implementation/test packages; 31 parametrized synthetic pytest cases authored; 9 normal Contents API source/test commits including one immediate source correction. Source/test blobs listed above were independently re-fetched from their final branch refs and their SHA identities matched. This does not prove isolated local pytest execution.

## CI and evidence distinction

- **V3 exact final source/test HEAD** `93352996075ccdcf001b133d6bca6d7f886a2ba5`: GitHub Actions **#1543 / run `41022814309` COMPLETED SUCCESS**, all 6 Ubuntu/Windows Python 3.11–3.13 test jobs explicitly reported success; Ruff included.
- **PR #8 exact final source/test HEAD** `d8d7743d69d210cec05a9de7115358f52dd8c965`: GitHub Actions **#1545 / run `41023005254` IN PROGRESS at evidence observation**; all six jobs began, none yet claimed GREEN. Intermediate #1538 / `41022351487` COMPLETED SUCCESS for **older** source-only HEAD `7da2af96080ad14cb6b05419d7c04d9ad4db208f`, and historical Run473 #1534 / `41016303125` COMPLETED SUCCESS. Neither is substituted for a final PR #8 source+test GREEN.
- **Local full pytest/Ruff** NOT VERIFIED: the isolated container cannot resolve the GitHub hostname to clone the repository. Do not claim local execution or full JARVIS PASS.
- Repo was independently observed **PUBLIC**. Only normal GitHub Contents API writes/automatic public-repository GitHub Actions were used; no manually duplicated workflow runs, protected evals, paid compute or external GPU sessions.

## Isolation, limits, next gates

All new READ/due functions remain disconnected and cannot dispatch ToolBackend actions, grant consent or authenticate time. The V3 budget is neither an external provider billing cap nor cryptographically authenticated execution proof; independent runtime/GPU/driver, model/tool bytes, human data approvals, JPY/time ceilings and service-side limits remain unresolved.

Preserve frozen V1/V2/Local UI/Launcher contracts and evaluation evidence; Memory v1 schema; V3 Contract 1 with exactly 120 training/30 validation, one Candidate/no sweep; contamination, provenance, regression/reproducibility gates; V2 protected final evaluation gate; and both Draft/unmerged PRs. No live secrets, connected accounts, physical PC actions, irreversible writes or main merge.

**Next:** confirm exact-head #1545 six-job result, repair any real regression with smallest normal write; then advance Memory durable history/expiry audits, Planner UNKNOWN WRITE recovery and audit-before-action, proactive scheduling/replay resistance and V3 free-only identity/path verification. Full JARVIS remains NOT_PASSED.
