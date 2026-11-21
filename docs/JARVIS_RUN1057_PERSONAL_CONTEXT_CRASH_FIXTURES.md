# Run1057 — Personal Context replay crash and proactive race regressions

- Target: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `4628e8cf6b38b7826bbe699431b6040890dd6e7a`.
- Rebased source: PR #164, original child HEAD `73d9509688e7d8d72b4ac7d87cf54792ad0d5c44`.
- Original exact-head CI: run `44877053408` / run 6877, Windows/Linux × Python 3.11–3.13, 6/6 GREEN.
- Scope: test-only. Adds a spawned-process exit after replay-ledger native COMMIT and stabilizes the proactive two-process CAS race by retaining a WAL anchor connection.
- Synthetic disposable SQLite fixtures only. No live personal data, disclosure, tool dispatch, consent, trusted-clock, custody, or external-effect evidence.
- The original CI run validates only its original child head and older parent. This rebased branch requires fresh exact-head CI; no GREEN result is transferred.
