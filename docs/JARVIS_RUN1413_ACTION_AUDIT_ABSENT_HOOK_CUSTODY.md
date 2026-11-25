# Run1413 — ActionAudit absent class-hook custody

Status: isolated local hardening of the ActionAudit event carrier. No JARVIS PASS is claimed.

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `43eaf52c81b86ed8cdca7e18b6abea0eee3dcdfe`.
- Child branch: `research/run1413-action-audit-absent-hook-custody-20261125`.
- Scope:
  - `src/ark/agency/audit.py`
  - `tests/test_action_audit_event_absent_hook_custody_run1413.py`

## Finding and correction

The ActionAudit event validator retained `__new__`, `__getattribute__` and `__getattr__` through `vars(type).get(name)`. A missing class-namespace hook was therefore recorded as `None`, making true absence indistinguishable from an explicit `None` substitution. The validator also needed one retained epoch for the absence sentinel, public/private exact event type aliases, constructor descriptor and field/hook vectors.

The change:

- Captures a unique absent-class-hook sentinel and uses it in the original hook vector.
- Retains the sentinel, public/private event type aliases, original constructor and field/hook vectors in one import-time epoch captured by verifier defaults.
- Checks epoch identity before inspecting the original class namespace.
- Requires namespace absence for sentinel-backed hooks; present descriptors require namespace membership and exact identity.
- Rejects sentinel installation, explicit `None`, sentinel rebinding and coordinated public/private type-alias replacement before SQLite access.

## Regression coverage

- Explicit `None` and exact-sentinel installation for `__getattribute__` and `__getattr__`.
- Explicit `None` and exact-sentinel installation for `__new__` in isolated subprocesses to avoid CPython allocation-slot residue.
- Sentinel rebinding and coordinated public/private event type replacement.
- Original event carrier epoch remains accepted.
- The lookup-hook tests replace the SQLite connection callback and assert it is never reached after carrier tampering.

## Scope and evidence limits

ActionAudit v1 DDL, event fields, chronology, append-only local sequence checks, public APIs and audit-before-action ordering are unchanged. This is in-process Python class-definition integrity only. It is not a Python sandbox, authenticated event history, independent storage custody, trusted-clock proof, durable consent, cross-store atomicity, fsync/power-loss durability or exactly-once external-effect evidence.

No real backend, dispatch, model, live user data, network, paid/external compute/service, Candidate generation/promotion, protected V2 evaluation, credentials, hardware action, destructive operation, frozen-contract change, main write/merge or UI/frontend work occurred. PR #5/#8/#9 remain Draft/unmerged; PR #9 remains untouched.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result or PASS is claimed.
