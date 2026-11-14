# Run519 — Registered READ / fixture receipt, atomic Memory and offline PCM

**Status as of 2026-11-01 12:59 JST:** independent, free-only local foundations. Source/tests saved on the Draft PR #8 research branch. The final combined HEAD's six-environment CI was still queued at this evidence-writing point. No execution backend, real user-data read, microphone, persistent action, Candidate, GPU or paid service was invoked.

## Exact work and source identity

- Original work basis for Run519: PR #8 HEAD 982100ca62eb2b6d020c5ed90dc17b1cfc42febd.
- Old Memory test error diagnostic expectation corrected at HEAD 45a6378ed84c3d37bbeccd4fe8a0ae93f7ad2fd5; source/test [CI 41270568126](https://github.com/Iam-2squared/ark-ai/actions/runs/41270568126) **6/6 GREEN**. No safety condition was relaxed. The preceding Run518 CI 41266752405 was 6/6 FAIL due to this obsolete regex.
- New non-dispatching registry/fixture/journal identity join: src/ark/agency/disconnected_registered_fixture_join.py, source commit 0c797d8b393d0299eea751263289834db2b47df1. Tests: tests/test_registered_disconnected_fixture_join_run519.py, 28 authored pytest cases. The first combined CI 41270945788 was 6/6 FAIL due to one unused test import. Test-only import correction at 16b64dc0329fdb35807b8a65eb717a44e9874b23; [CI 41271031136](https://github.com/Iam-2squared/ark-ai/actions/runs/41271031136) was running at this record point.
- Single-transaction Memory row/event epoch final-denial custody: src/ark/memory/atomic_epoch_review.py source commit 1b12856ffdd0da194169baf39dde3b1d38195bcc; tests/test_memory_atomic_epoch_final_denial_run519.py at HEAD 1890d9514e518aa4af6bbb739c6850e7a0f8034e. 10 authored pytest cases. [CI 41271106178](https://github.com/Iam-2squared/ark-ai/actions/runs/41271106178) was running at this record point.
- Offline audio-only PCM conversion witness final-denial custody: src/ark/offline_pcm_mono16.py commit 67332bcc2c25c2288151c7ab041450a7dfafead0; tests/test_offline_pcm_final_privacy_epoch_run519.py at HEAD 712f28812063a0e35be1f2ae6273c708151d4089. 15 authored pytest cases. [CI 41271233110](https://github.com/Iam-2squared/ark-ai/actions/runs/41271233110) was queued at this record point.

**All new non-V3 test cases**: 53 (28 registered join + 10 Memory + 15 offline PCM); plus one existing diagnostic assertion amended. Cases are authored, not independent local PASS claims. This evidence document does not claim any CI run had finished when it had not.

## Foundation invariants

1. Registry READ action identity is an `act_`-prefixed canonical digest; disconnected fixture/journal identity is separately `req_`-prefixed. A local correlation binds both to the actual registry revision, exact scope/grants, synthetic time, exact canonical fixture arguments, deterministic result and journal-row preparation. The correlation hash is not signed, no backend is dispatched, and it is not stored in journal v1; callers must retain it separately. This joins existing components only in a non-authorizing, reversible path. WRITE is denied even with a grant.
2. Memory's atomic read-only SQLite row/event witness rechecks all original result carrier objects **after** each denial-property callback. It rejects same-value replacements of fingerprints/counts/digests, scope or source path retargeting, and synthetic authority escalation. Existing SQLite DDL and content privacy are unchanged; it still does not authenticate historical writers.
3. Offline mono PCM conversion rechecks original audio bytes, source/owner/privacy digests, conversion formats and final output hash carriers after denial getters. A false-valued getter that changes the returned PCM or input is rejected; the result cannot claim consent, source authenticity, speech recognition or audio disclosure authorization. This is fixture-only in-memory audio conversion, not microphone access or ASR.

## Frozen/gated boundaries preserved

No V1/V2/Local UI/Launcher contract/evaluation revision, protected final evaluation, real Candidate/adapter/weights, external GPU, paid API, real ToolBackend dispatch, automatic WRITE retry, user-data erasure, human-review decision or main merge. PR #5 and PR #8 remain Draft/unmerged. **ARK overall NOT_PASSED.**

## Next plan / 今後の方針

Close exact-head CI on the joint PR #8 source after the unrelated work packages, fix only actual failures, then validate retained cross-identity join on restart without treating SQLite or locally supplied witnesses as externally authenticated. Continue Memory CAS/expiry/history, Planner UNKNOWN WRITE manual triage, trusted-clock audit-before-action, Scheduler overlap/restart and privacy-safe Personal Context; all on free-only isolated lanes.
