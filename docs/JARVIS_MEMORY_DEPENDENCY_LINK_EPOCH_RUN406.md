# ARK JARVIS foundations — Run406 disconnected Memory / dependent WRITE recovery evidence

**Scope:** isolated, reversible, FREE-only changes on Draft PR #8. No main merge, no live ToolBackend, no real person/issuer approval, no notification, no V3 Candidate generation, no external GPU/API, no protected V2 final evaluation, no frozen schema or contract change.

## Work packages and concrete source/fixture boundaries

### A. Content-free Memory snapshot final witness epoch

- `src/ark/memory/coherent_snapshot_review.py`: separate checks after final canonical JSON encoding and after final SHA-256 digest calculation. Previously an injected hashing callback could mutate a request/source/hydrated record *after* the last epoch check and return stale-looking witness data.
- `tests/test_memory_snapshot_final_digest_epoch_run406.py`: **8** new local SQLite regression cases. Cover mutation of request, source Path carrier and hydrated record at serialization/hash boundaries (6), mutate-then-restore between serialization and hash callbacks (1), and stable deterministic output (1).
- Final provenance digest remains metadata-only; no raw Memory contents are embedded in the witness. Frozen Memory v1 SQL schema, data, retention and CAS contracts are unchanged. These callback fixtures do not establish real OS fd/inode custody or external provenance.

### B. DAG-aware dependent WRITE holds after disconnected recovery

- `src/ark/agency/synthetic_write_plan_recovery_review.py`: extend the *diagnostic-only* result with `downstream_write_hold_step_ids` and `terminally_blocked_write_step_ids`. Propagate direct UNKNOWN/reservation uncertainty and terminal failed/cancelled/blocked states through transitive dependencies, including intermediate READ steps. Do not mislabel a dependent pending WRITE as independently proved safe.
- Preserve `uncertain_step_ids` as *direct* uncertain WRITE evidence. A dependent hold is different from declaring a WRITE externally executed or externally UNKNOWN. All three collections are read-only diagnostic identifiers; no dispatch/automatic replay.
- `tests/test_synthetic_write_plan_dependency_holds_run406.py`: **8** new local SQLite cases. Cover pending DAG, RUNNING/UNKNOWN prerequisite + restart, failed prerequisite, explicit BLOCKED/CANCELLED, failed READ bridge, independent WRITE, and direct uncertain descendant without double-counted holds.
- **Observed CI failure and repair:** initial terminal propagation implementation excluded every terminal-status node from descendants. Planner auto-propagates BLOCKED to successors, so four regression cases failed at original test HEAD `731a6bc8533c6d5c3ca150da5942a06571a0142b` (CI #920 / `40147726738`; Ubuntu Python 3.13 reported 4 failed, 2049 passed). The semantics-preserving source fix at `85a1aec1246cf3ad5ba09a9d54c6f356ba7307fc` tracks actual dependency-descendant reachability independently of membership in the terminal root set. **Do not relabel failed CI #920 as GREEN; verify the fixed SHA on its own CI.**

### C. Multi-WRITE linked crash/reopen integration

- `tests/test_synthetic_write_plan_linked_restarts_run406.py`: **3** end-to-end fixture cases. Exercise two distinct RUNNING/UNKNOWN WRITEs with nonempty ledger, pre-action ActionAudit and link sidecar records; independently retained four-store witness rechecks across SQLite reinitialization; refuse post-restart automatic replay of both; reject erased nonempty retained link history; and keep a PENDING dependent WRITE held when its prerequisite has a persisted reservation + audit link.
- A synthetic link is a separately committed local record, not user consent, authenticated outcome, permission, trusted time, atomic cross-store snapshot or an external exactly-once receipt.

## Regression and evidence requirements

- Work-basis checkpoint before this invocation: `99ed02197b1d52607ee7fcdbae93334a53eab4cd` (Run405; GitHub CI #916 / `40145087670` completed SUCCESS).
- Source/test commits in chronological order: `e26ec37d73da399f5b5e5dcafdd13a2f3addac1c` (Memory source), `a2485407a684432209e8c91e325fa1bfcbadef3c` (Memory tests), `6a660fcd40ee2051e1ced61b8b9e29c7de5bcfb5` (plan source), `731a6bc8533c6d5c3ca150da5942a06571a0142b` (plan tests), `7cf5a1881494ef9e47672bc90394bcfe3fee7e8d` (linked fixtures), `85a1aec1246cf3ad5ba09a9d54c6f356ba7307fc` (terminal closure repair).
- Newly added cases: **19**; baseline Run405 **2037** pass; expected collected after all changes **2056** (not a PASS assertion until exact-head CI confirms it).
- Requirements before integrating dependent features: exact same HEAD Ruff + pytest GREEN on Ubuntu/Windows Python 3.11–3.13; independent four-store retained proofs must continue to fail closed; keep UNKNOWN WRITE non-replay; no new authority from these diagnostics.

## Remaining architecture blockers / non-proofs

Authenticated user issuer/consent, real trusted clock, real backend receipt, cross-SQLite atomic snapshot, hardened OS file identity, device integration, actual Candidate model, and external exactly-once effects remain **NOT PROVED / NOT ENABLED**. Protected/frozen V1/V2/Local UI/Launcher and V3 Contract 1 boundaries remain untouched. V3 PR #5 stays Draft/NOT_PASSED.

## Next engineering queue / 今後の方針

1. Check exact-head source/test CI after terminal-propagation repair; investigate any failure instead of inheriting prior GREEN.
2. Extend dependent WRITE recovery to mixed local terminal states, independent cross-store epochs and crash locations, always no replay.
3. Harden Memory coherent snapshot/retention and Personal Context revocation race cases with real offline fixtures but no personal-data export.
4. Evolve deny-by-default issuer/clock/permission admission contracts and observation/scheduler fixtures without connecting real devices, backend execution, or paid services.
