# ARK AI — Run930 non-UI integrity and recovery work

**Scope:** disconnected/local-first non-UI work only. **Basis:** `496d7c28958b5b0e0bc2f2eb8fe37923ba5c6584` (previous Run929 canonical checkpoint). **Source/test completion:** `ed42ec27e143ee978bb827053d0b5907b72e8a5a`. Draft PR #8, `research/jarvis-foundations`. All content is synthetic; no external executor, physical PC, paid provider, approved human action, Candidate or protected evaluation is involved.

## Coherent packages authored (25 NEW parametrized cases)

### 1. Memory SQL-side TEXT admission (7 cases)

- Source change [`844af9ac`](https://github.com/Iam-2squared/ark-ai/commit/844af9acb4535183c6048dc376f2941c3cd35df2): The existing SQL-side bounded hydration query now computes an aggregate count of rows where `content`, `metadata_json` or `source_id` is *not* actual SQLite TEXT. Reject **before** `get`/`search` hydrate even a small BLOB/INTEGER/null-backed value. This is additional type validation inside the same existing read snapshot, not a schema migration or a change to MemoryScope/CAS semantics.
- Tests [`6457212f`](https://github.com/Iam-2squared/ark-ai/commit/6457212f22890fcaba9c1d7998af9f5ab41fb95a): 3 corrupted column variants × 2 independent read APIs = 6 denial cases, plus one valid UTF-8 metadata roundtrip. After rejection, fixture row type and single create event remain unchanged. No user Memory modified.
- Caveat: SQL-side admission and local SQLite quick_check do not prove authenticated provenance, prior write integrity, multi-process WAL/SHM custody or end-to-end privacy erasure. Only selected rows enter this preflight.

### 2. Planner recovery and terminal propagation (3 cases)

- Tests [`93b9679a`](https://github.com/Iam-2squared/ark-ai/commit/93b9679a45a1d2a6a3915f9cf7d3763bc5db4dd9) cover a four-step DAG with root → child → grandchild and an independent root. Repeated cold recovery of RUNNING must preserve one durable journal event and `ambiguous_running_steps`; no auto replay or dispatch authority. A terminal FAILED root must cascade BLOCKED to its descendants without rewriting the independent root. A pending dependent cannot be RUNNING while its parent is unknown; failed append must leave the event count unchanged.
- Caveat: `SyntheticPlanJournal` is a replay-only test fixture; a local hash-chain does not establish external completion or authorized event ordering. COMMIT-UNKNOWN still requires manual adjudication.

### 3. Observation private-content minimization (10 cases)

- Tests [`d5d49e9e`](https://github.com/Iam-2squared/ark-ai/commit/d5d49e9eae4c71dee9cb8783fd48af90f81a6a4a) verify five independent metadata changes alter `observation_id` while retaining the same SHA-256 of identical synthetic input bytes; no raw payload is carried into the envelope or its repr. Three disallowed payload shapes (empty, >65,536 bytes, mutable bytearray) and a hostile `__bytes__` carrier must not be accepted. A separate case retains direct ObservationEnvelope v1 NUL compatibility while optional fixture adapter NUL veto stays strict.
- Caveat: all bytes are synthetic, memory-only, no sensor access or real privacy/consent provenance.

### 4. Registry-bound WRITE gate limitations (5 cases)

- Tests [`ed42ec27`](https://github.com/Iam-2squared/ark-ai/commit/ed42ec27e143ee978bb827053d0b5907b72e8a5a) verify a READ registry's permission does not silently downgrade the same action when the registered effect becomes WRITE; different revisions and bound IDs are required. Three scope/expiry mismatch cases refuse READ. A WRITE local one-shot spent once cannot be spent twice within the same PermissionGate, but **can be reused after creating a new gate**, explicitly recording that the process-local mechanism is not durable approval and must not drive real effects. The synthetic backend raises if `execute` is ever called.
- Caveat: this test demonstrates a known missing persistence boundary; it does not solve restart-safe exactly-once authorization. No tool backend was intentionally invoked.

## CI evidence (observed at report preparation; not an exact-head PASS claim)

- Previous checkpoint [Run929 CI #43975296853](https://github.com/Iam-2squared/ark-ai/actions/runs/43975296853): complete success, **6/6 GREEN** on Windows/Ubuntu × Python 3.11/3.12/3.13, exact older SHA `496d7c28958b5b0e0bc2f2eb8fe37923ba5c6584`.
- [#43982606195](https://github.com/Iam-2squared/ark-ai/actions/runs/43982606195): Memory source/test `6457212f`, **IN PROGRESS**.
- [#43982795767](https://github.com/Iam-2squared/ark-ai/actions/runs/43982795767): Planner tests `93b9679a`, **IN PROGRESS**.
- [#43982925763](https://github.com/Iam-2squared/ark-ai/actions/runs/43982925763): Observation tests `d5d49e9e`, **IN PROGRESS / QUEUED matrix**.
- [#43983053876](https://github.com/Iam-2squared/ark-ai/actions/runs/43983053876): policy tests `ed42ec27`, **QUEUED**.
- **25 new cases AUTHORED, not yet validated at the newest SHA on all six CI jobs.** No complete local pytest was executed. Do not infer current-head pass from the last older GREEN.

## Frozen authority / blockers / next work

Frozen V1/V2/Local UI/Launcher contracts and evidence remain untouched. PR #5 protected Draft/unmerged; PR #9 paused Draft/unmerged. PR #8 Draft/unmerged, no main merge. No paid/API/GPU services, Candidate/weights/adapter generation or promotion, protected evaluation opening, new credential/connection, real tool action, irreversible operation, or frontend development.

**Known blockers:** WAL/SHM cross-process last-close aliases, Memory concurrent CAS/expiry/coherent event snapshots, Planner external COMMIT-UNKNOWN evidence, durable one-shot claims, independent consent/provenance and trusted-clock audit-before-action, real Windows/GGUF verification. Local mock code and fixture tests cannot grant authority.

**Next plan:** (1) close newest exact-head CI 6/6 or repair verified regressions without loosening gates; (2) disposable cross-process WAL/SHM failure repro, concurrent Memory CAS and row/event type rejection; (3) Planner durable unknown-result/manual-only recovery; (4) persist registry-bound occurrence and approval/audit custody, with disconnected mock backend only after lower-layer evidence; (5) continue privacy-safe Personal Context and free-only V3 preflight guards. UI remains paused.
