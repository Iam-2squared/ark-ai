# ARK AI Run913 — non-UI due-page admission, source-carrier fences, WAL failure phases

Prepared 2026-11-16 JST. This report concerns **synthetic, detached/free-only code and tests**, not operational permission, live data, model training, user consent, independent custody or completed JARVIS functionality.

## Exact work basis and four coherent packages

- **Initial exact branch/PR #8 work-basis HEAD:** `9cc6fa2e74cfad080339b94c4fd36998b47520ef`. Prior Run912 checkpoint CI [#43807110372](https://github.com/Iam-2squared/ark-ai/actions/runs/43807110372): **GREEN 6/6** Windows/Ubuntu × Python 3.11–3.13. This is a **prior** head, not evidence for Run913 code.
- **Memory due-page SQL preflight:** [source `a34056cb`](https://github.com/Iam-2squared/ark-ai/commit/a34056cb8fdebb4f946d0ec523158bb250026fa1), [8 authored tests `f508b8b8`](https://github.com/Iam-2squared/ark-ai/commit/f508b8b860123421ec50a814af09cb3e45590adb). Under the existing `BEGIN IMMEDIATE` and caller clock, preflight `typeof` and BLOB byte lengths for precisely the deterministic expired, optionally scoped/limited page **before** `SELECT *` hydrates TEXT. Rejects over-budget and BLOB contamination without row deletes or expiry events. Preserves default unlimited-purge semantics, event-in-same-transaction, CAS row-image DELETE, explicit page limit, unrelated future rows, and multibyte Japanese. No v1 schema/policy change. A separate local Python SQLite-only SQL smoke confirmed normal due and invalid BLOB query behavior; **not** an ARK suite PASS.
- **Disconnected due-reservation ledger source custody:** [source `9968b8c0`](https://github.com/Iam-2squared/ark-ai/commit/9968b8c00c8768084e45231ce8c7d45ad4a37576), [test `fecd9d05`](https://github.com/Iam-2squared/ark-ai/commit/fecd9d05fa953b7f00e18776f227b4da27632ad7), [assertion refinement `852c7d18`](https://github.com/Iam-2squared/ark-ai/commit/852c7d18441b4c5eb38ce52b2e3fa836c8562ff9). **5 authored parametrized cases**: init-time exact Path carrier pin, refusal of a valid different ledger or value-equal new Path before opening SQLite, and unchanged receipt/read-only restart. Denial-only receipt flags tested directly. This is in-process source continuity, **not** independently authenticated path custody, trusted time or authority.
- **Actual disposable WAL last-close diagnostics:** [source `119bcc29`](https://github.com/Iam-2squared/ark-ai/commit/119bcc29e1c1dd4e8a4ef3c4c6087a30708ca00e), [4 authored cases `75ea5f30`](https://github.com/Iam-2squared/ark-ai/commit/75ea5f30132f58eab3dd48ada71864881dfbb9f8). Distinguishes `cold_restart_construct` from `cold_restart_read` for Memory, ActionAudit and revocation. Error receipts disclose only phase/status/kind/keeper, never exception text, local path or private row. Linux/POSIX-only subprocess fixture is disposable; missing WAL/SHM is unsupported rather than false success. This **does not fix** intermittent Windows/Ubuntu WAL/SHM last-close races or permit sidecar alias relaxation.
- **Disconnected proactive quarantine source+policy continuity:** [source `43bd4fa6`](https://github.com/Iam-2squared/ark-ai/commit/43bd4fa64ba68664a5a530a43984cbc095395cd1), [7 authored cases `44e5169d`](https://github.com/Iam-2squared/ark-ai/commit/44e5169df02128595261a4c2e896e4d707ae552f). Exact original `Path` and frozen policy tuple carriers are now checked before future SQLite opens, refusing separate-call source or policy retargeting, including value-equal copies; unchanged synthetic quarantine/restart remains inert. No policy/schema migration, dispatch, notification, automatic replay or permission granted.

**Total: 4 coherent non-UI work packages, 24 newly authored parametrized test cases.** These numbers denote **authored**, not confirmed GREEN. Ordinary GitHub Contents API writes only, no raw-Git bypass/force push. All writes were preceded by a fresh PR #8 HEAD read; no detected concurrent writer changed the branch during these updates.

## CI snapshot — exact-head promotion prohibited

- Prior Run912 `9cc6fa2e...` [#43807110372](https://github.com/Iam-2squared/ark-ai/actions/runs/43807110372): **GREEN 6/6**.
- Memory test HEAD `f508b8b8...` [#43811925979](https://github.com/Iam-2squared/ark-ai/actions/runs/43811925979): **IN PROGRESS** at observed review.
- Due-reservation assertion HEAD `852c7d18...` [#43812224976](https://github.com/Iam-2squared/ark-ai/actions/runs/43812224976): **QUEUED**.
- WAL test HEAD `75ea5f30...` [#43812494796](https://github.com/Iam-2squared/ark-ai/actions/runs/43812494796): **QUEUED**.
- Quarantine tests HEAD `44e5169d...` [#43812760789](https://github.com/Iam-2squared/ark-ai/actions/runs/43812760789): **QUEUED**.
- Later technical report and canonical checkpoint commits will have their own auto-triggered CI. Never assume latest-head GREEN from earlier runs; no duplicate workflow dispatch.

## Frozen gates and honest limitations

V1/V2/Local UI/Launcher contracts and evidence unchanged. Protected V2 evaluation unopened. V3 PR #5 Dataset/Candidate/provenance/approval/identity/compute gates unchanged. UI PR #9 untouched, UI work paused. PR #5/#8/#9 Draft and unmerged; main unchanged. No external GPU/billable compute, paid API/subscription, credential/account connection, actual Candidate/weight/training, real user context/export, hardware test, real backend WRITE/notification/approval, destructive action, auto-retry of ambiguous UNKNOWN, main merge, force push or safety bypass.

SQLite cross-process last-close SIDECAR_REFUSED remains UNKNOWN/FAIL even when a separate marker was durably committed. New phase granularity is diagnostic only. Planner cross-store COMMIT-UNKNOWN, durable exactly-once external effects, trusted audit clock, independent source/witness custody, actual consent and physical offline GGUF proof remain blocked. Overall **ARK/JARVIS NOT_PASSED**.

## Next plan / 今後の方針

1. Confirm Run913 exact code/test/technical-report and checkpoint CI in six environments. On fail, inspect logs and repair only via allowed ordinary source/test path without weakening contracts; work separate non-UI lanes during CI.
2. Use new WAL diagnostic phase distinction to narrow disposable two-process sidecar close/revocation race, never infer durable dual success or replay.
3. Advance Memory CAS/expiry/event high-water and Planner crash/UNKNOWN nonreplay; integrate immutable registry, exact PermissionGate, audit-before-action and disconnected/mock-only execution after lower-layer exact-head GREEN.
4. Continue privacy-safe Personal Context, proactive/observation fixtures and detached free V3 identity/reproducibility guards. Keep UI paused, protected evaluation closed, all three PRs Draft/unmerged.
