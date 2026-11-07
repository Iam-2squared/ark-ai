# Run494 — disconnected evidence authorities and bounded V3 snapshot enumeration

Date: 2026-10-31 Asia/Tokyo. This report describes only the source/test
changes saved on two isolated Draft PRs; it is not a JARVIS completion gate.

## Work packages (four coherent source + test pairs)

1. **Multi-store epoch vectors (PR #8).** Source
   `8577529209502337d875b4aae000786c5af4ceb1`, tests
   `e3bc7f39ba83c3c72971e5cd716563a37a8bf332`.
   Five reflected result descriptors must remain exactly false on capture and
   progress review: coherent snapshot, trusted time, independent custody,
   Memory disclosure and Tool dispatch. Three new pytest functions, 11 cases.
   Existing exact-type error behavior was accidentally changed on the first
   source commit, detected by CI run `41165494597` (Ubuntu 3.12: 1 failure,
   5,165 pass / 1 skip). Restored the established `exact vector` diagnostic
   with source fix `8e9fcccf5112617bf49ad6b6547ca5564d81dbb8`.
   Old regression test was retained; no grant behavior added.

2. **Privacy-safe Context membership (PR #8).** Source
   `837ebd5c98857fc71960ac783a9043027d8f1037`, tests
   `c96d92f6b63dc6b7336603811325dd5bced58c63`.
   Reject an exact result DTO claiming consent, disclosure, retention or
   trusted-clock authority by reflected class-property replacement.
   Two new pytest functions / 5 cases. No private content read or exported.

3. **Query-only SQLite schema seals (PR #8).** Source
   `b7f710f2679ed9730b0203aaf33e49cd1b534d44`, tests
   `a77c6111f8e17c592284c2fa761c36b98065d23c`.
   Both capture and prior-seal comparison deny source authentication, independent
   custody, WAL attestation, cross-store atomicity and data-disclosure permission
   impersonation. Three new pytest functions / 11 cases. No application row
   reads or writes; database remains caller-owned and query-only.

4. **V3 identity manifest resource bounds (PR #5).** Source
   `8e73a863c9be86f9b5d6516f8dea611ce29996d2`, tests
   `f86f7fc63d996a9b8d128cf89bbe355e697e72d1`.
   Enforce a 16,384-entry local directory-enumeration budget *before sorting*;
   cap relative path bytes and reject invalid/overlong UTF-8 identity labels.
   Four new pytest functions / 5 expanded cases. Initial six-job CI
   `41165540546` failed Ruff I001 on import-section spacing, not semantics.
   Fixed via `ebc83999d83fb108db08be67fea0ece178523f90`; no tests removed.

**New tests:** 12 pytest functions and 32 expanded cases. All four packages
are purely local metadata/fixture code. No paid GPU, remote inference, models,
weights, training, protected V2 evaluation, real Tool, consent action,
irreversible change, or main merge was performed.

## CI / provenance at technical-report drafting

- Prior PR #8 Run493 source `b3a9c941ee80c768ed8e9db0a69d4195c18dae7d`,
  run [#1771](https://github.com/Iam-2squared/ark-ai/actions/runs/41161548147):
  all six Ubuntu/Windows Python 3.11–3.13 jobs GREEN, independently checked.
- PR #8 first Run494 epoch source/test CI
  [41165494597](https://github.com/Iam-2squared/ark-ai/actions/runs/41165494597):
  observed FAIL (one changed expected diagnostic). Corrective source above.
- PR #8 corrected *source* HEAD
  `8e9fcccf5112617bf49ad6b6547ca5564d81dbb8`,
  [41165783405](https://github.com/Iam-2squared/ark-ai/actions/runs/41165783405):
  QUEUED at drafting. **Not yet declared exact-head GREEN.**
- PR #5 initially failed local-manifest source/test run
  [41165540546](https://github.com/Iam-2squared/ark-ai/actions/runs/41165540546)
  on Ruff I001 in six jobs. Corrected source HEAD
  `ebc83999d83fb108db08be67fea0ece178523f90`,
  [41165719631](https://github.com/Iam-2squared/ark-ai/actions/runs/41165719631):
  QUEUED at drafting. **Not yet declared exact-head GREEN.**
- Independent local full pytest/Ruff: NOT VERIFIED. GitHub Actions is the
  current test evidence; documentation commits do not validate a new source HEAD.

## Frozen controls and limitations

- Memory v1 contract blob `b6e93821ecd69270a7634aceb20775dc36e9953c`;
  Agency v1 contract blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`.
- V3 frozen contract blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`,
  companion hash file blob `176154514bd6be22685ca0555bc682c3bd8d45dc`.
  All four reread with unchanged SHA. Main remains
  `7a843f17eb96ed13d66f23b58b06406b3002e405`.
- Local metadata hashes are not signatures, trusted clocks, independently
  authenticated writers, coherent cross-database epochs or physical-outcome
  receipts. New inventory limits reduce normal resource exhaustion but are not
  hostile-writer-safe file snapshotting.
- PR #5 remains Draft/unmerged; Candidate/paid actions are blocked by their
  explicit authorization gates. UNKNOWN WRITE stays quarantined.

## Next

1. Resolve both current exact-source six-job CI matrices; preserve old tests,
   smallest fixes only, no duplicate manual workflow dispatch.
2. Progress Memory CAS/history provenance and Planner manual UNKNOWN-WRITE
   recovery, then trusted-clock audit-before-action and occurrence fencing.
3. Continue local-only context consent-veto/expiry and Observation mock adapter
   readiness; gate any integration on exact-head GREEN.
4. Independently review V3 path/identity/approval/provenance guards without
   opening frozen evaluation, creating a Candidate or starting paid compute.
