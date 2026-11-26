# Run595 — non-UI receipt authority and detached READ journal custody

**Scope:** free-only, reversible, disconnected fixtures on Draft PR #8 `research/jarvis-foundations`.
**Work basis:** `da1636360e70a6198db24551442048d096d0b0d9`.
**Outcome:** normal GitHub Contents API writes only; no force push, paid services, real execution, model training, or protected evaluation.

## A. Observed Run594 failure — repair without relaxing the safety check

GitHub Actions [#41749835002](https://github.com/Iam-2squared/ark-ai/actions/runs/41749835002),
head `da1636360e70a6198db24551442048d096d0b0d9`, completed **FAILURE 6/6**.
The Ubuntu 3.12 job `126311891717` reports **Ruff E501** at
`tests/test_proactive_receipt_original_authority_run593.py:49`: 106-character
`pytest.raises` line. The exception pattern was preserved and merely split
over multiple lines through commit `8227736bb2c9da21e6de185595a08a14c2fe6b21`.
No authority decision or business logic changed.

## B. Detached due reservation — original post-COMMIT receipt denials

- **Source** `src/ark/agency/disconnected_due_reservation.py`, commit
  `f3bebf4654f9f056537223e187a54a1bd3921f84`.
- **Tests** `tests/test_due_reservation_receipt_denials_run595.py`, commit
  `4c9c435ef8cb2c557d46db3dd68c30b471914133`.
- Preserve import-time identities of all four `DueReservationReceipt` denial
  properties. After local COMMIT check exact receipt type, occurrence, caller
  time scalars, witness carrier, and every original denial descriptor after
  each getter. A late getter cannot rewrite an earlier descriptor or replace
  a same-valued receipt identifier without detection.
- **11 authored parameter-expanded cases:** four false-only replacements,
  four true replacements, one late descriptor rewrite, one equal-value carrier
  replacement, and one unchanged restart-readable control.

COMMIT may have persisted the slot before diagnostics reject the returned
receipt. It is not a notification, trusted clock, consent, dispatch permission,
proof of exactly-once external effects, or license to retry.

## C. Detached READ journal — witness and recovery authority

- **Source** `src/ark/agency/disconnected_read_journal.py`, commit
  `aa2beda2fae98dff43ee2e412dbae826d33a490a`.
- **Tests** `tests/test_read_journal_original_denial_custody_run595.py`,
  commit `a232985d0c32ec5c684a59cbce82a68a83b756d8`.
- Keep the four original `ReadJournalWitness` denial descriptors and
  `ReadJournalSnapshot` descriptors captured at import, rather than accepting
  an already-substituted False-valued property as the baseline. Each witness
  getter is followed by descriptor and count/tip carrier rechecks.
- The append's returned witness passes the same validation after COMMIT;
  the recovery snapshot compares against the original snapshot descriptors.
- **15 authored parameter-expanded cases:** four preinstalled witness
  replacements, four recovery-snapshot replacements, two reentrant
  descriptor changes, four post-COMMIT witness substitutions, one unchanged
  recovery control. These are *authored tests*, not locally certified passes.

This closes local class-level monkeypatch attack surfaces only. It does not
authenticate the SQLite file, establish independent witness custody, confirm
actual READ execution, authorize automatic replay, or repair COMMIT-UNKNOWN.

## CI evidence / explicit non-claims

The preceding GitHub failures and replacement code have separate CI runs:

- [#41755920750](https://github.com/Iam-2squared/ark-ai/actions/runs/41755920750) — Ruff repair at `8227736b...`.
- [#41756108857](https://github.com/Iam-2squared/ark-ai/actions/runs/41756108857) — due source at `f3bebf46...`.
- [#41756176232](https://github.com/Iam-2squared/ark-ai/actions/runs/41756176232) — due source + test at `4c9c435e...`.
- [#41756353347](https://github.com/Iam-2squared/ark-ai/actions/runs/41756353347) — READ source at `aa2beda2...`.
- [#41756437276](https://github.com/Iam-2squared/ark-ai/actions/runs/41756437276) — both source/test packages at `a232985d...`.

These runs were **not yet certified GREEN on the final checkpoint HEAD**
at the time of drafting. No local pytest PASS or actual machine evidence is
invented. Review exact CI jobs and logs before any integration/PASS label.

## Next integration gate — registry, permission, audit before mock action

The current audited foundations are *not* a trusted execution chain:

1. `registry.py` binds an immutable backend registration revision;
   `policy.py` enforces exact-scope `PermissionGate` checks but its token
   consumption is process-local, not restart-safe approval.
2. `audit.py` persists local digest-only events with schema and event
   continuity checks. It is not an independently authenticated, trusted-clock
   append receipt, and an audit row cannot attest to a real side effect.
3. Disconnected occurrence and READ journals reserve *synthetic identities*,
   not a globally atomic cross-database action/authorization/effect.
4. An integration fixture must keep live dispatch disabled; bind registry
   revision + exact call + scope + occurrence to a durable audit-intent
   *before* mocked action; refuse mismatched/stale witnesses; preserve
   `UNKNOWN` after ambiguous COMMIT/crash; never auto-replay a WRITE.
5. Any future real ToolBackend needs separate approval for user identity,
   trusted time, durable grants, audit custody and side-effect reconciliation.
   No existing fixtures can be promoted to real authority by naming alone.

**Next:** verify latest exact-head Ubuntu/Windows CI, repair observed failures
through normal Contents API only; then prioritize a disconnected integration
proof joining immutable registry, precise PermissionGate, durable audit intent,
and synthetic occurrence recovery. Keep Memory generation-CAS and Planner
FAILED/BLOCKED manual recovery independent. Privacy revocation, Observation,
V3 free-only guards remain open lanes. All frozen V1/V2/Local UI/Launcher/V3
contracts and PR #5 gate remain untouched; PR #9/UI work remains PAUSED.
