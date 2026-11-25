# Run1052 — V3 authorization-packet output reparse-policy pin

## Exact work basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent HEAD: `034c756345b218ce41770ffccad7390a17ec018b`.
- Child branch: `research/run1052-authorization-output-reparse-policy-pin`.
- Source: `src/ark/learning/authorization.py`.
- Regression: `tests/v3/test_authorization_packet_reparse_policy_pin_run1052.py`.

## Finding

The review-only authorization-packet output path guard recognized Windows reparse-point attributes, but its module-level attribute mask was not pinned against rebinding. A present malformed `st_file_attributes` carrier was also treated as if the reparse bit were absent.

## Change

- Pin the import-time reparse-point attribute mask and reject a changed or non-exact-integer policy before metadata access.
- Reject a present malformed metadata-attribute carrier instead of treating it as a non-reparse entry.
- Retain the absent-field default on platforms that do not expose the Windows metadata field.
- Preserve the existing review-only packet schema, exclusive-create behavior and authorization denials.

## Regression coverage

Synthetic tests cover policy-mask rebinding before attribute access, boolean/null/string/float metadata carriers, absent-field portability, and rejection by the packet writer before opening the output. No privileged Windows junction is created.

## Limits and frozen boundaries

This is repeated local metadata admission, not atomic descriptor-relative traversal or hostile concurrent-filesystem-writer protection. Packet creation remains review-only and is not user approval, billing evidence, preflight authorization, Candidate authorization or permission to execute. No model, GPU, converter, quantizer, external service, Candidate, protected V2 evaluation, promotion, frozen Contract 1, main branch or UI branch is accessed or changed.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #5 remains OPEN/DRAFT/UNMERGED; V3 remains NOT_PASSED.
