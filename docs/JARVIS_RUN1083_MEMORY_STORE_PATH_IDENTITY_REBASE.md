# Run1083 — SQLite Memory constructor path identity rebase

## Exact basis
- Parent: Draft PR #8, `research/jarvis-foundations`
- Parent HEAD at branch creation: `916aae6c6578086fee5e83c77c23375712676c90`
- Prior reviewed child: Draft PR #208, `research/run1079-memory-store-path-identity`
- Prior child HEAD: `a972f734df45b09bd558e5c960ef94672589c1d3`
- Prior exact-head CI: run [44943016519](https://github.com/Iam-2squared/ark-ai/actions/runs/44943016519), GREEN 6/6. This result does not transfer to this rebase.

## Rebased change
Reapply SQLiteMemoryStore's constructor-bound Path identity. A store retains the exact Path object selected at construction and rejects wrong-type, equal-value replacement, or retargeting to another valid regular SQLite database before public operations process inputs. The identity is rechecked at writable and read-only connection boundaries.

The synthetic regression fixtures prove that retargeted reads/searches/writes fail before opening or creating the foreign database, while preserving the existing no-follow path checks, sidecar checks, in-operation epoch checks, WAL bootstrap and CAS behavior.

## Scope and limits
- Memory v1 DDL, row/event format, public API and CAS semantics are unchanged.
- This is in-process Path-object identity hardening, not OS-backed directory-handle custody, a sandbox, authenticated provenance, consent or privacy-use authorization.
- Disposable synthetic SQLite only. No live personal data, paid/external compute, Candidate, training, protected V2 evaluation, frozen-contract change, UI, credentials, physical-PC action or main merge.
- PR #8 remains Draft/unmerged. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required for this rebased child.
