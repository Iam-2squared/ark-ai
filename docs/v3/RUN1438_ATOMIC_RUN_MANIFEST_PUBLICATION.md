# Run1438 — crash-consistent create-only V3 run-manifest publication

## Exact basis

- Parent: gated Draft PR #5, branch \`research/v3-learning-evaluation\`.
- Exact parent work-basis HEAD: \`ea373c3496d06e2789cee5bb58836054ef35ed28\`.
- Child branch: \`research/run1438-v3-atomic-manifest-publication-20261126\`.
- Source: \`src/ark/learning/run_manifest.py\`.
- Regression tests: \`tests/v3/test_run_manifest.py\`.

## Finding and correction

The previous writer opened the final \`run-manifest.json\` with exclusive-create mode and streamed bytes directly into the visible final path. A process crash during the write could leave a partial final filename, making later recovery ambiguous and preventing a safe create-only retry.

The revised writer:

1. Builds and canonicalizes the manifest before publication.
2. Writes the complete payload to an exclusive temporary sibling outside the Candidate directory.
3. Handles short writes, verifies the byte count, and fsyncs the temporary file.
4. Uses a same-filesystem hard link to publish the final name atomically without replacing an existing file.
5. Verifies the final path resolves to the completed temporary inode.
6. Fsyncs the Candidate directory on POSIX where directory fsync is supported.
7. Removes the temporary sibling. If publication or cleanup has an uncertain result, it fails closed and instructs the caller to inspect before retry.

No fallback to direct final-path streaming or overwrite is provided.

## Regression coverage

- Partial writes are completed before the atomic link.
- The link callback observes the full canonical payload and a prior file fsync.
- A failed link leaves no partial final manifest and cleans the temporary sibling.
- An existing final manifest is preserved byte-for-byte and never replaced.

## Boundaries and limitations

- Tests use only synthetic local fixture directories and synthetic evidence bytes. No Candidate run was created by this automation.
- This changes only how the existing manifest bytes are published; manifest schema, canonical content, frozen experiment recipe, dataset/provenance/contamination evidence and authorization semantics are unchanged.
- Hard-link support and same-filesystem placement are required. The writer fails closed instead of falling back to a weaker write.
- POSIX directory fsync is attempted; Windows has no equivalent directory-sync path here. This is not a universal power-loss durability guarantee or independent custody.
- A failed/unknown publication may leave a final manifest after the hard link succeeded. The caller must inspect the path before any retry; no automatic retry or overwrite occurs.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result is claimed.

No preflight, model/tokenizer load, GPU query, training, export, Candidate generation/promotion, protected V2 evaluation, paid/external compute, credentials, hardware, destructive action, frozen-contract change, main write/merge, or UI/frontend work occurred. PR #5 remains Draft/unmerged.
