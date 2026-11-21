# ARK AI Run900 — Non-UI WAL aggregate, Memory persisted-JSON admission, Mock READ descriptor custody

**Observed report time (JST):** 2026-11-16T01:57:57.021+09:00. Timestamp is ordinary wall clock, not trusted action time, privacy consent, runtime provenance or payment authorization.

**Work-basis HEAD:** `a8ddb8ca05c9186a97cead490690cbc271d47fe7` (Run899 canonical checkpoint). **Complete source/test HEAD:** `8b539e153cbd57854db7391f4db7d42db511b8ed` on `research/jarvis-foundations`, Draft PR #8. PR #5 remains Draft at `805b377697472268db02650a89c7a94b1c5337c8`; paused Draft UI PR #9 remains at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`; main and frozen evidence remain untouched. **ARK/JARVIS NOT_PASSED.**

## NEW — three independent non-UI coherent source/test packages, 28 authored test cases

### 1. Synthetic privacy-revocation WAL result aggregation admission — 15 tests

- Source commit: [`2417774a`](https://github.com/Iam-2squared/ark-ai/commit/2417774a3058746766a28d2f1c3050a8434b1dcd); tests: [`98942dce`](https://github.com/Iam-2squared/ark-ai/commit/98942dce69d3b655da319a426fd469919e61b22f).
- `scripts/diagnose_revocation_wal_processes.py` now accepts only two exact child-category mappings with allowlisted status/phase combinations, and treats only exact `bool` as durable readback. Untrusted/incorrectly structured synthetic probe output becomes a bounded `INVALID_REPLY:UNKNOWN` anomaly instead of contaminating aggregate Counter keys with arbitrary payloads, false success or private strings. Preserves independent SQLite row verification and never retries refused sidecars.
- Tests substitute the diagnostic `_probe` callback without launching children, check 8 malformed responses, 6 wrong probe shapes or durability carriers, and 1 normal synthetic positive. No real personal scope, no user-context data and no consent or execution claim.
- **Limitations:** Synthetic statuses and `durable=True` are injected fixture values; tests do not prove genuine Windows last-close WAL/SHM custody or authenticated revocation.

### 2. Memory v1 persisted metadata JSON parser budget — 3 tests

- Source commit: [`c46cfc08`](https://github.com/Iam-2squared/ark-ai/commit/c46cfc0869d26af3b37ead1526b46fb623da17ad); tests: [`6d65bca8`](https://github.com/Iam-2squared/ark-ai/commit/6d65bca87f0c5cbd0c978a074360775ecdfca018).
- `src/ark/memory/sqlite_store.py` applies a conservative **3,200,000-character** metadata JSON cap before `json.loads` in the shared `_record` hydration path. This exceeds the frozen Memory v1 maximum of 64 entries with 4096-character names and values, including worst-case 6-character control escapes, without changing the schema or data API. Oversize corrupted persisted metadata is a `MemorySchemaError`.
- Two exact-on-disk corrupted-row cases exercise `get` and `search` without invoking the monkeypatched JSON parser; one control tests normal persisted metadata roundtrip and dense event record.
- **Limitations:** This bounds parser input *after* SQLite row fetch, not the bytes read by SQLite, globally shared memory or independent writer authenticity. Additional deep-parser/malformed-payload classification remains future work.

### 3. Detached READ mock result original-descriptor custody — 10 tests

- Source commit: [`be68fa32`](https://github.com/Iam-2squared/ark-ai/commit/be68fa321d693582308e9665a55b5e5aaa34fcb0); tests: [`8b539e15`](https://github.com/Iam-2squared/ark-ai/commit/8b539e153cbd57854db7391f4db7d42db511b8ed).
- `src/ark/agency/disconnected_read_tool_bridge.py` now checks the imported original `DisconnectedToolResult` slot/constructor/denial property descriptors with the toolbox's preexisting `_require_original_result_denials` guard, in addition to its original `DisconnectedToolRequest` guard, **before** traversing a mock receipt. Prevents compositional bypass of standalone result-custody checks via an installed Python descriptor. A replaced result-validator function is refused before invocation.
- Eight result field/denial descriptor fault cases, one replaced validator and one positive `math.sum` read-only fixture. No `ToolBackend`, real READ, WRITE, durable permission, consent or replay authorization.
- **Limitations:** Process-local Python identity tests cannot be an adversarial sandbox, backend attestation, durable exactly-once proof or real action permission.

## CI / evidence and free-only status

- Start-basis `a8ddb8ca05c9186a97cead490690cbc271d47fe7`: [Actions #43732648908](https://github.com/Iam-2squared/ark-ai/actions/runs/43732648908) independently verified **GREEN 6/6**, Windows/Ubuntu × Python 3.11–3.13. This proves only Run899 baseline.
- New source/tests automatic pull-request CI runs: [#43737127922](https://github.com/Iam-2squared/ark-ai/actions/runs/43737127922) WAL source; [#43737195909](https://github.com/Iam-2squared/ark-ai/actions/runs/43737195909) WAL tests; [#43737599564](https://github.com/Iam-2squared/ark-ai/actions/runs/43737599564) Memory source; [#43737655651](https://github.com/Iam-2squared/ark-ai/actions/runs/43737655651) Memory tests; [#43737989814](https://github.com/Iam-2squared/ark-ai/actions/runs/43737989814) READ source; [#43738180389](https://github.com/Iam-2squared/ark-ai/actions/runs/43738180389) READ tests. **IN PROGRESS/QUEUED during latest checks**, some intermediate Linux jobs passed. **Do not call the Run900 complete HEAD GREEN** until its *own* six jobs finish, nor count the 28 authored cases as certified PASS.
- Normal GitHub Contents API only; before each write read PR HEAD and checked expected SHA. No force-push, raw Git object bypass, duplicate CI reruns, main merge, new account, paid service, external GPU/API, hardware use, Candidate creation or promotion, protected evaluation, or UI/frontend change.

## Known blockers and Next plan / 今後の方針

1. Verify the exact complete source/test HEAD's six CI jobs; fix actual failures by normal path and avoid running an equivalent workflow twice. Overlap outstanding CI with independent non-UI audits/fixtures.
2. Isolate **Windows SQLite WAL/SHM last-close races**, durable-winner versus refusing-loser and true independent privacy veto custody. Synthetic path scans and row readback are not atomic open-handle proof.
3. Improve Memory corrupted metadata pre-SELECT admission/JSON deep-parser behavior, retained CAS/event continuity and cross-namespace coherent snapshots; preserve frozen v1.
4. Advance Planner UNKNOWN restart quarantine; only after lower-level GREEN, integrate immutable Registry, exact-type PermissionGate, pre-action durable audit, and disconnected Mock READ. Never auto-replay COMMIT-UNKNOWN or silently perform real WRITE.
5. Continue privacy-safe Personal Context, proactive/Observation backend fixtures and free-only detached V3 path/approval/identity validation without opening protected PR #5 gates. UI PR #9 paused.

**No PASS claim for integrated JARVIS, protected V2/V3, real model/PC, human-review or runtime identity.**
