# Run1136 — V3 identity file descriptor-stat dependency custody

## Exact basis

- Parent: gated Draft PR #5 through Draft PR #294.
- Parent branch: `research/run1116-v3-code-tree-no-follow-rebase`.
- Parent basis HEAD: `33732054ccce31b9cd87999895b9d7f6d5ab87de`.
- Child branch: `research/run1136-v3-identity-fstat-custody`.

## Finding

The base/tokenizer/tool identity hasher in `src/ark/learning/identity.py` compared path metadata with descriptor metadata using live `os.fstat` and `os.path.samestat` attributes. The surrounding reparse-point policy pinned the OS module, scanner, platform discriminator and stat classifiers, but did not pin the path module or these two file-identity primitives. A replaced descriptor-stat or same-file comparator could therefore supply a forged identity during local byte hashing. The `Path.open` return was also a reentrant callback boundary with no immediate policy recheck before descriptor inspection.

## Change

- Capture the import-original `os.path`, `os.fstat` and `os.path.samestat` identities.
- Pin the live module attributes and captured aliases in the existing fail-closed policy guard.
- Use the captured descriptor-stat and same-file primitives for both initial and final handle checks.
- Recheck the complete policy immediately after `Path.open` returns and around the final descriptor check.
- Add synthetic regressions for OS-module substitution, captured-alias replacement, callback-time replacement and normal byte hashing.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff or CI PASS is claimed until that run completes. Fixtures use only disposable local files and do not load model weights.

This remains an in-process dependency-identity guard, not a Python sandbox, atomic directory-handle custody, authenticated upstream provenance, trusted time, human approval or compute authorization. No frozen V3 Contract, execution snapshot schema, authorization packet, dataset/provenance/contamination evidence, runtime identity or training recipe changes. No model download, training, Candidate generation/promotion, protected V2 evaluation, paid/external compute, credentials, hardware action, UI/frontend work or main merge occurs. PR #5 remains Draft/unmerged; integration is limited to the isolated PR #294 branch.
