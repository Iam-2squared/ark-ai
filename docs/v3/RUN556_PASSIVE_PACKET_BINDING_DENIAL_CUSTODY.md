# Run556 — Passive V3 packet binding: original denial descriptors

This record covers a **local, read-only, unapproved** packet verifier. It
does not authorize preflight, training, external GPU/API use, Candidate
creation, protected V2 evaluation, promotion, or main merge.

## Threat and change

A third party can replace a `LocalPacketBindingWitness` property with a
different property that still returns the literal `False`. Checking only
`getattr(witness, permission) is False` is insufficient to establish that the
shipped deny-only property remains intact. This change captures original
descriptor identities when `authorization_packet_verify` is imported and
rechecks all four identities **after** the final snapshot/packet epoch checks
and reflective denied-authority callbacks.

- Source: `src/ark/learning/authorization_packet_verify.py`
  ([commit d0a5fe45](https://github.com/Iam-2squared/ark-ai/commit/d0a5fe45a66963b0699e5e909a4fb01e93860fcf)).
- Regression: `tests/v3/test_packet_binding_original_denials_run556.py`
  ([test commit 13fc9c3e](https://github.com/Iam-2squared/ark-ai/commit/13fc9c3ebdbbe11f52ae511d17aad52925d108de)).
  Four preinstalled False-only replacements, one post-construction
  False-only replacement, one unchanged passive fixture (**6 authored
  parametrized test cases**; NOT 6 independently verified PASS results).
- Ruff I001 import-group correction only:
  [f9600822](https://github.com/Iam-2squared/ark-ai/commit/f9600822e89d8fc3089743b432ae8ea66dfc3f5a).
- CI: [test-head run 41447230372](https://github.com/Iam-2squared/ark-ai/actions/runs/41447230372)
  failed at Ruff I001; corrected-head CI
  [41447401309](https://github.com/Iam-2squared/ark-ai/actions/runs/41447401309)
  was QUEUED when this note was prepared. Final result must be checked on
  its exact HEAD; do not imply GREEN from earlier V3 runs.

The unchanged snapshot/packet immutable-input checks and digest bindings
remain in place. This is an in-process reflection guard, **not** an external
provenance attestation, human authorization or verified model/file identity.

## Non-negotiable boundaries

Frozen V3 Contract 1, frozen V2 evaluation policy and all historic gates
remain untouched. PR #5 stays Draft/unmerged. External/potentially billable
compute, Candidate generation, protected evaluation, automatic promotion,
and irreversible file mutation remain forbidden without their explicit gates.
