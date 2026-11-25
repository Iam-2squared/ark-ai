# Run1412 — Detached read journal absent-hook custody

Status: isolated hardening of the synthetic READ recovery journal under Draft PR #8. No execution, replay or durability PASS is claimed.

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `7178d91c4ae332908dd8bd34fd9f8ab939385bd3` (PR #8 exact rebase basis)..
- Child branch: `research/run1412-read-journal-rebase-20261126`..
- Scope: `src/ark/agency/disconnected_read_journal.py` and one synthetic regression file.

## Finding

The exact `ReadReceipt`, `ReadJournalWitness` and `ReadJournalSnapshot` class guards retained `__new__`, `__getattribute__` and `__getattr__` entries with `vars(type).get(name)`. For hooks absent from a class namespace, the retained value was `None`; explicitly installing `None` was therefore indistinguishable from true absence. The snapshot and receipt/witness validators also lacked one retained epoch binding all exact type aliases and descriptor-vector objects.

## Change

- Capture a unique absent-class-hook sentinel and use it in all three carrier hook vectors.
- Retain the public/private exact type aliases, field vectors, hook vectors, deny-only descriptor vectors and sentinel in one import-time carrier epoch.
- Verify epoch identity before class namespace checks.
- Require namespace absence for sentinel-backed entries and exact descriptor identity for present entries.
- Make the snapshot guard use the same complete carrier validator, so receipt/witness/snapshot identity is checked consistently before recovery result inspection.

## Regression coverage

- Explicit `None` and exact-sentinel installation are rejected for `__getattribute__` and `__getattr__` on all three carriers.
- Explicit `None` and exact-sentinel installation for `__new__` are tested in isolated child processes to avoid interpreter-level type-slot residue.
- Sentinel rebinding, joint hook-vector replacement and joint snapshot type-alias replacement are rejected.
- The original carrier epoch remains accepted.
- No journal is opened and no receipt is appended by these class-guard tests.

## Evidence boundary

The journal remains a synthetic, local, READ-only, digest-only recovery view. It grants no dispatch, replay, effect, independent-custody or user-consent authority. This does not prove trusted time, process isolation, independent storage custody, fsync/power-loss durability, cross-store atomicity or exactly-once external effects.

ReadJournal DDL, schema, receipt/event hash format, 128-row bound, path checks, CAS, public APIs and frozen contracts are unchanged. No ToolBackend, executor, model, MemoryStore, network, paid/external compute/service, Candidate generation/promotion, protected V2 evaluation, credentials, hardware action, destructive operation, main write/merge or UI/frontend work occurred. PR #5/#8/#9 remain Draft/unmerged; PR #9 remains untouched.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result or PASS is claimed.
