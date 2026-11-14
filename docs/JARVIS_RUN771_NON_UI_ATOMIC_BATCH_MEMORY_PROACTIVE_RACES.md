# ARK AI — Run771: coherent multi-WRITE audit snapshot and independent process-race fixtures

**Evidence draft saved at:** 2026-11-11T02:49:40.282+09:00 Asia/Tokyo/JST (administrative host-clock sample, not an authenticated ARK trusted clock).
**Initial work-basis HEAD:** `31cc94ce715d274004325168cdab86a282e1afe9` (Run770 checkpoint, CI [#42861048283](https://github.com/Iam-2squared/ark-ai/actions/runs/42861048283) completed all six jobs GREEN).
**Branch:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), not merged.
**Source/test final package HEAD:** `ed21d15e2dc5ed0aebe00eaa33947e435767d7c3`. The future checkpoint write will create a different HEAD, which cannot honestly be predicted here.

## Package A — coherent atomic batch binding review (one new module, nine tests)

- New opt-in non-UI module: `src/ark/agency/disconnected_atomic_batch_binding_snapshot_review.py` (initial create `ef0d926d90d0e2d1aba1a65c2f753aa54efcb05a`; import/regex fix `185f7b3425f7f88e61a3396818abb697f27ffe5c`).
- New tests: `tests/test_atomic_batch_single_snapshot_run771.py`, commit `630eaa1a1a153ed3fb7523bff02f5e652d149626`, **nine parameterized cases**.
- Preflights an exact bounded tuple of 1–32 unique occurrence-ID/registered WRITE requests. Derives canonical registered bound-action and request hash, checks caller-held witness, and validates the full local intent/preaction audit chain under **one SQLite BEGIN read transaction** before querying all occurrence bindings. Reports `ABSENT`, `LOCAL_MATCH`, or `LOCAL_CONFLICT` for each in input order, not a combination of snapshots from separate times.
- Rechecks input identities and class/callback definitions; result explicitly denies dispatch, automatic replay, independent authentication and effect proof and requires manual review. The local witness is not an externally authenticated anchor; the result never writes an intent, consumes approval or invokes any backend.
- Tests cover mixed local states, stale witness, unrelated tampered audit and modified schema, duplicate occurrence/invalid batch, READ vs WRITE registration, and request mutation. All use a disposable DB and a backend that would throw if called.

## Package B — independently competing Memory CAS processes (two tests)

- New `tests/test_memory_multiprocess_generation_cas_run771.py`, commit `98a713a2208107c086e76d90896e18de1d3b2a9c`.
- Two independent Python processes race the same retained generation token in a disposable SQLite database, first with identical payloads, then with distinct payloads. Require exactly one successful local update, one rejected stale generation, one persisted update event and no replay. Cold re-observation must advance the event-prefix digest without elevating the token to consent or tool authority.
- No frozen Memory v1 API or SQLite schema changes. A matching content image never attributes the COMMIT to a particular caller. This is a local concurrency regression, not cross-database atomicity or authenticated provenance.

## Package C — concurrent proactive due preparation and owner isolation (three tests)

- New `tests/test_proactive_multiprocess_due_race_run771.py`, commit `ed21d15e2dc5ed0aebe00eaa33947e435767d7c3`.
- Two independent processes proposing the same owner/policy due window (same or different observation hashes) must admit exactly one hash-only local preparation. A cold-start attempt before the minimum interval is rejected. Independent owners may each prepare under distinct hashed scope without serializing away one another.
- No notification, background action, external capture, trusted clock or credential connection is triggered. Raw owner text must not appear in the SQLite main file (this is a limited plaintext-minimization check, not full filesystem/backup privacy proof).

## CI/evidence discipline

- **Exact initial basis:** [#42861048283](https://github.com/Iam-2squared/ark-ai/actions/runs/42861048283) `31cc94ce...`: Windows/Ubuntu × Python 3.11–3.13 **6/6 GREEN**.
- Source commit `ef0d926d...`: [#42867657189](https://github.com/Iam-2squared/ark-ai/actions/runs/42867657189); corrected source `185f7b3425...`: [#42867761877](https://github.com/Iam-2squared/ark-ai/actions/runs/42867761877); batch tests `630eaa1a1a...`: [#42867949936](https://github.com/Iam-2squared/ark-ai/actions/runs/42867949936); Memory tests `98a713a220...`: [#42868176981](https://github.com/Iam-2squared/ark-ai/actions/runs/42868176981).
- These latest runs were **IN PROGRESS / QUEUED** when first checked, so their outcomes must be fetched fresh before any GREEN claim. No local full pytest or final exact-HEAD 6/6 GREEN is claimed. The original workspace cannot clone GitHub directly; GitHub Contents normal writes and Actions are the only repository-side validation used.
- Do not infer a successful CI from a prior SHA. Fix a real failing job using its exact logs and normal authorized GitHub Contents path, preserving guards.

## Security boundaries and next plan

PR #5 frozen V3 Draft and PR #9 paused UI Draft remain unmerged/untouched; `main`, V1/V2/Local UI/Launcher/ObservationEnvelope v1 evidence and contracts are unchanged. No UI work, paid/external GPU/API, Candidate training/export, protected V2 final evaluation, real ToolBackend, physical-PC work, secret/account connection, external effect, irreversible change, promotion or main merge.

The multi-WRITE batch snapshot closes a **local torn-read window**, not the larger real-world authorization gap: it does not supply a trusted issuer/clock, human approval, independent tamper-evident custody, a cross-store transaction or exactly-once side effects. UNKNOWN WRITE remains permanently manual-only unless a separately reviewed reconciliation contract exists. **ARK/JARVIS/V3 NOT_PASSED.**

**Next plan / 今後の方針:** inspect latest exact HEAD Windows/Ubuntu CI and correct any observed failures; retain a useful atomic batch state as a read-only planner recovery input only after exact-head GREEN; preserve Memory CAS lifetime/ABA and expiry fencing under process contention; examine proactive retention/privacy and startup behavior; advance registry-bound PermissionGate/audit/mock-only integration without live dispatch; continue free-only V3 approval/path/identity reviews without touching gated evaluation or Candidate state.
