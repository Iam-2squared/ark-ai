# Run1133 — V3 execution snapshot fstat identity custody

## Exact basis

- Parent: gated Draft PR #5 through Draft PR #294.
- Parent branch: `research/run1116-v3-code-tree-no-follow-rebase`.
- Parent basis HEAD: `9aff784cd10ba3803f23163ae1a0f02439807364`.
- Child branch: `research/run1133-v3-execution-fstat-custody`.

## Finding

The local execution-snapshot loader compared path metadata with descriptor metadata using the mutable `os.fstat` module attribute. Its existing fail-closed policy pinned the `stat` module and classification predicates, but not the `os` module or descriptor-stat callable. A substituted `fstat` could therefore supply a forged descriptor identity after the file was opened.

## Change

- Capture the import-original `os` module and `os.fstat` callable.
- Pin the live module/function and captured alias before any snapshot path or descriptor inspection.
- Use the captured `fstat` callable for both initial and final descriptor checks.
- Add regressions for OS-module binding replacement, captured-alias replacement, and a reentrant `Path.open` callback that attempts replacement between admission and descriptor inspection.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff or CI PASS is claimed. The tests use disposable local JSON fixtures only.

This remains a local in-process dependency-identity check, not a Python sandbox, atomic filesystem custody, authenticated provenance, human approval, or compute authorization. The loader does not start training or access external compute. No frozen V3 Contract, execution snapshot schema, authorization packet, dataset/provenance/contamination evidence, runtime identity, or training recipe changes. No protected V2 evaluation, Candidate generation/promotion, paid/external compute, credentials, hardware action, UI/frontend work, or main merge occurs. PR #5 remains Draft/unmerged; integration is limited to the isolated PR #294 branch.
