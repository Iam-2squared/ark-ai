# JARVIS Run1258 — ActionAudit outcome-boundary regressions rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `e3448745e237fa320641ad7b38a67098dfd640df`.
- Test-only rebase from Draft PR #434, exact source child HEAD `13e0e0758eadd84a19334c7ba781188b6dbc3b68`.
- Test body carried forward unchanged from the exact-head-GREEN source child.
- No ActionAudit source, v1 DDL, public event fields, frozen contract or migration plan changes.

## Regression coverage

The tests enforce exact-type outcomes, codepoint and UTF-8 budgets, control/format/surrogate rejection before SQLite or clock access, Unicode-classifier dependency substitution failure, valid 256-byte UTF-8 round-trip, and fail-closed reads/appends for corrupt persisted outcomes.

## Evidence boundary

The source child CI [45335525269](https://github.com/Iam-2squared/ark-ai/actions/runs/45335525269) was GREEN 6/6 on its older parent. That result does not certify this rebased child. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

The open outcome vocabulary, ActionAudit v1 DDL, public event fields and migration plan remain unchanged. Synthetic ToolCalls and disposable local SQLite only; no backend dispatch or live personal data.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
