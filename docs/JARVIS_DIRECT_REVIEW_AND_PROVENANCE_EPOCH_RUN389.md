# ARK AI — direct review and privacy provenance epoch hardening (Run 389)

Status: **engineering review / disconnected fixture only**. The code and
regression tests referenced here are saved on Draft PR #8. This note does not
state CI PASS without an exact-head GitHub Actions result, change frozen
contracts, authenticate approval, grant any external action, or authorize
integration into main.

## Scope of this source change

Four independently owned entrypoints are hardened so their *direct* callers
cannot unknowingly rely on an outer coordinator to pin their inputs.

1. `agency/synthetic_recovery_triage.py`: pin the Planner database Path,
   ActionAudit Path, optional occurrence-to-audit sidecar Path, original plan
   topology container, registry revision, ToolCall fields and arguments object,
   and all supplied retained witness fields. Recheck after independent reads.
   A same-path Path replacement or a late retained-witness edit rejects the
   diagnostic rather than treating a locally matching receipt as reliable.
2. `proactive_synthetic_continuity_review.py`: use a single captured ledger
   Path to open a read-only SQLite transaction, recheck its object identity
   after row/schema/historical checks and after closing, and bind optional
   independently retained witness values against reentrant modification.
   Neither a trigger marker nor a matching witness sends a notification.
3. `personal_context_review.py`: retain the original snapshot clock and
   provenance digest and recheck source scopes, record identity, source,
   metadata, TTL, revision and content provenance across selection and
   final bundle hashing. Ephemeral selected fixture content is kept local.
   A returned bundle ID is not a consent record or authorization.
4. `agency/synthetic_approval_cancellation_fence_review.py`: direct
   cancellation review now pins the local ledger Path, registry revision,
   ToolCall authority fields/arguments, envelope and retained witness before
   the first veto read, checking after each potentially reentrant phase.
   Successful synthetic non-cancellation does not mean authenticated consent.

Regression modules:

- `tests/test_direct_synthetic_recovery_epoch_run389.py`
- `tests/test_proactive_witness_source_epoch_run389.py`
- `tests/test_personal_context_provenance_epoch_run389.py`
- `tests/test_direct_cancellation_fence_epoch_run389.py`

Each test uses only in-process hooks and synthetic SQLite fixtures. No real
tool executor is invoked. Intermediate CI failures, if any, remain attributable
only to their exact HEAD and must be resolved before describing the final head
as GREEN.

## Non-equivalence to production trust

Object identity checks are **not inode/OS custody**; a same-path file
replacement by an independent OS actor, a restored ABA source mutation, or a
change after the last check is not ruled out. Independent SQLite transactions
are not one atomic cross-store snapshot. A caller-supplied timestamp is not a
trusted clock. SHA digests and locally retained rows do not sign a human
issuer, prove user intent, or establish irrevocable consent. A local
reservation, audit receipt, Planner status or prepared Trigger cannot show
that an external WRITE occurred exactly once.

In particular, `UNKNOWN WRITE` must never be auto-retried, and a READY or
locally consistent result must never activate notifications, cameras,
microphones, personal-data disclosure or other backends. All frozen V1/V2/
Local UI/Launcher evidence and Memory v1 DDL remain untouched. V3 PR #5
remains Draft/NOT_PASSED, the protected V2 FINAL remains closed, and all
JARVIS foundation changes stay isolated in Draft PR #8.

## Next safe validation

- Require exact-head Ubuntu/Windows Python 3.11–3.13 CI and Ruff for the new
  source/tests, then recheck the eventual checkpoint-result SHA independently.
- Keep mock-only negative fixtures for reflected data mutation and replay.
- Pursue externally authenticated issuer/subject/recipient consent, trusted
  time, durable cross-process token consumption and actual backend
  acknowledgments only behind their separate explicit authorization gates.
