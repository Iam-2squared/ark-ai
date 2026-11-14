# ARK AI — Run487 disconnected integrity and V3 code-identity evidence

This document records **four** no-new-cost, reversible source/test packages and
**29 newly authored parameterized pytest cases**. It does not grant permissions
to execute tools, disclose Personal Context, perform training, open protected V2,
merge either Draft PR, or spend money. All cases are synthetic/local-only.

## Work basis and exact committed byte identities

Initial observed PR #8 HEAD: `dfbcd69f93a19a95110c7b7dfa3af5ce15dbe5ea`.
Initial observed PR #5 HEAD: `683cfa5f580dfff1fe8402f9859f875877e15a76`.
Current authored source/test HEADs before this document:
- PR #8 `f458ffe66682c8767a50472478f2128a464ad5f5`
- PR #5 `afb462ed85b7ca7ce0f9c75b4efd641297fa0ddf`

1. **Planner complete-plan WRITE membership (8 cases):** PR #8
   `src/ark/agency/disconnected_write_restart_binding.py` blob
   `2c4645185b8c76d844698c6cc4828cd831eb1239`;
   `tests/test_disconnected_write_restart_completeness_run487.py` blob
   `853bbf1b115a89abd9292dc6d70f065364564acb`.
   Previously a caller could present only one known WRITE slot while other
   reservations for the *same* plan existed in SQLite. A read-only exact-plan
   set comparison now rejects omitted durable WRITE slots, including a slot
   hidden behind a claim lacking its reservation ID. Unrelated plans remain
   independent. UNKNOWN/RUNNING/RESERVED WRITEs remain quarantined; no replay.

2. **Independent Personal Context replay restart tip (8 cases):** PR #8
   `src/ark/personal_context_replay_recovery.py` blob
   `609ed7e004f7f4a97b278f0e9b6a37e015d06016`;
   `tests/test_context_replay_independent_restart_tip_run487.py` blob
   `cf0d8da88dedebcac80b6b9f0d9d0b379688c859`.
   The public `witness()` callback may return an old/forged but exact-type
   observation while a SQLite append happens. An independent read-only
   transaction checks the actual persisted tip against callback observations
   before classification and again after result construction. Additional
   history is still **ADVANCED_HISTORY_UNVERIFIED**, never consent or
   permission. These reads cannot prove authenticated writer/retained custody.

3. **Bounded retained Memory JSON (8 cases):** PR #8
   `src/ark/memory/disconnected_witness_ledger.py` blob
   `8133a2a85b42db9c8f9f418844ac8edba6242847`;
   `tests/test_memory_witness_json_depth_run487.py` blob
   `bca1e557d0f04c8b3879f8da6578221674b91d46`.
   The 4KiB retained JSON payload now also has a deterministic maximum of 64
   container levels, checked outside quoted strings, with decoder recursion
   rejection normalized into the existing domain error. The escaped-quote
   scanner comparison and an unused fixture were corrected during authoring.
   Memory v1 database schema and frozen contract are unchanged.

4. **V3 code-manifest packaging recheck (5 cases):** PR #5
   `src/ark/learning/identity.py` blob
   `b0a0867da50bc5fbe3744235dd1fd0f66d97cba7`;
   `tests/v3/test_code_tree_packaging_epoch_run487.py` blob
   `32adcedd9ee5b34ef9be6f9ad3b7cd3d174baf74`.
   `build_code_tree_identity` now rehashes `pyproject.toml` after hashing
   the learning Python subtree, rejecting changed packaging bytes during
   manifest construction. This is local best-effort consistency, **not**
   an atomic directory snapshot or proof against adversarial same-byte
   replacement. No GPU, torch runtime, external network, real Candidate,
   or protected evaluation was invoked.

## CI and limitations at evidence composition

- Prior Run486 exact-head PR #8 source/test CI #1689 (GitHub Actions
  `41118860216`) and document CI #1690 (`41119009690`) have six GREEN
  Ubuntu/Windows Python 3.11–3.13 jobs; prior checkpoint #1691
  (`41119183007`) succeeded. All are **older heads** than Run487.
- Run487 PR #8 intermediate #1693 (`41124882121`) and #1695
  (`41124970568`) were still running at the last job inspection;
  final source/test #1699 (`41125283519`) was QUEUED. PR #5 source/test
  #1701 (`41125460905`) was QUEUED. Do not claim exact-head GREEN
  before all jobs finish. Documentation/checkpoint writes will trigger
  independent subsequent CI, not duplicate manual workflow launches.
- Independent whole-repository local pytest/Ruff is **NOT VERIFIED**:
  `git ls-remote` failed DNS resolution of github.com. No invented test
  totals or source runtime identities are used.
- The three observed frozen PR #8 blobs remain:
  Memory SQLite v1 `0aba6392b39563df520aa8b378d0b313f0cc0a0d`,
  Memory contract `b6e93821ecd69270a7634aceb20775dc36e9953c`,
  Agency contract `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`.
  Main `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged.
  Other historical frozen V1/V2/Local UI/Launcher and V3 contracts
  were not intentionally edited; no assertion of a rehashed full tree.

## Remaining blockers

The synthetic local hash/witness chain cannot authenticate writer/owner,
independent custody, real consent/revocation, trusted clock, WAL history,
multi-database atomicity, actual external exactly-once side effects, or
a JARVIS-complete system. Execution and dispatch remain impossible here.
V3 real base/tokenizer hashes, approved 120/30 dataset, pinned GPU/tool
identities, human authorization and external billing ceiling remain unresolved.
No real Candidate/training/preflight, paid provider, protected V2 final
evaluation, automatic promotion or main merge is permitted.

## Next plan / 今後の方針

1. Inspect latest PR #8 #1699 and PR #5 #1701 **exact-head** CI, then fix
   any genuine failures minimally without bypassing the normal Contents API.
2. Strengthen coherent SQLite restart boundaries and Planner manual
   reconciliation while keeping UNKNOWN WRITE quarantined.
3. Audit trusted-clock and audit-before-action design, scheduler duplicate
   prevention, Context retention/revocation and observation fixtures.
4. Keep V3 identity/authorization/reproducibility protections free-only.
   Approval-gated real work remains blocked.
