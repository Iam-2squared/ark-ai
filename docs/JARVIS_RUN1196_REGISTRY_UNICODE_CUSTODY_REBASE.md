# Run1196 — ToolRegistry Unicode format-control custody rebase

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `2df6b261554428cd01871f2723ce87c4dd05e4b4`.
- Reconciled source: Draft PR #361 exact child HEAD `e877c8a74e1de44159cac66f09967f4ed8a3fb84`.
- Original source PR #361 base HEAD: `0b7a4fc098e38be38445d09e05c65c5759888a3d`.
- New child branch: `research/run1196-registry-unicode-custody-rebase`.

## Change

The opt-in ToolRegistry identity boundary now pins the import-time `unicodedata` module and exact category function before identity inspection. It rejects every Unicode General Category `Cf` scalar in registration labels and registered ToolCall scopes, including both `resolve` and `bind`, while preserving existing code-point/UTF-8 budgets, NUL, C0/C1 and separator checks.

The frozen generic ToolCall v1 constructor and PermissionGate authority remain unchanged. The registry guard is an in-process dependency-integrity check, not a Python sandbox, authenticated backend identity, durable authorization or permission to execute tools.

## Regression coverage

The synthetic format-control matrix includes assigned examples across Arabic, Syriac, interlinear annotation and supplementary-plane tag blocks. It exercises registration fields, resolve/bind scope admission and Unicode category dependency substitution. Mock backends remain undispatched.

## Validation and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No backend execution, paid service, external compute, Candidate, protected evaluation, credential, hardware action, frozen-contract change, UI/frontend work or main merge is included. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
