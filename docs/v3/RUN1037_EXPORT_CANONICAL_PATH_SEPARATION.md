# Run1037 — V3 export path canonicalization and source separation

## Scope and exact work basis

- Parent: gated Draft PR #5, branch research/v3-learning-evaluation.
- Exact parent HEAD: 6c805360a4145b933526624286d523f155067373 (after the exact-head GREEN Run1035 packet-reader child was integrated).
- Source: src/ark/learning/export_plan.py.
- Regression: tests/v3/test_export_canonical_path_separation_run1037.py.
- This package only constructs and validates a deterministic export plan. It does not create output directories, run converters/quantizers, load models, or contact external compute.

## Finding

The existing output guard rejected lexical traversal, existing destinations, symlinked parents, output under the base/Candidate roots, and known Current GGUF output-name collisions. It did not establish a complete canonical separation relation among the repository source tree, base model directory, merged Candidate directory, converter, quantizer, and optional Current model path. It also relied on Path.is_symlink() for ancestry, which does not identify every Windows reparse-point directory.

## Change

- Require existing base and merged-Candidate directories to be exact native paths, real directories, and free of symlink/reparse-point ancestry.
- Resolve both source roots strictly and reject equality or nesting in either direction.
- Require a new output leaf beneath an existing canonical parent; reject traversal and symlink/reparse-point ancestry.
- Reject output paths overlapping the repository source tree, base model tree, or merged Candidate tree.
- Detect Windows FILE_ATTRIBUTE_REPARSE_POINT as well as POSIX symlinks at the path boundary.
- Require a supplied Current model locator to be a non-reparse regular file when building a plan; reject aliases into either model source tree and collisions with all four planned output filenames.
- Require converter and quantizer to be distinct canonical regular files, separate from model source trees and the Current model.
- Use the canonical absolute paths in the generated argv and output plan.

## Regression coverage

Synthetic local fixtures exercise source-tree output rejection, identical/nested model roots, symlink and reparse-point directories, reparse-point output parents, Current-model containment and symlink rejection, missing Current model, converter/quantizer aliasing, converter/source overlap, and canonical absolute argv construction.

## Limits and frozen boundaries

These are repeated local metadata/path checks, not atomic descriptor-relative traversal, hostile concurrent filesystem-writer protection, authenticated file provenance, or an immutable filesystem snapshot. The plan remains data only. No converter, quantizer, model, GPU, external service, Candidate, preflight, training, Validation, protected V2 evaluation, or promotion is invoked. V3 Contract 1, V1/V2/Local UI/Launcher evidence, main, and the paused UI branch remain unchanged. PR #5 remains Draft/unmerged and V3 remains NOT_PASSED.
