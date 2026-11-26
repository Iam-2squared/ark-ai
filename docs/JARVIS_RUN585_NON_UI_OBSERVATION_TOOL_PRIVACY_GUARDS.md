# ARK AI — Run585 non-UI foundational work and CI evidence

Work basis: PR #8 `c9892dedcdd7697857949642a4de53c17567c691`, previously verified by [six-job CI #41659242477](https://github.com/Iam-2squared/ark-ai/actions/runs/41659242477). All work is additive/reversible on Draft PR #8, not an integration or PASS declaration.

## Package A — Disconnected closed observation fixture lineage

- New `src/ark/observation_fixture_chain_review.py` blob `979b6b8d74cbf30dad899e291a506ce8bbcaf7d4` provides bounded, read-only verification of a **closed** sequence: exact v1 ObservationEnvelope values, one source/privacy scope, strictly increasing timestamps, first parent absent, subsequent parent equal to previous content digest, deterministic digest-only local receipt.
- `tests/test_observation_fixture_chain_review_run585.py` covers repeatability, parent/scope/source/chronology disagreement, non-tuple and unbounded input, reflected mutation, deny-only result, substituted authority properties. This is an optional strict reviewer; legitimate non-chain observation DAGs remain allowed by the unchanged v1 contract.
- The reviewer retains no content or raw media, never opens a device/database or authorizes a tool. The local lineage digest does **not** authenticate provenance, clock, privacy consent or independent historical custody.

## Package B — Disconnected fixture tool result must remain deny-only

- `src/ark/agency/disconnected_toolbox.py` blob `7de552090ac6541bf59afad0ad99a6af1976bf75` pins the original `DisconnectedToolResult` authority descriptors; checks them before caller input processing, at each epoch boundary and after every False getter. A reflective result mutation or a replaced always-False/True getter is rejected.
- `tests/test_disconnected_tool_result_denials_run585.py` covers unchanged fixture output and early refusal for all three authority fields, plus result-digest and later-descriptor corruption during a getter.
- Two existing higher-level disconnected batch tests expect their existing **typed wrapper denial** after early lower-level fail-closed validation. Only their message assertions were aligned; no permission or dispatcher source was weakened.
- These are disconnected in-memory calculations only. No backend or user approval exists here; no real-world exactly-once claim.

## Package C — Canonical masking proof for local private fixture

- `src/ark/offline_context_redaction.py` blob `e95868764a26171fb3c1889db198930fcb7d3616` now rejects modified or noncanonical JSON before hashing a supposedly reviewed masking/owner/scope/source descriptor. It parses the serializer output and compares it to the exact expected object and import-pinned canonical encoding, then rechecks the input epoch.
- `tests/test_offline_redaction_serialization_run585.py` covers a valid complete mask, forged owner/scope/source/result/span list, noncanonical whitespace, non-JSON/wrong types, and a serializer callback that mutates a frozen span.
- Complete masking is **not** authenticated consent, legal erasure, privacy export approval or proof the original source is gone. Partial mode still may contain source text and must not be exported.

## CI chronology and limitations

- Prior PR #8 exact-head six jobs [#41659242477](https://github.com/Iam-2squared/ark-ai/actions/runs/41659242477): **6/6 GREEN**, *before these changes*.
- Observation-source CI [#41666420473](https://github.com/Iam-2squared/ark-ai/actions/runs/41666420473) and test-head [#41666516686](https://github.com/Iam-2squared/ark-ai/actions/runs/41666516686): the latter reached Ubuntu pytest with 7,638 PASS/1 SKIP/4 FAIL. New test setup accidentally patched hashing before constructing its observation fixtures and accidentally coerced a list to tuple. Both test assertions were corrected, preserving source checks.
- Tool source [#41666680119](https://github.com/Iam-2squared/ark-ai/actions/runs/41666680119) and test [#41666766477](https://github.com/Iam-2squared/ark-ai/actions/runs/41666766477): the latter reached Ubuntu pytest with 7,645 PASS/1 SKIP/6 FAIL — the four above plus two old upper-layer error-message expectations. Both old tests were fixed to assert the existing typed fail-closed wrapper.
- Privacy source [#41667083208](https://github.com/Iam-2squared/ark-ai/actions/runs/41667083208) and test [#41667155874](https://github.com/Iam-2squared/ark-ai/actions/runs/41667155874): the latter failed Ruff on an invalid JSON-test string literal, fixed at `2acc8f9251f789b866abfdf336c9bca7593a6ade`. This is a test-only syntax repair; no masking semantics were relaxed.
- Newest source/test/fix HEAD **does not yet have six-job final GREEN evidence at note writing**; consult per-HEAD Actions, not historical green. New pytest definitions are authored cases, not independently executed local PASS metrics. No duplicate workflow was deliberately dispatched.

## Custody, frozen artifacts, free-only boundary

- Frozen PR #8 Memory `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c` and Planner `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`; PR #5 frozen `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` — independently checked unchanged.
- PR #5 `805b377697472268db02650a89c7a94b1c5337c8` and UI PR #9 `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` remain Draft/unmerged; main `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged.
- No new UI/frontend changes, real ToolBackend, notification, device capture, external compute, paid service, GPU, model/Candidate creation, protected evaluation opening, main merge, credential, irreversible erasure or user authorization inference.

Next: require final exact-head CI, fix only real failures, then prioritize restart-safe audit-first occurrence, durable authorization, Memory CAS/COMMIT UNKNOWN, Planner recovery and Personal Context retention/consent revocation. ARK/JARVIS/V3 remain **NOT_PASSED**.
