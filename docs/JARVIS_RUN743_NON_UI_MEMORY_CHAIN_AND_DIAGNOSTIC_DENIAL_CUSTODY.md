# ARK AI — Run743 non-UI retained witness preaccess and final-denial custody

## Scope and provenance

Branch `research/jarvis-foundations`, Draft PR #8, **unmerged**.
Exact verified beginning HEAD: `92a85c12446ea316e0df698435b1d97749d87f31` (Run742 canonical checkpoint).
Work saved through source/test HEAD `cb5e01441419c6640385f919519afb84fd418275`.
This is limited to **disconnected, local review-only** Memory and public-only diagnostic code.
No changes to frozen V1/V2/Local UI/Launcher contracts or evidence, PR #5, paused UI PR #9, or main.
No tool dispatch, real SQLite I/O, private data export, physical-PC work, protected evaluation, Candidate adapter, external GPU or paid service was requested.

### Package A — retained Memory chain verification ingress and receipt identity

- [Source `f4f11b86`](https://github.com/Iam-2squared/ark-ai/commit/f4f11b86d2b79dda47464f65843a456acbf3e7e1):
  In `src/ark/memory/retained_epoch_chain.py`, detached receipt verification now checks the originally bound chain reviewer, edge reviewer, epoch validator, SHA parser, epoch budget, exact result class, JSON serializer and SHA-256 implementation **before retained epoch fields reach these helper callbacks**.
- The independent receipt's original five field objects are retained before recomputation. All five are rechecked for **identity**, not merely equal values, around the comparison and after each denial property. The source epoch snapshot and protocol are rechecked at the same boundaries.
- [15 new authored parametrized tests `41639887`](https://github.com/Iam-2squared/ark-ai/commit/41639887e2dbdfc18b68a125b05026475e122a1b) cover ordinary detached verification and ten substituted helper/parser/budget/module conditions, plus four equal-valued reflective field swaps in the last denied-authority getter.
- This is not a Python sandbox, independently witnessed history, proof of original source, CAS ownership, real database identity, user consent, authority to disclose Memory or permission to dispatch.

### Package B — final public diagnostic receipt denial reentrancy

- [Source `14cdf7d`](https://github.com/Iam-2squared/ark-ai/commit/14cdf7d2a360cb72507499677d597df13ffef0e5):
  `src/ark/private_diagnostic_segment_review.py` now pins every result field after construction and checks exact object identity, expected sequence/count/tip and original protocol **before and after each denied-authority getter**, including the last. It then rechecks all retained input segments before returning.
- [7 new authored parametrized tests `cb5e014`](https://github.com/Iam-2squared/ark-ai/commit/cb5e01441419c6640385f919519afb84fd418275) cover the expected public-only result, five final-getter mutations and one early-getter mutation.
- This corrects a case where `private_data_export_authorized` could return `False` yet rewrite the already checked final synthetic review. The changed report is rejected. Hashes/retained scalar claims remain **caller-controlled**, never an authenticated audit, legally effective consent, or export grant.

## Exact verification and limits

- Previous exact checkpoint run [#42650056305](https://github.com/Iam-2squared/ark-ai/actions/runs/42650056305), HEAD `92a85c12`: **six of six jobs completed GREEN** (Ubuntu/Windows × Python 3.11–3.13). This applies ONLY to the previous HEAD.
- New commit-specific CI [#42657755106](https://github.com/Iam-2squared/ark-ai/actions/runs/42657755106) for `f4f11b86`, [#42657910285](https://github.com/Iam-2squared/ark-ai/actions/runs/42657910285) for `41639887`, [#42658024335](https://github.com/Iam-2squared/ark-ai/actions/runs/42658024335) for `14cdf7d2`, and [#42658120809](https://github.com/Iam-2squared/ark-ai/actions/runs/42658120809) for `cb5e0144` were **in progress or queued at observation time**. No new exact-head six-platform GREEN, 22-case all-platform PASS or local full pytest has been established at writing.
- No duplicate manual CI was launched. Normal GitHub Contents API writes only; no raw-Git push/ref override, no forced update, no executable write bypass. Existing automatic CI may start on each synchronizing commit.
- In-process descriptor and helper identity checks are **defense in depth**, not isolation against arbitrary same-process Python code. Mutually forged receipt and retained witnesses, real SQLite path TOCTOU/sidecar races, Windows reparse/ACL custody, restart-safe action authority and authenticated clocks remain unproven.

## Independent follow-up audit / next priority

Read-only inspection of `src/ark/agency/planner_journal_review.py` confirms this lane is deliberately a synthetic SQLite journal: a recovered RUNNING step remains UNKNOWN and must never be automatically retried. It is NOT permission to issue real actions, and an in-database digest does not authenticate a maliciously rewritten journal. Retain this boundary while advancing Planner persisted exact READ results, restart recovery, and audit-before-action for **mock/disconnected execution only**.

**Next order:** (1) assess the exact latest-head CI and repair any concrete failure with minimal semantics-preserving changes; (2) Memory CAS/ABA and manual COMMIT-UNKNOWN reconciliation; (3) Planner durable READ and registry-bound PermissionGate; (4) restart-safe occurrence/audit-first mock execution; (5) Personal Context retention/privacy, proactive/observation fixtures and V3 free-only identity/authorization blockers. Keep PR #5 Draft/unmerged and UI PR #9 stopped/unmerged. No frozen gate, protected evaluation, Candidate promotion or paid action is authorized.

Overall ARK / JARVIS and V3: **NOT_PASSED**.
