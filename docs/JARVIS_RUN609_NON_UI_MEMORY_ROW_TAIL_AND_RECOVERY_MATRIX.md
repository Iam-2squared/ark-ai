# Run609 — non-UI Memory event tail and mixed-plan recovery matrix

**Scope:** Draft PR #8, isolated/reversible ARK core. No frontend changes, new
credentials, paid compute, real hardware or external ToolBackend.

## Finding 1 — retained row-delta scan formerly accepted a shortened event tail

At work-basis HEAD `9d69d7a1f5b9cd8017f45f0912e508cc0c339aec`,
`src/ark/memory/sqlite_retained_row_delta_review.py` required strictly
increasing event IDs but did not enforce a dense genesis-to-tip history or
cross-check SQLite's `sqlite_sequence` event high-water mark. A local actor
could remove the final CREATE event *and its associated live row*, leaving a
plausible earlier prefix; a single local snapshot could then appear internally
consistent despite unaccounted historical append activity.

Source fix `439e3eba8df3ba0bfa7a8e862eccd71add905f69` adds:

- Dense global `event_id == prior + 1` checking from event 1 onward.
- A same-read-transaction `sqlite_sequence` check: no sequence row only for
  zero events, and exactly equal to the last event ID otherwise.
- Fail-closed `MemoryRowDeltaRejected`; no repair, re-creation, retry or
  mutation of persisted data.

Regression tests `f2bc57569f4f0ad1a404cf3d13ebe4f0bbe564ed`
(`tests/test_memory_retained_row_delta_highwater_run609.py`) define **six
parameter-expanded pytest cases**: removal of a closed historical lifecycle;
removal of the live tail and its row; forged/missing high-water mark; deletion
of the entire closed history; and normal empty/append behavior.

**Boundary:** `sqlite_sequence` is a **local** hint, not a tamper-proof
independent witness. A privileged actor able to rewrite both journal and
high-water marker can defeat it. Retained external custody, verified writer
identity, authenticated consent and real action outcomes are NOT established.

## Finding 2 — bounded mixed-plan restart matrix

`tests/test_mixed_recovery_topology_matrix_run609.py` saved at
`875a29a99b1e3c2e77f3ba2db275697f1d55ad02` specifies **199
parameter-expanded cases** over all two-step combinations of READ/WRITE
and seven recovery states, plus three reserved-PENDING WRITE cases.

Properties under test:

- Started dependent steps require successful ancestor state claims.
- WRITE never produces `READY_MOCK_ONLY`; UNKNOWN/RUNNING WRITE is held.
- PENDING descendants of terminal or unknown ancestors do not become ready.
- A durable reserved PENDING WRITE stays quarantined even if dependencies
  report success, failure or unknown.
- Repeating the same synthetic review is deterministic. Every report has
  `dispatch_authorized=False`, `automatic_replay_authorized=False`,
  `write_authorized=False` and `external_outcome_verified=False`.

This is model-based *synthetic* recovery verification, not an authorization
policy, a real executor, or exactly-once physical action.

## Evidence, execution and gates

- 2 independent packages, **205 newly authored parameter-expanded test
  cases**. Case count is **not** locally executed pytest PASS.
- Local git checkout unavailable (GitHub DNS not resolvable from the working
  container); writes used only the ordinary GitHub Contents API and
  SHA-checked expected blobs.
- Baseline checkpoint `9d69d7a1f5b9cd8017f45f0912e508cc0c339aec`
  independently confirmed **6/6 GREEN** by Actions run
  [#41852208045](https://github.com/Iam-2squared/ark-ai/actions/runs/41852208045).
  The current source/tests CI must be separately verified at their exact HEAD.
- Source CI
  [#41860557426](https://github.com/Iam-2squared/ark-ai/actions/runs/41860557426);
  Memory tests CI
  [#41860682228](https://github.com/Iam-2squared/ark-ai/actions/runs/41860682228);
  Planner matrix CI
  [#41861011236](https://github.com/Iam-2squared/ark-ai/actions/runs/41861011236).
  These IDs are evidence references; consult live Actions status, do not
  assume green without independent readback.
- Existing frozen V1/V2/Local UI/Launcher/Mem/Planner/V3 controlling evidence
  and contracts unchanged. PR #5 and paused UI PR #9 remain Draft/unmerged;
  no main merge, candidate promotion, protected evaluation or GPU execution.

## Next engineering work

After exact-HEAD six-job verification, prioritize cross-process Memory CAS
COMMIT-unknown quarantine and retained-event review, planner crash recovery
and immutable registered mock-tool audit-before-action, privacy-aware local
context revocation, proactive/observation source provenance and V3 free-only
identity/path guards. Integration must remain isolated until each lower-level
invariant has GREEN evidence.
