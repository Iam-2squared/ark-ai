# ARK JARVIS Run469 — READ readiness, Memory event results and schedule continuity

Status: **Draft / disconnected / non-authoritative**. This is a source-and-fixture
checkpoint, **not** a JARVIS PASS, authentication claim or permission to dispatch.

## Exact basis and saved code

- Entry work-basis PR #8 HEAD: `04492e3b6a4874f61928b996f55d1f4149c03a15`.
- Final source/test HEAD before this documentation: `5e67867be364900aed982916797c84c1d02d0d5a`.
- All changes were ordinary forward GitHub Contents writes, without force pushes,
  raw Git-object bypass, merges, external services or real Tool/OS actions.

### Package A — Registry-bound READ readiness review

- `src/ark/agency/disconnected_read_preflight.py`,
  blob `b1809da0d799dc8a42908ca2e8f355893108211d`.
- `tests/test_disconnected_read_preflight_ready_epoch_run469.py`,
  blob `222290e8b358999b6501b9631a941451a39d5037`.
- Exact, ordered ready-step carriers are now cross-checked against detached,
  authoritative plan states and successful prerequisites. Fabricated descendants,
  missing/duplicated steps, list results, clones and order changes are rejected
  before grant checks. This is diagnostic only; no backend execution occurs.
- Seven focused tests authored; their latest exact-HEAD CI remains to be checked.

### Package B — Memory v1 event result custody

- `src/ark/memory/sqlite_store.py`,
  blob `2ed441a90a9e80e1729cd4848fefc24262528a4d`.
- `tests/test_memory_event_result_custody_run469.py`,
  blob `de36f1e94d09dd03faed2fa2bb57735ea36c83bc`.
- The ordinary public `events()` reader now pins its original exact result class,
  the original SQLite row/MemoryScope field carriers and earlier returned events
  during later hydration callbacks. Forged classes, equal-valued replacement
  carriers and reflective mutation of an earlier event fail closed. The frozen
  Memory v1 schema, event ordering, clock rules, content exclusion, storage rows
  and existing mutation/CAS behavior are unchanged.
- Seven focused tests authored. The review is bounded to public `events(limit<=1000)`;
  this does not establish independent tamper provenance or cross-store atomicity.

### Package C — Recurrence preview and durable quarantine identity

- `src/ark/disconnected_schedule_preview.py`,
  blob `5810c5ae751fd828b624414b77357fbfb7ea8f1d`.
- `tests/test_schedule_preview_quarantine_bridge_run469.py`,
  blob `1f3a00684ff836fb03ac9bedd6c165d25b7cb0fd`.
- Pinned the original inert preview result class to reject a substituted
  authority-advertising subclass. Cross-component disposable SQLite fixtures
  now verify all three expired preview IDs match the quarantine ledger, survive
  re-opening with an independently retained witness, reject stale retained
  history, refuse nonexpired slots and reject another policy's occurrence ID.
- Five focused tests authored. Advancing the caller-owned synthetic cursor in
  a test is not a scheduler, consent decision, trusted clock or execution grant.

## CI and evidence scope

- Pre-invocation checkpoint #1478, run `40988864884`, exact earlier HEAD
  `04492e3b6a4874f61928b996f55d1f4149c03a15`: **COMPLETED SUCCESS, 6/6**
  Ubuntu/Windows Python 3.11–3.13. Earlier source HEAD #1476, run
  `40988304821`, also **COMPLETED SUCCESS 6/6**.
- Newly written source/test commits cause ordinary CI; the final new
  source/test run is **#1484, run `40993984716`**, exact HEAD
  `5e67867be364900aed982916797c84c1d02d0d5a`.
  It was **QUEUED/IN PROGRESS** at the latest source inspection; do not
  call new packages GREEN until this exact run completes successfully.
- 19 newly authored pytest cases across three packages. No complete local
  repository checkout was available due container GitHub DNS failure;
  do not infer local pytest/Ruff, Windows PASS or model/hardware evidence.
- The six saved source/test blobs were independently fetched and matched
  the SHAs above at the final source/test HEAD.

## Frozen boundaries, blockers and next priorities

Frozen V1/V2/Local UI/Launcher evidence, Memory v1 schema, Action Audit,
V3 Contract 1, historical provenance/contamination/regression rules and
protected V2 evaluation remain unchanged. PR #5 and #8 remain Draft/unmerged.
No real Candidate training/weights, paid/external GPU/API, real personal data,
new credentials, real system capture/action, promotion, evaluation opening
or main merge. All caller-supplied grants, timestamps, policies, witnesses
and digests remain unauthenticated and must not be treated as independent
permission or trust.

Next: verify exact-HEAD #1484 six-environment CI; fix only observed failures;
continue Memory CAS/expiry and retained history integrity, Planner durable
UNKNOWN WRITE quarantine, registry-bound trusted permission and audit-before-action
behind disconnected mock execution. Read-only PR #5 audit still leaves the
immutable HF revision/hashes, human-reviewed dataset/decisions, runtime identity,
GPU/cost ceilings and provider billing proof unresolved.
