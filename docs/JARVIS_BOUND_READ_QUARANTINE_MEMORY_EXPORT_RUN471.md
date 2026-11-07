# Run471 — READ binding, scheduler quarantine, Memory read, and V3 export safety

All work is disconnected, local-first or validation-only. It neither authorizes an
external action nor grants owner approval. Source/test changes were saved using
ordinary GitHub Contents writes, after branch-head checks; no force push or merge.

## Exact work branches and source/test HEADs

- JARVIS PR #8 Draft, branch `research/jarvis-foundations`: work basis
  `4bbfa0762540ac7be4794c7244ee8941ffd9ebb6`, final source/test HEAD
  `88326541345f1bd7f7d3c580b577f1677e653f92`.
- V3 PR #5 Draft, branch `research/v3-learning-evaluation`: work basis
  `70852b312d2a7c6b12e796ce1838c2379fe1bcb6`, final source/test HEAD
  `2072549789588939dc958aa0ce51f74edf04da28`.
- All nine affected source/test files were read back and their Git blob SHA
  observed after saving. These source blobs are **not** trusted runtime/file
  identities or evidence that an external system was contacted.

## Four independent packages

1. **Planner/ToolRegistry READ carrier custody (PR #8).** Pin every original
   `BoundAction` and its exact call, registration, registry revision and bound
   action identifier across reentrant PermissionGate callbacks and result
   construction. Reject even equal-value carrier replacements; no tool backend
   is executed. Source blob
   `32c7e4794a7e07723d854db3914a7a966d58d445`,
   test blob `4a2c6a1cc4a5f7d3b45062554488450c1b91e7ec`.
   **9** new parametrized test cases authored.
2. **Scheduler quarantine SQLite source/witness custody (PR #8).** Retain
   original path, policy tuple, retained witness fields and result carriers
   across open/BEGIN/validation/commit/return. Pre-COMMIT failures roll back;
   post-COMMIT diagnostic rejection never claims rollback. No proactive
   timer, notification, consent or external effect. Source
   `fe1a3db7719104eccfa656c57efe8a9a094c21e1`,
   test `b845fd0e2dd509fa63f6380f5e48a3414a5f1df2`.
   **7** tests authored.
3. **Memory hydrated original nested objects (PR #8).** Private read-epoch
   witness now retains actual original `MemoryScope` and metadata carriers,
   preventing allocator `id()` reuse from hiding an equal-value reflective
   substitution. Frozen Memory v1 schema and public API unchanged. Source
   `4be68251ab948052f3119407ed3358fc864e4077`,
   test `f7fd70a329fee9b2ab1d20fd638037b473e4e9cd`.
   **4** tests authored; no personal data.
4. **V3 non-executing paired export path guards (PR #5).** Validate output
   destination before tool hashing; deny path traversal, symlink or aliased
   parents, existing output leaves, Candidate/base input tree overlap and
   normalized collision with any of four paired GGUF output names. Keep the
   pre-existing converter-byte mismatch test meaningful by giving it
   independent synthetic input roots. Source
   `a5c9786731a982fec5e454d0e961e4e5fdc60e42`,
   updated test `96e9b48bf8de248fa870e2e846a94c529aa53413`,
   new test `a779a8930069388f9c193c1989eb3279cc36f2c1`.
   **12** tests authored; no converter, GPU, HF model or Candidate invoked.

Total **32 authored cases, nine ordinary source/test commits**. Authored does
not imply executed or passed until the corresponding exact source/test HEAD CI.

## Evidence and remaining blockers

- Prior PR #8 checkpoint HEAD `4bbfa0762540ac7be4794c7244ee8941ffd9ebb6`
  passed all six CI jobs in #1502 / run `41000360408`. Prior exact
  source/test #1501 / `41000109991` also passed 6/6.
- PR #5 intermediate HEAD `e52952885d707364ebf38584ecde14d38b4b8cef`
  passed six jobs in #1508 / run `41004675814`.
- New exact-head PR #5 CI #1509 / `41004714195` and PR #8 CI
  #1511 / `41004835004` were still not fully concluded at inspection.
  Do not transfer earlier GREEN to these source/test HEADs.
- GitHub DNS was unavailable from the local container for checkout; there is
  no independent local whole-repository pytest/Ruff execution evidence.
- Export validation is intentionally a path precheck, not a proven
  race-free OS-handle seal. Scheduler witnesses are self-contained SQLite
  checks, not independent clock/approval or external audit attestations.

**Frozen contracts remain intact.** No V2 protected evaluation, GPU,
real training/preflight, paid service, Candidate creation/promotion,
credentials, user-specific Personal Context, real Tool dispatch, main merge
or human review was performed or inferred. PR #5 and PR #8 remain Draft,
separate and unmerged. Overall JARVIS and V3 PASS remain **NOT_PASSED**.

## Next plan / 今後の方針

1. Verify exact-head PR #8 #1511 and PR #5 #1509 across all six jobs.
   On failure inspect real logs and fix only the failing invariant.
2. Continue Memory row/event/CAS/expiry snapshot integrity and Planner
   durable UNKNOWN WRITE quarantine without replay or real dispatch.
3. Expand free-only V3 output path alias/TOCTOU and evidence/approval review.
   Require explicit user authorization before any real or billable execution.
