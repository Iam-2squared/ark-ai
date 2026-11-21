# Run558 — Passive local identity artifact: original-denial custody

This is an offline, zero-cost V3 guard improvement on Draft PR #5.
It changes neither frozen V3 Contract 1 nor its human and training gates.

## Implemented

`src/ark/learning/identity_artifact_verify.py` now pins the four original
`LocalIdentityArtifactWitness` authority-denying property descriptors at
module import, before any caller callback can replace the baseline.
`verify_local_identity_artifact` rejects substituted callbacks immediately
before opening a local file, and checks them again after constructing and
reading the synthetic report. Returning `False` alone is no longer enough:
a replacement getter could itself read/modify private files or fabricated
evidence. The existing bounded canonical-JSON, retained SHA, alias, inode,
byte-recheck and no-network constraints remain unchanged.

`tests/v3/test_identity_artifact_original_denials_run558.py` adds six
new parameter-expanded cases: four preinstalled False-only denial
substitutions prevented **before local file opening**, one later constructor
substitution rejected, and one clean file review. Earlier getter-mutation
tests in `test_identity_artifact_denial_epoch_run505.py` and
`test_identity_artifact_postparse_custody_run501.py` were aligned with
the stronger pre-read refusal. Independent later constructor/file-change
tests in the existing suite remain in place.

## Exact evidence and limitations

- Work-basis PR #5 HEAD:
  `a0993bfdd35ad7992095ff0b3216f994b8b3bbb9`.
- Source `d8a14c849c52cae971c09ced5b9f1f1fc31484e7`;
  new tests `856c8510e3c77884a0cf84ce4f5b7621361fab76`;
  inherited regression corrections
  `82a6735b7cfa09b5cef59f51d126c860564e9053`,
  `cdcf2f27f99fcd4a1314e24308d8f847cec46e3e`.
- Original source-head CI
  [41473615331](https://github.com/Iam-2squared/ark-ai/actions/runs/41473615331)
  failed only 10 inherited expectations now superseded by pre-read rejection.
- Corrected exact source/test CI
  [41473823605](https://github.com/Iam-2squared/ark-ai/actions/runs/41473823605)
  **6/6 GREEN** (Ubuntu/Windows Python 3.11–3.13), verified before this
  technical note was written.

These are deterministic passive local fixtures, **not** model identity,
copyright/provenance attestation, reviewed data, user consent, GPU approval,
real Candidate/adapter generation, protected V2 evaluation, promotion,
or main merge. V3 stays Draft and NOT_PASSED. A file SHA is not a human signature.
