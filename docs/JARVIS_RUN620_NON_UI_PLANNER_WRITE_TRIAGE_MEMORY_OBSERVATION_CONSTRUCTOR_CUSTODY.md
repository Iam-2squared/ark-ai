# ARK AI — Run620 / Non-UI local constructor custody

> **Status:** four reversible, disconnected source+test packages saved to Draft PR #8. Changes are not an ARK/JARVIS PASS, not real hardware/runtime validation, and not external authorization. This report records code/test authorship; only exact-head Actions job conclusions can establish remote CI validation.

## Work basis and invariants

- Work-basis: Run619 checkpoint `d764371ab685c1d11965e0398df3b5cb5f9946a2`.
- Starting Actions run [#41945600652](https://github.com/Iam-2squared/ark-ai/actions/runs/41945600652): verified **6/6 GREEN** (Ubuntu/Windows, Python 3.11–3.13), before Run620.
- Workstream: `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). No UI/frontend changes; PR #9 remains untouched and Draft. Frozen V1/V2/Local UI/Launcher contracts/evidence and main were not edited. PR #5 stays Draft and no V3 Candidate/preflight/paid compute was run.
- Scope: entirely local in-process class/constructor-code identity checks. Such checks detect Python runtime monkeypatching, **not** malicious code execution by an already-compromised process, trusted clock, authenticated consent, or external exactly-once outcomes.

## Package 1 — Planner recovery result, before SQLite

- `src/ark/agency/planner_journal_review.py`: pin the import-original `SyntheticPlanRecovery.__init__` alongside the deny-only descriptors and exact class identity. Original admission checking now rejects a class with a substituted initializer **before** `recover()` opens its SQLite read and before `append()` begins the local durable event. Revalidation in `_checked_snapshot()` also rejects a constructor replaced during a reentrant snapshot callback.
- `tests/test_planner_recovery_constructor_custody_run620.py`: **5 parameter-expanded cases authored**: preinstalled constructor for recover/append (2), changed constructor after legitimate snapshot for recover/append (2), unchanged RUNNING recovery remains manual-only (1).
- A rejected in-flight `append()` is not evidence that a prior independent external effect was rolled back. No real backend or replay.

## Package 2 — manual WRITE triage nested item, before constructor call

- `src/ark/agency/offline_write_manual_triage.py`: pin the original `OfflineWriteTriageItem` class and `__init__` in the existing deny-only authority verifier; check immediately before creating an operator checklist item. The read-only packet cannot execute a newly installed item constructor, even if that constructor would return an apparently safe item.
- `tests/test_manual_write_item_constructor_custody_run620.py`: **5 authored cases**: two preinstalled-attack cases (READ/WRITE); two reentrant child-review replacements (READ/WRITE); one original UNKNOWN WRITE checklist non-authority case.
- Local packet remains an investigation hint only; it neither proves a human review nor grants permission, dispatch, or automatic replay of UNKNOWN WRITE.

## Package 3 — Memory ambiguous COMMIT dual-observer result

- `src/ark/memory/ambiguous_commit_pair_review.py`: pin the original `MemoryAmbiguityPair.__init__` in `_require_original_review_carriers`, which is checked at function admission, throughout both observers and immediately before constructing the returned reconciliation receipt. This closes a case where a valid-looking deny-only result could execute a monkeypatched constructor.
- `tests/test_memory_ambiguous_constructor_custody_run620.py`: **5 authored cases**: preinstalled forged constructor with unchanged/matching row (2), replacement during either triage or outcome review (2), unchanged read-only reconciliation (1).
- Agreement between local SQLite observers does **not** authenticate the writer or justify a retry after ambiguous COMMIT.

## Package 4 — Observation fixture initializer

- `src/ark/observation_fixture_adapters.py`: pin import-original `ObservationEnvelope.__init__`; reject substitution immediately before constructing a fixture envelope (after reentrant content hashing), and check again following construction. Original `__post_init__` validation remains independently invoked; no camera/mic/screen acquisition added.
- `tests/test_observation_fixture_initializer_custody_run620.py`: **6 authored cases**: text/binary, preinstalled/digest-time tampering (4), replacement during post-init (1), normal minimal-content fixture (1).
- No raw media is included in result envelopes; SHA-256 fingerprints are not provenance, consent, or device identity.

## CI, reproducibility, and limits

- **21 new parameter-expanded test cases authored** (5 + 5 + 5 + 6), *not* a local pytest PASS count. Local clone was unavailable: the container Git client could not resolve `github.com`; therefore local `pytest`, `ruff`, and Windows physical-PC gates were not executed.
- Each source/test file was saved via the ordinary GitHub Contents API, after inspecting the latest PR HEAD before **each** write. No raw Git objects, ref rewriting, force-push, equivalent manual workflow reruns, or destructive operations.
- Distinct changes are independent, but CI was triggered by sequential GitHub Contents commits; early runs validate earlier heads only. During composition, Runs [#41950582015](https://github.com/Iam-2squared/ark-ai/actions/runs/41950582015), [#41950915816](https://github.com/Iam-2squared/ark-ai/actions/runs/41950915816), and [#41951097599](https://github.com/Iam-2squared/ark-ai/actions/runs/41951097599) were observed **IN PROGRESS**; [#41951521625](https://github.com/Iam-2squared/ark-ai/actions/runs/41951521625) was **QUEUED** for the last test source head. Final-head GREEN is **NOT** claimed here.
- No paid/external GPU/API or additional service, real Candidate/adapter/weight generation, protected V2 final evaluation, credential, private disclosure, actual ToolBackend action, main merge or PR #9 UI work.

## Follow-on priority

1. Verify latest exact source/test/report/checkpoint HEAD with all six CI jobs. Investigate real failures; preserve security semantics and fix only proven test/code inconsistencies through ordinary permitted paths.
2. Expand read-only Memory COMMIT-UNKNOWN row/event/CAS reconciliation and independent retained evidence. Always quarantine UNKNOWN WRITE, never auto-replay.
3. Join durable Planner restart with registry-bound permission, audit-before-*mock*-action and occurrence fences after lower-layer exact-head GREEN. Keep real backend dispatch disabled.
4. Advance backend-only Personal Context privacy lifecycle, proactive scheduler state and Observation fixtures; continue free-only V3 identity/approval/reproducibility guard checks without opening paid/protected gates.
