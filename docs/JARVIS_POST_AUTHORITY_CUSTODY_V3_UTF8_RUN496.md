# ARK AI Run496 — Post-authority result custody and V3 UTF-8 identity

Scope: isolated, free-only, detached local groundwork. **No JARVIS PASS or real Tool authorization.** No paid/API/GPU training, Candidate generation, frozen V2 evaluation, promotion, secrets, sensor capture, or main merge.

## Exact work basis

- PR #8 initial checkpoint HEAD: `e5cf929d9eb16ac6bcd3ac97e4414124000277e1`; final **source/test** HEAD before this report: `3730e1ce0bd896c85ab9c7af3d78309b565bb0f9`.
- PR #5 initial source HEAD: `c42521c16b7d52cd39c4c2aff413ab001c321b29`; final **source/test** HEAD: `1a9abe3fe57c01ab2f03d8f6ad717543d30fc94f`.
- Both PRs remain Draft, unmerged, and independent. Any subsequent report or checkpoint commit has a different HEAD, and does not retroactively validate the source/test HEAD.

## Five independent packages and negative tests

| Package | Source SHA | Added test file | New pytest cases | Invariant |
|---|---|---|---:|---|
| Synthetic Scheduler preview | `dec116957c538d223a003a45fb29eca2e1923c5d` | `tests/test_schedule_preview_late_authority_run496.py` | 5 | After evaluating denied consent/clock/replay authorities, recheck policy/cursor/result; mutated due labels never enable execution |
| Local Personal Context request binding | `e144e478156d68501299b3c8046df62bf1528275` | `tests/test_context_binding_late_authority_run496.py` | 3 | A False-returning result getter cannot retarget a source preview or binding receipt |
| Synthetic RIFF/WAV inspection | `6ce4acafd475576cf7932c1a112bb48039a98dab` | `tests/test_offline_wav_post_authority_run496.py` | 5 | Revalidate metadata fields after the final denied disclosure getter; no microphone, ASR, or audio export |
| Disconnected Memory delta | `d2e100057dadc997319f8d44268f325332a4dd4b` | `tests/test_offline_memory_delta_authority_run496.py` | 8 | Exact receipt class/fields and non-authoritative source, erasure, atomicity, and Tool flags; recheck source/result after callbacks |
| V3 Candidate lineage identity (validation-only) | `8172f94141445f94350fabd6d3abc83c118f8793` | `tests/test_v3_artifact_identity_utf8_run496.py` | 9 | Reject DEL, malformed UTF-8 surrogate, and >4,096 UTF-8-byte fields, without loading weights |

**Total:** 5 packages, 13 new pytest functions / 30 expanded cases. The WAV and V3 fixture literals were corrected in ordinary test-file updates before final CI; no test condition was weakened.

## CI provenance (not a PASS declaration)

- Previous PR #8 source HEAD `fb8843bd331fae3f122b878be0a97aaa02c1a575`: [#1793](https://github.com/Iam-2squared/ark-ai/actions/runs/41170158527), six matrix jobs GREEN.
- Previous PR #8 checkpoint `e5cf929d9eb16ac6bcd3ac97e4414124000277e1`: [#1795](https://github.com/Iam-2squared/ark-ai/actions/runs/41170295130), six matrix jobs GREEN.
- Previous PR #5 source HEAD `c42521c16b7d52cd39c4c2aff413ab001c321b29`: [#1787](https://github.com/Iam-2squared/ark-ai/actions/runs/41169960149), six matrix jobs GREEN.
- This run's final **PR #8** source/test `3730e1ce...`: [#1807](https://github.com/Iam-2squared/ark-ai/actions/runs/41173686694), QUEUED at last listing.
- This run's final **PR #5** source/test `1a9abe3...`: [#1805](https://github.com/Iam-2squared/ark-ai/actions/runs/41173650595), QUEUED at last listing.
- Independent local pytest/Ruff: NOT VERIFIED because direct container-to-GitHub DNS resolution failed. GitHub CI is distinct from this independent verification; do not extrapolate prior GREEN to new source.

## Frozen custody and limitations

- Frozen Memory v1 contract blob: `b6e93821ecd69270a7634aceb20775dc36e9953c`.
- Frozen Agency v1 contract blob: `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`.
- Frozen V3 contract and accompanying hash-file blobs: `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`, `176154514bd6be22685ca0555bc682c3bd8d45dc`. All four were re-read unchanged.
- Local dataclass identity/hashes are untrusted evidence unless independently authenticated. No durable multi-store atomicity, truthful consent, trusted clock, authentic sensor provenance, deletion assurance, or external effect is asserted.
- Keep UNKNOWN/RUNNING WRITE quarantined without autonomous retry. PR #5 remains blocked on exact model/tool bytes, genuine human dataset approvals, runtime identities, explicit compute/cost authorization, and protected evaluation gate.

## Next plan / 今後の方針

1. Confirm PR #8 #1807 and PR #5 #1805 **at their exact source/test HEADs**; isolate any real CI failures without changing frozen contracts.
2. Strengthen Memory CAS, expiry/event witnesses and coherent snapshot proofs; independently retained custody still unresolved.
3. Advance manual UNKNOWN WRITE recovery, immutable ToolRegistry binding, trusted-clock audit-before-action and occurrence/replay protection (disconnected first).
4. Improve privacy revocation/retention veto, durable Scheduler due reservations and synthetic observation fixture integrity; do not connect to live sensors without proven authorization.
5. V3 only free local provenance/identity/preflight checks. No GPU, real Candidate, V2 final opening, or automatic promotion.
