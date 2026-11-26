# Run1079 — PlanGraph immutable status publication

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Exact parent HEAD: `394f3573e18f0d1d6a8913dbb6e7e0f562012585`
- Child branch: `research/run1079-plan-graph-immutable-status`
- Final source commit: `a8192307cfa4d8609dc2f3965647304214097e33`
- Regression commit: `07352cb55ff24352813b86ff5c341ce94a72d7d4`

## Finding

PlanGraph retained a revision/state epoch and checked it before reads/transitions, but the live status mapping remained a mutable dictionary. Ordinary code with access to the private mapping could replace an entry without calling the revision-guarded transition method. The existing epoch check would detect a single unpaired mutation, but the mapping itself did not prevent in-place writes.

## Change

- Publish status as an exact `MappingProxyType` with no retained external backing-dict reference.
- Protect ordinary reassignment of the status mapping and its epoch witnesses.
- On each valid transition, stage all direct and cascading statuses, build a new immutable mapping and complete next epoch, then publish the three references together.
- Pin the original `__setattr__` implementation and reject its substitution before status use.
- Preserve revision checks, dependency gating, terminal propagation, plan topology, journal schema and existing transition semantics.

## Synthetic regression coverage

Five tests cover mapping write refusal, protected state-field reassignment, reflective single-carrier/epoch replacement, immutable snapshot replacement after a valid transition, and terminal FAILED-to-BLOCKED descendant propagation.

## Evidence and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. This protects the in-process PlanGraph status API against ordinary mutation and detects single-field reflective drift; it is not a Python sandbox, independent durable custody, cross-process CAS, trusted authorization or proof of external tool effects. The separate Planner journal/recovery and audit-before-action controls remain required.

No paid service, external compute, Candidate, training, protected V2 evaluation, frozen-contract change, live personal data, credentials, physical-PC action, UI/frontend work, PR #5, PR #9 or main merge is involved. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
