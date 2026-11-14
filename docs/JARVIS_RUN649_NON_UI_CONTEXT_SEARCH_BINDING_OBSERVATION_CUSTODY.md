# ARK AI — Run649 non-UI Context / Observation carrier custody

**Scope:** Three independent local-only, reversible, non-UI safety packages on Draft PR #8. No UI/frontend, real tool dispatch, physical-PC actions, paid API/compute, external GPU, new credentials, protected V2 final evaluation, Candidate training/promotion, or main merge. JARVIS is **NOT_PASSED**.

## Work basis and exact saved implementation

- Initial PR #8 work-basis HEAD: `d5cdfd923d749242e274b03e6593b1429464004b` (Run648 report); initially Run648 CI [#42150177666](https://github.com/Iam-2squared/ark-ai/actions/runs/42150177666) was IN PROGRESS, subsequently observed **6/6 GREEN**.
- **A — Synthetic Context lexical search:** `src/ark/offline_context_search.py`, commit `fd71255c5aa2c8c6f0a0d5ff683deee2ad1db350`, captures original slotted fields and lookup hooks of the outer search preview and nested hit carrier before reading synthetic private excerpts or constructing results. New `tests/test_offline_context_search_result_slot_custody_run649.py`, commit `6f7c30841dcf13a7a36ed510d2f58523f16cbb54`: **14 authored cases** (preinstalled/reentrant malicious descriptors, unchanged deny-only preview). Exact source+test [CI #42151453696](https://github.com/Iam-2squared/ark-ai/actions/runs/42151453696) **6/6 GREEN** (Ubuntu and Windows, Python 3.11–3.13) at later observation.
- **B — Personal Context request binding:** `src/ark/personal_context_request_binding.py`, commit `63028ad98527c4e0502fd14eb9dee3d3d487db2e`, pins input preview private JSON slot descriptors and result-binding descriptors and lookup/constructor hooks before reading private fixture text. Class-level authority check avoids executing replacement descriptors. New `tests/test_personal_context_binding_slot_preaccess_run649.py`, commit `39e2b336139d736526e2988044b2c2ccdc7f44a6`: **16 authored cases** (malicious slots before/during parse; unchanged content-free denial-only binding). Source+test [CI #42151745990](https://github.com/Iam-2squared/ark-ai/actions/runs/42151745990) IN PROGRESS at latest job observation; Ubuntu Python 3.11 GREEN, remaining jobs NOT YET VERIFIED.
- **C — Disconnected observation fixture:** `src/ark/observation_fixture_adapters.py`, commit `315446da42805f54d22566c14b5f22d22193e39c`, pins v1 ObservationEnvelope's field descriptors, original validator, constructor and lookup hooks before converting already supplied local text/binary fixtures. New `tests/test_observation_envelope_validator_slot_custody_run649.py`, commit `ff66b52ec1141566a646a917d52a46e29bac1350`: **10 authored cases** (preinstalled/reentrant executable accessors, normal content-minimized transcript). No camera, microphone, network or real observation ingestion.

**Total new authored regression cases: 40 (14 + 16 + 10). This number does NOT assert that those cases have passed on any unverified HEAD.**

## CI incident — earlier rejection changed legacy test diagnostics

- Observation-source [CI #42151893412](https://github.com/Iam-2squared/ark-ai/actions/runs/42151893412) on Ubuntu Python 3.11 reported **53 FAIL / 9,313 PASS / 1 SKIP**. Real job log showed older tests expecting constructor/validator-specific error messages while the strengthened original-class preflight rejected the compromised class earlier. This was not evidence of 53 distinct source-level authorization bypasses; the expected denial phase changed.
- Repaired using the **ordinary safeguarded GitHub Contents API**, without weakening the field/validator guards: source commit `1bf7d46efdd157cbd5d6fa8c9ae512d9ed5544af` separates import-original validator identity from the deliberately injectable postconstruction fixture validator and preserves meaningful early failure categories; older tests `tests/test_observation_fixture_constructor_custody_run608.py` commit `c16941fe399aab50e71a018e92cb627abd6c6807` and `tests/test_observation_fixture_pinned_validator_run479.py` commit `925ff0c98b68a5b6fc4a1a64d7a5e1c7d809dcad` now accept earlier fail-closed rejection without executing malicious callbacks.
- Latest source+test+repair HEAD before this report: `925ff0c98b68a5b6fc4a1a64d7a5e1c7d809dcad`. [CI #42152879253](https://github.com/Iam-2squared/ark-ai/actions/runs/42152879253) QUEUED at most recent scan; the exact-head **6/6 GREEN is NOT yet verified**. No duplicate workflow run was requested.
- Confirmed compare of work basis through repair HEAD: **9 fast-forward commits across exactly 8 files** (three modified non-UI source files, three new non-UI tests, two legacy non-UI tests). This report is a subsequent documentation-only change.

## Authority and evidence limitations

These are in-process synthetic fixture defenses against test-controlled reflection, not sandboxing against arbitrary interpreter access. A SHA-256, original class descriptor, synthetic owner digest or local timestamp **cannot authenticate actual consent, privacy revocation freshness, observation provenance, runtime identity, independent witness custody or exactly-once external effects**. No privileged connector, operating-system integration, real user Memory, camera/microphone access, automatic candidate promotion, or outgoing tool call is enabled.

V1/V2/Local UI/Launcher frozen contracts and evidence unchanged; PR #5 and PR #9 retain Draft/unmerged status, with **all new UI development paused**. No data-destructive action or account connection was made.

## Next plan / 今後の方針

1. Confirm latest repaired exact-head six-job CI; if FAIL inspect the actual failing job logs and make the smallest semantics-preserving correction, while working independent non-UI code only.
2. Memory: continue manual-only COMMIT-UNKNOWN, row/event-generation coherence, multi-handle CAS and retention/expiry/restart boundaries.
3. Planner: persistent UNKNOWN and terminal dependency propagation with no automatic replay of ambiguous WRITE effects.
4. Registry-bound PermissionGate + durable occurrence + audit-before-action offline integration, then Personal Context revocation and proactive observation readiness, always mock-first and free-only.
