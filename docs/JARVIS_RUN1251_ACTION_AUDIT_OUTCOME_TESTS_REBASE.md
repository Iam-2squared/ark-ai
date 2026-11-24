# JARVIS Run1251 — ActionAudit outcome-boundary tests rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `99654a0ecc75fe53de7f38d92db42095391df6e4`.
- Test-only rebase from Draft PR #430, source child HEAD `0efcc590f492ae186c5e4de42431c1d0c1b2c9ee`.
- The bounded outcome implementation is already present in the parent at `src/ark/agency/audit.py`; this child changes no ActionAudit source, v1 DDL, public fields, frozen contract or migration plan.

## Coverage

- Reject empty/whitespace, over-codepoint, over-UTF-8-byte, control/format, lone-surrogate and wrong-exact-type caller outcomes before SQLite access or clock sampling.
- Reject a substituted Unicode category dependency before database access or clock sampling.
- Round-trip a valid 256-byte UTF-8 outcome through the existing v1 ActionAudit API.
- Reject oversized/control-corrupt persisted outcomes on read and append without clock sampling or repair.

## Evidence boundary

The source child CI [45328911861](https://github.com/Iam-2squared/ark-ai/actions/runs/45328911861) completed successfully on the older parent. That result does not certify this rebased child; fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

Test-only with synthetic ToolCalls and disposable local SQLite. No real backend, dispatch, personal data or external service. This is local input/resource-integrity evidence, not an authenticated event chain, independent custody, trusted time, consent, cross-store atomicity or external-effect proof.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
