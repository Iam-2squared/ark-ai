# ARK JARVIS Foundations — Run432 Independent Fault Matrix

Source-based engineering record saved at **2026-10-26 03:58:20 Asia/Tokyo/JST** (ordinary unauthenticated runtime clock). The source and tests are isolated offline fixtures; this document is NOT JARVIS PASS, verified consent, signed time, external-outcome attestation, or replay authorization.

**Work basis:** Draft PR #8 checkpoint `dd6c3a570cb9712dcdadc4031cba664b641845e6`, independently verified CI #1212 / run 40219049185: six Linux/Windows jobs SUCCESS at invocation opening. PR #5 remains separate Draft / NOT_PASSED and its protected V2 evaluation and Candidate gates remain closed.

## Four development work packages

### 1. Explicit in-memory observation fixture adapters

- Source `src/ark/observation_fixture_adapters.py`: commit `e3e325774eb87da78c4957fbb568f2adeca3aec7`.
- Tests `tests/test_observation_fixture_production_adapters.py`: `0c3b0de5f18f648faf2e6efa45ee0a330a5f4f23`, Ruff formatting fix `f0e496cb590aa06ef52617e8b6aa58663e09bb10`.
- Text/transcript and supplied image/screen bytes enter through exact-type fixture-only APIs. Raw inputs are hashed, bounded to 4 MiB, and never retained in `ObservationEnvelope`. Stable adapter IDs and explicit caller timestamps/privacy scopes bind identity. Synthetic parent-lineage review is possible without acquiring media or starting a sensor.
- Does NOT read disk, sample microphone/camera/screen, use network, prove capture authenticity, grant notification/Tool authority, or attest consent.

### 2. Memory original-scope read custody

- Source `src/ark/memory/sqlite_store.py`: `4483b266b6e21934c8f1a36cbee1dfa8a1138241`.
- Tests `tests/test_memory_get_original_scope_carriers_run432.py`: `16baab581ba2468210a7c78a999eb8970612920d`.
- `get()` now pins the caller's original owner/namespace carriers before opening SQLite and rechecks after connection, BEGIN, schema validation, SELECT, hydration, clock, expiry comparison and before return, including missing-row and `include_expired` paths. An equal-valued reflected carrier substitution cannot silently change the validated identity epoch.
- No Memory v1 SQL/schema, storage migration, personal-data erasure or external connection.

### 3. Two independent process competitors for one WRITE reservation

- Regression `tests/test_occurrence_cross_process_reservation_race_run432.py`: `c3e212c16aef13f70a8fd817d79a03f32bc67847`.
- Three disposable-SQLite competition cases: duplicate token with distinct occurrence, duplicate occurrence with distinct token, and duplicate both. Child Python interpreters rendezvous at a local start barrier, then race the normal `SyntheticOccurrenceStore.reserve_synthetic` path; the expected invariant is exactly one durable inert receipt and one rejected replay. Reopening the store must retain one token digest row; no backend is allowed to execute.
- Local SQLite uniqueness is not cross-database atomicity, signed human issuer approval, or real external exactly-once execution.

### 4. Personal Context bundle result custody

- Source `src/ark/personal_context_review.py`: `84a509cd243067fbc4cf120f88597dcab8d11b66`.
- Tests `tests/test_context_final_bundle_result_epoch_run432.py`: `b75b1a9fb44f7da8b929807d59121568d36e263c`, Ruff formatting fix `cc47895c4b1b1a85a6eb52201337bb886f9ba09a`.
- Pin selected context-item object and scalar carriers before the final bundle digest; verify selected items and the original coherent snapshot/policy after digest and constructor. Reject forged results, swapped equal strings/tuple carriers, rewritten personal content and late privacy scope/policy drift. Stable bundle construction remains ephemeral and no new consent/disclosure path is introduced.

## Test and CI discipline

Forty new parameter-expanded cases were submitted across the four packages (18 observation, 11 Memory, 3 multi-process occurrence, 8 Personal Context). Submitted case counts are not passed counts. Initial observation-test heads #1214–#1217 were **FAILED** from two Ruff E501 lines; the normal Contents fix at `f0e496cb590aa06ef52617e8b6aa58663e09bb10` corrected the lines without weakening semantics. Context-test head #1220 was **FAILED** from one Ruff E501 line; `cc47895c4b1b1a85a6eb52201337bb886f9ba09a` corrected that formatting. Preserve the original FAILED histories; never re-label them GREEN.

**Final four-package source/test HEAD at the time of this report:** `cc47895c4b1b1a85a6eb52201337bb886f9ba09a`. Its separate CI #1221 / run `40223600447` was **IN PROGRESS**, not yet six-job GREEN at the last sample. Its result, and the separate future technical-document/checkpoint HEAD CI, must be checked independently. Only CI logs can establish a full pytest count or Windows/Linux PASS. Do not launch equivalent manual reruns.

## Boundaries and next integration order

Frozen V1/V2/Local UI/Launcher evidence, Memory v1/ActionAudit v1 DDL, V3 Contract 1, protected final evaluation, and contamination/provenance/regression/reproducibility conditions remain unchanged. PR #5 must remain Draft/NOT_PASSED; its immutable materialized HF identity, 120/30 rights/contamination/human review and exact budget/hardware/timeout authorizations are still blocked. No paid compute, Candidate adapter/weights, credential, new service, physical-PC action, irreversible mutation, main merge, live Tool dispatch, notification or sensor access was initiated.

Prioritize exact-head CI closure; then independent SQLite crash/restart/partial-history WRITE holds, event and multi-process CAS coherence, privacy revocation freshness, and unauthenticated-clock/issuer deny-only contracts. Never auto-replay UNKNOWN/RUNNING or reserved PENDING WRITE results, infer cross-file SQLite atomicity, or promote draft foundation code to real-world execution.
