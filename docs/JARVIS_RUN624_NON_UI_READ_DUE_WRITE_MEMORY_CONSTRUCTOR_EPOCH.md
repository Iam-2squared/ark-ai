# Run624 — disconnected READ, due-prefix, WRITE restart and Memory event-alignment constructor custody

Scope: **Draft PR #8, non-UI, zero-cost local/synthetic foundations only**. Work-basis
HEAD: `074002dc5a515c82a81c4e9f39376597446e2e0d` (Run623 exact-head
[CI #41964983388](https://github.com/Iam-2squared/ark-ai/actions/runs/41964983388)
**6/6 GREEN** at invocation start). No main merge, frozen-contract change,
paid service, external GPU, device access, actual ToolBackend dispatch, notification,
physical-PC action, approval grant, genuine identity/clock or external WRITE.

## Four independent guarded source-and-regression packages

1. **Registry-bound detached READ plan preflight**, `src/ark/agency/disconnected_read_preflight.py`
   blob `210878732872d41d0997b184718f5e7cb82ab9f5`. Its
   `DisconnectedReadPreflight` constructor identity is captured from the
   import-time class dictionary and verified before any registry-bound review,
   after policy/hash callbacks and before constructing the non-authorizing
   result. Four authored cases in
   `tests/test_disconnected_read_plan_result_constructor_custody_run624.py`
   blob `992713b7d2193e56be7bf2ac0cbf27d601989a33`: preinstalled
   malicious initializer, two digest-phase installations, inert baseline.
   Candidate test HEAD [#41969478774](https://github.com/Iam-2squared/ark-ai/actions/runs/41969478774)
   (CI was IN PROGRESS at earlier observation); this is not a production
   permission gate and never consumes a one-shot token.

2. **Proactive due-prefix retained witness**, `src/ark/agency/disconnected_due_prefix_review.py`
   blob `2961d42a4ed4e741f6e90ad872c47309c0044511`.
   Pins the result initializer; inspects denial descriptors through original
   `vars(type)` to avoid invoking substituted class-level `__get__` during
   review. Four authored cases in
   `tests/test_due_prefix_constructor_static_custody_run624.py` blob
   `c7d13a003ff7945f8bf2aca0b2d82e8f2de2ed69`:
   preinstalled constructor, hostile descriptor, reentrant SQLite snapshot
   callback and normal read-only baseline. Candidate test HEAD
   [#41969608604](https://github.com/Iam-2squared/ark-ai/actions/runs/41969608604).
   Retained witnesses are caller supplied, not independently authenticated;
   no notification or replay is authorized.

3. **Durable WRITE slot restart quarantine**, `src/ark/agency/disconnected_write_restart_binding.py`
   blob `fc6fa01d94c1dd9f18747b90bf5a69e8497aff3f`.
   Pins `OfflineWriteRestartReport.__init__` at import time, rejects
   preinstalled or reentrant replacement at entry/scan/final construction,
   and constructs from the bound result class. Original fingerprint domain
   bytes are preserved; an accidental escape alteration was corrected
   *before* creating the regression tests. Four authored cases in
   `tests/test_write_restart_original_constructor_custody_run624.py`
   blob `f2fbba06c91728efa1e254d80c474799b334161e`:
   preinstalled constructor, callback before SQLite review, SQLite scan
   mutation, baseline UNKNOWN WRITE quarantine. Candidate test HEAD
   [#41969820203](https://github.com/Iam-2squared/ark-ai/actions/runs/41969820203).
   No cross-store atomicity, external outcome authentication, safe automatic
   WRITE retry, or trustworthy historical authorship is claimed.

4. **Memory SQLite row/event reconciliation**, `src/ark/memory/sqlite_event_alignment.py`
   blob `d0d85b3d7d8ff4169d995339176c65f5e8ddc504`.
   Pins the original `MemoryEventAlignmentReview` initializer alongside
   the four preexisting deny-only descriptors. The reviewed SQLite schema,
   event lifecycle, AUTOINCREMENT high-water check and hashed content-free
   report semantics remain unchanged. Four authored cases in
   `tests/test_memory_alignment_original_constructor_run624.py`
   blob `c06dff695c1f5fa064e7691c357e8cab94c3c1ba`:
   preinstalled forgery, reentrant row/event charge, benign report.
   Candidate test HEAD [#41969974403](https://github.com/Iam-2squared/ark-ai/actions/runs/41969974403).
   Hashes/SQLite are not verified authorship, user consent, physical erasure
   proof, or a durable independent external anchor.

## Evidence limitations / no implied PASS

**Four source packages; 16 new parameter-expanded pytest cases AUTHORED, not
locally executed PASS.** Normal GitHub Contents API updates only; exact PR8 HEAD
re-read before *each* write; no raw Git objects, branch overrides, force-push,
duplicate workflow dispatch or unreviewed service connection. The working
container cannot resolve github.com for git clone; no local pytest/Ruff claim.
The last exact source+test HEAD and any later documentation/checkpoint HEAD
must receive **their own six-platform CI verification** before GREEN is claimed.
Incremental CI run ids are evidence only for their own exact HEAD.

Read-only inspection confirms PR #5 Draft HEAD
`805b377697472268db02650a89c7a94b1c5337c8`,
PR #9 Draft HEAD `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`,
and main `7a843f17eb96ed13d66f23b58b06406b3002e405`
unchanged at the audit. **UI feature/integration/test work remains PAUSED**.
Frozen V1/V2/Local UI/Launcher evidence and protected V2 final evaluation
unchanged; PR #5 remains Draft and pre-paid-compute blocked. **ARK/JARVIS/V3
NOT_PASSED.**

## Next plan / 今後の方針

1. Verify every latest exact-head Ubuntu/Windows Python 3.11–3.13 CI job;
   inspect actual failing logs and repair semantically, never poll duplicate
   equivalent runs or infer an aggregate PASS from intermediate heads.
2. Once exact lower-level GREEN is observed, prioritize Memory retained
   COMMIT-UNKNOWN row/event/CAS manual-only reconciliation, no automatic
   replay or consent inference.
3. Advance Planner durable crash recovery and detached/mock ToolRegistry,
   exact PermissionGate, occurrence and pre-action audit through isolated,
   reversible no-dispatch integrations, gated on dependency evidence.
4. Continue privacy-safe Personal Context, proactive state, observation
   fixture contracts and static V3 approval/identity/path guards in free
   lanes only. No new UI, Candidate promotion, external compute or main merge.
