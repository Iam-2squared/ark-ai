# ARK AI Run938 — scoped due-page atomicity, corrupt preaction quarantine, Planner independence, private diagnostics

**Work basis:** Draft PR #8 / research/jarvis-foundations at
e60c65b592d94e0edeb42e5a8f33c227e30f4a2c (Run937 checkpoint).
**Scope:** four independent, non-UI regression packages. These are local
synthetic/disconnected tests, **not** authenticated authorizations, hardware
validation, or a JARVIS integration PASS.

## New code and precise invariants

1. **Memory due-page expiry**
   [78f01af5](https://github.com/Iam-2squared/ark-ai/commit/78f01af5965269f85306705deaab053218734e3a).
   Six parameterized cases in
   tests/test_memory_expiry_due_page_atomicity_run938.py check that a
   corrupted second due row in the same scope does not poison a healthy
   bounded first page; selecting both rows must abort the whole deletion
   transaction; repeated calls and cold reopen must not silently repair
   the row or append a false expiry event. Three SQLite BLOB fault columns:
   content, metadata_json, source_id.

2. **Atomic intent/audit quarantine**
   [794d1d71](https://github.com/Iam-2squared/ark-ai/commit/794d1d71920401edcb92fa5901147259ce9dc034).
   Four independent corruption cases in
   tests/test_atomic_preaction_corrupt_pair_quarantine_run938.py modify
   only a disposable local fixture's audit digest, intent chain, audit
   occurrence identity, or remove one local audit row. Constructor,
   retained-witness inspection and append must all deny. Rejected
   appends must not alter the damaged rows or create a new intent.

3. **Planner terminal/independent branch separation**
   [5fb9d76e](https://github.com/Iam-2squared/ark-ai/commit/5fb9d76ee8988790062c4a5b32f751d81624f192).
   Two parameterized FAILED/CANCELLED cases in
   tests/test_planner_isolated_terminal_branch_run938.py: a two-level
   failed branch is BLOCKED with correct derived revision updates; stale
   completions and forbidden child retries cannot change the status digest;
   an unrelated branch can still progress without changing topology.

4. **Personal Context private diagnostics**
   [9ea29606](https://github.com/Iam-2squared/ark-ai/commit/9ea296063bcf058d27e56a76fc1ee0928009d3ac).
   Four cases in
   tests/test_context_preview_private_diagnostics_run938.py cover a
   valid digest-checked synthetic preview and three failed variants
   (wrong content hash, wrong scope, expired fixture). Private fixture
   content must not appear in object reprs or denial exception text.
   Valid preview still has all four authority flags False.

**16 NEW parameterized cases AUTHORED (6+4+2+4).** All four packages
are test-only and preserve existing production source, frozen contracts,
historical evidence, UI PR #9, and main. A CI run starting is not test PASS.

## Verification and limits

Run937 checkpoint HEAD e60c65b592d94e0edeb42e5a8f33c227e30f4a2c:
[CI #44034230497](https://github.com/Iam-2squared/ark-ai/actions/runs/44034230497)
completed, all six Windows/Ubuntu x Python 3.11–3.13 jobs GREEN,
as inspected at Run938 start. This is prior-head evidence.

New committed test HEADs generated workflow runs:
[Memory #44041134252](https://github.com/Iam-2squared/ark-ai/actions/runs/44041134252),
[Atomic #44041196679](https://github.com/Iam-2squared/ark-ai/actions/runs/44041196679),
[Planner #44041257823](https://github.com/Iam-2squared/ark-ai/actions/runs/44041257823),
[Context #44041413536](https://github.com/Iam-2squared/ark-ai/actions/runs/44041413536).
They were IN PROGRESS / QUEUED when initially inspected. Their final
conclusions must be checked against exact source SHAs; the latest checkpoint
also triggers a new run after saving. **Do not infer latest-HEAD GREEN.**
No local full pytest run or physical-PC test was performed.

No paid/external compute, cloud GPU, Candidate generation/promotion,
protected V2 evaluation, real backend, user data, credentials, new account
connections, protected contract modifications, automatic retry of ambiguous
external effects, physical-device actions, UI feature changes or main merge.
This fixture exercise does not prove trusted clock, external consent,
independent audit custody, durable exactly-once external effects, or
cross-store atomicity. Draft PR #5 remains under its controlling approval gate;
PR #8 remains draft; PR #9 remains paused draft.

## Next plan / 今後の方針

1. Inspect the complete exact-HEAD six-job Python matrix. Investigate any
   failing job's actual logs; correct only via normal GitHub Contents writes
   and preserve fail-closed behavior.
2. Continue Memory expiry, WAL/SHM independent-process and generation CAS
   plus event-prefix coherence, particularly crash/last-close ambiguity.
3. Advance Planner persisted COMMIT-UNKNOWN/manual-only recovery and terminal
   projection; do not conflate in-process DAG tests with durable journals.
4. Develop independently verifiable exact-registry authorization, trusted
   clock, audit-before-action and mock-only execution handoff. No live tool
   dispatch until consent provenance and full integration gates are proven.
5. Continue privacy-safe Personal Context, proactive/observation contracts and
   free-only V3 guard reviews without UI or Candidate/training work.

**Overall ARK/JARVIS: NOT_PASSED.**
