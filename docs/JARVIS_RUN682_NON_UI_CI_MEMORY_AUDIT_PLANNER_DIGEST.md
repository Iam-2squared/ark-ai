# ARK AI — Run682 FREE-ONLY / NON-UI core evidence (2026-11-07 JST)

## Scope and unchanged safety boundaries

All work in the existing OPEN/Draft/unmerged PR #8, `research/jarvis-foundations`.
Initial verified work basis: `735a3d504cc475668e9a0b63d9c75a1ea7967394`.
No UI/frontend work (PR #9 untouched), no main merge, frozen V1/V2/Local UI/Launcher
contract/evidence modification, protected V2 final evaluation, real external action,
hardware, credential, external compute, Candidate, or paid API. The tests use only
mock/disconnected execution and local SQLite fixture files.

## Package A — Exact incoming CI failure repaired (test-only)

Incoming checkpoint-head [CI #42353524151](https://github.com/Iam-2squared/ark-ai/actions/runs/42353524151)
failed **6/6**: Ubuntu Python 3.11 and 3.12 each reported **7 FAIL,
10,316 PASS, 1 SKIP**. All seven failures were inherited assertions in three
test files expecting a *late* "authority descriptor changed" exception after a
SHA-256 monkeypatch. Run681's stronger guard correctly rejects the replaced
digest primitive *before the callback ever runs*, with "mixed-plan digest
implementation or domain changed". The following normal Contents API commits
update exact failure expectations and additionally assert the injected digest
callback is **never invoked**. Production code and safety checks were untouched:

- `2ef6dab01f636212608878d7623fca84d45b4949`:
  `tests/test_mixed_recovery_false_descriptor_run599.py`
- `75799c7f33bfc4b73cf0d36b57cc408b049e4ba8`:
  `tests/test_mixed_recovery_pregetter_authority_run606.py`
- `744ec2f1b8d2109312a85ecb5b96b39a84692429`:
  `tests/test_recovery_original_constructor_boundary_run615.py`

[Automatic CI #42356857768](https://github.com/Iam-2squared/ark-ai/actions/runs/42356857768)
was **3/6 GREEN, 3/6 IN PROGRESS** at the last recorded sample. This was
not the final checkpoint HEAD and must not be represented as final GREEN.

## Package B — Memory CAS unrelated-scope noninterference

`16f616b25041f2aff608e83ce8278860cb529dd2` added
`tests/test_memory_cross_scope_cas_noninterference_run682.py` with **4 parameterized cases**
on independent SQLite handles: another owner creates, updates, or
deletes/recreates their own row; another source in the same owner/namespace
updates without changing the target lifetime. In all cases a valid target
generation token can still perform one local CAS while target row/revision
integrity, event ordering, and no-consent properties remain intact. This is
not historical writer attribution or real-world execution authorization.

Intermediate [CI #42356946765](https://github.com/Iam-2squared/ark-ai/actions/runs/42356946765)
identified **1 test-only FAIL**: in the shared-namespace case, the scoped
event list must of course include the legitimate target CAS append. The
assertion wrongly expected an unchanged *whole scope* stream. A normal
test-only correction `6218741852d853da3051ac8a8e654755dc1848f9`
asserts that the original scoped stream remains a prefix and the one new
event belongs to the target; other-owner scopes remain exactly unchanged.
**No Memory production logic was changed or weakened.**
[Corrected CI #42357208552](https://github.com/Iam-2squared/ark-ai/actions/runs/42357208552)
was in progress at the last sample.

## Package C — Audit gap isolation across independent tokens

`501467910b3f0a3163f7649504da5b1e77555914` added
`tests/test_offline_audit_independent_token_crash_gap_run682.py` with **3 cases**:
restart after a first token's reservation, after local audit append, or
after local link; a separately identifiable token may obtain its own inert
reservation while the original remains non-replayable. All local counters
and links are conserved; backend invocation is forbidden; no receipt
certifies actor consent, trusted clock, actual external outcome or a
cross-store atomic transaction. The audit-head intermediate CI inherited
the above Memory test expectation and is NOT independently GREEN evidence.

## Package D — Standalone Planner successful-READ correlation primitive custody

The per-step `review_synthetic_succeeded_read_correlation` is callable
without the already guarded all-step bundle. Previously, its local result
SHA-256/JSON implementation and byte-domain were not independently
pinned across caller-supplied fixture reads. The code now pins original
`hashlib`, `json`, `sha256`, `dumps`, and digest domain at import
and rechecks them before/after sensitive local steps; substituted or
equal-content different-object domain values are rejected before execution.

- `1221213fd6fa55bc0d357ea94b6aadf47d2d7cb3` — standalone
  `disconnected_planner_success_receipt_review.py` hardening.
- `7a4bb591c6d52ea34b382d2220dcf06bba71832a` — **6 new
  parameterized tests** added to `test_planner_registered_succeeded_read_correlation_run675.py`,
  requiring early rejection/no poisoned callback, then valid restored
  behavior with no backend dispatch. [CI #42357302815](https://github.com/Iam-2squared/ark-ai/actions/runs/42357302815)
  (source) and [#42357319890](https://github.com/Iam-2squared/ark-ai/actions/runs/42357319890)
  (source+tests) were queued/in progress at sampling. **Do not claim PASS.**

## Scope of evidence and remaining gaps

**13 new test cases authored (4 Memory + 3 audit + 6 Planner)**, plus
7 inherited CI cases repaired to assert stronger early rejection. All
nonterminal CI must be checked at its exact source/test HEAD after completion;
later checkpoint commits will have their own distinct run.

The fixture-only token, mock action, local hash, independently committed
SQLite ledgers and process-supplied clock **cannot prove** real consent,
provenance, independent actor identity, exactly-once external action,
cross-store atomicity, or trusted time. An ambiguous WRITE remains
quarantined without automatic dispatch or replay.

[Draft V3 PR #5](https://github.com/Iam-2squared/ark-ai/pull/5)
continues to require real approved dataset rights/provenance and immutable
Hub/tool identities, exact environment and distinct cost/preflight/Candidate
approvals. No authorization was granted or requested.

## Next / 今後の方針

1. Confirm automatic CI for the exact latest checkpoint HEAD across
   Ubuntu/Windows × Python 3.11–3.13; investigate any failures with job
   logs, then make minimal normal-path corrections, never a safeguard bypass.
2. Expand Memory CAS/ABA/expiry/COMMIT-UNKNOWN tests and coherent snapshot
   coverage across real independent SQLite handles without asserting
   ambiguous writer attribution.
3. Tie per-step Planner recovery evidence to registry revision and
   independent READ journal, keeping SUCCEEDED WRITE / UNKNOWN manual-only.
4. Develop disconnected authorization/audit-before-action, cancellation
   and privacy-safe personal context/startup/observation back-end without
   UI work, protected evaluator opening, GPU spend or main merge.
