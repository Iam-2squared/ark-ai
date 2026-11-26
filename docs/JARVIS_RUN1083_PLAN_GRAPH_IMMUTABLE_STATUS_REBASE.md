# Run1083 — immutable PlanGraph status snapshots rebase

## Exact basis
- Parent: Draft PR #8, `research/jarvis-foundations`
- Parent HEAD at branch creation: `916aae6c6578086fee5e83c77c23375712676c90`
- Prior reviewed child: Draft PR #209, `research/run1079-plan-graph-immutable-status`
- Prior child HEAD: `49dc4994bc57e04a029ea033e4288d3458c20900`
- Prior exact-head CI: run [44943059185](https://github.com/Iam-2squared/ark-ai/actions/runs/44943059185), GREEN 6/6. This result does not transfer to this rebase.

## Rebased change
Reapply immutable PlanGraph status publication. Status readers receive exact MappingProxyType snapshots; ordinary reassignment of the status mapping and epoch witnesses is rejected; complete direct and cascading transition results are staged before the next immutable mapping and epoch are published. The original `__setattr__` implementation is pinned before status use.

The repaired regression fixtures use the mapping-proxy backing dictionary only for deliberate reflective-drift simulation and `object.__setattr__` only for explicit private-epoch fault injection. Ordinary mutation remains denied. Existing dependency gating, revision checks, terminal propagation, topology digest, journal schema and transition semantics are preserved.

## Scope and limits
- This is in-process mutation hardening, not a Python sandbox, independent durable custody, cross-process CAS, trusted authorization or proof of external effects.
- Synthetic tests only. No planner dispatch, automatic replay, paid/external compute, Candidate, training, protected V2 evaluation, frozen-contract change, live data, credentials, UI/frontend work or main merge.
- PR #8 remains Draft/unmerged. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required for this rebased child.
