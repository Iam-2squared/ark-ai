# Run461 — Detached epoch continuity, pinned POSIX reads, WRITE alias fencing

Status: **source/test saved; focused local validation only; exact-head CI NOT GREEN**.
Work-basis HEAD: `bb40a28f91f3a9eada030a782317598995e12d01` (Run460 checkpoint).
Final source/test HEAD: `b31ba86f4ec4be53b6c7a62879662b3ab9a5c68d`.
Branch: `research/jarvis-foundations`, Draft PR #8, **not merged**.

## Four meaningful independent work packages

1. **Pure store-epoch continuity** — `src/ark/disconnected_epoch_vector.py`
   Git Blob `02084f2175dd9526dbbcad594fd261121f6b478a`;
   `tests/test_disconnected_epoch_vector_run461.py`
   `e284e86d4c76b66d44aadc6b4f4c3294587c36cb`.
   Rejects untrusted out-of-order/duplicated store identities, malformed
   exact types/hashes, schema/incarnation changes, generation/event/clock
   regression, same-generation drift and advanced generation without advanced
   event/state witnesses. At most 16 synthetic stores. It does **NOT**
   acquire a coherent snapshot from SQLite, verify external custody, prove
   trusted time, grant disclosure or authorize dispatch. It cannot repair
   a rolled-back retained baseline.

2. **POSIX descriptor-pinned synthetic file seal** —
   `src/ark/disconnected_posix_handle_seal.py` Git Blob
   `0e6f5d7de2fc8f195dc66bdd7dd0b36f524b3a16`;
   `tests/test_disconnected_posix_handle_seal_run461.py`
   `62f4f0ed90af26698c150486d258009de91ee074`.
   Read-only maximum 8 MiB, exact absolute Path, individually anchored
   O_DIRECTORY/O_NOFOLLOW parent descriptors, final O_NOFOLLOW file open,
   regular-file/hardlink checks, pre/post fstat and directory-relative path
   revalidation, double read and metadata/content digest. Synthetic file,
   symlink ancestor, grandparent, hardlink, file replacement and read-time
   parent/source swap fixtures included. **Fails closed on Windows or any OS
   without the requisite POSIX dir_fd/NOFOLLOW primitives.** This detects
   races observed during read, but cannot guarantee the path remains pinned
   forever; inode reuse, kernel/filesystem trust, concurrent post-check swaps
   and authenticated origin remain outside its proof.

3. **WRITE occurrence reservation alias fencing** — amended existing
   `src/ark/agency/disconnected_write_recovery_fence.py` Git Blob
   `a24bd3de6863c5951838da03fe1a4b2113e39d2d`, plus
   `tests/test_disconnected_write_reservation_uniqueness_run461.py`
   `3d8950c9d96e20d300e0e43530ae91b0c3f0d453`.
   Previously distinct WRITE steps could claim the same valid `slot_...`
   reservation. Now rejects duplicate reservation identities across all
   WRITE states, even if each step would otherwise remain blocked. Allows
   distinct slots and preserves READ mock-only/no-authorization semantics.

4. **Source-grounded observation CI regression correction** —
   `tests/test_observation_window_review_run361.py` Git Blob
   `7b3a2d895bee49320b05c0daeb7a2a330cfc4eb2`.
   Earlier test had assumed a reflected-mutated `content_sha256` could be
   restored using a newly allocated string with equal characters; the
   current production guard intentionally pins the *original field carrier*
   by identity, so it must continue rejecting that new string. Regression
   now explicitly rejects equal-valued replacement and only accepts
   restoration of the saved original object. This is a stricter test,
   **not a weakened gate or production-authority change**.
   It was source-inspected, not run locally against the full observation
   package in this invocation.

## Validation and CI evidence, with limits

- Isolated Python 3.13.5 + pytest 9.0.2 on Linux/POSIX: **63 PASSED**,
  including all three new/changed standalone packages, plus Python
  `compileall` PASS. Changed/new local source/tests have no >100-column
  lines. No local Ruff or complete-repository pytest was available because
  `github.com` DNS resolution failed from the container; no Windows,
  Python 3.11/3.12 or all-six matrix GREEN is asserted.
- Independent seeded (uncommitted) stress probes: **2,000** synthetic
  epoch transitions (1,714 intentionally valid, 286 intentionally
  rejected); **300/300** changed-byte retained file reviews rejected.
  These are NOT extra committed pytest cases or system-wide evidence.
- Readback matched the **six exact source/test Git Blob SHAs** listed
  above. The observation correction was additionally read back by SHA.
- Previous #1244 / `40237313817`: Ubuntu 3.12/3.13 pytest
  **FAIL**, two older privacy test assertions; Windows jobs now
  **CANCELLED** (not GREEN), following prior in-progress reports.
- Historical #1251 / `40246006387`: Ubuntu 3.11 shows three
  old-head pytest failures, the two old privacy expectation errors plus
  the observation carrier-restoration expectation corrected in this run.
  Windows three jobs remained **IN PROGRESS** at inspection; no final
  modern-head verdict is inferred from this old-head result.
- GitHub Actions backlog at inspection: **158 QUEUED**. New source/test
  runs #1404–#1409 were **QUEUED**. Evidence/checkpoint exact-head
  runs must be separately inspected after saving; do not mark GREEN
  based on successful GitHub Contents writes.
- No dispatch, external Tool, account connection, real user data, live
  microphone/camera, paid API/GPU, Candidate training, protected V2
  evaluation opening, approval, promotion, frozen-contract change or merge.

## Future dependency gates

Do not integrate these detached diagnostics with Memory, Planner, ToolRegistry,
PermissionGate or actual files until the relevant saved source/test HEAD is
GREEN across required CI, all original corpus regressions pass, coherent
cross-store custody has independent trusted witnesses, and the existing
authorization review gates are explicitly satisfied. On Windows, implement
an independently reviewed handle/reparse-point probe, not a silent
fallback to an unsafe pathname open.

Priority: diagnose queued current-head CI when it runs; preserve untouched
frozen V1/V2/Local UI/Launcher and V3 Contract 1; continue Memory
CAS/event/snapshot coherence, Planner restart nonreplay, trusted-clock
audit-before-action and privacy-scope enforcement in isolated safe lanes.
