# Run1057 — Personal Context replay-ledger reparse admission

- Target: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `4628e8cf6b38b7826bbe699431b6040890dd6e7a`.
- Rebased source: PR #165, original child HEAD `b3682ac8b7f487f72f7629f70c008f5e648b58c8`.
- Original exact-head CI: run `44877361487` / run 6878, Windows/Linux × Python 3.11–3.13, 6/6 GREEN.
- Source guard pins the import-time Windows reparse-point mask, rejects policy rebinding and malformed present metadata, and checks ancestors, database leaf and SQLite sidecars.
- Hash-only replay schema, row format and denial-only authority remain unchanged. Synthetic stat metadata only; no privileged junctions or live personal data.
- Original CI applies only to the original child head and older parent. Fresh CI on this rebased exact head is required.
