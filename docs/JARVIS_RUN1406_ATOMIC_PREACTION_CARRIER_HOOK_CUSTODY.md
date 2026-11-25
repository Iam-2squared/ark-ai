# Run1406 — atomic pre-action carrier hook absence custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `36368ccc4160727c79fb24704a675d589575b414`.
- Child branch: `research/run1406-atomic-preaction-carrier-hook-absence-20261125`.
- Child HEAD before this evidence document: `0b6af1f7907041e7f88fa2453fb5dee5e1cbe656`.
- Source file: `src/ark/agency/disconnected_atomic_preaction_ledger.py`.
- Source blob after implementation: `4c0638dbca642026bf727a7afba12fc2f6784d05` (carrier type alias pinning is a subsequent source commit).

## Finding and correction

The atomic pre-action fixture retained class attributes with `vars(cls).get(name)`. For absent `__new__`, `__getattribute__` and `__getattr__` hooks, that returned `None`; explicitly installing `None` therefore compared equal to absence. The ledger implementation also treated `vars(type).get("__getattribute__") is None` and `__getattr__ is None` as proof of absence, which accepts explicit `None`.

The carrier guard now uses a unique absence sentinel and checks both namespace membership and descriptor identity for every retained field/hook/denial slot. Its exact class-slot vector and sentinel are captured in keyword-only defaults. The ledger path guard separately pins its exact type, constructor hook inventory, absence sentinel and original descriptors before reading instance path identity. The `snapshot=False` path still deliberately skips only the snapshot carrier, preserving the existing independent witness/claim validation boundary.

## Regression coverage

- Explicit `None` for each absent hook on all three carrier types is rejected.
- The exact absence sentinel installed as a hook is rejected.
- Sentinel and equal-valued hook-vector replacement are rejected.
- `snapshot=False` continues to skip the snapshot carrier only.
- Explicit `None`, exact sentinel, sentinel replacement and hostile lookup hooks on the ledger class are rejected before instance path access.
- A clean local SQLite fixture still satisfies the path contract and exposes no execute method.

Tests use local temporary SQLite only and do not invoke backend dispatch, approval, replay, or external effects.

## Scope and evidence limits

This is local in-process carrier/ledger class integrity. The intent and digest-only pre-action audit still do not authenticate issuer provenance, user approval, trusted time, independent custody, provider billing, external effects or exactly-once execution. The SQLite fixture remains disconnected and has no execute API. Schema, row-chain, audit-chain, occurrence identity, CAS, path policy and frozen contracts are unchanged.

No live user data, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, destructive operation, main write/merge or UI/frontend work occurred. PR #5/#8/#9 remain under their existing gates. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.
