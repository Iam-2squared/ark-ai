# Run452 — Private Fixture Diagnostic Surfaces and Bounded CI Runner

**Saved at (Asia/Tokyo/JST):** 2026-10-26T22:17:22.024+09:00 (ordinary unauthenticated wall clock; NOT trusted-time or user consent evidence).
**Starting basis:** `da20f0efda5f24737b453702360aff2d95a7b62e` (Run451 checkpoint).
**Branch:** `research/jarvis-foundations`, Draft PR #8, **unmerged**.
**Source/test + workflow HEAD at preparation:** `c19454666f61e4ed4d618b8acaf8fd842eeb9376`.
**Project status:** JARVIS **NOT_PASSED**, all frozen and protected boundaries unchanged.

## Package A — Private Context, local text and WAV accidental-logging guard

Ten sensitive dataclass fields across six existing, disconnected modules are now
`dataclasses.field(repr=False)`, without default values or altered positional
constructor parameters: `personal_context_offline_preview.py` (content,
canonical_local_json), `offline_context_search.py` (content, excerpt, query),
`offline_text_index.py` (text, query), `local_text_chunking.py` (both source
and chunk text), `offline_pcm_wav.py` (wav_bytes) and
`offline_context_redaction.py` (masked_text, which may still contain
unmasked sensitive content). **Count: 11 fields** (2+3+2+2+1+1).

Added `tests/test_privacy_sensitive_repr_run452.py` (blob
`e8234308a4aca34442203117dea2dcae2aeefe43`):
11 parametrized field checks plus four nested object/metadata-preservation
tests; positional constructors, explicit data access, and explicit
`dataclasses.asdict` intentionally remain unchanged.

These protections are only for implicit dataclass `repr`/`str` diagnostics.
They do **not** prevent explicit `asdict`, attribute access, serialization,
pickling, tracing of other objects, memory dumps, logs of direct payload
strings, or external disclosure. NO authenticated owner or privacy grant is
established.

## Package B — Detached Tool JSON and nested batch diagnostics

Seven sensitive dataclass fields across four existing, effect-free modules
are now `field(repr=False)`: `agency/disconnected_toolbox.py`
(request canonical_args_json, result canonical_result_json),
`agency/disconnected_batch_plan.py` (step canonical_args_json,
plan canonical_plan_json), `agency/disconnected_result_budget.py`
(result canonical_result_json), and `agency/disconnected_reference_binding.py`
(result canonical_result_json and bound canonical_args_json).

Added `tests/test_disconnected_tool_sensitive_repr_run452.py` (blob
`9c579267012e181767a42901981ac4606427feba`):
seven parametrized field checks and three nested fixture/retained-value tests.
The source still performs NO real registry dispatch, no permission approval,
no audit assertion, and no replay. No tool call or model was executed.

## Package C — CI fail-closed timeout against pathological Windows pytest logging

Only the Draft PR #8 workflow `.github/workflows/ci.yml` was edited
(blob `9e4f4e94ad0b4091d1e60cdb3b5de9f81d935954`):
`jobs.test.timeout-minutes: 45`. Six OS/Python cells and all original
lint, full pytest, JS, packaging and evaluation commands remain intact.
A timeout is a **FAIL**, never a pass or skipped test. It cannot affect jobs
already running under an earlier workflow definition.

Read-only job evidence:
- Historical #1237 / workflow `40233213149`, Ubuntu 3.11 job
  `121289190392`: **2931 passed, 1 skipped, 2 failed** (two
  `test_privacy_cross_process_veto_projection_run434.py` assertions).
  That expectation was previously corrected in Run448, but latest exact-head
  CI GREEN is still not available.
- Windows 3.13 job `121289190570`: `pytest` marked IN PROGRESS;
  fetched log length 4,217,219 characters with a multi-megabyte
  `test_fixture_rejects_oversized_payload[text-aaaa...]` node ID
  in error rendering. Run438's shortened-ID guard is on a later HEAD;
  it does not retroactively repair this old active job.
- Neither active jobs nor queued workflows were cancelled or duplicated.

## Validation scope and evidence gaps

- **10/10 changed source modules** confirmed at the repository branch: exact
  expected sensitive fields present as `field(repr=False)`; two new test
  files and workflow reviewed for line length <=100, correct imports and
  unchanged six-job matrix. All source/test content exists on PR #8 HEAD.
- Parametrized test definitions amount to **25 new test cases** if collected
  (11+4 and 7+3); this is **not a PASS claim**.
- Current working container cannot resolve GitHub to clone the full repo;
  local exact-source pytest and Ruff were **NOT RUN**. GitHub Actions remain
  **QUEUED** at inspection: #1354 / `40328636093` on
  `c19454666f61e4ed4d618b8acaf8fd842eeb9376`;
  workflow-change #1349 / `40328338734` on
  `a021b1d06a888756a1b5597377e6e26566089ef4`;
  previous #1342 / `40319249935` on Run451 checkpoint also QUEUED.
- Dataclass format shielding is an accidental-logging improvement only:
  no real user data loaded, no private database or recording opened. Human
  consent, provenance, revocation, trusted clock and external result identity
  remain unproven; no real ToolBackend is authorized.

## Next plan / 今後の方針

1. Verify the exact source/test HEAD, this doc HEAD and final checkpoint HEAD
   with six-environment GitHub CI as the queue drains. Triage any actual
   failures before integration; never turn a timeout into GREEN.
2. Treat all explicit `asdict`/JSON/pickle/export paths as **sensitive**,
   and review durable Memory/Personal Context privacy lifecycle next.
3. Continue independent Memory CAS and Planner recovery safety work; only
   connect previously detached Context/Tool/Audio components after the
   lower-level exact-head GREEN evidence and separate trust gates.
4. Keep PR #5 Draft/unmerged, PR #8 Draft/unmerged, frozen V1/V2/Local
   UI/Launcher/Memory/ActionAudit/V3 contracts and evidence unchanged.
   No protected V2 evaluation, Candidate generation/promotion, paid/external
   compute, new secrets/accounts, real-world Tool dispatch, irreversible
   operation or main merge. UNKNOWN/RUNNING/reserved PENDING WRITE remains
   quarantined and never auto-replayed.
