# V3 Run1008 — exact export path admission before filesystem access

**Work basis:** Draft PR #32 exact head \`2fc3a711f1f532e80fec7287c0db0acd778c11be\`. This is an isolated free-only child branch. It changes only the non-executing export-plan path preflight and its tests.

## Implementation

- Added exact concrete \`pathlib.Path\` type admission for base, merged Candidate, converter, quantizer, output and optional deployed-model paths. Path subclasses are rejected before their \`__fspath__\` callbacks can run.
- Replaced character-count path limits with a 4,096-byte native filesystem-encoding budget, checked before path I/O and before execution-snapshot validation or converter/quantizer identity reads.
- Reordered output admission so every ancestor is inspected with no-follow \`lstat\` before probing the leaf. The final leaf is inspected with \`lstat\`, which rejects a dangling symlink without following it.
- Preserved the existing source-tree non-overlap and deployed-model collision checks. The helper still creates no output directory and executes no converter or quantizer.

## Regression coverage

\`tests/v3/test_export_path_preaccess_run1008.py\` adds eight parameter-expanded cases:

1. Reject path subclasses for output, base, Candidate and deployed-model inputs without invoking \`__fspath__\`.
2. Reject a converter path subclass before snapshot validation.
3. Reject a multibyte native path over the byte budget before \`lstat\`.
4. Reject a symlinked output ancestor before any output-leaf-following probe.
5. Reject a dangling output symlink through final-leaf \`lstat\`.

## Boundaries

This is path-admission-only work. No Candidate files or weights were generated; no model was loaded; no converter, quantizer, training, export, external GPU, paid API/service, or physical hardware was used. The path checks are not atomic directory-handle custody and do not eliminate a hostile concurrent filesystem race. V3 remains NOT_PASSED; PR #5 remains protected Draft/unmerged. Existing V1/V2/Local UI/Launcher contracts and PR #9 remain untouched.

**Validation:** source and regression test authored. Exact-head six-job CI is pending after the Draft child PR is opened; no PASS is claimed.
