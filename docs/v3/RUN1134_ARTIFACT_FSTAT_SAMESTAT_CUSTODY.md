# Run1134 — V3 identity artifact descriptor and same-file primitive custody

## Exact basis

- Parent: gated Draft PR #5 through Draft PR #294.
- Parent branch: `research/run1116-v3-code-tree-no-follow-rebase`.
- Parent basis HEAD: `78811b50b6d2e31bb6b828d64918deba666cc044`.
- Child branch: `research/run1134-v3-artifact-fstat-samestat-custody`.

## Finding

The local identity-artifact verifier compared path and open-descriptor metadata through mutable `os.fstat` and `os.path.samestat` attributes. Its prior policy pinned the `stat` module and mode classifiers, but not the descriptor-stat or same-file comparison primitives. It also did not recheck the stat policy between a potentially reentrant `Path.open` callback and the first descriptor inspection.

## Change

- Capture the import-original `os` module, `os.path` module, `os.fstat` callable and `os.path.samestat` callable.
- Pin both live module attributes and captured aliases in the existing fail-closed policy check.
- Use the captured descriptor and same-file primitives for artifact identity checks.
- Recheck policy immediately after each file-open callback and before descriptor-stat calls.
- Add synthetic tests for OS-module binding and captured-alias replacement and reentrant replacement from `Path.open`.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff or CI PASS is claimed. The tests use disposable canonical JSON fixtures only.

This remains a local in-process identity check, not a Python sandbox, atomic filesystem custody, authenticated upstream provenance, human approval, or compute authorization. No frozen V3 Contract, execution snapshot schema, authorization packet, dataset/provenance/contamination evidence, runtime identity, or training recipe changes. No protected V2 evaluation, Candidate generation/promotion, training, paid/external compute, credentials, hardware action, UI/frontend work, or main merge occurs. PR #5 remains Draft/unmerged; integration is limited to the isolated PR #294 branch.
