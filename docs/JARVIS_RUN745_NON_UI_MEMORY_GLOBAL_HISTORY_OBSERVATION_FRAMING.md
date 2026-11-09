# ARK AI — Run745: Memory CAS global history and Observation NUL framing

**Scope:** Free-only, disconnected, non-UI foundations. This report records source and authored regression fixtures, not an ARK/JARVIS PASS, authenticated user consent, or a hardware measurement.

**Report saved at (UTC administrative wall-clock):** 2026-11-09T18:47:24.091Z

## Exact work basis and saved source

- Initial work-basis and prior GREEN checkpoint: `58b58acf31805620d0e4624aef17e04c24f4d18d`, CI [#42669128739](https://github.com/Iam-2squared/ark-ai/actions/runs/42669128739), six Windows/Ubuntu × Python 3.11–3.13 jobs completed successfully. It is NOT CI evidence for any new source.
- Draft PR #8, `research/jarvis-foundations`, remained open/unmerged. Four normal GitHub Contents API commits form the fast-forward source/test range, with terminal source/test HEAD `0c0e956d901ab2a4011401888e2b5ec38266b598`.
- Changed paths exactly: `src/ark/memory/generation_cas_outcome_review.py`, `tests/test_memory_cas_outcome_global_highwater_run745.py`, `src/ark/observation_fixture_chain_review.py`, `tests/test_observation_fixture_nul_framing_run745.py`. Commit comparison was performed before this report; no UI/frozen files changed.

## Package A — global Memory event high-water during CAS outcome review

- Source: `cf9eac68084a0a0ca68fd907b535a5afd2206131`. Added `_check_global_memory_event_highwater` inside the **existing SQLite read transaction** before a second target snapshot.
- Retained per-row event history can appear coherent when an **unrelated owner or namespace** has had middle or tail events deleted. The added aggregate `COUNT/MIN/MAX(event_id)` and `sqlite_sequence` check rejects event-ID gaps, lost tail, missing/duplicate/changed high-water rows. No data repair or mutation is performed.
- Test: `603f19dfd7fac6b104942017297465de6ba5c5de`, eight new cases: one normal cross-scope record and matching subsequent update, six distinct malformed foreign-history/sequence conditions, and one read-only/no-authorship check.
- Limit: an actor capable of a coherent database + `sqlite_sequence` rewrite can still forge a matching local state. This does **NOT** identify which writer committed, permit automatic retry, prove previous history outside SQLite, erase anything, or authorize actions.

## Package B — unambiguous closed observation chain labels

- Source: `bf3edbf8bb4a161982445ce0b5d1919ddba96efe`. The optional disconnected closed-chain reviewer now refuses NUL bytes in caller-supplied UTF-8 `source_id` and `privacy_scope`, **before reading envelope fields**.
- Its historical v1 chain fingerprint uses `DOMAIN + source + NUL + privacy + NUL + observation IDs`. Embedded NUL makes the provenance field boundary ambiguous; the strict reviewer refuses it without modifying the underlying ObservationEnvelope contract or changing the digest for already accepted NUL-free labels.
- Test: `0c0e956d901ab2a4011401888e2b5ec38266b598`, seven cases: six source/scope embedded-NUL variations and one normal two-scope deterministic separation/denial witness.
- Limit: local fixture identity and hash checks cannot authenticate a sensor/source, prove consent, perform multimodal acquisition, or grant dispatch.

## CI and evidence identity

- Source/test commits automatically triggered GitHub Actions CI [#42676523256](https://github.com/Iam-2squared/ark-ai/actions/runs/42676523256), [#42676599478](https://github.com/Iam-2squared/ark-ai/actions/runs/42676599478), [#42676749406](https://github.com/Iam-2squared/ark-ai/actions/runs/42676749406), and [#42676818862](https://github.com/Iam-2squared/ark-ai/actions/runs/42676818862); **in progress/queued at last run-specific inspection**. Exact source/test HEAD 6/6 GREEN and all 15 cases passing on Windows/Linux are **UNPROVEN** until their real job conclusions are read.
- No local full pytest, physical-PC GGUF validation, actual Windows handle/ACL/reparse testing, paid service, external GPU, live ToolBackend, Candidate generation, frozen V2 evaluation, or main merge was performed.
- PR #5 (`805b377697472268db02650a89c7a94b1c5337c8`) and paused UI PR #9 (`3b49048dd70eebcb6268299b9ecef4e301bbc0fd`) remained Draft/unmerged and untouched. Main `7a843f17eb96ed13d66f23b58b06406b3002e405` was untouched.

## Next plan / 今後の方針

1. Confirm exact-head Python CI on all six jobs. If failures exist, inspect real logs and perform the smallest normal-API semantics-preserving repair, without backdating GREEN.
2. Memory: strengthen retained independent global event witnesses, cross-scope CAS/ABA/expiry and manual-only post-COMMIT uncertainty; do not auto-retry ambiguous WRITEs.
3. Planner/Tool: persisted exact READ recovery/terminal propagation, immutable registry/type gates, crash-safe one-shot audit-before-action and disconnected/mock integration after lower-level exact-head GREEN.
4. Privacy/observations: source chain and retention/revocation replay; proactive scheduler provenance with explicit no-consent/no-dispatch boundaries.
5. Preserve frozen V1/V2/Local UI/Launcher and V3 approval/identity/evaluation gates; do not resume UI, trigger paid compute, or merge Draft PRs without authorization.
