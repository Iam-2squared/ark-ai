# Run1212 — ToolRegistry Unicode format-control custody on latest foundation

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD at branch creation: `54fd6b1825c0dc96e8896e08ce8a35d6d0e1ec16`.
- Rebased from Draft PR #380 exact child HEAD: `e1be2cd1ee694165ea1f94e1a27ca60c3ebae250`.
- Prior exact-head CI [45198738945](https://github.com/Iam-2squared/ark-ai/actions/runs/45198738945) was GREEN on PR #380's predecessor child only; it does not transfer.
- New child branch: `research/run1212-registry-unicode-custody-latest`.

## Change

Carries forward the opt-in ToolRegistry identity guard and its expanded regression matrix onto the latest PR #8 parent. The registry pins the import-time `unicodedata` module and exact `category` function before identity inspection. It rejects Unicode General Category `Cf` controls in registration labels and registered ToolCall scopes across registration, resolve and bind, while preserving the existing codepoint/UTF-8 budgets and explicit C0/C1, NUL, bidi and separator checks.

The test matrix covers assigned controls across Arabic, Syriac, interlinear annotation and supplementary-plane tag blocks, plus Unicode category dependency substitution before registration and before resolve/bind. The mock backend remains undispatched.

## Compatibility and evidence boundary

The source file on the new parent was byte-identical to PR #380's parent source before the guard was applied. The frozen generic ToolCall v1 constructor and PermissionGate authority are unchanged. This is an in-process identity/dependency integrity check, not a Python sandbox, authenticated backend identity, durable authorization or permission to execute tools.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, UI/frontend work, frozen-contract change, destructive operation or main merge. PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
