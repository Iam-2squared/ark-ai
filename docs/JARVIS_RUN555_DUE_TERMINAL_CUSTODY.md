# Run555 — Disconnected due restart and Planner terminal denial custody

## Scope

All work remains on PR #8 `research/jarvis-foundations`, Draft/unmerged.
These local-only fixtures do not schedule real notifications, access a
ToolBackend, open a permission gate, authenticate human consent, or prove
trusted time or an exactly-once external effect. No irreversible operations,
frozen contracts, production runtime or main branch were changed.

## Package A — Synthetic due restart

`src/ark/agency/disconnected_due_recovery_review.py` now retains the
**import-time original** denial-only property descriptors of the retained
`DueReservationWitness`, delegated `DisconnectedDuePrefixReview`, and
returned `DisconnectedDueRecoveryReview`. This rejects a preinstalled
False-only callback replacement that was previously indistinguishable
from the original property when only its returned Boolean was checked.

A retained prefix report is also pinned across the later digest and final
denial callbacks. After *every* returned denial getter (including the last),
the review rechecks original descriptors, report fields, retained/observed
SQLite witnesses and prefix fields. A SQLite append remains unverified,
never a replay or notification permission.

`tests/test_due_restart_original_denial_custody_run555.py` adds **15 authored
parameter-expanded cases**: six result-property replacements, six prefix
replacements, witness-property replacement, late prefix mutation, and clean
read-only restart. The initial CI failed Ruff B009 for two constant-name
`getattr` calls; these were changed to direct descriptor access without
changing source semantics or loosening any refusal.

## Package B — Planner hypothetical FAILED/BLOCKED terminal receipt

`src/ark/agency/disconnected_batch_terminal_projection.py` now pins the
four `DisconnectedBatchTerminalReceipt` denial-property definitions at
module import. Both the pure projection and independent verification use
those originals instead of adopting a substituted preinstalled False-only
property as their baseline. This is a synthetic DAG state description, not
a durable authenticated real terminal outcome.

`tests/test_terminal_original_denial_custody_run555.py` adds **9 authored
cases**: four forged projection getters, four forged verifier getters, and
a clean failed-parent/blocked-child scenario.

## Evidence and follow-up

The source/test files and this technical record were saved using ordinary
GitHub Contents API writes. Check the exact final head and full six-job CI
before declaring GREEN; authored test counts are not independently run
local pytest PASS counts. Separate SQLite read snapshots do not imply
cross-store atomicity, and neither synthetic due history nor terminal
fixtures authorize a real tool, restart replay or scheduler notification.

Next: complete CI triage; then connect Planner terminal persistence with
registered READ receipts using exact stable identities and fail-closed
recovery, and continue Memory COMMIT-UNKNOWN manual-only review and
privacy-safe local Personal Context boundaries. PR #5 V3 and PR #8 remain
reversible, isolated and unmerged.
