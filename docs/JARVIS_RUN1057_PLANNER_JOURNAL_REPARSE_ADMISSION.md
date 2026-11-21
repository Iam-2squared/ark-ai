# Run1057 — Planner journal Windows reparse admission

- Target: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `4628e8cf6b38b7826bbe699431b6040890dd6e7a`.
- Rebased source: PR #167, original child HEAD `8452e7f057b7bfde4c9f120f49dbfa3f6710b134`.
- Original exact-head CI: run `44877445463` / run 6880, Windows/Linux × Python 3.11–3.13, 6/6 GREEN.
- Pins the Windows reparse-point mask, rejects malformed metadata and checks ancestors/database leaf/SQLite sidecars before SQLite access.
- Planner journal remains disconnected and replay-only. Recovered RUNNING steps remain UNKNOWN; no dispatch or automatic replay is added.
- Synthetic stat fixtures only; no privileged junctions. Fresh exact-head CI is required on this rebase; original CI is not transferred.
