# JARVIS Run1271 — ActionAudit outcome-boundary regressions rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `993fbcb3efb69c4c818327aefb8e3d40ea9d673e`.
- Rebased test-only package from Draft PR #440, whose prior child head was `8f085029b875a3ae7612df9f31edfb7e4d9a88b1` on older base `e3448745e237fa320641ad7b38a67098dfd640df`.
- The test body is carried forward unchanged apart from its run label; no ActionAudit source, v1 DDL, public event fields, frozen contract or migration plan changes.

## Regression coverage

The tests enforce exact-type outcomes, codepoint and UTF-8 budgets, control/format/surrogate rejection before SQLite or clock access, Unicode-classifier dependency substitution failure, valid 256-byte UTF-8 round-trip, and fail-closed reads/appends for corrupt persisted outcomes.

## Evidence boundary

Prior PR #440 CI [45343217726](https://github.com/Iam-2squared/ark-ai/actions/runs/45343217726) was GREEN 6/6 on its older parent only. It does not certify this rebase. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

The open outcome vocabulary, ActionAudit v1 DDL, public event fields and migration plan remain unchanged. Synthetic ToolCalls and disposable local SQLite only; no backend dispatch or live personal data.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
