# ARK Run1378 — Observation fixture encoder self-custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `e212e77cb3432e0e226cebd4b9c1f2836eb064bc`.
- Parent source blob before the change: `01e9638d9fa18bfead66f52ed0f8a2f1377a6845`.
- Rebased source content blob: `1ed7f66a4eab80a5378527e851972244c8a48846`.
- Child branch: `research/run1378-observation-encoder-custody-latest-20261125`.
- Rebased from Draft PR #540 / Run1361. Its exact-head CI run `45553163237` was GREEN on the older base only; it does not transfer to this exact parent.

## Finding and change

The disconnected Observation fixture text adapter retained the original bounded UTF-8 encoder in one alias, but a mutable module binding and the retained alias/vector could be substituted together. A replacement could otherwise receive caller-private text after metadata preflight.

The adapter now holds the import-time encoder in an identity vector, verifies the vector and callable at the fixture budget guard, and invokes the retained callable. This closes the simultaneous module/alias/vector substitution covered by the synthetic regression. The UTF-8 byte-budget algorithm and Observation Envelope v1 contract are unchanged.

## Regression coverage

- Preinstalled replacement of the bounded text encoder.
- Replacement during metadata preflight.
- Simultaneous replacement of the module binding and retained alias.
- Retained-vector substitution.
- Denial before the replacement receives private fixture text or the hash callback runs.

## Scope and evidence boundary

This is a disconnected in-memory fixture adapter only. No live capture, camera, microphone, screen, file/network access, dispatch, consent, source authenticity, or production readiness is claimed. No schema/API/lineage/retention/frozen-contract change.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No PASS is claimed before that run completes. No paid/external compute or service, Candidate, protected V2 evaluation, credentials, hardware, destructive action, main merge, or UI/frontend work. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched.
