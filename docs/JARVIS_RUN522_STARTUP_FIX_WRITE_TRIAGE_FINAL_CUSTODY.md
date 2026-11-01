# Run522 — startup integrity CI repair and offline WRITE checklist custody

**Status: Draft / local-only / diagnostic only / ARK-JARVIS NOT_PASSED.**
**Branch:** `research/jarvis-foundations`, PR #8; source+test work basis `9e75a1dd58876ee3eb39cccc6b9df243aecc4051` before this document commit.

## Observed CI regression, corrected without weakening protection

Run521 final source CI [41278527291](https://github.com/Iam-2squared/ark-ai/actions/runs/41278527291) finished **FAIL, six out of six environments**. The Ubuntu and Windows job logs showed seven failures in `tests/test_startup_post_traversal_custody_run521.py`: `checks >= 3` asserted only *completed* `_assert_integrity` calls. On the third attempt, the original integrity validator correctly raised before the wrapper incremented its counter, yielding two completed checks. No premature return of altered READY state was observed in those seven failures. Commit `e24ceb53c4929a0c72126e8bc10d8ab70a2acda0` moves the wrapper increment before calling the original validator, counting attempted checks without changing production validation or lowering the asserted threshold. Its exact-commit CI is [41281766421](https://github.com/Iam-2squared/ark-ai/actions/runs/41281766421); do not inherit success from older HEADs.

## NEW — manual WRITE triage final-denial and nested-item epoch

In the disconnected, read-only `build_offline_write_triage_packet` function:

- Constructed nested checklist-item identities and primitive fields are pinned **before** creating the report, including before any denial-property callback.
- After its last denial-property callback, it re-checks all packet fields and all pinned nested items, plus original steps, retained local witness and ledger path.
- False-valued authority getters cannot silently replace the investigation state, disposition, reservation ID, packet fingerprint, or nested tuple.
- The packet continues to report **no human review completed, no external outcome verified, no dispatch, no replay**, and cannot discharge an UNKNOWN/RUNNING WRITE.

Source safety hardening is at commits `f702acd357ac1731ad380aed9315e4262c1127f3` and `c43e67b65d3557188f22d2e0ed1f82b078db17ad`. Eleven new cases (five nested fields, five packet fields and one valid UNKNOWN fixture) were authored in `tests/test_offline_write_triage_last_denial_run522.py`, combined source+test HEAD `9e75a1dd58876ee3eb39cccc6b9df243aecc4051`. Exact [CI 41281914831](https://github.com/Iam-2squared/ark-ai/actions/runs/41281914831) was IN PROGRESS at initial inspection; final six-platform GREEN is not claimed here.

## NEW — observation reuse cannot acquire action authority

`review_synthetic_observation_reuse` now checks **all four denied capabilities** of the returned local fixture report: media capture, disclosure, notification, and dispatch. It then rechecks the original cached witness, observation envelopes, both lineage review witnesses, and all return fields **after the last false-valued capability getter**. A getter that falsely denies dispatch while changing a previous lineage hash, expiry time, source identity or the result is rejected. This is a simulated private observation only and does **not** capture media or verify consent.

Source commit `34825f5c8022c7cd423e6c7d7f8a7bb92c441785`; eleven new focused cases in `tests/test_observation_reuse_denial_custody_run522.py` at exact source+test HEAD `3422761ad9120f761550a5af73331f294936fb2f`. No six-platform CI success is inferred from the earlier startup or triage HEAD.

## Explicit trust and authorization limits

These local checksum and SQLite fixtures cannot prove who originally wrote the record, human consent, a trusted clock, historical/externally completed effects, forensic erasure, or cross-store atomicity. A late failure after durable COMMIT must be manually reviewed and must never trigger automatic WRITE retry. No ToolBackend action, notification, new credential/account connection, paid service, external GPU, model generation/training, protected V2 opening, Candidate promotion, frozen-contract change, main merge or physical-PC action occurred.

**Next:** finish exact-head six-platform CI; if failed, inspect concrete job logs and fix only demonstrated defects through normal GitHub Contents writes. Independently continue Memory CAS, Planner durable UNKNOWN WRITE recovery, registry-bound mock READ, trusted-clock/audit-before-action and scheduler deduplication; retain every prohibition above.
