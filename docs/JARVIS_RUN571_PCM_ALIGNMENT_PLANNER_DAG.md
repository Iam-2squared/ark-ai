# ARK AI — Run571 offline PCM alignment and Planner DAG checks

Scope: reversible **free-only / disconnected** JARVIS groundwork. This note
records source/test additions, not a claim that a physical PC, microphone,
trusted clock, ASR, user consent or external execution was tested.

## Package A: detached PCM activity verifier integrity

- `src/ark/offline_pcm_activity_regions.py` now pins the import-time detector
  function and exact activity DTO classes; detached verification checks these
  before comparing any report and again after recomputation. It rejects a
  replacement detector even when that detector returns an equal-looking
  report or a function that would mutate a report during callback.
- `tests/test_offline_pcm_activity_verifier_pin_run571.py` adds eight authored
  test cases: normal recheck; three original-dependency substitutions; three
  reflected summary mutations; one spoofed recomputed report.
- Inherited `tests/test_offline_pcm_activity_detached_verify_run500.py`
  test expectation was updated after inspecting the actual Ubuntu 3.12 CI log.
  Earlier error-string expectation `changed` no longer matched the strict
  early `original activity verifier replaced` rejection. New test asserts
  that the reflected mutation callback was **not** called; production checks
  were not weakened.

## Package B: disconnected PCM activity span ↔ transcript claim intersection

- New `src/ark/offline_activity_transcript_overlap.py` verifies the original
  PCM activity report against independently provided PCM bytes and checksum,
  and the original synthetic transcript binding against its retained
  fingerprint; then intersects region spans and transcript intervals on the
  sample-frame axis. Includes region count, span samples, overlapping and
  uncovered span samples, regions with overlap, ppm ratio and domain-separated
  SHA-256; never returns raw audio or transcript text.
- New `tests/test_offline_activity_transcript_overlap_run571.py`: eleven
  authored parameter-expanded cases for determinism, redaction, empty activity,
  bridged-silence interpretation, stale fingerprint, mismatched PCM,
  reflected report change, swapped verifier/transcript handler, replaced
  consent descriptor, altered frame count, changed analysis-window size.
- **Important semantic boundary:** activity regions include brief deliberately
  bridged silences; their overlap with claimed transcript spans is **not**
  the fraction of actual human speech correctly transcribed. Neither
  caller-supplied fingerprints nor local byte equality authenticate device
  origin, language, audio-to-text semantics or permission. The two original
  delegates and result-denial descriptors are import-pinned and rechecked.
  Independently retained witnesses remain a required separate authority
  boundary; this read-only tool does not grant access or perform ASR.

## Package C: Planner DAG independent oracle

- New `tests/test_planner_dag_metamorphic_run571.py` adds 41
  deterministic parameter-expanded tests with variable acyclic dependency
  shapes, independent ready-frontier calculation, permutation-insensitive
  topology/status digest, terminal FAILED/BLOCKED transitive descendant
  propagation, and cycle refusal. No frozen Planner contract or journal
  contract was changed.
- This is a regression test suite for existing Planner behavior, not new
  persistent recovery, ToolRegistry authorization, backend execution, or
  exactly-once action proof.

## CI, provenance and next gates

- Initial PCM verifier test HEAD `e2c87b51f0b9fe4419583c02876c19080ccb690a`
  [CI #41575059852](https://github.com/Iam-2squared/ark-ai/actions/runs/41575059852)
  exposed one inherited assertion expecting a late-stage failure string.
  Ubuntu 3.12: **7,361 passed / 1 skipped / 1 failed** on that earlier HEAD,
  from a logged regex mismatch; not an all-GREEN claim.
- Corrected inherited test commit `9446430c47e46040fcb6819c7022422786a77f58`
  started [CI #41575518286](https://github.com/Iam-2squared/ark-ai/actions/runs/41575518286).
  Other earlier source/test CI runs are not evidence for the newest HEAD.
  Verify all 6 Ubuntu/Windows Python 3.11–3.13 jobs on the
  final source/test+note+checkpoint HEAD before any exact-head GREEN claim.
- No manual duplicate dispatch, paid compute/API/GPU, real Candidate,
  protected V2 evaluation, contract edit, external tool/sensor action,
  identity fabrication, main merge or automatic promotion.
  PR #5 and #8 remain **Draft / unmerged**, overall
  **ARK/JARVIS/V3 = NOT_PASSED**.

Next: confirm CI and repair any actual failures using normal file writes;
then extend PCM-alignment nested report-carrier epochs and explicitly bound
the independent audio/transcript witness provenance. Independently advance
Planner durable FAILED/BLOCKED recovery and Memory COMMIT-uncertainty manual
reconciliation without changing frozen contracts.
