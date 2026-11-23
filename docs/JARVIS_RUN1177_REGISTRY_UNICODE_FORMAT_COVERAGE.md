# Run1177 — Registry Unicode format-control coverage

## Scope and exact basis

- Parent work basis: Draft PR #8, `research/jarvis-foundations` HEAD `0b7a4fc098e38be38445d09e05c65c5759888a3d`.
- Isolated branch: `research/run1177-registry-unicode-format-coverage`.
- This package changes only the opt-in ToolRegistry identity-admission boundary and its synthetic regression coverage.
- Frozen generic ToolCall v1 construction, Memory v1, PlanStep v1, PermissionGate authority, V2 evaluation, V3 Contract 1, and UI branches remain unchanged.

## Finding and change

The registry already rejected C0/C1 controls and a selected set of bidi/format code points in registration labels and ToolCall scopes. The selected list did not cover every Unicode `Cf` (format) character; for example Arabic number marks, Syriac abbreviation marks, interlinear annotation controls, and supplementary-plane language tags could pass the local registry boundary.

The change:
- Pins the exact `unicodedata` module and `category` function before registry identity text is inspected.
- Rejects any character whose Unicode general category is `Cf` in tool names, capabilities, backend IDs, and registered ToolCall scopes.
- Applies the same category rule in both `resolve` and `bind`, retaining the existing byte/code-point budgets and explicit NUL/C0/C1/line-separator checks.
- Leaves meaningful multilingual letters and the frozen generic ToolCall v1 contract unchanged.

## Synthetic regression coverage

The existing registry format-control matrix now includes stable assigned `Cf` examples from Arabic, Syriac, interlinear annotation, and supplementary-plane tag blocks. The matrix exercises registration fields plus both `resolve` and `bind` scope admission. Additional tests replace the Unicode category dependency and verify fail-closed rejection before registration or scope binding. Mock backends must remain undispatched.

## Limits and safety

This is a local input-integrity boundary, not a Python sandbox, authenticated backend identity, user consent, trusted time, durable authorization, or permission to execute tools. No backend execution, paid service, external compute, Candidate, protected evaluation, credential, hardware action, frozen-contract change, or main merge is included.

**Validation:** exact-head CI is pending. No PASS is claimed until all configured CI jobs complete successfully.
