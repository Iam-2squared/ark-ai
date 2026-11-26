# Run1059 — revocation race winner prefix assertion

- Target: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `c840ec805533499cf48cb42d9ba974d01fae045d` (Run1058 checkpoint result; exact-head CI run 44886809693 GREEN).
- Corrects the Run1058 test-only follow-up after CI run `44886475992` failed on all six jobs.
- The worker emits `REVOKED:<64-hex-digest>`; the assertion now counts outputs by `startswith("REVOKED:")`, not equality with the prefix-only string.
- The existing invariant remains: exactly one durable winner, exactly one safe loser (`ALREADY` or `AMBIGUOUS`), and independent one-row readback. No retry, consent, production source, schema, or authority change.
- Synthetic disposable SQLite fixtures only. Fresh exact-head CI is required; the failed run is not treated as evidence of success.
