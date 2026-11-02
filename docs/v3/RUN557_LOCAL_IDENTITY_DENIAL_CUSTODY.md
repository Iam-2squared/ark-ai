# Run557 — Local V3 identity bundle: original denial custody

**Scope:** passive, local-files-only metadata review; **V3 NOT_PASSED**. No real
HF revision, model/tokenizer bytes, GPU, Candidate, human review, protected
V2 evaluation, cost authorization, or promotion is claimed here.

## Boundary strengthened

`src/ark/learning/identity_bundle_verify.py` now retains the imported
definitions of all four authority-denial properties on both
`LocalIdentityBundleWitness` and `LocalIdentityArtifactWitness`.
A callback that returns `False` from a replacement property is **not** the
same denial mechanism. The verifier checks original definitions before local
file scans, at each pin/witness stability boundary, and during retained-bundle
verification. Late descriptor swaps are rejected, rather than re-baselined
after verifying syntactically well-formed local JSON and SHA-256.

The validated object still does **not** prove that the separately retained
hash belongs to a trusted artifact, nor that multiple file scans are atomic.
No component may authorize training, spend or release. No frozen contract,
dataset, reviewer decision or gate was changed.

## Implementation and test evidence

- Source: commit `4845dedb58bc7ce465479f597032e16cac1491b1`.
- New tests: `tests/v3/test_identity_bundle_original_denial_custody_run557.py`,
  commit `59f928dfb4ff33a97ad359c8a86277d4dccc6c7c`:
  **19 authored cases**, covering both witness classes' four preinstalled
  false-only substitutions at inspection/recheck, two delayed verifier
  callback replacements, and a valid unapproved local fixture.
- First code/test CI `41457434384` **FAILED** because earlier tests
  expected later callback invocation and diagnostics before the new
  pre-file-read quarantine. Those tests were revised without relaxing
  the source guard; reentrant late-callback coverage is retained.
- Corrected code/test CI **41457912314: 6/6 GREEN**, Linux and Windows
  Python 3.11, 3.12, 3.13. The run validates the source/test HEAD
  `34c3bdab4ebb067d1eb5163281c2295ed39aa24d`.
- New test counts denote authored cases, not independently executed
  local pytest commands. CI is GitHub-hosted, not an independent
  attestation of materialized model identity or user approval.

## Next prerequisite

Only individually authorized, independently pinned, locally materialized
model/tokenizer identity and the separately gated human-reviewed evidence
may be considered for a future explicit-approval path. This record does not
open such a path, authorize an external GPU action, or permit a main merge.
