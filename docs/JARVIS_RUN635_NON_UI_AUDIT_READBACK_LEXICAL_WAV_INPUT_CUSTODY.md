# Run635 — Non-UI audit-before-mock persistence and offline input contract hardening

**Prepared:** 2026-11-05T22:54:42.034+09:00 Asia/Tokyo/JST (environment clock, **not** authenticated audit/consent time).

## Scope and source authority

- Repository `Iam-2squared/ark-ai`, Draft PR #8 `research/jarvis-foundations`; invocation work-basis HEAD `ec1f80db7a20632e12a1c587d96ddb9bd516f4db`.
- Its baseline [CI #42031913508](https://github.com/Iam-2squared/ark-ai/actions/runs/42031913508): all six Ubuntu/Windows × Python 3.11–3.13 jobs **completed success**. That GREEN applies **only to the previous Run634 checkpoint**, not these changes.
- Exact source/test writes use the ordinary guarded GitHub Contents API with fresh PR HEAD and file-Blob SHA checks. No local Git checkout/pytest/Ruff proof: runtime cannot resolve GitHub DNS. Test counts are **authored cases**, never inferred PASS.

## Package 1: Verify a NEW persisted pre-action audit row before mock WRITE success

Files:
- `src/ark/agency/synthetic_mock_action_cycle_review.py`: commit `3e90e3b64b5fc2a9681ebcfbd6fc52ee5eda1f7a`, Blob `bf24d73a3979ed57a0af6a52c4cfc6f129a59f9b`.
- `tests/test_mock_cycle_audit_durable_readback_run635.py`: commit `250d0508155e12036709f55cc707fbdde08d9d42`, Blob `ff6d010f8c4c80381dbeac1122331b827c7e7124`, **4 authored parameterized cases**.

Before calling `audit.append`, read the local append tip in bounded validated pages and pin that pre-audit watermark. After the append callback, require an exact **new committed** row with event ID equal to prior tip + 1 and every persisted identity/outcome/clock field equal to the returned event. Re-read again after optional link callbacks and before journal SUCCEEDED. A no-op/forged append result, replayed earlier audit event, or hidden post-commit readback must not produce a successful marker.

Tests exercise forged fresh receipt, reused previously committed row, hidden committed readback, and an unchanged local mock-only success. A failed check leaves the already-running/reserved synthetic WRITE **UNKNOWN/manual-only**, never rolled back across separate databases; no ToolBackend dispatch.

CI for source/test commit [#42038883464](https://github.com/Iam-2squared/ark-ai/actions/runs/42038883464) in_progress. Source-only intermediate [#42038776711](https://github.com/Iam-2squared/ark-ai/actions/runs/42038776711) in_progress.

## Package 2: Offline lexical search input descriptors

Files:
- `src/ark/offline_text_index.py`: commit `20d4df2292a688ea492d7db7c7fa495be0cb067a`, Blob `c851fccecf44ef13ac9446d111eab8bf3843d437`.
- `tests/test_offline_index_input_getter_epoch_run635.py`: commit `40bb6180d97ae99a9b5b5f5a8d881e1afe944c5a`, Blob `8316fb4fac0495af070d756a6427df75efc3d04e`, **11 authored cases**.

Capture import-original `OfflineIndexQuery` and `OfflineIndexDocument` dataclass init, exact slot descriptors and lookup hooks. Refuse altered definitions before reading caller-provided text, IDs or provenance-claim hashes, and revalidate after normalization/digest callbacks. Tests cover preinstalled query/document getters, a tokenization-time swap, and the deterministic content-free success path. This is an entirely disconnected text fixture; not authenticated source custody, disclosure authorization or a real Personal Context connector.

CI for source/test [#42039200316](https://github.com/Iam-2squared/ark-ai/actions/runs/42039200316) in_progress.

## Package 3: Offline WAV request/result field-slot custody

Files:
- `src/ark/offline_pcm_wav.py`: commit `d851ca006d2efaa160707c3212a4a5eae4829263`, Blob `819aa25d1ce8a6c1d4885fc29f746e444e7ea051`.
- `tests/test_offline_wav_request_slot_custody_run635.py`: commit `511f96d8bdb7297f3df9b77f105be8163fc7198a`, Blob `6e96b787150cf5595f9d2b1bd3e8a59124a6b932`, **11 authored cases**.

Validate import-original request fields/constructor/lookup hooks before the first private audio-byte field read; likewise verify result field-slot and lookup hook integrity before accepting read-only metadata. Cases cover preinstalled forged slots, in-digest late slot replacement, and an inert valid generated PCM WAV. No microphone, ASR, consent inference, playback, capture, or external transmission.

Latest source/test CI [#42039516042](https://github.com/Iam-2squared/ark-ai/actions/runs/42039516042) queued.

## Integration boundary and follow-up

- **Authorship total:** 26 parameterized regression cases, NOT 26 PASS. Latest exact-head all-six GREEN is **not claimed** until its jobs actually finish. No duplicate manual workflow dispatch.
- Existing `main`, frozen V1/V2/Local UI/Launcher evidence, V3 Contract 1 and PR #5/#9 branches remain outside this work. All PRs remain Draft and unmerged. **New UI/frontend remains paused.**
- Audit persistence is local SQLite validation, not tamper-proof custody, authenticated trusted time or a two-phase commit across journal/reservation/audit stores. An external side effect is neither requested nor attested. UNKNOWN WRITE/COMMIT remains **manual-only with no automatic retry**.
- No spending, paid/external GPU, credential/account connection, Candidate generation/training/promotion, protected V2 final-evaluation opening, physical-PC action, destructive/irreversible work or main merge. Overall ARK/JARVIS/V3 **NOT_PASSED**.

**Next:** confirm all-six CI on final source/test HEAD; repair any real fail minimally via guarded writes. After a GREEN evidence gate, consider durable journal **terminal SUCCEEDED readback** before returning a mock success and preserve cross-store UNKNOWN behavior. Continue Memory event/CAS/expiry coherency, Planner recovery, durable Authorization/PermissionGate identity, observation backend contracts, free-only V3 guard read-only review. Keep UI paused and frozen gates intact.
