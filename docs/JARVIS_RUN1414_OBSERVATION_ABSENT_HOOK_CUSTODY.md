# Run1414 — Observation envelope absent-hook custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `86229ee377e91ed1925bd5cd192f565ddd8c2477`.
- Child branch: `research/run1414-observation-absent-hook-custody-20261125`.
- Scope: `src/ark/observations.py`, `src/ark/observation_fixture_adapters.py`, and one isolated subprocess regression module.

## Finding

Both observation layers recorded class hooks with `vars(type).get(name)`. For an absent `__new__`, `__getattribute__` or `__getattr__` hook, that produces `None`; an explicit `None` class member therefore compared equal to true absence. A sentinel-only comparison would still be insufficient if the exact sentinel were installed as a class member. The hook/type/vector aliases also lacked one retained import-time epoch at these two boundaries.

## Change

- Introduce unique absent-hook sentinels in the envelope and adapter modules.
- Capture the exact type aliases, field/hook vectors, original descriptors and sentinels in import-time epochs retained by keyword-only validator defaults.
- Check epoch and alias identity before reading the class namespace.
- For expected-absent hooks, require namespace non-membership; for expected-present descriptors, require membership and exact descriptor identity.
- Keep fixture input hashing, envelope fields and observation identity semantics unchanged.

## Regression coverage

- Explicit `None` and each module's exact sentinel installed as each absent hook.
- Sentinel rebinding, equal-valued-but-distinct hook-vector replacement and epoch replacement.
- Joint replacement of public/private envelope type aliases.
- Identity getter rejects hook substitution before the digest callback.
- All class-slot mutation probes run in isolated subprocesses to avoid leaking CPython type-slot changes into the test process.

## Scope and evidence boundary

Synthetic, disconnected fixture inputs only. No live microphone, camera, screen capture, file, network, ToolBackend, notification, device or production dispatch is introduced. Observation Envelope v1 fields, schema, digest domain, privacy labels, parent lineage, fixture byte limits and public adapter signatures are unchanged. No consent, trusted-clock, source authenticity, independent custody, physical deletion, authorization or exactly-once external-effect evidence is claimed.

No paid/external compute or service, Candidate generation/promotion, protected V2 evaluation, credential/account connection, hardware action, destructive operation, frozen-contract change, main write/merge or UI/frontend work occurred.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result or PASS is claimed.