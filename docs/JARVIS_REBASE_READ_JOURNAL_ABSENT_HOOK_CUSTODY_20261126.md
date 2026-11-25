# Rebase — detached READ journal absent class-hook custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `db7f12a406ef668b2f6bf1cdbf46715d8a406ce8`.
- `src/ark/agency/disconnected_read_journal.py` and the adjusted Run546 recovery regression were verified byte-identical between old basis `7178d91c4ae332908dd8bd34fd9f8ab939385bd3` and current parent.
- Rebased from Draft PR #600 / Run1412, exact child HEAD `2284ad53c79946a73551f32f8322fcaff2bf7237`.
- Prior exact-head CI run [45668096242](https://github.com/Iam-2squared/ark-ai/actions/runs/45668096242) was GREEN on that old child HEAD only; it does not transfer to this rebase.
- New child branch: `research/rebase-read-journal-absent-hook-custody-20261126`.

## Finding and correction

The exact ReadReceipt, ReadJournalWitness and ReadJournalSnapshot class guards retained absent `__new__`, `__getattribute__` and `__getattr__` entries with `vars(type).get(name)`. For hooks absent from a class namespace, the retained value was `None`; explicitly installing `None` was therefore indistinguishable from true absence. The snapshot and receipt/witness validators also lacked one retained epoch binding all exact type aliases and descriptor-vector objects.

This rebase adds a unique absent-class-hook sentinel and a retained import-time carrier epoch covering the public/private type aliases, field vectors, hook vectors, deny-only descriptors and sentinel. The validator checks epoch identity before class namespace inspection, requires namespace absence for sentinel-backed entries and exact descriptor identity for present entries. Snapshot validation uses the same complete carrier guard as receipt/witness validation.

## Regression coverage

- Explicit `None` and exact-sentinel installation are rejected for `__getattribute__` and `__getattr__` on all three carriers.
- Explicit `None` and exact-sentinel installation for `__new__` are tested in isolated child processes to avoid interpreter-level type-slot residue.
- Sentinel rebinding, joint hook-vector replacement and joint snapshot type-alias replacement are rejected.
- The original carrier epoch remains accepted.
- No journal is opened and no receipt is appended by the class-guard tests.
- Existing recovery tests assert denial descriptors are rejected before callbacks can run.

## Scope and evidence boundary

The journal remains a synthetic, local, READ-only, digest-only recovery view. It grants no dispatch, replay, effect, independent-custody or user-consent authority. This does not prove trusted time, process isolation, independent storage custody, fsync/power-loss durability, cross-store atomicity or exactly-once external effects.

ReadJournal DDL, schema, receipt/event hash format, 128-row bound, path checks, CAS, public APIs and frozen contracts are unchanged. No ToolBackend, executor, model, MemoryStore, network, paid/external compute/service, Candidate generation/promotion, protected V2 evaluation, credentials, hardware action, destructive operation, main write/merge or UI/frontend work occurred. PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result or READ journal/replay/durability/production-readiness PASS is claimed.
