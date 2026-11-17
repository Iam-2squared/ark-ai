# ARK AI Run951 — Non-UI Integrity Regression Work

**Scope:** isolated, synthetic, local-only, zero-new-cost; test-only. No UI/frontend, new services, external GPU, real tool execution, credentials, Candidate generation, protected evaluation, or main merge. No frozen V1/V2/Local UI/Launcher/V3 contracts or evidence modified.

## Work basis and packages

Initial exact PR #8 HEAD: `b51240bcdb84859132748d27f3a6fa3b80e6a992` (Run950 checkpoint). That HEAD was independently checked through PR metadata. [Run950 exact-head CI #44163292990](https://github.com/Iam-2squared/ark-ai/actions/runs/44163292990): **6/6 GREEN**, Windows and Ubuntu Python 3.11–3.13.

Four independent test-only packages were written through GitHub's normal Contents API. Each successive write used a fresh PR HEAD comparison:

1. **Memory global foreign-scope high-water** `2b3ef6116cb9b1b8f52f9e64b08e40292e600dd9`, `tests/test_memory_foreign_highwater_fail_closed_run951.py`: **4** cases for a foreign event gap, duplicate AUTOINCREMENT sequence marker, rewound sequence, and advanced sequence. Both observation and subsequent CAS updates must reject altered global event history without changing the primary owner row. These are local corruption detectors, not authenticated custody.
2. **Atomic pre-action SQLite auditing** `21c3ac4f7c6ed2aaa873d6808dc6eeae6b269a15`, `tests/test_atomic_preaction_audit_corruption_run951.py`: **7** cases, including 6 corruptions of an otherwise valid intent/audit chain (missing or orphan audit, wrong occurrence, altered audit digest, altered intent request or chain). Recovery must refuse corrupt fixture rows without repairing/reinterpreting them or granting external authority; an intact cold prefix remains inert.
3. **Planner durable journal replay** `d64d0c1a6be5eb52d22fdbd03ff302de0a9d46ce`, `tests/test_planner_cold_journal_corruption_run951.py`: **7** cases, including 6 synthetically corrupted schema/journal/header/event fields and an intact RUNNING cold-recovery control. Historical corruption must be denied, while a recovered RUNNING state remains manual-only and not auto-replayed.
4. **Detached free-only V3 packet cross-binding** `28486379f3728f4b47df6c430d6357c7cf36ae61`, `tests/test_v3_detached_packet_mismatch_run951.py`: **10** cases checking device/capacity/tokenizer mismatches, VRAM ordering, timeout, nonexact boolean budget, precision-losing integer, canonical-byte enforcement and non-authorizing valid packet review. **No actual V3 hardware, paid compute, model weights or Candidate is used.**

**Total: 28 newly authored pytest parameterized scenarios, no production-core changes.** These cases must not be described as passing until their exact-head CI completes successfully. Tests are in independent domains; CI jobs were allowed to pipeline automatically, with no manual reruns.

## Boundaries and remaining risk

- All tokens, hashes, SQLite sequences, planner transitions, clocks, device identities, and media labels in these tests are synthetic. They do not establish independent provenance, human consent, trusted time, irreversible erasure, or exactly-once real-world effects.
- Corrupted SQLite fixtures are intentionally left corrupted for human/manual inspection; these tests exercise refusal, not automatic repair.
- All writes are on the isolated `research/jarvis-foundations` branch, Draft PR #8. Draft PR #5 (V3 gated) and paused UI Draft PR #9 must remain untouched and unmerged.
- The existing V1/V2/Local UI/Launcher frozen evidence and protected final evaluation remain untouched, as do billing, model, identity, training and promotion approval gates.
- Exact-head CI determines validation; any FAIL requires logs and the narrowest normal-Contents fix before claims of GREEN.

## Next plan

1. Verify exact-head Windows/Ubuntu Python 3.11–3.13 CI for the latest checkpoint and repair failures only after examining job logs.
2. Review Memory cross-scope WAL/high-water corruption handling and coherent snapshot/CAS expiry in safe, reversible workstreams.
3. Continue Planner COMMIT-UNKNOWN quarantine, durable approval/registry and audit-before-action without dispatch or replay.
4. Continue non-UI Personal Context privacy/revocation, proactive occurrence handling, multimodal observation fixtures and no-cost V3 controls.
