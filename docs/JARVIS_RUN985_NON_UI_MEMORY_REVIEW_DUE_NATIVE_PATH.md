# ARK AI Run985 — Memory lifetime reviewer and disconnected due-ledger native-path admission

**Branch:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), no merge. **Work-basis:** `56c9b3fe75771e9af82ddb08269920c047503229` (Run984 checkpoint). All work is isolated, free-only, offline/synthetic and non-UI.

## Package A — read-only Memory generation/ABA review

- [Production source `3c6f8e44`](https://github.com/Iam-2squared/ark-ai/commit/3c6f8e448d32bc3a7132314cacf61ba2f99c6e86); [tests `034c7fe2`](https://github.com/Iam-2squared/ark-ai/commit/034c7fe2bac6ea554f279ec1e40966ef76b6d368); [Ruff import-only refinement `7db350a0`](https://github.com/Iam-2squared/ark-ai/commit/7db350a0c207129249d5ff51cedba9381e91ccbd).
- Optional `review_memory_revision_reuse` now rejects C0/C1 terminal controls, Unicode bidi and invisible formatting controls in the exact owner, namespace, and source labels **before deterministic memory-ID hashing or SQLite access**. Normal bounded Japanese labels remain admissible. The frozen Memory v1 acceptance contract and database schema were not changed.
- `sqlite_sequence` may contain a forged second row for `memory_events` because its `name` field is not unique. The read-only reviewer now uses `LIMIT 2` and rejects duplicates without hydrating arbitrarily many marker rows; this matches the bounded scan already used by the opt-in generation-fenced writer.
- **44 newly authored cases:** 14 malformed controls × 3 identity positions, one multilingual positive, and one synthetic 1,500-duplicate SQLite marker fixture that asserts the exact bounded query and unchanged database count.
- Not a signed event chain, cross-process custody guarantee, permission, or safe CAS replay. Global append evidence can still be coherently rewritten by an attacker controlling SQLite.

## Package B — offline Proactive Scheduler due-reservation path

- [Production source `c697a1bc`](https://github.com/Iam-2squared/ark-ai/commit/c697a1bcf27c7f1f61120a303aae4be7c020517b); [tests `68095e1b`](https://github.com/Iam-2squared/ark-ai/commit/68095e1b44aabc982a2fc878decc94ac24c6ae44); [Unicode fixture-escape refinement `28f2a43b`](https://github.com/Iam-2squared/ark-ai/commit/28f2a43b52391ae072f144190cab1c087c5fff53).
- Detached `DisconnectedDueReservations` checks strict UTF-8 encoding, NUL, encoded native filesystem path budget and the longest `-journal` sidecar suffix **before any ancestor lstat, SQLite bootstrap, restart or private-path probe**. `os.fsencode` is pinned to the original local dependency before inspection. This closes the earlier character-vs-byte mismatch on multibyte paths while retaining ordinary Japanese fixture paths.
- **6 newly authored cases:** multibyte path overflow, Unicode surrogate, NUL separator, over-budget ASCII journal suffix, normal Unicode fixture and replaced filesystem-encoder rejection without callback invocation.
- Still only a lexical preflight; no atomic descriptor-relative storage custody, consent, trusted schedule clock, notifications, actual external READ/WRITE, or automatic replay.

## Validation and limits

- **Prior exact work-basis CI [#44461239304](https://github.com/Iam-2squared/ark-ai/actions/runs/44461239304): all six jobs SUCCESS**, Windows/Ubuntu × Python 3.11–3.13.
- Initial new test CI exposed **Ruff I001** in the Memory regression import block (failed at lint before pytest); the test import block was corrected in `7db350a0`. Do not infer newest-head GREEN until its own six jobs finish.
- Total **50 newly authored parametrized tests**, no deletion or relaxation of prior denials, no local full pytest, no real GGUF/PC/hardware evaluation.
- No work on UI/frontend Draft PR #9, gated V3 Draft PR #5, main, frozen evaluations/evidence or external compute. No authorization/credentials, billable actions, model training, Candidate creation/promotion, irreversible deletion, or executable backend tool effect.

## Next independent work

1. Certify exact latest HEAD CI and correct actual failures at the narrowest fixture/source path.
2. Advance Memory WAL/SHM path/open races, coherent expiry/CAS and COMMIT-UNKNOWN quarantine; maintain manual-only uncertain write review.
3. Planner restart, immutable registry and exact permission checks, durable single-use authorization and audit-before-action, offline mocks first.
4. Personal Context retention/erasure, proactive occurrence/replay guards, observation fixture contracts and free V3 reproducibility guards. UI stays paused.
