# ARK AI — Canonical Project Status

**LATEST — 2026-10-31 / Run488: Context post-recheck integrity, synthetic clock authority guard, V3 exact-type identity, Memory CI correction and historical status archive**

**Saved at:** **2026-10-31T06:53:55+09:00 Asia/Tokyo/JST** (local wall-clock observation immediately before composition; **NOT** independently authenticated time, GitHub commit time, user approval or consent).

**Overall ARK/JARVIS status: NOT_PASSED.** Locally tested/disconnected components and preliminary V3 safeguards are not an integrated JARVIS, physical-PC proof, real-world Tool authorization, exactly-once external effects, trusted-clock provenance, independently authenticated custody, consent, Candidate training, protected V2 completion, or approval to merge.

## Canonical branches, work basis and checkpoint identities

- **Canonical:** `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) — **OPEN, DRAFT, UNMERGED** at last read.
- **Separate V3:** `research/v3-learning-evaluation` / [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) — **OPEN, DRAFT, UNMERGED**; preserve its controlling human authorization gate.
- **Initial invocation work-basis HEADs:** PR #8 `fe9c0e8e031ade566696acfb8ad98173f612a809`; PR #5 `afb462ed85b7ca7ce0f9c75b4efd641297fa0ddf`.
- **Final source/test HEADs (BEFORE documentation/checkpoint):** PR #8 `ef309357ac6a9b93a9cb8df6f00ee70e677d6619`; PR #5 `79376f3ce777dc877c63ce58785153e493b9b7fc`.
- **Checkpoint-write-basis HEAD:** PR #8 `b7e15d09b4a2346debbf55c15b7f0f3b6a2403cc` (**PRE-checkpoint**, includes archive and Run488 technical evidence). **Checkpoint-result HEAD:** cannot be self-certified in the file containing that commit; obtain the actual ordinary GitHub Contents update commit SHA and independently re-read branch HEAD after commit.
- **Main** last checked `7a843f17eb96ed13d66f23b58b06406b3002e405`, unchanged; neither PR merged.

## NEW in this invocation (4 source/test work packages, 21 new test cases)

1. **Memory failing CI repair (0 added tests):** The Run487 quoted-bracket case expected an internal exception message while `_decoded` correctly wrapped it as an invalid persisted epoch. Change only the test's expected rejection message; preserve 64-depth protection and the test itself. `tests/test_memory_witness_json_depth_run487.py` blob `c940b8da823e7a981f857efc6c0756960e9a99bf`; memory source unchanged.
2. **Personal Context final result epoch (6 new cases):** `src/ark/personal_context_replay_recovery.py` blob `6692936d64d476be42cd0d196d35af1a12893d05`; `tests/test_context_replay_result_final_epoch_run488.py` blob `6d9c1bde40b959005a5456f30ba639e6237787b2`. Re-validate synthetic report and all inert authority flags **after** the final independent read-only SQLite tip callback; reject late reflective mutation. No actual consent, erasure, disclosure or action authority.
3. **Synthetic clock authority (7 new cases):** `src/ark/agency/synthetic_clock_sequence_review.py` blob `84c049e48b9ad807c0d967c8235de6aa7dad07b9`; `tests/test_synthetic_clock_authority_epoch_run488.py` blob `83226144e0a7539e07facd591b200552b777664f`. Exact witness, constructor and generator completion reviews reject spoofed trusted-clock, dispatch or replay authority; supplied timestamps are still unauthenticated.
4. **V3 identifier carrier exact-types (8 new cases):** PR #5 `src/ark/learning/identity.py` blob `5b09e1f2615374ceb36d3f7df2b05949d74a3548`; `tests/v3/test_exact_local_identity_inputs_run488.py` blob `7081f69286812e1c3729032caf62ea9d921a731b`. Reject subclass/non-string HF model ID/revision and export tool git revision/role **before** local filesystem hashing. No real GPU/train/Candidate.
5. **Historical status retention:** The complete prior 932,553-character `docs/PROJECT_STATUS.md` was archived **verbatim** as [docs/history/PROJECT_STATUS_THROUGH_RUN487.md](history/PROJECT_STATUS_THROUGH_RUN487.md), blob `21ea22807b38c1947edf252878b00d1dc2d20903`, archive commit `a3e23bd6df8a6c5fb46fd58e915cd29bccf1ee66`. This avoids the 1MiB GitHub Contents size boundary while preserving all Run487 and earlier evidence. The archived document remains historical; this file is the sole canonical **latest** checkpoint. Never discard or silently rewrite frozen evidence.

**Run488 technical evidence:** [JARVIS_CONTEXT_CLOCK_MEMORY_V3_TYPE_RUN488.md](JARVIS_CONTEXT_CLOCK_MEMORY_V3_TYPE_RUN488.md), saved on PR #8 `b7e15d09b4a2346debbf55c15b7f0f3b6a2403cc`. All eight new/edited source/test blob identities and the archive blob were independently re-read by normal GitHub file reads.

## Exact-head tests / CI evidence (last observed statuses, not forecasts)

- Run487 **PR #8** source/test #1699 / `41125283519`, technical-document #1702 / `41125586981`, checkpoint #1703 / `41125716889`: **FAIL** in all six jobs because one existing quoted-bracket test expected the wrong wrapper exception message. The exact failed assertion was retained and corrected; no protected source contract was weakened.
- Run488 Memory correction at PR #8 `ebe9c3be95947dad56855fb5708bcae6237d1ea5`: #1704 / `41133741689` **IN PROGRESS** on last observed jobs, Ubuntu 3/3 and Windows 3.12 GREEN, Windows 3.11/3.13 running. This is an earlier source head, not final.
- Run488 **PR #8 final source/test** `ef309357ac6a9b93a9cb8df6f00ee70e677d6619`: #1710 / `41134136157` **IN PROGRESS** at last query; one Ubuntu job queued and five running. Intermediate #1707–#1709 not substituted for the final-source result. Technical doc #1712 / `41134319597` **QUEUED**; the present checkpoint produces its own separate CI. **Do NOT declare PR #8 latest source six-job GREEN yet.**
- Run488 **PR #5 exact final source/test** `79376f3ce777dc877c63ce58785153e493b9b7fc`: #1706 / `41133950984` **GREEN, all six** (Ubuntu/Windows Python 3.11, 3.12, 3.13 each SUCCESS). Source-only #1705 / `41133846144` also SUCCESS. This does not authorize training.
- Independent local complete pytest/Ruff **NOT VERIFIED**. A local `git ls-remote` failed with DNS resolution error for `github.com`; normal GitHub connector file reads and Actions CI provide separately identified evidence only.

## Frozen contract/evaluation + authorization boundaries

- Independently re-read unchanged: Memory SQLite v1 `src/ark/memory/sqlite_store.py` blob `0aba6392b39563df520aa8b378d0b313f0cc0a0d`; Memory v1 contract `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c`; Agency contract `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`. No intentional V3 Contract 1, V1/V2/Local UI/Launcher evidence, protected V2 final suite/scorer, contamination/provenance/regression/reproducibility gate change.
- No paid API/service, subscription, external/GPU compute, new account/credential, physical-PC action, actual ToolBackend/sensor, destructive operation, full Candidate training, protected V2 final evaluation opening, automatic Candidate promotion, or approval-requiring main merge. PR #5 and #8 remain Draft/unmerged.
- A local chain hash, alleged witness, synthetic approval, mock executor, untrusted timestamp or same-machine audit cannot prove independent custody, legitimate consent, protected evaluation permission, real-world effect completion or cross-SQLite atomicity. Missing signed/approved source and cost/device/data gates remain hard stops. UNKNOWN WRITE is never automatically retried.

## Next plan / 今後の方針 — priority order

1. Confirm #1710 **all six** jobs against exact final PR #8 source SHA; if FAIL, inspect logs and fix narrow behavior through normal GitHub Contents API only, retain tests. Check documentation/checkpoint CI without duplicate reruns.
2. Advance Memory CAS, independent retained-history/rollback witness semantics and coherent SQLite snapshot validation; do not claim external provenance.
3. Improve Planner UNKNOWN WRITE manual reconciliation, immutable ToolRegistry/exact PermissionGate, trusted clock audit-before-action, durable occurrence/replay safety; keep executor disconnected.
4. Advance Context consent/revocation/retention and Scheduler duplicate prevention, Observation fixture contracts and startup readiness with zero external effects.
5. Continue V3 free-only identity, path, runtime, approval packet and reproducibility checks. **No real model Candidate, external GPU/spend, protected V2 opening, promotion or main merge without the separate explicit gate.**

---

**Historical/frozen full checkpoint:** [Run487 and earlier archive](history/PROJECT_STATUS_THROUGH_RUN487.md) (archive blob `21ea22807b38c1947edf252878b00d1dc2d20903`; preserving 6,649 prior lines).
