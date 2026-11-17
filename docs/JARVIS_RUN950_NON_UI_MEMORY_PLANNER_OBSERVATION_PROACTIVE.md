# ARK AI Run950 — non-UI UTF-8 Memory, interleaved Planner CAS, Observation kind/time and proactive int64 guards

**Recorded at (JST, reporting wall-clock only): 2026-11-18T04:51:32+09:00**. **Exact work-basis HEAD:** `731bf6698c81a9b9f3f06737eeccf87f2a785b4f` (Run949 checkpoint). **Branch/PR:** `research/jarvis-foundations` / [Draft #8](https://github.com/Iam-2squared/ark-ai/pull/8). **Overall ARK/JARVIS: NOT_PASSED.** This report is not a trusted clock, consent, independent-custody witness or real-action authorization.

## Four coherent, independent non-UI regression packages committed via the ordinary GitHub Contents API

1. **Generation-fenced Memory UTF-8 identity admission** — [`ce8a75ef07fe2586d69f0f52ac8d35255664a898`](https://github.com/Iam-2squared/ark-ai/commit/ce8a75ef07fe2586d69f0f52ac8d35255664a898), `tests/test_memory_generation_utf8_byte_edges_run950.py`. **6** field/edge variants: 64/65 four-byte codepoints on owner and namespace (256/260 bytes), 128/129 on source (512/516 bytes), accept exact ceilings and deny over-limit opt-in CAS before row mutation. Check cold Memory baseline, event continuity and inert token denials. Frozen Memory v1 contracts/API/schema unchanged.
2. **Planner per-step revision CAS across independently interleaved roots** — [`78af5051d46a51b0f908045b72ae20a99ffcf134`](https://github.com/Iam-2squared/ark-ai/commit/78af5051d46a51b0f908045b72ae20a99ffcf134), `tests/test_planner_interleaved_revision_cas_run950.py`. **6** combinations (which root starts, SUCCEEDED/FAILED/CANCELLED terminal). A valid retained earlier *prefix* cannot make a stale expected revision valid after another root advances. Denial leaves journal tail/events unchanged; a correct revision may advance while the other RUNNING step remains ambiguous, with no dispatch/replay authority.
3. **Disconnected Observation identity separation** — [`8670d969b8d18b2525f01d651d78a6720609e9e1`](https://github.com/Iam-2squared/ark-ai/commit/8670d969b8d18b2525f01d651d78a6720609e9e1), `tests/test_observation_kind_clock_identity_run950.py`. **12** combinations (four kinds × two changed caller timestamps; four cross-kind pairs) verify identical raw synthetic payload digest and parent still yield distinct envelope identities under kind or time change, and never retain raw payload. No real media/device acquisition.
4. **Proactive recurrence int64 and boundedness** — [`2aa2e5fec203f0caba303bf6b8f5242f438ae0d0`](https://github.com/Iam-2squared/ark-ai/commit/2aa2e5fec203f0caba303bf6b8f5242f438ae0d0), `tests/test_proactive_int64_policy_edges_run950.py`. **10** cases: eight invalid clock arithmetic/bounds (including last-occurrence int64 overflow, count, grace and interval) plus two valid boundary forecasts at SQLite int64 maximum. Due labels remain non-authoritative and exhausted state inert.

**Total: 34 newly authored parametrized test cases (6+6+12+10)**; **no production-source, frontend/UI, frozen contract or evaluation changes**. Source inspection and tests are synthetic/local only; **no local full pytest or owner-PC GGUF execution**. Only exact-head CI can validate these tests on Windows/Ubuntu Python 3.11–3.13; their source-level expectations must not be represented as PASS before CI confirmation.

## CI evidence and immutable scope

- Prior checkpoint `731bf6698c81a9b9f3f06737eeccf87f2a785b4f`: [CI #44151579893](https://github.com/Iam-2squared/ark-ai/actions/runs/44151579893) **COMPLETED GREEN 6/6**, exact-head jobs independently inspected (Ubuntu/Windows Python 3.11, 3.12, 3.13); **previous HEAD only**.
- Memory `ce8a75ef`: [CI #44162667718](https://github.com/Iam-2squared/ark-ai/actions/runs/44162667718) **IN PROGRESS** at source-sampling time.
- Planner `78af5051`: [CI #44162741943](https://github.com/Iam-2squared/ark-ai/actions/runs/44162741943) **IN PROGRESS** at source-sampling time.
- Observation `8670d969`: [CI #44162809567](https://github.com/Iam-2squared/ark-ai/actions/runs/44162809567) **IN PROGRESS** at source-sampling time.
- Proactive `2aa2e5fe`: [CI #44162930536](https://github.com/Iam-2squared/ark-ai/actions/runs/44162930536) **QUEUED** at source-sampling time. Report and checkpoint writes yield distinct commits/CI that must be evaluated on their own exact hashes.
- **Latest exact HEAD 6/6 GREEN NOT VERIFIED.** No duplicate workflow run manually launched; no CI failure corrected without an actual failure log.

## Authorization and blockers

PR #5 remains Draft/unmerged under frozen Contract #1; PR #8 remains Draft/unmerged; paused UI PR #9 remains Draft/unmerged/untouched. main unchanged. Frozen V1/V2/Local UI/Launcher evidence, protected V2 final evaluation, provenance/contamination/regression/reproducibility and human-review gates untouched. **No** paid/external GPU, paid APIs/services/subscription, new credentials/account connection, real Candidate adapter/weight generation or promotion, actual tool backend, real multimedia capture, physical PC action, destructive action, protected evaluation opening, GitHub safety bypass or unapproved merge. A synthetic SQLite tail/clock/digest does **not** authenticate writers, establish trusted time/consent, prove erasure, or supply exactly-once external effects.

## Next plan / 今後の方針

1. Verify final exact-head six-job CI results; inspect concrete failing job logs and correct only narrow defects through the ordinary GitHub Contents API. Never transfer older GREEN status.
2. Continue Memory CAS/ABA and WAL/SHM last-close consistency with bounded event/expiry reads; preserve frozen Memory v1.
3. Continue Planner durable COMMIT-UNKNOWN quarantine plus immutable ToolRegistry/PermissionGate and one-shot authorization/audit-before-action, only after dependency-green evidence.
4. Continue Personal Context privacy veto/retention, Observation synthetic lineage and proactive cold-cursor state; free-only V3 path/identity guards without compute. No UI work. **Overall ARK/JARVIS NOT_PASSED.**
