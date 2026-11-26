# ARK JARVIS disconnected safety / V3 local identity — Run488

**Status:** evidence for free-only, isolated Draft PRs. **Complete JARVIS: NOT_PASSED.** All effect, clock, consent, history provenance, training, Candidate and promotion authority remain absent. This record describes exact repository bytes and CI observed *at composition*, not certification of the final checkpoint HEAD.

## Work basis and immutable comparison

- Initial PR #8 HEAD: `fe9c0e8e031ade566696acfb8ad98173f612a809`; initial PR #5 HEAD: `afb462ed85b7ca7ce0f9c75b4efd641297fa0ddf`.
- PR #8 source/test HEAD before archival docs: `ef309357ac6a9b93a9cb8df6f00ee70e677d6619`.
- PR #8 historical archive HEAD: `a3e23bd6df8a6c5fb46fd58e915cd29bccf1ee66`.
- PR #5 final source/test HEAD: `79376f3ce777dc877c63ce58785153e493b9b7fc`.
- Main base was `7a843f17eb96ed13d66f23b58b06406b3002e405` when checked. Both PRs were Draft, open, unmerged.

## Coherent work packages and blob evidence

1. **Memory existing test correction (zero new test cases):** Earlier PR #8 CI #1699 (`41125283519`) and #1703 (`41125716889`) failed all six environments on one expectation in `tests/test_memory_witness_json_depth_run487.py`. Source `_decoded` intentionally wraps invalid epoch shape as `MemoryWitnessLedgerRejected("invalid persisted witness epoch")`; a quoted-bracket test incorrectly expected the internal, swallowed `"invalid witness epoch structure"` message. Only the expected error text changed, preserving the test's failure requirement and 64-level nesting gate. Corrected test blob `c940b8da823e7a981f857efc6c0756960e9a99bf`; source remained `src/ark/memory/disconnected_witness_ledger.py` blob `8133a2a85b42db9c8f9f418844ac8edba6242847`. Test/commit basis: `ebe9c3be95947dad56855fb5708bcae6237d1ea5`.
2. **Personal Context restart report result custody (six new pytest cases):** A mutable final SQLite callback could alter a frozen diagnostic report *after* the single result check. The source now checks exact inert result shape and no-dispatch/no-consent flags both before and after the final durable-tip recheck; it cannot grant access or prove revocation, independent custody or consent. `src/ark/personal_context_replay_recovery.py` blob `6692936d64d476be42cd0d196d35af1a12893d05`, `tests/test_context_replay_result_final_epoch_run488.py` blob `6d9c1bde40b959005a5456f30ba639e6237787b2`.
3. **Synthetic clock witness authority integrity (seven new pytest cases):** Require falsity of trusted-clock, dispatch and replay authority descriptors on retained, constructed, and generator-returned local timestamp witnesses. Even one synthetic monotonic sequence remains untrusted; no clock/system access occurs. `src/ark/agency/synthetic_clock_sequence_review.py` blob `84c049e48b9ad807c0d967c8235de6aa7dad07b9`, `tests/test_synthetic_clock_authority_epoch_run488.py` blob `83226144e0a7539e07facd591b200552b777664f`.
4. **V3 exact-type identity before filesystem work (eight new pytest cases):** Reject spoofed `str` subclasses and invalid nonstrings for HF model ID/revision and export-tool git revision/role before local files are read/hashed. No model bytes, GPU, training, Candidate or protected V2 opened. `src/ark/learning/identity.py` blob `5b09e1f2615374ceb36d3f7df2b05949d74a3548`, `tests/v3/test_exact_local_identity_inputs_run488.py` blob `7081f69286812e1c3729032caf62ea9d921a731b`.

**Total:** four work packages including one CI repair; 21 newly authored pytest parameterized cases (Context 6, Clock 7, V3 8), plus the corrected existing Memory test. No changed frozen Contract/evaluation file.

## CI / verification at evidence composition

- **PR #5 final source/test SHA `79376f3ce777dc877c63ce58785153e493b9b7fc`: CI #1706 / `41133950984` SUCCESS.** Confirm six individual Ubuntu/Windows 3.11–3.13 jobs before treating as six-job GREEN; Actions summary already reported successful completion. Earlier source-only #1705 / `41133846144` SUCCESS.
- **PR #8 first repaired test SHA `ebe9c3be95947dad56855fb5708bcae6237d1ea5`: CI #1704 / `41133741689` IN PROGRESS** at last read.
- **PR #8 intermediate #1707 / `41134031854`, #1708 / `41134064046`, #1709 / `41134116162`: IN PROGRESS/QUEUED** at last read.
- **PR #8 final source/test SHA `ef309357ac6a9b93a9cb8df6f00ee70e677d6619`: CI #1710 / `41134136157` QUEUED** at last read. Historical archive #1711 / `41134200769` QUEUED. These are not declared GREEN.
- Independently run full local pytest/Ruff: **NOT VERIFIED**; `git ls-remote` failed because the sandbox could not resolve `github.com`. GitHub Contents API returned expected paths/blobs; that is source verification, not a test run.
- Run487 complete checkpoint was archived verbatim at `docs/history/PROJECT_STATUS_THROUGH_RUN487.md`, verified to retain original blob `21ea22807b38c1947edf252878b00d1dc2d20903` (932,553 UTF-8 characters). This preserves historical/frozen evidence while allowing the canonical latest status to remain smaller.

## Authorization, immutable and environmental limits

- Re-read exact frozen Memory v1 SQLite `src/ark/memory/sqlite_store.py` blob `0aba6392b39563df520aa8b378d0b313f0cc0a0d`; Memory contracts blob `b6e93821ecd69270a7634aceb20775dc36e9953c`; Agency contracts blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`. V3 Contract 1, V1/V2/Local UI/Launcher, protected V2 final evaluation, contamination/provenance/reproducibility gates unchanged by this invocation.
- No paid service/API, external or GPU compute, full training, real adapter/weights, Candidate promotion, physical-PC tests, real ToolBackend/sensors, new credentials, irreversible action, or approval-requiring main merge.
- Hashes and SQLite witnesses are unauthenticated local observations. Exactly-once external effects, timestamp authenticity, cross-DB atomicity, personal consent/erasure, authoritative human review and real deployment remain unresolved.

## Next plan / 今後の方針

1. Confirm all six CI jobs on the **exact** PR #8 final source SHA #1710; inspect only real failures, fix using ordinary Contents API and preserve the failing test.
2. Advance independent Memory CAS/retained history custody, Planner UNKNOWN WRITE manual reconciliation, audit-before-action and immutable registry/permission checks.
3. Improve Context revocation/retention, Scheduler duplicate prevention, Observation fixture safety and startup readiness without activating external effects.
4. Continue free V3 runtime/file/path/authorization/reproducibility gates. Do not cross paid compute, Candidate, frozen V2 or merge approval boundaries.
