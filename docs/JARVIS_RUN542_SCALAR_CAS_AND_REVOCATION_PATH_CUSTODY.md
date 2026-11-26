# ARK AI — Run542 disconnected CAS / privacy path hardening

This note records **synthetic, non-executing** local fixture hardening only. No trusted clock,
human consent, identity authentication, ToolBackend dispatch, notification, external
read/write, immutable storage attestation, deletion, or automatic replay is proved.

## Source and regression packages (normal GitHub Contents writes)

1. **Scheduler due-reservation retained CAS:** source commit `6234e75f2db5dbed98267a4ef89eeb14bf1bfeac`,
   tests `63d69b90470ad4a68b10cab334ad7edc70fdd4f2`, 6 authored pytest parameter cases.
   `DisconnectedDueReservations.reserve_due` compares the SQLite-observed witness
   count/fingerprint against the original caller-retained scalars under the write
   transaction, instead of using overridable dataclass equality. Existing-only
   `reopen_with_witness` also compares exact original scalars. Tests use forged
   always-True and always-False witness equality, stale count, stale fingerprint,
   legitimate reservation, restart, and no-authority receipts. This is *not*
   a trusted-clock, consent, notification, or real exactly-once guarantee.

2. **Personal Context request replay postinsert witness:** source commit
   `fc10292a304e46d0f4b9fa060d99d18325a26804`, tests
   `7a38ad5008050398f58374181193573ccb287e46`, 3 authored parameter cases.
   Postinsert `_inspect()` results must match retained count/chain SHA scalars
   before COMMIT. An injected valid-shape but wrong SQLite witness cannot
   trick a patched `__eq__` into accepting a synthetic request. Rejected
   transactions roll back; post-COMMIT UNKNOWN is **not safe to retry**.
   Context text remains outside the ledger.

3. **Privacy veto ledger obvious path aliases:** source commit
   `098684cf3c72dd7f5f1eabe9507be0df29611600`, tests
   `01ebb64c84bed460fd16111520c36d03633acc5a`, 4 authored cases.
   `SyntheticContextRevocationLedger` rejects symlink targets, symlinked
   ancestors, and multiply-linked existing files before its initial SQLite
   access and during later source-path checks. Ordinary one-link restarts
   remain supported. This is a **best-effort path inspection**, not atomic
   filesystem handle custody or protection from all concurrent swaps;
   database WAL/backups and deletion lifecycle are not certified.

## Evidence scope and constraints

The 13 authored test variants are **not** 13 separately executed local pytest
PASS. GitHub Actions is the existing public-repository CPU matrix, not paid
GPU/compute. At note creation the PR #8 latest-source/full-matrix outcome
must be checked against each exact commit; prior CI successes belong only
to their prior HEADs. No manual workflow reruns are required.

Frozen Memory v1 `src/ark/memory/contracts.py` blob
`b6e93821ecd69270a7634aceb20775dc36e9953c` and Planner
`src/ark/agency/contracts.py` blob
`13f1bb725f9c2c783e29402ca4a6e0f86b850ef9` remain unchanged.
PR #8 remains Draft/unmerged; main is not modified.

## Next integration prerequisites

Review exact-head CI before connecting any durable state to a higher-level
authority. Prioritize Memory generation CAS and post-COMMIT UNKNOWN manual
triage; Planner terminal-failure/READ journal and ToolRegistry/PermissionGate
cross-check; scheduler trusted-clock preaction audit and occurrence replay
fencing; Personal Context revocation/expiry across independent sources.
