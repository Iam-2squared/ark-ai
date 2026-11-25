# Run1417 — Proactive policy/state/ledger absent-hook custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `a1bff14b0ca731ee1d094d6611caf76c08640398` (PR #8 exact rebase basis)..
- Child branch: `research/rebase-run1417-proactive-state-absent-hook-custody-20261126`..
- Source: `src/ark/proactive_state_ledger.py`.
- Regression test: `tests/test_proactive_state_absent_hook_custody_run1417.py`.

## Finding and correction

The proactive policy, state result and SQLite ledger class guards recorded inherited/absent `__new__`, `__getattribute__` and `__getattr__` entries using `vars(type).get(name)`. An explicit `None` therefore compared equal to true absence. The policy/state/ledger guards also relied on separate mutable vectors without a retained epoch for every exact class alias and absence marker.

The change introduces one unique module-local absence sentinel and independent import-time epochs for the policy, state and ledger carriers. Each guard verifies its epoch, public/private type aliases, original field/method/denial vectors and sentinel before class-namespace inspection. Expected-absent hooks require namespace non-membership; expected-present descriptors require membership and exact identity. The ledger guard retains its exact slot layout and every entry point.

## Regression coverage

- Explicit `None` and exact-sentinel installation for absent hooks on all three carriers.
- Explicit replacement of an expected-present `__init__`.
- Sentinel rebinding, equal-valued vector replacement and epoch replacement.
- Joint public/private type-alias replacement for policy, state and ledger.
- All special class-slot mutation probes run in an isolated subprocess.

## Scheduler and evidence boundaries

This remains local synthetic proactive state infrastructure. No timer/scheduler activation, notification, user-facing suggestion, ToolBackend call, trusted clock, consent, dispatch or external action is introduced. SQLite schema, row/hash formats, policy digest, occurrence identity, CAS, COMMIT-UNKNOWN and recovery semantics, retention, public APIs and frozen contracts are unchanged. This is in-process class-definition integrity, not a Python sandbox or independent storage custody.

No live user data, credentials/account connection, hardware action, paid/external compute/service, Candidate generation/promotion, protected V2 evaluation, destructive operation, frozen-contract change, main write/merge or UI/frontend work occurred. PR #5/#8/#9 remain Draft/unmerged; PR #9 remains untouched. The older PR #580 path-policy package remains separate and unmerged.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result or PASS is claimed.