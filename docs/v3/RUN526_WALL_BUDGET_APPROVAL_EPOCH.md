# Run526 — V3 wall-time budget approval epoch (free-only)

**Scope:** standalone local runtime-guard validation, no torch/GPU import, no provider or Candidate operation, no protected V2 opening. PR #5 remains Draft/unmerged, and V3 overall remains **NOT_PASSED**.

## Source and exact evidence

- Work basis: PR #5 HEAD `566b27114a5449e2306a782d3652728958ca7a1c`.
- Production guard: `src/ark/learning/runtime_guard.py` update `db5897477a14c54274057b9375bd23016ee9b590`.
- Tests: `tests/v3/test_wall_time_budget_approval_epoch_run526.py` commit `4bb65b84ea8560b98f9be9abfd836ac91510abc1`. **12 authored pytest cases** (10 post-construction changed field/type examples plus an unchanged approval-boundary example and read-only field inspection).
- Exact source+test CI: [41294678904](https://github.com/Iam-2squared/ark-ai/actions/runs/41294678904), six jobs SUCCESS on Linux/Windows × Python 3.11–3.13. This evidence applies only to that exact head, not a later documentation commit. Local independent pytest/Ruff was not run because container DNS cannot resolve github.com.

## Invariant and limits

A synthetic budget created with approved `started` and `timeout_seconds` retains the original exact float pair. At every controlled `check()` boundary, any changed value or changed scalar type is denied and latched terminally, including an attempted extension of timeout, shift in start time, bool/int substitution, or NaN. Observing those fields without mutation preserves the original inclusive deadline and pre-existing timeout replay fence. The earlier behavior for non-exact supplied clock readings and rollback remains unchanged; this patch does not claim trusted monotonic clock origin or convert a Python attribute into a tamperproof sealed token.

The epoch itself is held inside ordinary local process memory and can be reflectively overwritten by a sufficiently privileged caller. No external actor authentication, OS-enforced process isolation, billing cap or durable audit-before-action is proven. No V3 training authorization, Contract 1, protected evaluation, dataset decisions, or frozen evidence was modified.

## Next safe work

1. Keep the approval snapshot/identity/provenance gate independent of budget diagnostics; do not treat this as paid-run authorization.
2. Only validate protected evaluation after its separate human gate. Continue free-only detached validation, source identity, bounded read and audit evidence development.
