# ARK AI Run956 — non-UI Memory mutation prehydration, WRITE restart fence, observation identity and proactive policy partition

**Recorded (ordinary JST report clock):** 2026-11-18T11:01:53.081+09:00. **Overall ARK/JARVIS: NOT_PASSED.** Only disconnected synthetic/free-only non-UI development. Report clock is not a trusted action/audit/consent time.

## Work basis, save chain and control constraints

- **Exact invocation work-basis HEAD:** `6ab217cae03c5a1eec2b21a6fbe7343d9dc2f5f8` (Run955 checkpoint, prior CI [#44211166343](https://github.com/Iam-2squared/ark-ai/actions/runs/44211166343) GREEN 6/6).
- **Target:** `research/jarvis-foundations`, Draft PR [#8](https://github.com/Iam-2squared/ark-ai/pull/8). The content below was saved through GitHub's normal Contents writes, without forcing branch refs. `main` untouched; V3 PR #5 and paused UI PR #9 remain Draft/unmerged and untouched.
- Frozen V1/V2/Local UI/Launcher/Observation-v1 and protected evaluation/training/contamination/provenance/reproducibility/human-review gates are not widened. No inference on the owner's PC, no real tools/dispatch, no paid compute or APIs, no external GPU, no Candidate creation or promotion, no protected V2 evaluation, no new accounts/secrets.

## Package 1 — Memory: SQL prehydration for deterministic-ID mutation targets

**Production change:** [`c36331d5`](https://github.com/Iam-2squared/ark-ai/commit/c36331d5553a2ef24d1411b7a3e8ae184ec023ca) adds `_require_memory_mutation_row_hydration_admission` to `src/ark/memory/sqlite_store.py`. Unlike `get()`, `put()` may select a row only by deterministic `memory_id`; `delete()` may miss a corrupt owner/namespace in its scoped WHERE. The new **same-`BEGIN IMMEDIATE` SQL-side primary-key preflight** bounds each target's TEXT fields, refuses BLOB types in TEXT fields and wrong integer storage classes before Python `SELECT *` materializes damaged persisted data. This is local defensive validation, **not proof of writer identity or event provenance**, and does not change the v1 schema, legitimate row encodings or API signatures.

**New focused tests:** [`f7140f9`](https://github.com/Iam-2squared/ark-ai/commit/f7140f9979ef5b4b8720019bc6cedf3efbf4f8f1) adds **9** cases: eight malformed owner/namespace/source/content/metadata/digest/clock storage variants that must reject both put and delete without appending an event, and one healthy Japanese Unicode create/update/delete roundtrip.

## Package 2 — Registry-bound WRITE and independent-process atomic pre-action

[`981f1ae`](https://github.com/Iam-2squared/ark-ai/commit/981f1ae3844b12feb06ca2b5b797c976bf2f375e) adds **4** focused tests: three local one-shot-token/occurrence replay orderings across a new process-local `PermissionGate`, plus one independent Python interpreter attempting to replay a previously reserved registered WRITE against a durable SQLite audit ledger. Assertions keep recorded rows and pre-action digests unchanged, exact registry-bound identity stable and the mock backend at zero calls. Even after a local permission check, an atomic pre-action record is **not** consent, a trusted clock, an external outcome, exactly-once external execution, or a right to retry ambiguous WRITEs.

## Package 3 — Content-minimized disconnected Observation

[`8d8e1f9`](https://github.com/Iam-2squared/ark-ai/commit/8d8e1f991244439145647249af0eacffba8ca07f) adds **24** synthetic-only observation identity cases, checking four media kinds against kind/source/privacy/timestamp/parent-hash partitions and differing payloads. Identical bytes have identical content SHA-256 but different provenance-bound `observation_id` when metadata differs. Neither `repr` nor returned envelope contains the raw test payload. **Frozen direct ObservationEnvelope v1 left unchanged**, and no image, microphone, screen or file was accessed. The first CI for this test uncovered an import-block Ruff I001; normal-path [`92864db`](https://github.com/Iam-2squared/ark-ai/commit/92864db76235b1a8961368555a1b6c59b1f57bf2) removes the extra blank after imports; no test assertions or contracts were weakened.

## Package 4 — Proactive rate-limit policy separation

[`4a71620`](https://github.com/Iam-2squared/ark-ai/commit/4a71620aafb616ce24f1b762cd26f41b70190351) adds **6** synthetic SQLite cases: independently varying owner/namespace/definition/policy revision while keeping source/observation digest constant must yield distinct prepared occurrence IDs without cross-policy rate-limit leakage; cold reopens refuse duplicate preparations; distinct source may produce a new digest-only marker only after the interval; same trigger cannot be reused after interval even on a reopened ledger. **No timers, real notification, external actions or authorization.**

## CI and bounded evidence, as of this report

- **Previous exact work-basis HEAD `6ab217ca`:** [CI #44211166343](https://github.com/Iam-2squared/ark-ai/actions/runs/44211166343) completed GREEN in all 6 Windows/Ubuntu × Python 3.11/3.12/3.13 jobs. This evidence does **not** validate Run956 changes.
- **Memory source `c36331d5`:** [#44218766357](https://github.com/Iam-2squared/ark-ai/actions/runs/44218766357), initial sampled Ubuntu 3/3 GREEN; Windows in progress.
- **Memory test `f7140f9`:** [#44218891173](https://github.com/Iam-2squared/ark-ai/actions/runs/44218891173), initial sampled Ubuntu 3/3 GREEN; Windows in progress.
- **WRITE recovery tests `981f1ae`:** [#44219139271](https://github.com/Iam-2squared/ark-ai/actions/runs/44219139271), initial sampled Ubuntu 3/3 GREEN; Windows in progress.
- **Observation first run `8d8e1f9`:** [#44219304763](https://github.com/Iam-2squared/ark-ai/actions/runs/44219304763) FAILED all six at Ruff I001 before pytest; minimal text-only repair `92864db` is a newer HEAD.
- **Proactive `4a71620`:** [#44219755708](https://github.com/Iam-2squared/ark-ai/actions/runs/44219755708) inherited the same observation Ruff I001 and FAILED before pytest.
- **Observation lint repair `92864db`:** [#44219967074](https://github.com/Iam-2squared/ark-ai/actions/runs/44219967074), **IN PROGRESS** on initial inspection. Exact latest source/test HEAD cross-platform GREEN remains **UNVERIFIED** at report save. Do not borrow prior green evidence or treat lint failures as execution results.

**Total: 43 authored test cases, one Memory runtime safety improvement, one lint-only correction.** This report does not claim local full pytest or all-six CI PASS. All synthetic hashes/rows/readbacks are local, untrusted witnesses.

## Prioritized Next plan / 今後の方針

1. Confirm the exact latest source/test HEAD's six CI jobs; inspect individual logs and repair concrete FAIL via normal Contents API, then switch to a nonconflicting backend lane during new CI.
2. Continue Memory WAL/SHM last-close concurrency, same-transaction target admission, stale generation CAS/ABA, event high-water, expiry/row snapshots. Frozen source schemas and valid behavior remain authoritative.
3. Deepen Planner COMMIT-UNKNOWN restart quarantine, immutable registry-to-PermissionGate exact binding, durable occurrence and audit-before-action, **mock-only** until cross-layer exact-head GREEN.
4. Work on privacy-safe Personal Context revoked-scopes, Proactive replay/retention and Observation non-capturing adapters, free V3 approval/path/identity guards. Any live tool, paid training, physical PC gate, protected evaluation, Candidate promotion, UI work or main merge remains separately blocked by the user's approvals.

**ARK/JARVIS NOT_PASSED.**
