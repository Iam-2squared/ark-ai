# ARK AI Run975 — non-UI complete-row admission and registry scope budget

This report records **three independent, reversible, free-only non-UI source+test packages**, implemented from the exact Run974 PR #8 checkpoint `e2e63b541b73061c85b2f2d3e9a3a147b20d850c`. No frontend, model, Candidate, hardware, external tool, or paid action occurred.

## Source changes and synthetic regressions

1. **Memory scoped get/search full-row SQLite admission** — source [`61c37214e`](https://github.com/Iam-2squared/ark-ai/commit/61c37214ea2bdceedfbd7e6aafb74078b2f5d9aa), tests [`760a670e1`](https://github.com/Iam-2squared/ark-ai/commit/760a670e19b26f595de6e26469a0d247f5fd37b2). The original bounded content/metadata/source aggregation remains unchanged. A second pre-`SELECT *` check, within the same SQLite read transaction and selected scope/page, rejects malformed identity/digest and non-integer timestamp/revision storage classes, including dynamically typed oversized numeric BLOBs. **6 authored tests** cover BLOB/oversized digests, timestamp storage class, cross-scope isolation, and valid Japanese rows.
2. **Memory all-scope event alignment row admission** — source [`f26685151`](https://github.com/Iam-2squared/ark-ai/commit/f26685151e556e68fe431a6388ee43b5a9f5bed7), tests [`d06f7f54a`](https://github.com/Iam-2squared/ark-ai/commit/d06f7f54abcb640fe84caa4419e78ccbdc923c44). The global read-only reconciliation now rejects BLOB/REAL values in created, updated, expiry and revision fields before streaming full records into Python. Existing event counting, hash-chain/clock skepticism and untrusted-writer warnings remain. **5 authored tests** cover four malformed numeric carriers and a valid multilingual/nullable-expiry history.
3. **Opt-in ToolRegistry scope width admission** — source [`1f74eeb91`](https://github.com/Iam-2squared/ark-ai/commit/1f74eeb91348de299cb0d400a336b62ad8c40981), tests [`48752f04c`](https://github.com/Iam-2squared/ark-ai/commit/48752f04cbc87792e8676ad10d7ff3a11e991ded). Registry `resolve` and `bind` now check the *exact* scope carrier and reject over 4096 codepoints or UTF-8 bytes before a reflected scope is scanned, hashed, or bound. The local scope-budget validator is identity-pinned. **5 authored tests** cover excess codepoints, multibyte UTF-8 size, reflected 256K-character input, valid 4095-byte Japanese scope, and a substituted validator. Frozen generic `ToolCall v1` contract is unchanged; no real backend is invoked.

**Total new authored regressions: 16.** These are test definitions, not a PASS claim. Existing v1 schema, public MemoryRecord/MemoryScope, ToolRegistration/ToolCall contracts, frozen V1/V2/Local UI/Launcher evidence and protected V3 gates are unchanged.

## Verification: exact HEAD only

- Prior, unmodified Run974 checkpoint `e2e63b541b73061c85b2f2d3e9a3a147b20d850c`: [CI #44374822229](https://github.com/Iam-2squared/ark-ai/actions/runs/44374822229), **GREEN all six** (Ubuntu/Windows × Python 3.11/3.12/3.13); this is **not** evidence for the Run975 commits.
- At report creation the Memory-alignment test commit `d06f7f54a` had associated CI **#44383669384 in_progress **.
- Latest executable source/test HEAD `48752f04cbc87792e8676ad10d7ff3a11e991ded` requires its *own* exact SHA CI; a newer run was not yet observed at report creation. Never infer green from any predecessor.
- No private PC GGUF or physical offline measurement. No claim that native filesystems, independent writers, trusted time, durable WRITE authorization or external effects are proven by these synthetic tests.

## Preserved controls and next steps

PR #5 and paused UI PR #9 remain Draft and unmerged; main and all frozen evidence are untouched. PR #8 remains Draft and no merge or authorization change is requested. No secrets, paid compute/API/GPU, live capture, real Tool executor, automatic unknown-WRITE retry, protected final evaluation, Candidate creation/promotion, or new account connection.

Prioritize (1) confirm latest exact-head six-matrix CI and repair only observed failures, (2) complete Memory WAL/SHM/CAS/ABA and COMMIT-UNKNOWN local recovery, (3) integrate Planner/registry/permission/one-shot audit-before-action strictly through disconnected mocks after green evidence, (4) private context revocation, proactive occurrence/replay and observation fixture integrity. **ARK/JARVIS NOT_PASSED.**
