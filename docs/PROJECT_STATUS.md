# ARK AI — Canonical Project Status

**LATEST — 2026-10-31 / Run494: four free-only packages, 32 new parameter-expanded tests, two CI regression fixes.**

**Saved at:** **2026-10-31T12:47:21+09:00 Asia/Tokyo/JST**, measured from the local-time source before this GitHub Contents write, **not a trusted/attested clock**.

**Overall ARK/JARVIS: NOT_PASSED.** Isolated reversible local/mock architectural foundations continue; no JARVIS end-to-end PASS, actual Tool execution, authenticated cross-store custody, genuine user consent, protected V2 evaluation, authorized Candidate, or human review is claimed.

## LATEST branch and SHA provenance

- **JARVIS foundations:** [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), `research/jarvis-foundations`, OPEN / DRAFT / UNMERGED. Run494 **initial work-basis HEAD** `e3a509eea4e3c67ec175399b402932b3edd0cdaa` (Run493 checkpoint). Final source/test HEAD `8e9fcccf5112617bf49ad6b6547ca5564d81dbb8`. Technical-report and **checkpoint-write-basis HEAD** `6e8961a3b4144a8c24e84fa3e3ee7ba5cd0bf1fa`. The checkpoint-result HEAD cannot appear inside its own contents without circular reference: the GitHub Contents write result plus subsequent head read establishes it.
- **V3 independent branch:** [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), `research/v3-learning-evaluation`, OPEN / DRAFT / UNMERGED. Initial Run494 HEAD `7bd2ad6450c3a887351705f11054313de49c809c`; final source/test/fix HEAD `ebc83999d83fb108db08be67fea0ece178523f90`.
- **main:** `7a843f17eb96ed13d66f23b58b06406b3002e405`, unchanged. No merges, force-pushes, raw Git-object safety bypass, deletion, physical-PC operation or irreversible action.
- Detailed code/test/CI provenance: [Run494 technical report](JARVIS_EPOCH_CONTEXT_SCHEMA_V3_SNAPSHOT_RUN494.md), saved on PR #8 as `6e8961a3b4144a8c24e84fa3e3ee7ba5cd0bf1fa`.

## NEW work in this invocation (4 independently scoped packages)

1. **Memory/Planner cross-store epoch-vector denial:** `src/ark/disconnected_epoch_vector.py`; reject reflected same-type result authority on capture, progress review, disclosure, dispatch, trusted time and custody. Source `8577529209502337d875b4aae000786c5af4ceb1`, test `e3bc7f39ba83c3c72971e5cd716563a37a8bf332` (11 new cases). Old exact-type diagnostic restored after CI detection via `8e9fcccf5112617bf49ad6b6547ca5564d81dbb8`.
2. **Privacy Context membership:** `src/ark/offline_context_membership_guard.py`; reflectively forged consent/retention/export/time authorization is rejected, unchanged no-content decision. Source `837ebd5c98857fc71960ac783a9043027d8f1037`, test `c96d92f6b63dc6b7336603811325dd5bced58c63` (5 cases).
3. **Read-only SQLite startup metadata seal:** `src/ark/disconnected_sqlite_schema_probe.py`; capture and compare require non-authorizing exact seal descriptors, not merely matching hashes. Source `b7f710f2679ed9730b0203aaf33e49cd1b534d44`, test `a77c6111f8e17c592284c2fa761c36b98065d23c` (11 cases).
4. **V3 local identity inventory:** `src/ark/learning/identity.py`; bounded local snapshot enumeration before sorting, relative path UTF-8 limits; no network/weight creation. Source `8e73a863c9be86f9b5d6516f8dea611ce29996d2`, test `f86f7fc63d996a9b8d128cf89bbe355e697e72d1` (5 cases). Ruff I001 blank-line regression corrected via `ebc83999d83fb108db08be67fea0ece178523f90`.

**Total: 12 new pytest functions, 32 expanded cases.** Tests are not counted as passing until the exact final source HEAD completes the GitHub Actions matrix.

## CI and tests — strict exact-source evidence

