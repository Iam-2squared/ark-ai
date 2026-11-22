# Run1083 — PermissionGate local token-state custody rebase

## Exact basis
- Parent: Draft PR #8, `research/jarvis-foundations`
- Parent HEAD at branch creation: `916aae6c6578086fee5e83c77c23375712676c90`
- Prior reviewed child: Draft PR #207, `research/run1079-permission-gate-state-custody`
- Prior child HEAD: `c827b6ee4b9b221877e24fb2e5c64b3222f90ac1`
- Prior exact-head CI: run [44944308868](https://github.com/Iam-2squared/ark-ai/actions/runs/44944308868), GREEN 6/6. This result does not transfer to this rebase.

## Rebased change
Reapply the local PermissionGate state-custody guard and its repaired regression fixtures onto the latest foundation. The guard binds the consumed-token ledger and lock to their constructor-owned identities, protects ordinary reassignment, snapshots consumed token IDs, and rechecks state at direct and registered authorization boundaries, after caller-controlled grant iteration, and under the token-spend lock.

The test repair uses the original real lock and set. Deterministic lock-wait and barrier fixtures exercise the under-lock recheck and one-shot concurrency without substituting a fake lock or ledger that the production custody contract intentionally rejects.

## Scope and limits
- Existing grant matching, expiry, registry binding and authorization semantics are preserved.
- This is process-local in-memory state custody, not restart-safe authorization, trusted-clock consent, independent custody, a sandbox, or proof of exactly-once external effects.
- Synthetic tests only. No real ToolBackend dispatch, live personal data, paid service, external compute, Candidate, training, protected V2 evaluation, frozen-contract change, UI/frontend work, credential action or main merge.
- PR #8 remains Draft/unmerged. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required for this rebased child.
