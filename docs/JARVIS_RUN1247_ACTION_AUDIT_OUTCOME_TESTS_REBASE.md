# JARVIS Run1247 — ActionAudit outcome-boundary regression rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `126bf11c2070c261de86b7a94ebdd0e67f52be6a`.
- This package carries the synthetic regression tests from the older Draft PR #13 onto the current foundation head.
- The bounded outcome implementation is already present in the parent source at `src/ark/agency/audit.py` (observed blob `d0117e8a23bf72a07682e004eb15711ea3f6c2cc`); this child adds tests only.
- Previous PR #13 CI [45154555897](https://github.com/Iam-2squared/ark-ai/actions/runs/45154555897) was GREEN 6/6 on its older child head. That result does not certify this rebased child; fresh exact-head CI is required.

## Coverage

- Reject empty/whitespace, over-codepoint, over-UTF-8-byte, control/format, lone-surrogate and wrong-exact-type caller outcomes before SQLite access or clock sampling
- Reject a substituted Unicode category dependency before database access or clock sampling
- Round-trip a valid 256-byte UTF-8 outcome through the existing v1 ActionAudit API
- Reject oversized/control-corrupt persisted outcomes on read and append without clock sampling or repair

## Scope and evidence boundary

Test-only. No ActionAudit source, v1 DDL, public event fields, frozen contract or migration plan is changed. The open outcome vocabulary is retained. The tests use synthetic ToolCalls and disposable local SQLite only; no real backend, dispatch, personal data or external service is used.

This is local input/resource-integrity evidence only. It does not establish an authenticated event chain, independent custody, trusted time, consent, cross-store atomicity or an external effect.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive action, frozen-contract change or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
