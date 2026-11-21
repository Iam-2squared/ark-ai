# Run1087 — Rebase reentrant path-policy custody onto the latest JARVIS foundation

## Exact basis

- Parent PR: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `073d08ca19dfc67de7dd8da6ce3956bbefc3974b`.
- Previous common parent for the four source packages: `916aae6c6578086fee5e83c77c23375712676c90`.
- Verified parent delta from that common parent to the new basis: two documentation-only commits modifying `docs/PROJECT_STATUS.md`; no source or test paths changed.
- New child branch: `research/run1087-reentrant-stat-custody-rebase`.

## Reapplied packages

1. Planner journal path-policy custody from Draft PR #219.
2. ActionAudit path-policy custody from Draft PR #220.
3. Memory SQLite path-policy custody from Draft PR #221.
4. Personal Context replay-ledger path custody from Draft PR #222.

Each package pins import-original stat predicates and rechecks policy around reentrant filesystem/metadata callbacks. The Personal Context replay ledger additionally rejects Windows reparse-point metadata for ancestors, the database leaf and SQLite sidecars. The changes preserve their existing schemas, public interfaces, replay/transition rules and denial-only authority boundaries.

## Exact-head source evidence carried forward

The four source packages and synthetic regression tests were previously validated on their own exact child heads:

- Planner PR #219: `698e4191ddebf1a84af14f30b7959257d56c1911`, CI run [44957865329](https://github.com/Iam-2squared/ark-ai/actions/runs/44957865329), GREEN 6/6.
- ActionAudit PR #220: `9090446ab9d58ac77ca22ec905ea41db511888e5`, CI run [44957865520](https://github.com/Iam-2squared/ark-ai/actions/runs/44957865520), GREEN 6/6.
- Memory PR #221: `24130ebce621442c058bb6a4d2019a8645a863fe`, CI run [44957860588](https://github.com/Iam-2squared/ark-ai/actions/runs/44957860588), GREEN 6/6.
- Personal Context PR #222: `f332fe623008ae6ff3b2da856ff80f533a82ba41`, CI run [44957859530](https://github.com/Iam-2squared/ark-ai/actions/runs/44957859530), GREEN 6/6.

Those runs validate only the original child heads. This rebased aggregate head requires a fresh complete Windows/Linux × Python 3.11–3.13 CI run; no result transfers.

## Limits

Repeated pathname metadata checks are not atomic directory-handle custody, a sandbox, immutable filesystem custody, independent provenance, authenticated audit history, trusted time, consent, power-loss durability, cross-store atomicity, or proof of exactly-once external effects. Tests use synthetic local paths and metadata only.

No paid/external compute, Candidate generation or promotion, protected V2 evaluation, frozen-contract change, real ToolBackend dispatch, UI/frontend work, credentials, physical hardware action, or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
