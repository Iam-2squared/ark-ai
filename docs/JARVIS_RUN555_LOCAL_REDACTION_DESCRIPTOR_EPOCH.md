# Run555 — Privacy-safe offline redaction descriptor epoch

## Scope

This is a standalone, disconnected synthetic text-masking fixture. No private
Memory record, personal account, live microphone, camera, network endpoint,
notification or ToolBackend is used. Redacted output **is not consent,
irreversible erasure, verified anonymization or export authority**.

## Implementation

In `src/ark/offline_context_redaction.py`, the four False-valued
`RedactedOfflinePreview` denial descriptors are retained **before** the
potentially reentrant result constructor and callback checks. Final
post-denial integrity verification now detects a later swap of an earlier
denial getter, even if the replacement also returns False.

Unlike an import-time custody contract, this fixture accepts an explicitly
installed False-only denial callback present at review start, but refuses a
replacement of that established callback during its own review. Earlier
fixture tests intentionally allow this behavior; it does not authenticate a
callback or grant any permission. The masked string, exact owner/scope/source
digests, masked-character count and output digest remain checked against
their original values.

`tests/test_offline_redaction_denial_descriptor_epoch_run555.py` adds four
parameter-expanded cases: three reentrant substitutions of an already
checked privacy/authority getter by the final False getter, and one clean,
fully masked non-authorizing receipt. Authored cases are **not** independent
local pytest PASS evidence; confirm the exact source/test HEAD six-job CI.

## Boundaries

The caller supplies the masking ranges; this is not a PII detector.
Incomplete masking can expose raw text, and even complete masking is not
anonymization proof. No erasure, consent, content export, real notification,
cross-store atomicity or external effect follows from a successful preview.
Frozen Memory/Planner contracts, V1/V2/Local UI/Launcher evidence and main
remain unchanged. PR #8 stays Draft/unmerged.
