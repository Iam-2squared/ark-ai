# Run552 — Independent detached digest verification for unapproved V3 packet deltas

**Scope:** passive, detached, free-only V3 approval-path consistency. PR #5 remains Draft and unmerged. This is not an approved review packet, actual reviewer decision, training permission, Candidate model, GPU identity, or protected V2 evaluation.

## Problem and bounded fix

The detached checker previously validated the shape of the retained field-only delta and compared it to a freshly supplied producer result. If a re-review callback itself returned an identical fabricated result, both copies could agree on a syntactically valid but incorrect `delta_sha256`. Local agreement of two caller-controlled objects is not a verified hash.

- **Source:** `src/ark/learning/authorization_packet_delta_recheck.py` at commit `9492bbacda0eea14a8b4e559702b4437f5d85f2b`. Before accepting a fresh review callback, the detached checker independently recomputes `SHA-256(ARK-v3-unapproved-packet-delta-review-v1\\0 || canonical_json(old_file_sha256, new_file_sha256, changed_paths))`. The domain-separated digest must exactly match the retained field `delta_sha256`. The independent local saved-packet verification, denied-only original property descriptors, two file rechecks, and no-authorization contract are preserved.
- **Regression:** `tests/v3/test_detached_delta_original_denials_run551.py` at final corrected source/test HEAD `31f632635c6965fc4362d1fada8aace98a094c6e`, updating the pure synthetic callback fixture to use a canonical digest and adding **two** parameter-expanded checks: corrupted digest and changed field paths with unchanged digest. Both must be rejected even when the mock producer returns the exact same forged object. The established original denial substitutions remain covered.
- **Exact source/test HEAD CI:** [run 41410990515](https://github.com/Iam-2squared/ark-ai/actions/runs/41410990515) — **6/6 GREEN** (Ubuntu/Windows, Python 3.11, 3.12, 3.13), independently inspected. This evidence applies to that exact HEAD, not subsequent documentation commits.
- A test-fixture byte-escape typo was corrected before the final green result; no production authorization or security condition was relaxed.

## Boundaries

This detached checker is a passive consistency test for **unapproved** local packet files. It does not authenticate file custody across machines, verify GPU/model/dataset files, assert legal provenance, authenticate a human reviewer, attest a clock, spend any funds, begin training, open protected evaluations, generate/promote Candidates, perform a tool action, or merge main. Original frozen V3 contract and prior V1/V2/Local UI/Launcher evidence remain untouched.

## Next plan / 今後の方針

1. Continue independently retained model/file identity and reproducibility/contamination audits without opening any protected gate.
2. Keep expensive training, data/legal ambiguity and human-approval boundaries blocked; do not reinterpret local mock hashes as authorization.
3. Verify exact-HEAD CI after each subsequent source/test write; keep PR #5 Draft/unmerged.
