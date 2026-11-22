# Run1132 — V3 platform-policy identity custody

## Exact basis

- Parent: gated Draft PR #5 through Draft PR #294.
- Parent branch: `research/run1116-v3-code-tree-no-follow-rebase`.
- Parent basis HEAD: `9aff784cd10ba3803f23163ae1a0f02439807364` (after the Run1126 scanner-identity integration).
- Child branch: `research/run1132-v3-platform-policy-custody`.

## Finding

The no-follow code-tree walker selected its Windows-versus-POSIX metadata comparison using the mutable module attribute `os.name`. The existing import-original policy pinned the `os` module and `os.scandir` callable but not the platform discriminator. A changed `os.name` could therefore select a different metadata comparison policy without replacing the module or scanner.

## Change

- Capture the import-original `os.name` value alongside the `os` module and scanner.
- Pin both the live platform attribute and its captured module-level alias in the existing fail-closed policy check.
- Select the metadata compatibility branch from the captured platform value only.
- Add synthetic regressions for replacement of both the live `os.name` attribute and the captured alias; both must fail before metadata comparison.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff or CI PASS is claimed here. The fixtures are synthetic and do not exercise a hostile concurrent filesystem writer.

This remains an in-process identity guard, not a Python sandbox, atomic directory-handle custody, or complete TOCTOU defense. No frozen V3 Contract, execution snapshot, authorization packet, dataset/provenance/contamination evidence, runtime identity, or training recipe changes. No protected V2 evaluation, Candidate generation/promotion, training, paid/external compute, credentials, hardware action, UI/frontend work, or main merge occurs. PR #5 remains Draft/unmerged; integration is limited to the isolated PR #294 branch.
