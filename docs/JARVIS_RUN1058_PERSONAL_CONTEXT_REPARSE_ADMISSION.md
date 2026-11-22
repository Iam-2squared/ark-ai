# Run1058 — Personal Context replay-ledger reparse admission

- Target: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `cab78192933c9383b92b9b58d41d6abe2c7023b8` (after the exact-head-GREEN Planner journal reparse-admission integration from PR #172).
- Rebased source: PR #171, child HEAD `1fedef3a45d10ef67b9e657688c8f20114ec2dd0`.
- Original exact-head CI: run `44881652597`, 6/6 GREEN on the previous parent. This evidence does not transfer to this rebase.
- Source guard pins the import-time Windows reparse-point mask, rejects policy rebinding and malformed present metadata, and checks ancestors, database leaf and SQLite sidecars.
- Hash-only replay schema, row format and denial-only authority remain unchanged. Synthetic stat metadata only; no privileged junctions or live personal data.
- Fresh exact-head CI is required on this rebased child before integration.
