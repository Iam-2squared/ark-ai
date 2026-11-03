# Run541 — Passive V3 shape-source denial descriptor custody

**Scope:** free-only, read-only, unapproved V3 snapshot diagnostics. No model bytes, tokenizer download, training, billing, protected V2 evaluation, Candidate, promotion, or human authority. PR #5 remains Draft/unmerged.

## Exact source basis and changes

- Before: `e5bc380ef6bf9f8bfdeeda4317ccc08357dfaaed`.
- Source implementation: `6b692e4885c810bb9df631ff870eec085aab64fa`, `src/ark/learning/offline_readiness_transition.py`.
- Regression tests: `211a0daa0818e4bd206ed37386f31bd4f74005ab`, `tests/v3/test_passive_source_denial_descriptor_run541.py`.
- The passive transition now retains the six exact `UnapprovedSnapshotShapeReview` authority-property descriptors while comparing the initial two source reviews and while independently re-inspecting both snapshots. A downstream false-only getter cannot silently replace a source descriptor, even with another getter returning `False`.
- **Six authored parameter-expanded pytest cases:** three cross-report descriptor substitutions, two final/reinspection substitutions, and one unchanged zero-authority regression. Authored cases must not be equated with independently executed local pytest PASS.

## CI source evidence

- GitHub Actions [41359040730](https://github.com/Iam-2squared/ark-ai/actions/runs/41359040730) for the source+test HEAD `211a0daa0818e4bd206ed37386f31bd4f74005ab`: 6/6 observed job successes; all six listed conclusions: success, success, success, success, success, success.
- The documentation write creates a **new HEAD** and its own CI; source exact-HEAD evidence is not automatically evidence for that new commit. No local model execution was performed.

## Limits and authorization boundary

These checks distinguish a stable *synthetic syntax review* from mutable callback results. Neither source JSON hashes nor false-only properties certify file bytes, pinned HF revision, dataset provenance, human review, licensing, budget caps, paid provider billing limits or authorization. Experiment 001/frozen V3 contracts remain unchanged; real training and protected V2 evaluation stay blocked.

## Next

Review subsequent exact-HEAD CI independently, then focus on genuine free-only artifact identity/path checks that do not read protected evaluations or synthesize missing human decisions.
