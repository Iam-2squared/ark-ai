# Run1079 — PermissionGate local token-state custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Exact parent HEAD at branch creation: `394f3573e18f0d1d6a8913dbb6e7e0f562012585`
- Child branch: `research/run1079-permission-gate-state-custody`
- Final source commit: `4f880b019e841dc37c181a487e050b3cc2d552a3`
- Final regression commit: `db63e28135ad361a8dedbd692e1ca1887fe46819`

## Finding

The exact-type PermissionGate previously guarded its public authorization methods but retained its consumed-token set and lock as replaceable instance attributes. Replacing the set or clearing it in place could erase process-local replay history; replacing the lock could detach the critical section from the original state.

## Change

- Protect ordinary reassignment of the token ledger, lock and state epoch.
- Capture the original lock factory and exact lock type.
- Maintain a frozenset snapshot of consumed token IDs alongside the original set/lock identities.
- Recheck the state before authorization, after caller-controlled grant iteration, at registered authorization boundaries and after acquiring the token-spend lock.
- Advance the state snapshot only after the original token set is updated under the original lock.
- Reject reflected replacement, in-place removal, invalid token-ledger members and state drift before another token can be spent.

The registry and audit schemas, ToolCall v1, grant matching, token expiry and existing authorization semantics are unchanged.

## Synthetic regression coverage

The new test module covers ordinary state reassignment, reflective set/lock replacement, in-place token-history removal, reentrant grant-iterator mutation, and registered authorization after ledger tampering. Tests use local in-memory objects and a disconnected mock backend; no backend execution is requested by the registered gate tests.

## Evidence and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. The gate remains process-local and in-memory: this does not provide restart-safe approval, trusted time, authenticated consent, independent custody, a sandbox, or exactly-once external effects. The disconnected durable occurrence ledger remains a separate denial-only control.

No paid service, external compute, Candidate, training, protected V2 evaluation, frozen-contract change, live personal data, credentials, physical-PC action, UI/frontend work, PR #5, PR #9 or main merge is involved. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
