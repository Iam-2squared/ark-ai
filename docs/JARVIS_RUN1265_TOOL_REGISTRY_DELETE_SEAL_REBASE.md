# JARVIS Run1265 — ToolRegistry deletion-seal regressions rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #443, branch `research/run1261-memory-native-commit-hard-exit-current`, itself a child of Draft PR #8.
- Exact parent work-basis HEAD: `866224cda5786116186e21d24d19e20ceaa614ee`.
- Test-only package from Draft PR #441, exact source child HEAD `89159a0d0f10afd5615e474a6a93e2dee1aa2212`.
- Test body carried forward unchanged from the exact-head-GREEN source child.
- No ToolRegistry source, identity algorithm, ToolCall contract or PermissionGate contract changes.

## Regression coverage

The tests reject ordinary deletion of each sealed registry slot, reflective deletion of the registration map at the public bind boundary before backend access, and replacement of the class-level deletion guard before registry reads. A healthy registry still binds deterministically. The backend is an inert sentinel; no dispatch or external action occurs.

## Evidence boundary

Source child PR #441 CI [45343279753](https://github.com/Iam-2squared/ark-ai/actions/runs/45343279753) was GREEN 6/6 on its older parent. That result does not certify this dependent child. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

This is local in-process integrity evidence only. It is not remote backend attestation, execution authorization, dispatch, or external-effect certification.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
