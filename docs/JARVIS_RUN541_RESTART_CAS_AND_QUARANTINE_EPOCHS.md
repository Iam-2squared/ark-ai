# Run541 — disconnected restart, Memory CAS and schedule prefix custody

**Scope:** three independent local-only source/test packages on Draft PR #8. Nothing authenticates a real WRITE, authorizes retries, invokes a ToolBackend, starts timers, contacts providers or proves consent/clock identity.

## 1. WRITE restart final callback custody

- Source: `37c0c76bbb858ffd7790aa0b05fd862ccbba0fb6`, `src/ark/agency/disconnected_write_restart_binding.py`.
- Tests: `9b4d664e159f3e8efce4bd32a118b1b1c4930e84`, `tests/test_write_restart_final_callback_custody_run541.py` (**6 authored cases**).
- The six false-only `OfflineWriteRestartReport` authority descriptors are retained before invoking getters. A getter cannot replace another descriptor with a False-only equivalent; the last independent SQLite ledger read is followed by revalidation of original Planner step claims, recovery dispositions and the report. The ledger remains a synthetic slot witness, not proof of external execution.

## 2. Memory post-COMMIT ambiguity review

- Source: `6b8605de72e2f92bfc424d5aebf123f7bf42eb13`, `src/ark/memory/generation_cas_outcome_review.py`.
- Tests: `24386f8c96ea46e3dc125c441f1c1c4de1b74dd6`, `tests/test_memory_cas_outcome_exact_epochs_run541.py` (**6 authored cases**).
- Replace patchable dataclass equality in the twice-read ambiguous-outcome comparison with exact generation-token field vectors, including the final post-denial SQLite observation. Pin the original observation and equal-text output carriers across callbacks. A post-COMMIT exception remains **manual-only UNKNOWN** even when a matching row is visible; identical bytes cannot attribute the committing writer or grant retry.

## 3. Scheduler restart quarantine prefix review

- Source: `eea2e514ecd276051898b2754026063c1d8f0325`, `src/ark/offline_schedule_resume_review.py`.
- Tests: `5d3f9db1232fd1110b41997c161aab7446e7aabc`, `tests/test_offline_schedule_resume_witness_equality_run541.py` (**4 authored cases**).
- Compare exact count and chain SHA-256 fields at each of the three independent quarantine inspections. A synthetic `QuarantineWitness.__eq__` overridden to always return True cannot make a forged source callback match the retained prefix. No timer, alert, replay, consent or trusted-clock status is inferred.

## Evidence / CI

- The inherited Run540 checkpoint HEAD `a54f0d1cbb3722e972afdc6261eb8091a76f6837` has all six GitHub Actions jobs GREEN: [41354812977](https://github.com/Iam-2squared/ark-ai/actions/runs/41354812977). **That is the older work basis only.**
- New runs at technical-note creation (no claim that they have completed): `[41359323477](https://github.com/Iam-2squared/ark-ai/actions/runs/41359323477)` HEAD `5d3f9db1232fd1110b41997c161aab7446e7aabc` queued/NOT YET VERIFIED; `[41359275633](https://github.com/Iam-2squared/ark-ai/actions/runs/41359275633)` HEAD `eea2e514ecd276051898b2754026063c1d8f0325` in_progress/NOT YET VERIFIED; `[41359214982](https://github.com/Iam-2squared/ark-ai/actions/runs/41359214982)` HEAD `24386f8c96ea46e3dc125c441f1c1c4de1b74dd6` in_progress/NOT YET VERIFIED; `[41359170156](https://github.com/Iam-2squared/ark-ai/actions/runs/41359170156)` HEAD `6b8605de72e2f92bfc424d5aebf123f7bf42eb13` in_progress/NOT YET VERIFIED; `[41358873768](https://github.com/Iam-2squared/ark-ai/actions/runs/41358873768)` HEAD `9b4d664e159f3e8efce4bd32a118b1b1c4930e84` in_progress/NOT YET VERIFIED; `[41358828641](https://github.com/Iam-2squared/ark-ai/actions/runs/41358828641)` HEAD `37c0c76bbb858ffd7790aa0b05fd862ccbba0fb6` in_progress/NOT YET VERIFIED.
- **16 new authored parametrized cases**, not independently executed local pytest PASS. CI jobs, including Windows 3.11–3.13, must be inspected at each exact HEAD. This note's Contents write creates another distinct HEAD/CI.

## Frozen contracts and safety

Frozen Memory v1, Planner, V1/V2/Local UI/Launcher, V3 contract/evaluation boundaries, and main are unchanged by these isolated packages. No paid compute or API, credentials, Candidate generation, real microphone, actual retention deletion, destructive file operations, human sign-off, protected V2 evaluation or PR merge. PR #5 and #8 remain Draft.

## Next plan

1. Check latest exact-head tests/CI, fix only verified failures by normal Contents API; no equivalent workflow reruns.
2. Advance Planner FAILED/BLOCKED persistent fixtures with registry-bound READ receipts under independently GREEN lower-layer evidence.
3. Reconcile Memory expiry/revocation with generation fenced CAS and ambiguous outcomes without ever authorizing automatic retry.
4. Extend synthetic scheduler occurrence/clock audit and privacy-safe startup readiness. All clocks remain caller assertions until real trust evidence exists.
