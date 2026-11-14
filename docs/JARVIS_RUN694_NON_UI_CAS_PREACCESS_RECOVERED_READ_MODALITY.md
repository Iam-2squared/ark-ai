# ARK AI — Run694: opt-in CAS payload preaccess, Planner UNKNOWN receipts, and cross-modal observation lineage

**Scope:** Free-only, non-UI, offline/synthetic core safety work on Draft PR #8 (`research/jarvis-foundations`). Initial work-basis HEAD: `3a512e2e83bab7d0d3586857d91749d8296b70ec` (Run693 checkpoint). Baseline exact-head [CI #42409662127](https://github.com/Iam-2squared/ark-ai/actions/runs/42409662127) **6/6 GREEN** across Ubuntu/Windows × Python 3.11–3.13, independently checked before the new writes.

## A. Memory generation CAS: reflectively malformed proposed payload must fail before SQLite

The optional `generation_fenced_memory_update()` validated byte-encodability of content and JSON metadata but relied on `MemoryWrite.__post_init__` for original type, size, entry-count and expiry checks. Python frozen slots can still be reflectively replaced after construction. A malformed proposed content/metadata/expiry could therefore reach the private CAS transaction or trigger a non-domain exception. The **opt-in** CAS path now refuses:

- non-exact/blank or >1,000,000-character content;
- boolean, negative, non-integer or SQLite-range-overflow expiry;
- non-plain or >64-entry metadata mappings;
- non-exact, blank or >4096-character metadata keys and non-string or oversized values;
- malformed UTF-8 in content/metadata (the existing strict-encoding rejection remains).

This occurs before identity hashing, the `_connect()` path and `BEGIN IMMEDIATE`. Valid post-init mapping-proxy metadata, Unicode and the 64-entry / 4096-character boundaries remain supported. The frozen Memory v1 API/schema and its historical validation semantics are **not** modified.

- Source: `src/ark/memory/generation_fenced_cas.py` commit `28ada791edfc209ac88deb87c3f24311200f5879`.
- New tests: `tests/test_memory_generation_reflected_payload_preaccess_run694.py` commit `be743808d1953a32406ccfca8992e19641e92f68`, **19 parametrized cases**. Reject before hooked private SQLite and preserve retained CAS token/row/event; verify a later independently submitted valid local write still advances. Definitive *pre-transaction* rejection does not mean that a *COMMIT-UNKNOWN* write is retryable.

## B. Planner: no recovered READ receipt for an UNKNOWN or terminal sink

A pre-built offline READ fixture does **not** prove that its corresponding Planner step completed. New tests drive a four-step diamond through three succeeded ancestors and a RUNNING, FAILED or CANCELLED sink, then cold-recover the Planner journal. Only the three actually SUCCEEDED step-specific receipts may enter the synthetic READ bundle. The fourth detached fixture is rejected even though its bytes already exist. After the sink genuinely transitions to SUCCEEDED in the local journal, four separate receipts are required.

- Tests: `tests/test_planner_unknown_sink_receipt_exclusion_run694.py` commit `a7295c06f7d6116ecb9149e7433e56e40a626cbf`, **4 parametrized cases**. Backend execution count must remain zero.
- This is a recovered *local* journal/receipt consistency claim. No independent READ provenance, trusted clock or real WRITE execution is authenticated.

## C. Observation: duplicate digest across modalities is still ambiguous lineage

A different observation kind/adapter may produce a different observation ID for identical raw fixture bytes. New disconnected adapter tests establish that the closed-chain reviewer refuses a duplicate content digest across TEXT/IMAGE, TRANSCRIPT/SCREEN, and reversed ordering even if the parent pointer and timestamps appear valid. Distinct cross-modal payloads yield deterministic digest-only, denial-only reports with no raw fixture bytes.

- Tests: `tests/test_observation_cross_modal_digest_alias_run694.py` commit `a03169f0280784079d15a43b2eee9bf731ea596a`, **6 parametrized cases**.
- Import-spacing-only correction: `4c4c26faaa4d4ed7c45d8d812c310973c9a11834`. No safety condition relaxed. Camera/mic/screen acquisition, consent, capture-source authentication and real dispatch remain outside scope.

## CI evidence / accuracy boundary

- Baseline incoming Run693 [#42409662127](https://github.com/Iam-2squared/ark-ai/actions/runs/42409662127): **6/6 GREEN**, exact old checkpoint HEAD only.
- A source-only ancestor [#42412266129](https://github.com/Iam-2squared/ark-ai/actions/runs/42412266129): **3/6 GREEN and 3 IN PROGRESS** at recheck; cannot certify test-inclusive HEAD.
- B ancestor [#42412346372](https://github.com/Iam-2squared/ark-ai/actions/runs/42412346372): **1/6 GREEN and 5 IN PROGRESS** at recheck.
- C initial head [#42412453551](https://github.com/Iam-2squared/ark-ai/actions/runs/42412453551): **6/6 FAIL** at Ruff I001 because of one extra blank line before module constants in the new Observation test, before pytest.
- A test-inclusive predecessor [#42412604925](https://github.com/Iam-2squared/ark-ai/actions/runs/42412604925): **6/6 FAIL** for the same still-unfixed Ruff import-spacing error. No regression failure is inferred from these lint-stage jobs.
- Corrected source/test head [#42412680841](https://github.com/Iam-2squared/ark-ai/actions/runs/42412680841): **IN PROGRESS** (all six jobs) at last review. Its actual outcomes, this report HEAD and the eventual canonical checkpoint-result HEAD must be checked separately. Do not infer 29 new cases passed solely from prior commits or the absence of failure.

## Frozen gates, explicit exclusions and Next plan / 今後の方針

No modifications to `main`, frozen V1/V2/Local UI/Launcher contracts or evidence, protected V2 final evaluation, V3 Draft PR #5, or paused UI Draft PR #9. No external GPU/compute, billable API/service, model/Candidate generation or promotion, credentials, physical PC action, actual ToolBackend invocation, real notifications, user consent/approval fabrication, irreversible operation or merge. JARVIS/ARK/V3 remain **NOT_PASSED**.

1. Resolve corrected exact-HEAD CI, inspect precise logs if it fails, and make only ordinary Contents-API semantics-preserving fixes. Do not launch duplicate workflow runs.
2. Preserve opt-in Memory CAS/ABA/COMMIT-UNKNOWN and expiry/WAL row/event custody; do not attribute another writer's matching row to this caller or replay UNKNOWN writes.
3. Extend Planner independent durable per-step READ custody and restart-safe occurrence/audit-before-action mock integration; require separate authenticated consent/trusted-clock evidence before any live integration.
4. Continue privacy-safe Personal Context, proactive/Observation backend fixtures and free-only V3 path/identity/approval guards, with the UI paused and PR #5/#8/#9 all Draft/unmerged.
