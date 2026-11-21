# Run923 — non-UI WAL lifecycle, private context admission and revocation readback

**Development basis:** `9c0d43f0fb892d8113985f6941822db6bf6cc360`. **Branch:** `research/jarvis-foundations`, Draft PR #8, unmerged. **Prior baseline CI:** [#43913953014](https://github.com/Iam-2squared/ark-ai/actions/runs/43913953014) was observed GREEN at the original basis (Ubuntu/Windows × Python 3.11–3.13). This report is not an authorization grant or a JARVIS completion verdict.

## Source + regression packages — 31 cases authored

1. **Actual ARK WAL last-close diagnostic.** Source commit [`ed97362f`](https://github.com/Iam-2squared/ark-ai/commit/ed97362f4659795c95aa597d5e4bbbfd02178076), test commit [`fb5e0e07`](https://github.com/Iam-2squared/ark-ai/commit/fb5e0e0719106ddfc8de01159c0355d798b344d1). In `scripts/diagnose_ark_store_wal_last_close.py`, require the held SHM descriptor to be single-linked before child close, to be unlinked when the last client closes (or still linked while an explicit keeper remains), and to have no pathname after the final close. Reject a mismatch **before** a cold reopen can create a replacement sidecar; report `SIDECAR_LIFECYCLE_MISMATCH` rather than `OK`. Bound the CLI iteration string before integer parsing. Twelve injected descriptor-observation regressions across Memory/Audit/revocation and three oversized-input regressions; no real database or side effect.

2. **Private retained-context batch admission.** Source commit [`9a91601d`](https://github.com/Iam-2squared/ark-ai/commit/9a91601d01dbe27c333f37dd469d5dd6f1895c9a), test commit [`21e9adbb`](https://github.com/Iam-2squared/ark-ai/commit/21e9adbb98f13c9427a01fdcfb111a5a32294212). In `src/ark/personal_context_offline_preview.py`, enforce exact `OfflineContextFixture` entries and the 1–32 count and retained-record cardinality before allocating private snapshots or invoking the context rebuild. Five malformed inputs and one healthy synthetic retained-verification case; no private content exported.

3. **Independent synthetic revocation WAL evidence.** Source commit [`aa6f0eab`](https://github.com/Iam-2squared/ark-ai/commit/aa6f0eab85062ad10fb1b00e9b94d9b968234004), test commit [`8b602461`](https://github.com/Iam-2squared/ark-ai/commit/8b602461808ff3a9a56b03659802da57a2017383). In `scripts/diagnose_revocation_wal_processes.py`, preflight an exact two-object SQLite catalog and a ≤4,096-byte cumulative object identity/DDL budget via SQLite SQL **before** hydrating catalog or synthetic revocation rows. Nine malformed catalog outcomes must not enter the private row reader; one valid synthetic veto fixture preserves readback. Existing exact DDL, row and quick-check semantics remain.

## Validation limits and open risks

The 31 cases are **AUTHORED**, not automatically certified passed. The changed commits trigger the ordinary PR CI matrix automatically; do **not** infer a newest-HEAD GREEN from the prior basis. No local full ARK pytest matrix, target Windows GPU/GGUF, real personal-data ingestion or protected V2/V3 evaluation occurred. These isolated diagnostic/fixture checks are not a substitute for two-process WAL/SHM identity custody, replay-safe authorization, trusted-clock audit evidence or independent cross-store atomicity.

Preserve: frozen V1/V2/Local UI/Launcher contracts/evidence; unchanged Draft PR #5 and paused Draft UI PR #9; no changes to main, model/Candidate data, human-review artifacts, approval grants or real execution. No paid compute, paid APIs, purchases, credentials, secret connections or irreversible operations.

## Next plan / 今後の方針

1. Confirm the **exact** source/test/report/checkpoint HEAD six-job CI and isolate any failure to one non-weakening fix; leave other independent lanes available.
2. Compare actual WAL held-descriptor and cold-read outcomes for different keeper scenarios using disposable stores only. A failed last-close probe remains blocked, not auto-retried.
3. Advance Memory coherent CAS + event/expiry integrity, Planner cold COMMIT-UNKNOWN triage, and retained audit authority separately.
4. Integrate registry-bound immutable identity, exact PermissionGate, durable one-shot and trusted-clock audit-before-action only after matching lower-layer GREEN; keep disconnected mock execution separate from live tools.