- **Previous PR #8 Run493 source** `b3a9c941ee80c768ed8e9db0a69d4195c18dae7d`: run [#1771 / 41161548147](https://github.com/Iam-2squared/ark-ai/actions/runs/41161548147), **6/6 GREEN** verified per job.
- **Earlier Run494 PR #8 epoch source/test:** [41165494597](https://github.com/Iam-2squared/ark-ai/actions/runs/41165494597), **FAIL** (Ubuntu 3.12: 5,165 pass, one failure on old `exact vector` diagnostic). Existing test retained, source repaired.
- **PR #8 final Run494 source/test HEAD** `8e9fcccf5112617bf49ad6b6547ca5564d81dbb8`: [41165783405](https://github.com/Iam-2squared/ark-ai/actions/runs/41165783405), **6 matrix jobs QUEUED at last check**, not GREEN. Later documentation/checkpoint-only commits do not prove a new source revision.
- **Previous PR #5 Run493 source** `7bd2ad6450c3a887351705f11054313de49c809c`: run [#1767 / 41161362307](https://github.com/Iam-2squared/ark-ai/actions/runs/41161362307), **6/6 GREEN**.
- **Earlier Run494 PR #5 source/test** [41165540546](https://github.com/Iam-2squared/ark-ai/actions/runs/41165540546): **FAIL 6/6 jobs** from Ruff I001 spacing; fixed without weakening tests.
- **PR #5 final Run494 source/test HEAD** `ebc83999d83fb108db08be67fea0ece178523f90`: [41165719631](https://github.com/Iam-2squared/ark-ai/actions/runs/41165719631), **1/6 GREEN, one running, four queued** at last check; not full GREEN.
- Independent local full pytest/Ruff: **NOT VERIFIED** (direct GitHub network DNS unavailable). No duplicate manual workflow dispatch.

## Frozen and authorization boundaries (unchanged)

- Memory v1 contract `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c`; Agency v1 contract `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`.
- Frozen V3 `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` and companion hash blob `176154514bd6be22685ca0555bc682c3bd8d45dc`, freshly confirmed unchanged. Preserve V1/V2/Local UI/Launcher evidence, V2 final suite, Experiment 001 and all contamination/provenance/regression/reproducibility gates.
- No external/paid GPU, paid APIs, billable services, paid compute, credentials/secrets/account connections, real Candidate/adapters/weights, protected V2 suite, Candidate promotion, real Tool execution, user-consent action, destructive operations, main merge or hardware action.
- SQLite hashes and local snapshots are not independent writer attestation, genuine cross-database atomic snapshots, trusted clocks, human authorizations or exactly-once real-world outcomes. UNKNOWN/RUNNING WRITE remains quarantined. V3 remains Draft and awaits authentic identities, human dataset review, cost cap and explicit gates.

## Next plan / 今後の方針

1. Confirm exact-head six-job CI for PR #8 `8e9fcc...` and PR #5 `ebc839...`. If failures occur, inspect logs, repair only affected semantics through the normal permitted path, and perform independent work while CI runs.
2. Advance Memory CAS, event history, independent coherent-state checks; Planner registry-bound identities, terminal propagation and manual UNKNOWN WRITE recovery; trusted-clock audit-before-action and occurrence/replay protection.
3. Extend Scheduler durable replay fencing, Personal Context revocation/expiry/consent veto and offline Observation fixtures, testing lower-level gates before integration.
4. Continue V3 local identity, manifest/provenance, reproducibility and approval guards, without paid compute, protected final evaluation, Candidate promotion or main merge.

---

**Previous intact historical checkpoint:** [Run493 `e3a509eea4e3c67ec175399b402932b3edd0cdaa`](https://github.com/Iam-2squared/ark-ai/blob/e3a509eea4e3c67ec175399b402932b3edd0cdaa/docs/PROJECT_STATUS.md). Previous Run493 technical report and archived Run487–492 evidence remain in GitHub history and `docs/history/`; none of the frozen contracts or old evidence files were rewritten.
