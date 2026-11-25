# JARVIS Run1287 — ActionAudit outcome-boundary regressions rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `101be0cb505d8ae045027faf54f8d982c0a4f9d2`.
- Rebased test-only package from Draft PR #452, whose prior child head was `4a02fa2a1e874e349d4325afa75ada93fa99a994` on older parent `993fbcb3efb69c4c818327aefb8e3d40ea9d673e`.
- The test body is carried forward unchanged apart from its run label; no ActionAudit source, v1 DDL, public event fields, frozen contract, or migration plan changes.

## Regression coverage

The tests enforce exact-type outcomes, codepoint and UTF-8 budgets, control/format/surrogate rejection before SQLite or clock access, Unicode-classifier dependency substitution failure, valid 256-byte UTF-8 round-trip, and fail-closed reads/appends for corrupt persisted outcomes.

## Evidence boundary

Prior PR #452's source package was test-only and had no transferred CI claim for this new parent. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

The open outcome vocabulary, ActionAudit v1 DDL, public event fields, and migration plan remain unchanged. Synthetic ToolCalls and disposable local SQLite only; no backend dispatch or live personal data.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work, or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
