# Run554 — Scheduler restart: historical-prefix continuity (free-only)

Work basis: PR #8 `8d15c86d728f0a4c6c91895f6e688384be3db8bb`, Draft and unmerged.

## Reconciliation added

`src/ark/agency/disconnected_due_recovery_review.py` now integrates the
**already-existing** one-transaction historical-prefix checker from
`disconnected_due_prefix_review.py` into the restart diagnosis.

Formerly, `review_restarted_due_reservations` compared the count and entire
current ledger fingerprint with a caller-retained witness. A later appended
row made this a **new** fingerprint, so a valid-looking appended ledger could
also conceal an update to a previously reserved occurrence. The separate
prefix checker already rejected this scenario, but a normal restart report
did not invoke it.

The new integration:

1. keeps legacy count-regression and same-count rewrite rejection;
2. checks the old **full-row** prefix hash against the independently supplied
   retained witness under a single read-only SQLite transaction;
3. checks that the prefix review's current count/fingerprint matches the
   initial restart observation. An intervening append or inconsistent
   cross-read snapshot must be diagnosed, never silently accepted;
4. rejects any prefix review granting notification, dispatch, replay,
   trusted-clock, custody or writer authority;
5. retains `ADVANCED_HISTORY_UNVERIFIED` for legitimate appended histories.
   Verification of local prefix bytes is **not** authentication of the writer.

Source commit: `c7eb002fec348530d8b2067e1ab22922f835cb5e`.
Tests commit: `e109c83e314700980460d18d1a44ed6a62f60ff8`.
Six new parameter-expanded cases exercise clean append, two coherent
historical edits, concurrent observation drift, fabricated prefix results,
and false authority substitution. These are authored tests, not claimed
local pytest pass counts.

GitHub Actions exact test-head run:
https://github.com/Iam-2squared/ark-ai/actions/runs/41430971854
CI result must be read separately; this note does not claim GREEN.

## Constraints deliberately unchanged

The supplied clock, historical witness, writer and policy digest remain
unauthenticated local fixtures. Nothing here issues a notification, schedules
an actual action, opens a sensor, consumes a token, proves cross-store
atomicity, or authorizes replay. Frozen V1/V2/Local UI/Launcher evidence,
Planner/Memory contracts, V3 contract, protected evaluation and main are not
modified. No paid API, GPU, Candidate, external compute or human decision.
