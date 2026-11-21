# Run529 — detached, local V3 authorization-review packet file custody

**Scope:** review-only file reload; no paid compute, model access, GPU, HF download, Candidate weights, protected V2 evaluation, or user authorization.

## Verified design

- New isolated module: `src/ark/learning/authorization_packet_file_review.py`.
- `verify_local_authorization_packet_file(snapshot, packet_path, retained_packet_file_sha256=...)` checks exact dict and concrete absolute `Path` input plus an independently retained lower-case SHA-256, then reads **an existing** regular non-aliased file without creating or changing it.
- The local source is bounded to 65,536 bytes. Pre/post `lstat`, open-handle `fstat`, device/inode/size/mtime and byte reread reject detectable retargeting. Symlinked ancestors, symbolic-link leaves, hardlinks, relative paths and traversal are rejected. This is local custody, **not an atomic path traversal guarantee against adversarial filesystem actors**.
- Strict JSON decoding rejects duplicate keys and nonfinite numeric constants; canonical JSON round-trip must match the exact stored bytes. The full file digest must equal an independently retained value, and the existing `verify_detached_authorization_packet` must independently rebuild the exact unapproved experiment review packet. The path is read again after the nested verifier, so a callback that rewrites the saved file cannot yield a clean result.
- The returned `LocalPacketBindingWitness` carries only an inert snapshot/file/internal digest relationship. All external compute, Candidate, protected evaluation and merge authority flags remain **false**. No live consent, cloud bill, model provenance, or external outcome is inferred.

## Regression tests and CI

- `tests/v3/test_authorization_packet_file_review_run529.py` supplies **17 authored pytest cases**, covering normal reload, bad retained digest, file modifications, byte-budget overflow, duplicate/noncanonical/malformed/nonfinite JSON, file aliases and ancestor symlinks, file drift during decoding/rebinding, and callback mutation of the original snapshot.
- Source/test HEAD `d471a7fa7918c1085f7ef7da378ce619d94170be`, exact-head CI [41305493393](https://github.com/Iam-2squared/ark-ai/actions/runs/41305493393): **6/6 GREEN** (3 Ubuntu, 3 Windows). This does not automatically validate later documentation commits.
- The authored count is not a claim of independent locally run pytest: local git checkout cannot resolve GitHub DNS in this runtime.

## Hard stops

Draft PR #5 stays unmerged; frozen V3 Contract 1, V1/V2, Local UI/Launcher, Candidate validation and protected V2 evaluation remain untouched. The packet, hash and any synthetic hardware/budget fields are **not** user consent or a provider-side billing hard cap. Real preflight/training remains blocked on exact upstream/model/tool identities, human-reviewed dataset, measured runtime environment, explicit payment authorization and enforceable cost cap.
