# ARK AI — Run490 Technical Evidence: Read-only restart & local V3 hash custody

**Status:** four isolated development packages; standard CI on the exact newest source HEADs is pending at this report's construction. This document does not authorize execution, training, approval, notification, or merging.

## Exact work basis and saved code

- Initial JARVIS work-basis/checkpoint HEAD: `9b66f8187d71070bafbace089dacd6e699fc11c6`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), branch `research/jarvis-foundations`.
- Initial separate V3 HEAD: `b754608f41e9848ed7c8755aa46608d1af056910`, [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), branch `research/v3-learning-evaluation`.
- Final saved JARVIS **source/test** HEAD before this technical report: `c3b11b2eaa4a908b6c8e6b3f58e14607adcc44be`.
- Final saved V3 **source/test** HEAD: `7cebbbbd3e0915028a1aa447b0baf7511df8a49e`. No Candidate bytes, training or external GPU work.
- Main remained at last verified `7a843f17eb96ed13d66f23b58b06406b3002e405`; no merge.

## Four bounded work packages (15 new pytest test functions)

1. **Scheduler existing-only restart (3 functions).** `src/ark/agency/disconnected_due_reservation.py` blob `e2f9bb2d77e44ea649c270653c31eb60bb9e9a60`; `tests/test_due_restart_read_only_run490.py` blob `ad9f7ca8b1a39b432392877457ad327dc46cdc02`. `require_existing=True` uses SQLite `mode=ro` and an ordinary read `BEGIN`, not `BEGIN IMMEDIATE`. Explicit fixture creation retains `rwc` and write transaction. Tests verify no mutating SQL and inspect under a separate SQLite RESERVED writer lock. No automatic replay or scheduling.
2. **Memory retained-witness restart (3 functions).** `src/ark/memory/disconnected_witness_ledger.py` blob `10d5d9aa9ceead2401035800293ec568a0695b55`; `tests/test_memory_witness_restart_readonly_run490.py` blob `c7a4b8566790faeaed8fd0b4584d29cb32abbeca`. Existing ledger inspection opens `ro` with a non-write read transaction. Creation remains explicit and write-locked. A caller-retained chain tip still does not prove independent witness custody or Memory disclosure authorization.
3. **Planner durable WRITE-slot restart (3 functions).** `src/ark/agency/disconnected_write_slot_ledger.py` blob `81d8931678bcc606605e27ed616057894495f2e6`; `tests/test_write_slot_restart_readonly_run490.py` blob `08c6ebec54b5540953afc2926634f39b79d7e747`. Existing-only init now opens with `mode=ro`, `BEGIN`. Explicit `create=True` keeps `rwc` and write-intent. UNKNOWN or RUNNING WRITE remains quarantined, never automatically resumed.
4. **V3 artifact lineage SHA-256 custody (6 functions).** `src/ark/learning/lineage.py` blob `deec6301aa2fe03b95b875b5d7aebe15f90782c0`; `tests/v3/test_lineage_file_custody_run490.py` blob `51989b40c600e47dc167722e55cc3473985e0e77`. Existing local file hashing now checks exact path carriers, rejects explicit parent aliases/symlinked ancestors/multi-link files and checks file descriptor plus on-path metadata before/during/after hashing. This is a local-files-only protection, **not** a proof of tamper-proof OS custody. Frozen missing/non-file error expectations are retained.

## CI observations and corrections

- Prior Run489 exact PR #8 source HEAD `af8c5aef6bc6be1b338f2e6dff34e3575d135970` [#1721](https://github.com/Iam-2squared/ark-ai/actions/runs/41140289600) completed **6/6 GREEN**. PR #5 prior source HEAD `b754608f41e9848ed7c8755aa46608d1af056910` [#1722](https://github.com/Iam-2squared/ark-ai/actions/runs/41140350170) completed **6/6 GREEN**.
- PR #5 intermediate [#1728](https://github.com/Iam-2squared/ark-ai/actions/runs/41146400976) and [#1729](https://github.com/Iam-2squared/ark-ai/actions/runs/41146424014) failed. #1729 Ubuntu 3.12 completed Ruff and had **625 passed / 1 failed**, due solely to an established test asserting the error substring `non-symlink file` for missing/non-file hash input. Normal `update_file` corrected the error contract without weakening file checks, resulting in `7cebbbbd3e0915028a1aa447b0baf7511df8a49e`. Exact [#1734](https://github.com/Iam-2squared/ark-ai/actions/runs/41146607177) was **QUEUED** at the most recent check; no newer GREEN claim yet.
- PR #8 newest code [#1733](https://github.com/Iam-2squared/ark-ai/actions/runs/41146566038), HEAD `c3b11b2eaa4a908b6c8e6b3f58e14607adcc44be`, was **QUEUED** at the most recent check. Intermediate Actions runs are not evidence of final-head GREEN. Public standard CI only; no manual duplicate workflow dispatch.
- Independent local all-`pytest` and `ruff` were not run. A GitHub CI success is evidence for its exact trigger SHA, not proof of integrated runtime behavior.

## Immutable gates and limitations

- Memory v1 contract `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c` and Agency contract `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9` remain unchanged. Frozen V1/V2/Local UI/Launcher and protected V2 final-evaluation materials were not intentionally touched; an exhaustive new audit was not performed.
- Neither SQLite local transaction isolation nor path metadata inspection proves authenticated clock/time, consent, independent provenance, storage rollback prevention, cross-database atomicity or real-world exactly-once effects. No ToolBackend, notification, real Candidate adapter/weight generation, protected V2 final scoring, training, external compute or paid service was invoked.
- Both PRs remain Draft/unmerged. No Candidate promotion, frozen contract change or main merge.

## Next plan / 今後の方針

1. Verify exact latest PR #8/#5 source runs across all six Linux/Windows jobs; correct only well-supported failures using the normal GitHub Contents API.
2. Expand Memory/Planner coherent recovery snapshots and add explicit unknown-after-COMMIT manual resolution interfaces, **without** triggering WRITE replay.
3. Bind trusted-clock occurrence claims to durable, audit-before-action mock execution paths; harden deterministic permission/registry identity.
4. Prepare privacy-safe Personal Context consent withdrawal and expiry lifecycle, read-only Scheduler recovery, Observation fixture adapters, and V3 reproducibility/provenance checks. Real external actions remain separately gated.
