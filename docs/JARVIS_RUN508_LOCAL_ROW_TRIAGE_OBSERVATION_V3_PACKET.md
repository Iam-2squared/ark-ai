# ARK AI — Run508 isolated free-only integrity work

**Evidence prepared:** 2026-10-31T16:56:07.302Z UTC (workflow-visible wall clock, not trusted-time attestation). **Overall JARVIS and V3: NOT_PASSED.** All additions are reversible isolated local-only code/fixtures; no model execution or side effects.

## Exact work bases and branch custody

- PR #8 Draft/unmerged `research/jarvis-foundations`: initial HEAD `358dd1cc042ba9fb23ffb6c62b2f22af88a963e2`; final **source/test HEAD** `651d71307ef472c170ced7cbb175b191a4ea7799` before this evidence-only commit.
- PR #5 Draft/unmerged `research/v3-learning-evaluation`: initial HEAD `f8f6e2abfd914478466e5c260d9da95341684d13`; final **source/test HEAD** `9b5eb790aa8584bef898498383c9d98f4c24e477`.
- main `7a843f17eb96ed13d66f23b58b06406b3002e405`. No merge or changes to frozen contracts.
- Frozen Memory contract blob `b6e93821ecd69270a7634aceb20775dc36e9953c`, Agency contract `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`, V3 `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` unchanged.

## NEW isolated code/test packages

1. **Memory event-alignment complete row commitment.** `src/ark/memory/sqlite_event_alignment.py` blob `0097a299f22ce0597cbe3146bc366b89530b543e`, tests `tests/test_memory_alignment_full_row_digest_run508.py` blob `ac879876cf02ea99b3a4bba66e9791cddc14df3c`. In addition to identity/revision/content hash, the local digest now commits to canonical metadata SHA-256, created/updated timestamps and expiry. Five new pytest parameter expansions/cases. Changing metadata or expiry alone previously left the local alignment digest unchanged. This is still **not** signed provenance, irreversible erasure or cross-process custody.
2. **Detached UNKNOWN WRITE checklist checksum verification.** New `src/ark/agency/offline_write_triage_verify.py` blob `9c201aef9ba5a1b3c4a07d1a39e0ed992c7cd6c2`, tests `tests/test_offline_write_triage_verify_run508.py` blob `a473740a3ad98b65d5eb52bdba4652c9bd18fd82`. Checks exact packet/witness types, metadata bound, no duplicate steps/reservations, safe terminal/quarantine dispositions, SHA-256 binding to retained witness, and denial-only authority flags. 22 authored pytest parameter expansions/cases. Retained witness is caller controlled and not independently authenticated. **No ledger write, tool call, approval, external outcome or replay.**
3. **V3 review packet output custody.** `src/ark/learning/authorization.py` blob `d8557138737eb47b90af868b47ed9489747bb553`, tests `tests/v3/test_authorization_packet_output_epoch_run508.py` blob `c254842e6d5b81c428dc6cf45f62c6711684034e`. New files only through exact anchored absolute paths; pin local JSON tree around serialization, rejecting serializer callback changes before writing. Five authored pytest cases. This is **not** consent, paid-compute authorization, full training permission, verified HF identities, or protected evaluation opening.
4. **Observation lineage result post-denial epoch.** `src/ark/observation_lineage_review.py` blob `585d37c0b4f61379e8e152e50b643bb3bec2a97c`, tests `tests/test_observation_lineage_post_authority_epoch_run508.py` blob `f02912e59995b4a4241d6572da2d040a4b11f3b8`. Recheck fixture inputs and result after authority-property callbacks, rejecting false-returning getters that mutate witnesses or privacy inputs. Five authored cases. No camera/mic capture, media disclosure or dispatch.

**Total: four coherent work packages, 37 newly authored pytest cases.** This is an authored test count, not a claim that local pytest or Ruff executed. Repository checkout from the local container failed with GitHub DNS lookup error; source and test writes used only normal GitHub Contents API. No raw Git object/write bypass.

## CI evidence at source-test HEAD

- **PR #5 exact-head** run [41221755534](https://github.com/Iam-2squared/ark-ai/actions/runs/41221755534), `9b5eb790aa8584bef898498383c9d98f4c24e477`: individual 6/6 (Ubuntu/Windows × Python 3.11, 3.12, 3.13) **GREEN**, workflow SUCCESS.
- **PR #8 final source/test** run [41221892145](https://github.com/Iam-2squared/ark-ai/actions/runs/41221892145), `651d71307ef472c170ced7cbb175b191a4ea7799`: **IN PROGRESS / not yet 6/6 certified** at evidence preparation. Do not reuse predecessor GREEN as final-head proof. Evidence/checkpoint commits launch their own separate runs.
- Earlier PR #8 `358dd1cc042ba9fb23ffb6c62b2f22af88a963e2` run [41217528638](https://github.com/Iam-2squared/ark-ai/actions/runs/41217528638) was SUCCESS (predecessor). PR #8 intermediate source/test run [41221647072](https://github.com/Iam-2squared/ark-ai/actions/runs/41221647072) was 3/6 Ubuntu GREEN, Windows pending at last job check; not a final-head gate.
- Local independent pytest/Ruff **NOT VERIFIED**, no claimed hardware/model test.

## Safety boundaries and limits

No external GPU/paid service, real Candidate/adapter, protected V2 final evaluation, automatic Candidate promotion, forged reviewer approval, frozen-contract edits, secrets/new connection, real ToolBackend/OS dispatch, destructive operation, hardware action or main merge. PR #5 and PR #8 stay Draft/unmerged. A local digest and caller-retained packet cannot authenticate an adversarial writer or prove external effects. File path/serializer guards do not guarantee security against an adversarial operating system or concurrent directory rename. All V3 human, identity, cost, dataset and hardware gates remain closed.

## Next plan / 今後の方針

1. Verify exact-head PR #8 6-job result; repair only observed failures, preserving denials and original contracts. Also distinguish evidence/checkpoint CI from source-head CI.
2. Advance Memory coherent CAS/event snapshots with an **independently retained** external witness; avoid claiming provenance from local hashes.
3. Extend Planner persistent manual-only UNKNOWN WRITE outcome review and ToolRegistry-bound exact-type PermissionGate / trusted-clock audit-before-action, **without any real dispatch or replay**.
4. Continue Scheduler occurrence persistence, privacy consent/revocation, Observation disconnected fixtures and V3 free-only reproduction/identity guards; stop all paid, protected or irreversible lanes at their explicit gates.
