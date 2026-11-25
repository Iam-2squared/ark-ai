# JARVIS Run1307 — ActionAudit outcome-boundary regressions rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `b11a17c6c078d1b4675fa4f392a7810e17ba7cb5`.
- Rebased test-only package from Draft PR #472, whose prior child was based on `101be0cb505d8ae045027faf54f8d982c0a4f9d2`.
- Test behavior is carried forward with the run label updated; no ActionAudit source, v1 DDL, public event fields, frozen contract, or migration plan changes.

## Regression coverage

- Exact-type outcomes and codepoint/UTF-8 byte budgets.
- Control, format and surrogate rejection before SQLite or clock access.
- Unicode-category dependency substitution fails closed.
- A valid 256-byte UTF-8 outcome round-trips.
- Corrupt persisted outcomes fail closed for reads and appends without clock access or repair.

## Evidence boundary

The predecessor branch's evidence is not transferred to this new base. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

The outcome vocabulary remains open. ActionAudit v1 DDL and public event fields remain unchanged. Synthetic ToolCalls and disposable local SQLite only; no backend dispatch or live personal data.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
