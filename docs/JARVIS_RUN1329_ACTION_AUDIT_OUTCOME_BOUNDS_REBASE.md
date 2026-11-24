# ARK Run1329 — ActionAudit outcome-boundary regressions rebased to current foundation

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`, exact work-basis `77d3b2f50d258bb3694afc0d03830e0d44644961`.
- Rebase source: Draft PR #488 / Run1307, prior child head `868656bbc4b329ad686033e3c670a17b34774e6c`, based on older parent `b11a17c6c078d1b4675fa4f392a7810e17ba7cb5`.
- Prior exact-head CI [45429883458](https://github.com/Iam-2squared/ark-ai/actions/runs/45429883458) was GREEN on that older parent only; it does not transfer to this rebase.
- New child branch: `research/run1329-action-audit-outcome-bounds-rebase-20261125`.

## Regression coverage

- Exact-type outcomes and codepoint/UTF-8 byte budgets.
- Control, format and surrogate rejection before SQLite or clock access.
- Unicode-category dependency substitution fails closed.
- A valid 256-byte UTF-8 outcome round-trips.
- Corrupt persisted outcomes fail closed for reads and appends without clock access or repair.

## Scope and evidence boundary

Test/documentation-only. No ActionAudit source, v1 DDL, public event fields, frozen contract or migration plan changes. The outcome vocabulary remains open. Synthetic ToolCalls and disposable local SQLite only; no backend dispatch or live personal data.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or new CI PASS is claimed. PR #5/#8 remain Draft/unmerged; PR #9 remains paused/untouched. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, UI work or main merge. ARK/JARVIS remains NOT_PASSED.
