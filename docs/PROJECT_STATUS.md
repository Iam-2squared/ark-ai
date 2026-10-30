# ARK AI — Canonical Project Status

**LATEST — 2026-10-31 / Run490: read-only durable restarts across four local stores, V3 lineage hash source custody.**

**Saved at:** **2026-10-31T08:52:07.917+09:00 Asia/Tokyo/JST**, local wall-clock observed immediately before requesting this normal GitHub Contents update. This clock is **not authenticated trusted time**.

**Overall ARK/JARVIS completion: NOT_PASSED.** These are five reversible, disconnected, free-only source/test work packages, **not** an integrated JARVIS, authenticated durable audit, proof of user consent, real-world exactly-once execution, automatic WRITE replay, Candidate promotion, protected V2 final evaluation, or a gate to merge.

## Canonical latest work basis / saved branches / PRs

- **JARVIS foundations** [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), `research/jarvis-foundations`, OPEN/DRAFT/UNMERGED. **Initial Run490 work-basis HEAD:** `9b66f8187d71070bafbace089dacd6e699fc11c6` (Run489 checkpoint). **Final Run490 source/test HEAD:** `2df2fb7cc48c3cba559150a5b75846f5e4de56ec`. **Technical-evidence final HEAD:** `0443d68dc6b9bacea9167639b966decf67340cd4` (contains source/test changes and [Run490 technical report](JARVIS_READONLY_RESTART_LINEAGE_CUSTODY_RUN490.md)). **Checkpoint-write-basis HEAD:** `0443d68dc6b9bacea9167639b966decf67340cd4`.
- **Separate free-only V3** [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), `research/v3-learning-evaluation`, OPEN/DRAFT/UNMERGED. **Initial work-basis HEAD:** `b754608f41e9848ed7c8755aa46608d1af056910`. **Run490 final source/test HEAD:** `7cebbbbd3e0915028a1aa447b0baf7511df8a49e`.
- **Checkpoint-result HEAD:** cannot truthfully be embedded in its own pre-commit file. The normal GitHub Contents update's returned commit SHA is the checkpoint-result HEAD; read it after saving and confirm the actual branch HEAD. Do not confuse it with the write-basis SHA.
- **Main** last verified `7a843f17eb96ed13d66f23b58b06406b3002e405`. No merge or candidate promotion was performed. External concurrent branch changes must be checked again before later writes.

## NEW Run490 work — five packages / 18 new pytest functions

1. **Scheduler read-only existing due ledger (3 tests).** `src/ark/agency/disconnected_due_reservation.py` blob `e2f9bb2d77e44ea649c270653c31eb60bb9e9a60`; `tests/test_due_restart_read_only_run490.py` blob `ad9f7ca8b1a39b432392877457ad327dc46cdc02`. Existing-only due reservations use SQLite URI `mode=ro` with `BEGIN`, no write-intent bootstrap; synthetic creation remains a separate `rwc`/write path. Assertions include an already-RESERVED independent writer.
2. **Memory retained witness existing ledger (3 tests).** `src/ark/memory/disconnected_witness_ledger.py` blob `10d5d9aa9ceead2401035800293ec568a0695b55`; `tests/test_memory_witness_restart_readonly_run490.py` blob `c7a4b8566790faeaed8fd0b4584d29cb32abbeca`. Existing SQLite history opens read-only; explicit new-store creation and CAS mutation remain write-bound.
3. **Planner durable WRITE-slot existing ledger (3 tests).** `src/ark/agency/disconnected_write_slot_ledger.py` blob `81d8931678bcc606605e27ed616057894495f2e6`; `tests/test_write_slot_restart_readonly_run490.py` blob `08c6ebec54b5540953afc2926634f39b79d7e747`. Existing reservation review no longer requests a RESERVED writer lock. UNKNOWN/RUNNING WRITE remains quarantined; no automatic replay.
4. **V3 artifact SHA-256 filesystem custody (6 tests).** `src/ark/learning/lineage.py` blob `deec6301aa2fe03b95b875b5d7aebe15f90782c0`; `tests/v3/test_lineage_file_custody_run490.py` blob `51989b40c600e47dc167722e55cc3473985e0e77`. Local hash inputs reject non-exact carriers, parent traversal, symlinked ancestors and multi-link files; compare on-path `lstat` and opened-handle `fstat` epochs before/during/after reading. Checks are not OS tamper-proofing.
5. **Personal Context replay existing ledger (3 tests).** `src/ark/personal_context_replay_ledger.py` blob `c00ae09c2493828e472d8055a6d3e0139900fe20`; `tests/test_context_replay_restart_readonly_run490.py` blob `a79517c4cb3068da0a46c5e2904b74709caa2b83`. Existing replay history only uses SQLite read transactions. Creation and synthetic CAS request reservations remain explicit writes; hashed identifiers still carry linkability risk.

All five packages are testable on standard non-GPU Python CI. No source changes to frozen evidence/contracts were made intentionally. None of these results independently authenticates a ledger writer, clock, user or external effect.

## CI/tests evidence — exact trigger SHA, not optimistic PASS

