# ARK AI — Run492 disconnected witness and V3 descriptor evidence

**Status: NOT_PASSED.** Five free-only, isolated source/test work packages. No Candidate, protected V2 opening, real Tool dispatch, consent, trust-root/time proof, actual scheduling, external GPU, paid API, or main merge.

## Read basis, branches, and save boundaries

- Starting PR #8 checkpoint: `7b723453cb84b57d7cb2a283d993706e93e5c3a0` (`research/jarvis-foundations`, OPEN/DRAFT/UNMERGED). Last source/test package HEAD before this evidence write: `ca92275b755d502a9e1ddfa69b04272d1667c7ae`.
- Starting PR #5 source HEAD: `7d3d1fe69e5d8e550ea444510c793395047d99f7` (`research/v3-learning-evaluation`, OPEN/DRAFT/UNMERGED). Final Run492 source/test HEAD `d96ac89ac576483514bc6d715015a5f0736faaca`.
- Main remains separately gated and unmerged. No force push or raw Git object write was used. All successful writes used the normal GitHub Contents API with fresh file blobs and branch-head reads.

## Source + new regression tests

1. **Scheduler / due retained witness** (`src/ark/agency/disconnected_due_reservation.py`, blob `dfcbe2ae4dec2dbce8f491959f296e92d4c168e4`). Recheck exact non-authorizing caller-retained witness at each SQLite reservation boundary and after read-only restart, including post-inspection. The two tests in `tests/test_due_retained_authority_recheck_run492.py` inject a property spoof only on the retained object *after* the relevant observed-witness check. A denied reservation must not create a due row. Read-only restart is not execution authority.
2. **Planner / disconnected WRITE slot CAS** (`src/ark/agency/disconnected_write_slot_ledger.py`, blob `9e48dbb7e1c6c005dbad46e43d4876ea8e50a2c0`). Validate retained and SQLite-observed witness exact types and independent-custody denial before INSERT and after reinspection. The two tests in `tests/test_write_slot_retained_authority_run492.py` reject pre-COMMIT authority spoof and equal-valued but nonexact hash carriers. A reservation never executes or automatically replays UNKNOWN WRITE.
3. **Privacy / Personal Context replay CAS** (`src/ark/personal_context_replay_ledger.py`, blob `17d65a56bb4658873ebe5ef5bcc809fc383afc76`). Validate each *observed* SQLite witness as an exact non-authorizing type, not only through digest/count equality. `tests/test_context_replay_sqlite_observed_witness_run492.py` provides one parametrized test at both read boundaries (two cases), and requires no committed replay row on rejection.
4. **Memory / detached epoch CAS** (`src/ark/memory/disconnected_witness_ledger.py`, blob `b82a3eb8a45660f718e4955c9892023640d151be`). Validate the observed epoch witness at startup, before append, and after uncommitted INSERT. `tests/test_memory_sqlite_observed_witness_run492.py` provides two parametrized cases that require rollback on equal-valued but nonexact hash carriers. No Memory content is persisted in this opt-in witness fixture.
5. **V3 / local identity descriptor** (`src/ark/learning/identity.py`, blob `d3ef77d434b7a52da0d07f17d987530c7ede3888`). Check opened file descriptor type, link count, device/inode and size/timestamp epoch against the path's pre-open stat, and recheck the descriptor and path after reading. `tests/v3/test_identity_open_descriptor_epoch_run492.py` has two offline tests, including a diverted `Path.open` to a separate same-size local file. This supplements the existing outer file-epoch checks; it does not claim atomic hostile-OS provenance or download any weights.

Total **8 new pytest functions / 10 test cases** (two parametrized functions count as four cases), with one follow-up correction to the due-slot regression fixture for precise retained-only spoof timing. No frozen regression was deleted or relaxed.

## CI evidence and limitations

- Previously verified: PR #8 Run491 source/test `d70d48a889d0481a6c98178a2c8c2d27f469c5c2`, [GitHub Actions #1749 / 41151918888](https://github.com/Iam-2squared/ark-ai/actions/runs/41151918888), **6/6 GREEN**. This predates Run492 and cannot prove Run492 HEAD.
- Previously verified: PR #5 Run491 source/test `7d3d1fe69e5d8e550ea444510c793395047d99f7`, [#1740 / 41151476912](https://github.com/Iam-2squared/ark-ai/actions/runs/41151476912), **6/6 GREEN**. This predates the descriptor change.
- **New PR #8 latest source/test** `ca92275b755d502a9e1ddfa69b04272d1667c7ae`: [#1762 / 41157215683](https://github.com/Iam-2squared/ark-ai/actions/runs/41157215683), **6 jobs QUEUED at last job inspection**, not GREEN.
- **New PR #5 latest source/test** `d96ac89ac576483514bc6d715015a5f0736faaca`: [#1761 / 41157173741](https://github.com/Iam-2squared/ark-ai/actions/runs/41157173741), **6 jobs QUEUED at last job inspection**, not GREEN.
- Local full pytest/Ruff: **not independently executed**; direct local `git ls-remote` failed DNS resolution. GitHub reads, workflow jobs and standalone local tests are distinct evidence sources. Check CI against exact final source SHA before any gate claim. No duplicate manual workflows dispatched.

## Frozen contracts and blockers

- Frozen Memory v1 `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c` and Agency `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`: unchanged at read.
- V3 `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` and `docs/v3/CONTRACT.sha256` blob `176154514bd6be22685ca0555bc682c3bd8d45dc` unchanged. This was a read-only check, not a fresh human approval or a complete end-to-end audit.
- V1/V2/Local UI/Launcher freeze, protected V2 final evaluation, V3 Experiment 001 and provenance/contamination/regression/reproducibility boundaries untouched by the packages. PR #5 remains under its own explicit immutable base/tokenizer/revision, human dataset and budget/billing authorization blockers.
- SQLite witnesses and SHA digests remain caller-controlled, not independently authenticated; CAS guarantees local serialized reservations, not exactly-once external actions. Unknown actions remain quarantined without automatic retry.

## Next plan / 今後の方針

1. Confirm final exact-source CI for PR #8 #1762 and PR #5 #1761. On any failure, inspect failing job logs, preserve gates, make the smallest semantics-preserving correction, then validate the corrected HEAD. No duplicate workflow runs.
2. Memory retained-tip/row/event CAS and independent-writer boundary; Planner UNKNOWN WRITE manual reconciliation and registry-bound PermissionGate; trusted-clock audit-before-action with fail-closed mock cases.
3. Scheduler restart-safe occurrence handling, privacy-safe consent/revocation/expiry, disconnected Observation fixtures.
4. Free-only V3 identity/snapshot/approval provenance and reproducibility checks. Stop before paid/external compute, real Candidate generation, protected V2 opening, promotion and unauthorized main merge.
