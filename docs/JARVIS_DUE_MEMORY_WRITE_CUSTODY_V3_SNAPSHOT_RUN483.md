# Run483 — independent synthetic safety repairs (free-only)

This addendum records five independently reversible source/test packages on **Draft, unmerged** branches. These changes do not prove real-world execution, user consent, trusted time, independently authenticated history, physical-PC readiness, training authorization, or a complete JARVIS. No credentials, paid API/GPU, model weights, Candidate, protected V2 evaluation, tool dispatch, irreversible action or main merge was performed.

## Exact source and test identities

| Package | Branch | Source blob | Test blob | New authored parameterized cases |
| --- | --- | --- | --- | ---: |
| Due-slot restart observed witness | PR #8 | `src/ark/agency/disconnected_due_recovery_review.py` `edb697df3fd793b976d950313a550ddf8807c185` | `tests/test_due_recovery_observed_custody_run483.py` `186c871ff098eaa47b87c04ac5755a42fd50d5ba` | 7 |
| Memory retained-chain edge custody | PR #8 | `src/ark/memory/retained_epoch_chain.py` `1bb052e80d049ed929d037dd32e6d48e49b2e1ee` | `tests/test_retained_memory_edge_custody_run483.py` `7b0b60ed2c4d28e7d992eed0f08e836cefd37d15` | 6 |
| Durable WRITE slot receipt authority | PR #8 | `src/ark/agency/disconnected_write_slot_ledger.py` `209189379ca17659968bcb38f3bace1ab665da5c` | `tests/test_write_slot_receipt_authority_run483.py` `ff0fb98658795a015cb3dd89a0e8cd053e90752c` | 8 |
| V3 saved execution snapshot byte-budget | PR #5 | `src/ark/learning/run_manifest.py` `b249b1c153e7456e883f8a5bb003ecd30da80ef3` | `tests/v3/test_candidate_snapshot_bounded_read_run483.py` `8766e59c7ad4b5efdd4c5d79182cba4506578772` | 11 |
| READ fixture bridge binding/receipt custody | PR #8 | `src/ark/agency/disconnected_read_receipt_bridge.py` `6cd53c6c28ab2880a6f6bf56f3ed0cb91b0c68f7` | `tests/test_read_bridge_verified_custody_run483.py` `1e54a724ff9bde9e3224a9d120826a2dd64672da` | 7 |

Total **39 new authored pytest cases**, not a stand-in for executed CI evidence.

### 1. Restart due witness: prevent mixed review epochs

`review_restarted_due_reservations` now pins its *observed* exact witness identity and fields, as well as the earlier caller-retained witness. It rechecks both across JSON serialization, SHA-256, and the result constructor. A forged result cannot quietly cite an earlier hash while the observed object changes in a callback. Added 6 callback mutation cases plus a denial-only baseline. Does not authenticate the due clock or persisted writer, notify anyone, or authorize replay.

### 2. Memory: retain every per-edge comparison receipt

`review_retained_memory_chain` now keeps the exact original receipt and scalar carriers for **each** comparison edge until final return, even after subsequent comparisons or construction of the chain result. Forged earlier edge digests/status/counts/scope carriers are rejected. The historical prefix remains *unverified on append*; this does not alter frozen Memory contracts or grant disclosure.

### 3. Planner: local WRITE reservation is never an action grant

`DisconnectedWriteSlotLedger` now pins the original receipt/witness classes and verifies that all synthetic action, replay, outcome, time and consent authority properties remain false after a SQLite COMMIT. Postcommit detection intentionally does **not** claim a rollback; no automatic retry is allowed. The SQLite row may be committed even when constructing/validating its receipt fails. This is a local uniqueness fixture, not exactly-once proof of real-world effects.

### 4. V3: cap saved snapshot read before equality comparison

The Candidate run evidence verifier previously used unbounded `Path.read_bytes()` for its saved execution snapshot, while other JSON evidence was bounded. It now reads no more than `len(expected_snapshot) + 1` bytes after rejecting an over-1MiB expected canonical snapshot. Existing exact byte equality remains mandatory. This does not run training, inspect a real model or create Candidate output, and is not a hostile-writer-safe file-descriptor seal.

### 5. READ bridge: preserve the recomputed binding and original receipt class

The disconnected READ bridge now pins the original `ReadReceipt` class and independently retains every recomputed fixture-binding carrier through construction and return. It rejects a substituted compatible-looking receipt or a binding edited by the receipt constructor, even if the original request/result remained unchanged. This does not invoke ToolBackend, grant external action authority, or bypass the detached journal's CAS/replay fence.

## CI provenance (as observed during authoring)

- PR #8 four-package **source/test** HEAD `07816a2d01320c2b16bcc3271d0a6a54f1cc743a`; CI run #1655 / ID `41093907124` **IN PROGRESS** on last read (superseded source baseline). The **five-package final source/test HEAD** is `298ad1cb28a8cb5d53d328c95d2a342c20209134`, CI #1658 / ID `41094569246` **QUEUED**, not GREEN.
- PR #5 final **source/test** HEAD `d8669d3bb45d8cd766123bdd6536fbec8664eba5`; CI run #1651 / ID `41093316371` **six-job GREEN**, Ubuntu+Windows Python 3.11–3.13 individually verified.
- Prior checkpoint HEAD `3683f5a8e9eb055e3ba860bd40d4c94194f47d35`, CI #1647 / ID `41085199568` **six-job GREEN**, historical baseline only.
- Independent local whole-repository pytest/Ruff **NOT VERIFIED**: the local git clone cannot resolve github.com. GitHub CI is the available execution evidence; no equivalent workflow reruns were manually triggered.

**Frozen identities re-read unchanged:** Memory sqlite_store `0aba6392b39563df520aa8b378d0b313f0cc0a0d`, Memory contracts `b6e93821ecd69270a7634aceb20775dc36e9953c`, Agency contracts `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`, V3 CONTRACT.md `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`. Preserve earlier V1/V2/Local UI/Launcher evidence, PR #5 Draft/unmerged and all protected evaluation/promotion/merge gates.

## Next plan / 今後の方針

1. Resolve exact-head PR #8 source CI; on failure inspect actual job logs and make the smallest normal-Contents-API fix without weakening boundaries.
2. Extend independent custody and crash recovery for Memory history, Planner UNKNOWN WRITE reconciliation, audit-before-action / trusted-clock evidence and occurrence anti-replay, while all mock outputs remain non-dispatchable.
3. Keep Personal Context privacy/expiry/revocation and offline Observation fixtures separate from live data or microphones.
4. Continue free-only V3 path/file/approval/reproducibility checks; never infer training/Candidate/paid-GPU authorization from synthetic evidence.
