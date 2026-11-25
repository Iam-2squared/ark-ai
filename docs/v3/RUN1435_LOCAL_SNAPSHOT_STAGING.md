# Run1435 — Local verified HF snapshot staging

**Exact source basis:** Draft PR #5, research/v3-learning-evaluation, HEAD
ea373c3496d06e2789cee5bb58836054ef35ed28. This package is a free-only,
source-level guard change on a child branch targeting PR #5.

## Change

The preflight and full-run loader path now stages the already-materialized Hugging
Face snapshot into a new TemporaryDirectory before handing a path to Transformers.

1. Recompute the source snapshot identity and require exact equality with the
   frozen base-file, tokenizer-file, and chat-template-probe digests.
2. Copy only the paths present in the frozen base-file manifest. Each file is
   streamed in bounded 1 MiB chunks while the copied bytes are hashed and counted.
   Path labels must be relative, traversal-free POSIX paths; manifest rows must
   identify regular non-symlink files.
3. Recompute the full identity over the staged tree and require the same frozen
   digests before loader use.
4. Recheck the staged tree immediately before both tokenizer and model loading.
   Both from_pretrained calls use the staged path, local_files_only=True, and
   trust_remote_code=False.
5. Retain the temporary-stage owner through the complete preflight/full-run scope
   and clean it on normal return or exception.

The change does not alter the frozen experiment recipe, dataset, tokenizer probe,
execution snapshot schema, authorization scopes, or Candidate output format.

## Synthetic regression coverage

- Exact manifest preservation in the staged tree.
- Source-byte replacement between initial identity capture and staging is denied
  by the copied-byte digest check.
- Fake tokenizer/model loaders both receive the same staged path, never the source
  directory; the temporary tree remains present while in use and is cleaned after
  the owner is closed.

These tests use small synthetic files and fake loaders. They do not import torch,
load real model weights, query a GPU, run preflight, train, or create a Candidate.

## Explicit limitations

This is a **local hash-then-stage improvement**, not an atomic filesystem custody
primitive. TemporaryDirectory permissions are best-effort; this does not attest
platform ACLs, defend against a hostile same-user process that can mutate the stage,
or eliminate the race between the final staged-tree rehash and the loader opening
its files. It does not prove fsync/power-loss durability. A real run needs temporary
disk capacity for a second copy of the local HF snapshot; insufficient space fails
closed. No network access or external service is introduced.

PR #5 remains Draft/unmerged. No V3 preflight/training, GPU action, Candidate
generation/promotion, protected V2 evaluation, paid/external compute, frozen
contract change, main write/merge, or UI/frontend work is authorized or performed.
