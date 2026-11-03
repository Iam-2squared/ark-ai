# Run528 — Non-authorizing V3 review packet post-write custody

**Branch:** PR #5 `research/v3-learning-evaluation`, Draft/unmerged. **V3 NOT_PASSED.** This hardening is free-only and does not open any training, paid compute or protected V2 final-evaluation gate.

## Change and witness

- Source `src/ark/learning/authorization.py`, commit `723cdb7ac30367d13ff0b540e0a59af3e848c8e1`.
- Focused synthetic tests `tests/v3/test_authorization_packet_postwrite_custody_run528.py`, combined package commit `5bc906ca91e8cec5d748c3ccf492fecd2d09e4e5`.
- The existing create-only `Path.open("xb")` writes a canonical, review-only JSON packet. A successful return from `write()` is not proof that all requested bytes reached a new non-aliased file.
- Now verify exact write count, recheck the in-memory packet JSON-tree epoch, inspect regular-file/hardlink identity, reread the bytes after the handle closes, compare them to the originally canonicalized bytes and reject a changed file/link/source epoch.
- Five authored pytest scenarios: short write; same-length wrong bytes; post-read mutation of the packet tree; newly created hardlink to the output; normal exclusive write and refusal to overwrite. Test fixtures use only temporary local paths.

## Deliberate limitations

- Review packets **do not constitute user approval** for training, GPU, preflight, subscriptions, Candidate, protected V2 opening, promotion or main merge.
- This is a local *post-write observation*, not a race-proof dirfd-based path walk or tamper-proof secure storage. A concurrent writer could change the file after the last inspection. True external provenance and provider billing caps remain outside this free-only test.
- All model/tokenizer/tool immutable byte identity, dataset review, contamination evidence and provider pricing/caps are still hard blocked by explicit evidence and authorization gates. Do not substitute placeholders.
- The test count is **authored**, not a standalone local pytest PASS. Exact-head CI must be inspected independently; a documentation commit has its own distinct HEAD/CI.
