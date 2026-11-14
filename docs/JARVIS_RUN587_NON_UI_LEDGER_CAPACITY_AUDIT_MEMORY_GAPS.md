# ARK AI — Run587: bounded reservations and append-only audit continuity

**Scope:** Free-only, local-only, non-UI changes on Draft PR #8. This note
records source/test artifacts, not independently proven authorization, human
consent, hardware identity or external exactly-once effects.

## Three work packages

1. **Synthetic WRITE reservation capacity under the SQLite writer lock.**
   `src/ark/agency/durable_occurrence_review.py` blob
   `f855571a9ef1d381cef086a0495cb3ecba92d5c2`.
   The prior bounded validator accepted up to 10,000 rows but a subsequent
   reservation could commit row 10,001, making future reads/restarts fail.
   The reservation path now checks the existing row count **inside BEGIN
   IMMEDIATE**, before the INSERT, and fails closed at capacity without
   consuming the next synthetic token. This does not authorize real dispatch.
   Regression file `tests/test_synthetic_occurrence_capacity_run587.py`
   blob `c46324b5e549542e7de694eb069aa46eb37e5c05`:
   three tests for full ledger/restart/retry, zero capacity, and competing
   writers racing for the last slot.

2. **Action audit event-ID continuity.**
   `src/ark/agency/audit_continuity_review.py` blob
   `92399ac82b69d882a1736c5ae8f21a4d52d6af70`.
   The read-only reviewer already checked increasing IDs and per-row
   request digest consistency, but could construct an apparently coherent
   history after a first/middle event was removed when no retained witness
   was supplied. A full-genesis scan now requires consecutive IDs starting
   at 1; it does not alter or repair the SQLite schema.
   `tests/test_audit_history_gap_run587.py` blob
   `2f9b9e5fcfbe0013b97e301e2e9f7df6d93b8b5e`:
   four parameter-expanded cases covering missing first/middle event,
   rewritten event ID, and legitimate restart append.

3. **Global Memory v1 event-ID continuity across all scopes.**
   `src/ark/memory/sqlite_event_alignment.py` blob
   `20b119c5d8024d596c6cda3aace625816459e3d2`.
   Memory event reconciliation now fails closed on missing global IDs
   rather than treating an internally consistent subset of rows/events as
   complete after matched deletions. No frozen Memory schema or contract
   changed. `tests/test_memory_global_event_gap_run587.py` blob
   `ddc9de903011ae8bd419cd8942bc5b77d3a5707e`:
   four parameter-expanded cases for matched row/event deletion, jumped
   event IDs, and a healthy cross-scope restart.

## Source and CI evidence

- Invocation work-basis Draft PR #8 HEAD:
  `6ec28349af19472fe1c9710bbaced47c802c8ee2`, exact-head
  [CI #41679111260](https://github.com/Iam-2squared/ark-ai/actions/runs/41679111260)
  **COMPLETED SUCCESS / six jobs GREEN** prior to these changes.
- Three implementation+test pairs were written sequentially using the
  normal GitHub Contents API, re-reading the latest PR HEAD immediately
  before every write. **Substantive work HEAD:**
  `f3c47056c42e0b7c275bd09e5a4f77c2273c0f0d`.
- Source/test intermediate CI: [#41687671865](https://github.com/Iam-2squared/ark-ai/actions/runs/41687671865),
  [#41687756389](https://github.com/Iam-2squared/ark-ai/actions/runs/41687756389),
  [#41688161642](https://github.com/Iam-2squared/ark-ai/actions/runs/41688161642),
  [#41688205764](https://github.com/Iam-2squared/ark-ai/actions/runs/41688205764),
  [#41688329175](https://github.com/Iam-2squared/ark-ai/actions/runs/41688329175),
  [#41688388174](https://github.com/Iam-2squared/ark-ai/actions/runs/41688388174)
  were started automatically by GitHub; their final results must be
  explicitly re-read and must not be inferred from the earlier GREEN HEAD.
- **11 new authored parameter-expanded cases** across three files (3+4+4);
  no independent local pytest run or pass result is claimed in this note.
  No manual duplicate workflow launch.

## Unchanged gates and limitations

Frozen Memory contract `b6e93821ecd69270a7634aceb20775dc36e9953c`,
Planner contract `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`,
V3 contract `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`;
existing V1/V2/Local UI/Launcher evidence unchanged. Draft PR #5 stays
under V3 gate and Draft PR #9 stays untouched with all new UI work paused.

Append-only ID validation is a **local consistency check**. It cannot
detect deletion of an entire suffix without an independently retained
witness, renumbering plus coherent rewriting, replacement of the whole
SQLite database, or a malicious writer with full local control. The
caller clock and synthetic token issuer remain untrusted. No real
ToolBackend, notification, GPU, paid service, Candidate training,
protected evaluation, main merge, approval or irreversible operation
was performed. **ARK/JARVIS/V3 NOT_PASSED.**

## Next plan

1. Confirm exact-head six-job Ubuntu/Windows CI; repair only proven
   failures without weakening fail-closed checks, and do other non-UI
   work while CI runs.
2. Extend independently retained prefix witness/restart integrity for
   Memory and Audit where continuity alone cannot detect suffix loss.
3. Continue ToolRegistry/PermissionGate exact identity, restart-safe
   audit-before-action, Planner terminal recovery and Personal Context
   revocation/retention; keep all external effects disconnected.
