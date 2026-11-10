# ARK AI — Run753 non-UI core: mixed recovery grammar, context search and retention custody

**Evidence boundary:** 2026-11-10 JST. FREE-ONLY, offline/mock-only, no UI changes, no paid/external GPU/API, no real Candidate, no protected evaluation, no physical PC action, no main merge. All new changes are on [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) `research/jarvis-foundations` through GitHub's normal Contents API. All identities below are repository-local; no actor, trusted-time, consent, durable permission or external-execution attestation is inferred.

## Exact work basis

- Independently fetched initial PR #8 head: `e247e16dfd3599af1b0702539cb2803e68a6a5ca`, Run752 checkpoint, with exact-head [CI #42733173991](https://github.com/Iam-2squared/ark-ai/actions/runs/42733173991) **COMPLETED SUCCESS 6/6** (Windows + Ubuntu, Python 3.11, 3.12, 3.13; finished 2026-11-10 01:22:59Z). This is evidence for the **old** head alone.
- Last source/test HEAD before this evidence report: `609ad05aabe466820c7604f24d53d8a18ca71abd`. On this HEAD, [CI #42739412122](https://github.com/Iam-2squared/ark-ai/actions/runs/42739412122) was **QUEUED** at the last read. Intermediate in-flight runs have different SHA and must not be treated as exact-HEAD proof.
- Main `7a843f17eb96ed13d66f23b58b06406b3002e405`; V3 Draft PR #5 `805b377697472268db02650a89c7a94b1c5337c8`; paused UI Draft PR #9 `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`: independently read **unchanged**, OPEN/DRAFT/UNMERGED. No frozen V1/V2/Local UI/Launcher/evaluation contract changed.

## A — Mixed Planner READ/WRITE recovery: immutable input grammar

- [Source `ac3dddfe6e7f08525de850fce8816da91660a62a`](https://github.com/Iam-2squared/ark-ai/commit/ac3dddfe6e7f08525de850fce8816da91660a62a): `src/ark/agency/disconnected_write_recovery_fence.py` pins the import-original plan/step/hash/reservation regexes, states and exact integer graph budget. The validator runs **before** executing `_PLAN.fullmatch` on a caller-supplied plan ID, and the same validator runs across existing per-step review epochs. A swapped matcher, expanded state grammar or elevated cap fails closed without laundering a synthetic WRITE claim.
- [8 authored regression cases `a62e364dab147b859877b4c72adfe745d09bfe48`](https://github.com/Iam-2squared/ark-ai/commit/a62e364dab147b859877b4c72adfe745d09bfe48): six grammar/budget rebinding cases, hostile matcher non-execution, normal reserved WRITE quarantine + over-budget/invalid-ID refusal. This remains detached synthetic classification: `READY_MOCK_ONLY` is never dispatch permission, `QUARANTINE_RESERVED_WRITE` is not an exactly-once outcome.

## B — Private Personal Context lexical fixture search: original byte-budget and codec boundary

- [Source `7f24b98388454ec934ac3ccfe79246bc8c652dd2`](https://github.com/Iam-2squared/ark-ai/commit/7f24b98388454ec934ac3ccfe79246bc8c652dd2): `src/ark/offline_context_search.py` pins original record/owner SHA matchers, domain, exact numeric size/time/row/query caps, hashlib/json/UTF-8 helper identities. Checks occur before owner/scope matcher use and at every retained source epoch, including after hash/serialization callbacks. An injected codec must not be called with local private search text.
- [13 new cases `fb10e848bd6cba6392f6ad15ba7ecbd802ac02da`](https://github.com/Iam-2squared/ark-ai/commit/fb10e848bd6cba6392f6ad15ba7ecbd802ac02da) exercise 8 grammar/budget variants, 1 malicious owner matcher, 3 replaced codecs and a normal no-export/no-consent result.
- The old mutation-in-hash test now expects earlier protective refusal rather than executing the poison callback: [`e2989d0428e202df1a84999ea8b53f5a54808593`](https://github.com/Iam-2squared/ark-ai/commit/e2989d0428e202df1a84999ea8b53f5a54808593). Existing constructor/slot callback tests keep their security checks but also accept this earlier refusal: [`e545c2e99f217be4962fa7bbe9cf017a0688b3e0`](https://github.com/Iam-2squared/ark-ai/commit/e545c2e99f217be4962fa7bbe9cf017a0688b3e0), [`549a7d4e79dfe1b584206e6745f31dd9ad3e2a58`](https://github.com/Iam-2squared/ark-ai/commit/549a7d4e79dfe1b584206e6745f31dd9ad3e2a58). No private data export, new live connector, or Memory consent asserted.

## C — Retention inventory: MemoryScope protocol custody before private SQLite scope fields

- [Source `71a0b0cc47069e5bf13e2ee5324f911e5a0c51e2`](https://github.com/Iam-2squared/ark-ai/commit/71a0b0cc47069e5bf13e2ee5324f911e5a0c51e2) at `src/ark/personal_context_retention_review.py`: import-time original MemoryScope class, owner/namespace field slots, constructor/attribute callbacks and retained clock bound checked **before the first private scope read**. Existing dual-veto read-only inventory and no-erasure/no-use-denial semantics are preserved.
- [7 new cases `bc629c8ef33ea8ccaf571c5d31d46d003a53abca`](https://github.com/Iam-2squared/ark-ai/commit/bc629c8ef33ea8ccaf571c5d31d46d003a53abca), with fixture correction [`609ad05aabe466820c7604f24d53d8a18ca71abd`](https://github.com/Iam-2squared/ark-ai/commit/609ad05aabe466820c7604f24d53d8a18ca71abd): 6 scope field/lookup/constructor injection cases plus enlarged clock bound. The in-process `MemoryScope.__new__` patch case was removed proactively because CPython slot monkeypatch restoration can damage unrelated tests (previous exact-head evidence). The source guard still pins `__new__`; only that hazardous same-process test mutation is omitted.
- No purge, privacy-veto override, actual user data retrieval or hardware verification.

**Total: 3 substantive source work packages, 28 newly authored parametrized/ordinary regression cases, 3 new test modules, 3 existing expectation updates, 10 normal per-file source/test commits.** These are authored/pushed, **not** a claim of exact-new-HEAD six-platform PASS.

## Independent free-only V3 read audit

On the separate, unchanged Draft PR #5 HEAD `805b377697472268db02650a89c7a94b1c5337c8`, reviewed `docs/v3/PRE_PAID_COMPUTE_GATE.md`, `docs/v3/HF_IDENTITY_REVIEW.md`, `src/ark/learning/runtime_guard.py` and `src/ark/learning/authorization_packet_verify.py`. Immutable 40-character Qwen HF Hub revision, materialized base/tokenizer hashes, 120/30 rights/provenance/human/contamination decisions, pinned runtime and llama.cpp bytes, exact GPU/VRAM/cost/time ceilings and explicit **separate** preflight/full-training approval remain unresolved. The project must not create Candidate weights, run preflight, purchase compute, open protected V2 or promote. The unapproved local review packet is not authority.

## Next / release blockers

1. Inspect current exact-head CI [#42739412122](https://github.com/Iam-2squared/ark-ai/actions/runs/42739412122) and eventual checkpoint-result CI separately. On failure inspect real logs and make only a semantics-preserving fix through the normal Contents API; previous six-job GREEN cannot validate new bytes.
2. Memory independent retained prefix/CAS/ABA and COMMIT-UNKNOWN cross-scope consistency, Planner synthetic durable READ and terminal recovery, exact ToolRegistry/PermissionGate identity and audit-before-disconnected-mock-action; connect only after lower-level exact-head verification.
3. Personal Context privacy/retention/revocation, proactive/observation fixture-only contracts, V3 no-spend guard review; no UI work. External authenticated clock, actor, consent, real hardware/GGUF, true durable exactly-once authorization, independent custody, and human-governed evaluation/promotion remain unproven.

**ARK/JARVIS/V3 NOT_PASSED.** This report is engineering evidence of source changes, not a claim of human review, execution permission or end-to-end integration.
