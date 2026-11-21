# Run1059 — ActionAudit Windows reparse admission

- Target: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `c840ec805533499cf48cb42d9ba974d01fae045d`.
- Rebased source: PR #168, original child HEAD `76a90dd2cb2bfe69c07b4ede80b6eaad61bebe3d`.
- Original exact-head CI: run `44877557891` / run 6881, Windows/Linux × Python 3.11–3.13, 6/6 GREEN.
- Pins the import-time Windows reparse-point mask, rejects malformed metadata and reparse ancestors/database leaves/SQLite sidecars, and admits the main leaf with direct `lstat` before SQLite access.
- Reparse/symlink sidecar denial retains a fixed path-free diagnostic. ActionAudit v1 schema and event contract remain unchanged.
- Synthetic stat fixtures only; no privileged junctions. Fresh exact-head CI is required on this rebase; original CI is not transferred.
