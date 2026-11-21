# ARK AI — Run668: non-UI recovery fence, coherent Memory WAL and READ preflight custody

## Scope and evidence standard

This record covers a free-only, reversible source/test change sequence based on
`4249fda3b6cf82b73907fe1d78ceb77f33828023` on Draft PR #8
(`research/jarvis-foundations`). It does **not** establish ARK/JARVIS PASS.
No real backend, training, Candidate adapter or weights, physical PC action,
network/tool dispatch, paid API, GPU, frontend/UI, protected V2 evaluation,
contract update or main merge occurred. PRs #5/#8/#9 remain Draft/unmerged.
`docs/PROJECT_STATUS.md` is the canonical latest checkpoint, not this note.

## Package A — Planner recovered hold fence

- Source `ceb866f4815b392b13d9121d97640113ba1562ed`: imports and pins
  the detached fence reviewer across module aliases, original claim/result
  carriers and deny-only descriptors at each projection stability boundary.
  The returned `plan_id` and decision membership/order must match the
  recovered exact DAG; the result remains dispatch/write/replay denied.
- Regression `7de5ba3b697d7d78029a56077739615b8622a68e`: five
  authored tests for honest non-executing projection, two counterfeit
  review callbacks and two executable class-level descriptor substitutions.
- [CI #42283133918](https://github.com/Iam-2squared/ark-ai/actions/runs/42283133918)
  produced a genuine Ubuntu 3/3 failure: one **test-only** expectation wrongly
  anticipated `HELD_WRITE_APPROVAL` for a pending WRITE dependent on an
  unverified pending READ. The correct existing semantic state is
  `WAIT_DEPENDENCY`. Test-only fix `1eaf2b9a4fba35b649a8785dc9a4f8732a0bae3e`;
  [correction CI #42283873739](https://github.com/Iam-2squared/ark-ai/actions/runs/42283873739)
  was later seen failing due to *other then-unfixed Memory test expectations*,
  not because of a new execution path. No policy semantics were weakened.

## Package B — retained coherent Memory WAL review

- Source `5b56dc9147b07f48fbc46f42eb6a0413afb5a804` pins original
  `RetainedCoherentMemoryReview` class, exact field slots, initializer,
  inherited lookup hooks and six denial properties **before** private row
  iteration and again across SQL, hash and constructor callback boundaries.
  A forged getter is refused without invoking it.
- Regression `ebf230ff28ce9966f1caf3f000b29fdafbaf2ed0`: six
  authored tests for early class/constructor/slot/denial rejection,
  constructor substitution in a reentrant digest, and honest inert snapshot.
- Early Ubuntu CI [#42283390269](https://github.com/Iam-2squared/ark-ai/actions/runs/42283390269)
  and [#42283505485](https://github.com/Iam-2squared/ark-ai/actions/runs/42283505485)
  exposed ten inherited test cases expecting a **later**
  `after final denial` failure. Under stronger protection, the unsafe
  descriptor is now refused before the first row read. Test-only repair
  `d2819bc767dd2f1d126e7db939aea0866f4870d5` updates the expected
  fail-closed point and explicitly asserts injected callbacks were never
  invoked. [Correction CI #42284052635](https://github.com/Iam-2squared/ark-ai/actions/runs/42284052635)
  subsequently had Ubuntu Python 3.11 and 3.12 GREEN when last checked,
  remaining jobs not yet confirmed.

## Package C — disconnected registry-bound READ preflight

- Source `4e955e4ccdadfab22247876edde6cb778dd43fc1` pins the
  `DisconnectedReadPreflight` original constructor, all five field slots,
  lookup hooks, and denial properties before registry/grant processing
  and before constructing the inert response.
- Regression `121ee946cf1726e3efab5f962337f1000554af55`: five
  authored tests including original request-bound READ and four
  counterfeit class/constructor/slot/getter substitutions; no backend runs
  or one-shot token is consumed.
- Existing lookup-substitution test adapted in
  `90fe25a7e1b5bb151beabf57119efba25e9fa005` to assert **earlier**
  refusal, rather than executing a swapped getter then rejecting later.
- Source [CI #42284374300](https://github.com/Iam-2squared/ark-ai/actions/runs/42284374300),
  test [#42284478609](https://github.com/Iam-2squared/ark-ai/actions/runs/42284478609)
  and corrected [#42284587704](https://github.com/Iam-2squared/ark-ai/actions/runs/42284587704)
  were IN PROGRESS/QUEUED in the sampled window. Do not infer final PASS.

## Evidence interpretation and limitations

The inherited Run667 exact-HEAD [#42275176894](https://github.com/Iam-2squared/ark-ai/actions/runs/42275176894)
was independently checked **GREEN 6/6** (Ubuntu/Windows 3.11/3.12/3.13).
For Run668, **16 authored new test cases** across three new test files
are NOT certified all-PASS or exact-final-HEAD 6/6 GREEN until the actual
six job conclusions are checked. Intermediate failures remain real;
corrected later commits do not retroactively make failed earlier runs GREEN.

All receipt digests, synthetic SQLite witnesses, supplied clock values,
local registry checks, and dependency-hold labels are **diagnostic only**.
They do not attest writer/actor identities, trusted occurrence time,
human consent, provenance of independent storage, real tool outcome,
cross-store atomicity, exactly-once external effects or permission to replay
an ambiguous WRITE. An unsafe callback rejected before execution also does
not prove the surrounding interpreter or external system is uncompromised.

## Next plan / 今後の方針

1. Verify exact latest HEAD across all six jobs; inspect failing logs and
   resolve any true regressions through the normal non-bypassing Contents
   path only, never by weakening a fail-closed decision.
2. Connect a separately reviewed success-result receipt into Planner
   recovery **only after** identity, event chronology and receipt provenance
   are independently validated; keep the existing unconditional rejection
   of unreceipted `SUCCEEDED` states.
3. Extend Memory CAS/COMMIT-UNKNOWN, ABA, expiry and same-WAL snapshot
   invariants, retaining manual reconciliation and no automatic write retry.
4. Cross-check ToolRegistry/PermissionGate/occurrence/audit-before-action,
   proactive startup quarantine and privacy/Observation fixtures using
   disconnected mocks; defer all real execution, protected V2 evaluation,
   Candidate promotion, UI work and main integration to their gates.