- **Prior exact source GREEN:** PR #8 Run489 source `af8c5aef6bc6be1b338f2e6dff34e3575d135970`, [#1721 / 41140289600](https://github.com/Iam-2squared/ark-ai/actions/runs/41140289600), **all 6 Linux/Windows jobs GREEN**. PR #5 prior source `b754608f41e9848ed7c8755aa46608d1af056910`, [#1722 / 41140350170](https://github.com/Iam-2squared/ark-ai/actions/runs/41140350170), **all 6 GREEN**. These are older HEADs.
- **V3 intermediate FAIL / fixed:** #1728 / `41146400976` and [#1729 / 41146424014](https://github.com/Iam-2squared/ark-ai/actions/runs/41146424014) failed. Ubuntu 3.12 #1729: Ruff GREEN, 625 pytest passed / 1 failed due to changed `non-symlink file` error text. The normal GitHub Contents update restored the existing missing/non-file contract, preserving new integrity checks. **Final V3 source/test** `7cebbbbd3e0915028a1aa447b0baf7511df8a49e`, [#1734 / 41146607177 **QUEUED**](https://github.com/Iam-2squared/ark-ai/actions/runs/41146607177); no final 6/6 GREEN claim unless that exact run completes successfully.
- **JARVIS final source/test** `2df2fb7cc48c3cba559150a5b75846f5e4de56ec`, [#1737 / 41146764863 **QUEUED**](https://github.com/Iam-2squared/ark-ai/actions/runs/41146764863); intermediate #1733 / `41146566038` and docs #1738 / `41146794128` are separate code/evidence HEADs. No latest-head 6/6 GREEN claim yet.
- Independent local full `pytest` / `ruff`: **NOT VERIFIED**; local `git ls-remote https://github.com/Iam-2squared/ark-ai.git HEAD` failed host DNS resolution this invocation. GitHub connector reads and GitHub Actions are different evidence paths; do not claim a local test.
- Public repository visibility verified `public`; ordinary standard GitHub CI only, with **no** manual duplicate rerun, paid GPU, paid API or external training initiated.

## Frozen evidence, limits, outstanding approval gates

- Frozen Memory v1 contract `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c` and Agency contract `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9` were verified unchanged. V1/V2/Local UI/Launcher and protected V2 final suite/scorer, V3 Contract 1, provenance/contamination/regression/reproducibility boundaries were not intentionally modified; this was not an exhaustive fresh audit.
- No paid compute/services, new credentials/accounts, real Candidate adapter or weight generation, external ToolBackend, actual audio/mic/OS effects, actual notifications, protected V2 evaluation opening, frozen-contract change, destructive operation, main merge or automatic promotion.
- SQLite hash chains and local snapshots cannot independently prove an authentic writer, full-store rollback without an externally retained tip, cryptographically trusted time, consent/erasure, cross-SQLite atomicity, source-path security against all OS races or exactly-once external side effects. Fail closed on uncertainty; never automatically retry unknown WRITEs.
- PR #5 remains Draft/unmerged under its controlling pre-paid-compute approvals, including unresolved real model/tokenizer byte identities, actual human-reviewed data, runtime and GPU identities, authorized spending and billing caps, protected final-evaluation gate.

## Next plan / 今後の方針

1. **Validate exact final code HEADs:** Check [PR #8 source #1737](https://github.com/Iam-2squared/ark-ai/actions/runs/41146764863) and [PR #5 source #1734](https://github.com/Iam-2squared/ark-ai/actions/runs/41146607177) across all six jobs; for FAIL, inspect failing job logs, correct the minimum without reducing safeguards, and verify the resulting new SHA. Do not dispatch equivalent duplicate runs.
2. **Memory/Planner:** Strengthen independent append-CAS, coherent snapshots, retained rollback proof limits, UNKNOWN WRITE manual reconciliation, restart-safe authorization/occurrence barriers and exact registry-bound permissions.
3. **Trusted Clock / audit-before-action:** Bind disconnected synthetic clock evidence to durable pre-action audit fixtures without implying hardware trust, human consent or external execution.
4. **Personal Context / Scheduler / Observation:** Consent/revocation/expiry lifecycle, proactive idempotency and recovery, startup readiness, mock observation fixture lineage, privacy isolation; only connect after exact-head GREEN lower-level invariants.
5. **V3 (free-only):** Verify approval/identity/path/code/runtime reproducibility guards without training or spending. No real Candidate, promotion or protected V2 gate opening without explicit user authorization.

---

**Previous canonical checkpoint:** [Run489 at immutable Git HEAD `9b66f8187d71070bafbace089dacd6e699fc11c6`](https://github.com/Iam-2squared/ark-ai/blob/9b66f8187d71070bafbace089dacd6e699fc11c6/docs/PROJECT_STATUS.md). Earlier archived [Run488](history/PROJECT_STATUS_RUN488.md) and [through Run487](history/PROJECT_STATUS_THROUGH_RUN487.md) remain. **Technical evidence**: [Run490 report](JARVIS_READONLY_RESTART_LINEAGE_CUSTODY_RUN490.md). All preceding Git commits/evidence remain reachable; this file is the latest checkpoint.
