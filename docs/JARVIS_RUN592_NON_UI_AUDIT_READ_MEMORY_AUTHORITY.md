# ARK AI — Run592: audit read continuity and Memory review authority custody

**Scope:** free-only, non-UI, disconnected/local foundation changes on Draft PR #8. Observed GitHub work-basis HEAD `05af11413bf2bb460f64f5c64f5f424c3243d93c`. This document is a source-grounded engineering note, not an independent runtime, human, consent, or security attestation.

## Package A — fail-closed SQLite audit pagination

- Source `src/ark/agency/audit.py`: the existing `_require_dense_committed_audit_sequence` predicate is now called inside the `events()` read snapshot, immediately after existing DDL/schema verification and before paginated rows are read.
- The predicate checks `COUNT/MIN/MAX(event_id)` and the `sqlite_sequence` high-water mark. A locally deleted first/middle/tail event, entirely emptied append-only table, rewritten ID or damaged high-water mark can no longer produce a superficially valid page without a rejection.
- Regression `tests/test_action_audit_read_sequence_run592.py`: eight parameterized deletion/page combinations plus a high-water mismatch and a successful two-page baseline: **10 authored cases**.
- Source commit `4c0a091de392cb159f97dfc5ed83d00df0382312`; tests commit `7294a46fb3e04ba646c46d49174bd981b4405474`.
- The local sequence counter is mutable and does not authenticate authorship; a coherent rewrite of all rows plus sequence can evade this check. The helper examines event identity continuity, not independent source trust or complete historical clock authenticity.

## Package B — Memory row/event audit result cannot acquire forged authority

- Source `src/ark/memory/sqlite_event_alignment.py`: the original frozen `MemoryEventAlignmentReview` result type and its four deny-only property descriptors are retained. A preinstalled or reentrant equal-value property replacement now causes a fail-closed exception. Exact row/event/scope/tip/digest result fields are checked both before and after all deny-only getter callbacks.
- Regression `tests/test_memory_alignment_authority_epoch_run592.py`: four parameterized preinstalled False-only substitutions, one reentrant substitution during event fingerprinting, and one unchanged positive review: **6 authored cases**.
- Source commit `31f7d59c01cafc09f0a036a745401f252218bbfe`; tests commit `66ac3101cf54588bc8844918af0005ce01e5d57c`.
- This is an offline integrity and authority-boundary improvement. It is not signed custody, consent verification, reliable erasure, trusted clock, or permission to dispatch.

## Validation and protected boundaries

- Before source work, exact HEAD `05af11413bf2bb460f64f5c64f5f424c3243d93c` had completed [GitHub Actions #41725691304](https://github.com/Iam-2squared/ark-ai/actions/runs/41725691304) with **six success jobs** across Ubuntu/Windows Python 3.11–3.13. That is **pre-change evidence only**.
- Automatic PR workflows for the source and tests started at [#41734018825](https://github.com/Iam-2squared/ark-ai/actions/runs/41734018825), [#41734077793](https://github.com/Iam-2squared/ark-ai/actions/runs/41734077793), [#41734213735](https://github.com/Iam-2squared/ark-ai/actions/runs/41734213735) and [#41734279443](https://github.com/Iam-2squared/ark-ai/actions/runs/41734279443). These were not yet certified exact-head GREEN when initially inspected; validate final six-job results separately.
- Sixteen is the number of authored regression scenarios, **not** a claimed local pytest PASS. No full local Python-repository environment was available; network access for a local clone was unavailable. Remote GitHub Actions is the execution gate.
- No freeze/DDL/contract/schema change, PR merge, UI/frontend work, model training, real backend dispatch, paid/external compute, new credentials, protected V2 evaluation or Candidate promotion. PR #5/#8/#9 remain Draft/unmerged pending gates.

## Next plan / 今後の方針

1. Verify latest exact-head six-job CI; repair only observed failures, without loosening fail-closed behavior.
2. Independently retained Memory generation-CAS and COMMIT-UNKNOWN quarantines; persisted Planner FAILED/BLOCKED recovery.
3. Registry-bound tool identity + exact-type permission + durable audit-before-action occurrence fencing. Unknown effects remain blocked and no disconnected fixture authorizes real dispatch.
4. Personal Context privacy/revocation and proactive duplicate prevention; offline observation fixtures and free V3 identity/provenance guards. UI remains paused.

**Note prepared:** `2026-11-03T22:52:27.290Z` (ordinary host wall-clock; not a trusted clock attestation).
