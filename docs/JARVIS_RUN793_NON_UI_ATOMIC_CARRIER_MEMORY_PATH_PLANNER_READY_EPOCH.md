# Run793 — non-UI free-only atomic carrier, Memory path, and Planner readiness hardening

Repository work basis: `f0233f9e245a6766390160ed2795d905ec5ee4f6` (Run792 exact HEAD).
Branch: `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).
Status: **implementation saved; latest exact-head 6-job CI pending at report preparation**.
The four packages are intentionally separate from frozen V1/V2/Local UI/Launcher,
protected V2 final evaluation, V3 Candidate approval, and the untouched UI Draft PR #9.

## Package A — local atomic intent/audit carrier custody

- Source: `src/ark/agency/disconnected_atomic_preaction_ledger.py`; first source
  commit `1ced484850bbf85ca97007bbc30bd4ca4de00796`.
- The optional SQLite ledger now checks import-original claim, witness,
  and no-dispatch snapshot field descriptors and construction/lookup hooks
  **before** reading their respective fields. The private `_scan` validates
  snapshot denial getters before inspecting a local audit journal. It still
  does not invoke a real ToolBackend, confer consent, or claim exactly-once
  external effects.
- `tests/test_atomic_carrier_preaccess_run793.py`: 11 submitted cases
  (3 claim slots + 2 witness slots + 5 denial slots + one local restart/CAS).
- Real intermediate CI for source/test HEADs
  [#43032612695](https://github.com/Iam-2squared/ark-ai/actions/runs/43032612695)
  and [#43032763003](https://github.com/Iam-2squared/ark-ai/actions/runs/43032763003)
  showed Ubuntu pytest failure in existing
  `test_atomic_recovery_quarantine_run763.py::test_rebound_snapshot_authority_cannot_run_before_recovery`.
  Root cause: the new *genesis witness constructor* over-checked the unrelated
  snapshot denial class while the existing higher-level recovery test
  intentionally substituted that getter. This prevented the expected
  adapter-layer denial from executing.
- Semantics-preserving repair saved at
  `1d9de812b73fadf64904489cccfcdfb0306e869f`:
  genesis and preaccess claim/witness validation check only the relevant
  input carriers; the full snapshot/denial guard still runs before the
  private SQLite `_scan`. The earlier recovery negative test remains unchanged.
  **The repaired HEAD is not claimed GREEN until its six actual CI jobs pass.**

## Package B — coherent multi-namespace Memory SQLite path custody

- Source commit `cc36e33f8c83fd6235590ee97c60998488d67d99`:
  `src/ark/memory/coherent_snapshot_review.py` applies the existing
  `_require_safe_memory_path(..., create=False)` both before and after
  `Path.resolve()`, with the pinned request/source epoch rechecked between
  steps. A store path switched to a file/parent symlink, hardlink, or unsafe
  SQLite sidecar after object initialization cannot be used for a
  multi-namespace private read.
- Tests committed `27959e7e97e298cc3a911698b0a7c62d992a25c5`:
  `tests/test_memory_coherent_path_custody_run793.py`, 5 submitted cases,
  including an ordinary local read and four alias/sidecar denials.
- This is **lexical/lstat preflight**, not OS handle-based atomic ancestry
  protection against concurrent local rename or privileged filesystem attack.
  No erasure, namespace widening, or external source authorization.

## Package C — Planner ready-set epoch coherency

- Source commit `45f55288554be1273f27d4aa427e07c0d8d94432`:
  `PlanGraph.ready_steps()` pins the actual in-process status epoch before
  its validation phase and rechecks it both after the initial validation and
  after the dependency scan. A legitimate reentrant transition cannot
  silently yield a previously computed runnable list, even when the graph
  is internally valid after the transition.
- Tests committed `f71f5425fbaa69702429ea738608917bc46827e1`:
  `tests/test_planner_ready_epoch_run793.py`, 3 submitted cases: preflight
  reentrant transition, postscan transition, and ordinary terminal BLOCKED
  propagation. These are synthetic Graph transitions, not ToolBackend dispatch.
- No persistent journal migration, automatic WRITE replay, or live planner
  execution is introduced.

## Package D — Personal Context durable replay ledger sidecar privacy

- Source commit `5bd86dbc25b28a8fcf52c001ae56ae33386a18ea`:
  `src/ark/personal_context_replay_ledger.py` now checks each SQLite
  `-wal`, `-shm`, and `-journal` companion with `lstat`. A fresh
  database refuses any orphaned sidecar; an existing context replay ledger
  refuses symlinks, hardlinks, directories, or other nonregular companion
  files. This occurs before SQLite opens the private ledger. No plaintext
  context or actual source content is copied to the ledger.
- Tests committed `68dafd5032f78ae463aae584b2fc7b89f87be2e9`:
  `tests/test_context_replay_sidecar_custody_run793.py`, **8 submitted
  cases**: three orphan variants, three symbolic-link variants, one hardlink,
  and one ordinary genesis/reopen.
- This is local pathname preflight only; cannot prove atomic OS path custody
  against a concurrent attacker-controlled rename. No permission to disclose,
  replay a context request, remove retention protections, or dispatch tools.

**Total newly submitted Run793 tests: 27** (11 Atomic + 5 Memory +
3 Planner + 8 Personal Context). These tests are not marked six-job GREEN
without matching CI verification.

## Exact evidence discipline / pending gates

- Previous exact-head Run792:
  [CI #43024567602](https://github.com/Iam-2squared/ark-ai/actions/runs/43024567602)
  **GREEN 6/6** (Windows and Ubuntu, Python 3.11–3.13), independently
  checked through all six job conclusions.
- Early Run793 Atomic CI failures are **real** (not predicted). Latest
  source/test/run-report HEAD success is **NOT YET CERTIFIED** at this
  report writing. CI should be inspected at matching head SHA and individual
  six jobs, and only real failures should trigger minimal fixes.
- No local pytest, Ruff or external hardware execution is claimed.
- Source changes are limited to four non-UI modules; no frozen contract
  or historical evidence was deliberately altered.
- PR #5 Draft/unmerged; PR #9 Draft/unmerged, untouched, UI development
  paused. No paid/external GPU/API, new credentials, authenticated approval,
  real Candidate training or promotion, protected evaluation, irreversible
  actions, or approval-required main merge.

## Next plan / 今後の方針

1. Confirm the repaired Atomic and the latest composite six-job exact-head
   CI; if a job fails, inspect its log and correct the smallest faulty phase.
2. Continue Memory generation CAS/ABA and manual-only COMMIT-UNKNOWN review,
   including independently retained event-prefix witnesses and coherent path
   custody (no implicit consent to erase or extend retention).
3. Continue Planner durable terminal/restart reconciliation and independent
   journal witness checks, without replaying an ambiguous WRITE.
4. Advance registry-bound one-shot occurrence + audit-before-action through
   explicitly disconnected/mock fixtures only, after exact-head lower-level
   evidence is GREEN.
5. Keep Personal Context, scheduler, observation and free-only V3 approval/
   identity/path safeguards isolated and reversible; JARVIS/V3 NOT_PASSED.
