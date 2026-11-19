# Run1002 — V3 export input path separation

**Work basis:** gated Draft PR #5 exact head `805b377697472268db02650a89c7a94b1c5337c8`. This is a free-only child branch targeting PR #5; it does not change the frozen V3 contract or PR #5 itself.

## Change

The non-executing export-plan validator now:

- requires the base and merged-Candidate source roots to be existing local directories;
- rejects lexical parent traversal and symlinked roots/ancestors for either source;
- resolves both roots before comparing them and rejects equal or nested/overlapping source trees;
- canonicalizes the optional Current deployed-model path and rejects a Current model located inside or equal to the merged-Candidate source tree; and
- retains the existing new-output, output/input separation, and deployed-output collision checks.

The source-tree checks run before converter/quantizer identity hashing. The new tests use temporary directories and synthetic marker bytes only.

## Validation boundary

This patch only builds or rejects an in-memory export plan. It does not create output directories, invoke subprocesses, hash model weights, load a model, run conversion/quantization, open protected evaluation, or start training. No paid/external service, GPU, Candidate, credentials, or real model artifact is used.

These are local path-admission checks, not atomic directory-handle custody or a guarantee against a hostile concurrent filesystem writer. The patch does not close hash-then-use TOCTOU or prove artifact provenance.

**Exact-head CI:** pending at report creation. No PASS is claimed. PR #5 remains Draft/unmerged; PR #9/UI remains paused and untouched. Overall ARK/JARVIS remains NOT_PASSED.
