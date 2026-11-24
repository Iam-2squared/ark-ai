# JARVIS Run1281 — Bounded V3 training evidence reads

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `94f68f2b45a512eca79fab2ec043845f4d14c60a`.
- Child branch: `research/run1281-v3-training-evidence-reader`.
- Source change commit: `abcc520ae98aff6d00925ef73c16491deb4ee401`.
- Focused test commit: `43c4943fa74dcba197f2b346ba654061e1a845dd`.

## Change

The private `training_cli._verify_file` path no longer calls unbounded `Path.read_bytes()`. Evidence labels map to explicit finite limits:

| Evidence artifact | Maximum bytes | Existing basis |
| --- | ---: | --- |
| Provenance manifest | 67,108,864 (64 MiB) | Same ceiling already used for dataset JSON ingress |
| Contamination report | 67,108,864 (64 MiB) | Same ceiling already used for dataset JSON ingress |
| Preflight report | 1,048,576 (1 MiB) | Same ceiling already used for canonical run-manifest JSON |

The reader rejects non-regular, linked, symlink/reparse-point, ancestor-reparse, missing, empty, and oversized paths before content use. It opens with no-follow/nonblocking flags where supported, checks the opened descriptor against the pre-open path epoch, reads at most limit + 1 bytes, and rechecks descriptor and path epochs after the read. The existing frozen SHA-256 comparison remains mandatory.

## Validation boundary

The new tests use synthetic temporary files only. They cover finite per-artifact limits, no open for oversized/symlinked inputs, a same-byte inode replacement at open, bounded read length, post-read descriptor-epoch drift, and a FIFO swap without blocking on POSIX.

These checks are local file-custody defenses, not atomic directory-descriptor traversal, authenticated provenance, trusted time, immutable storage, or protection against every hostile concurrent filesystem writer. They do not authorize or run model loading, preflight, GPU work, Candidate generation, protected V2 evaluation, or external compute.

No V3 Contract 1, V2 contract, frozen schema, dataset semantics, authorization scope, Candidate policy, or promotion behavior changes.
