# ARK AI — Run697 non-UI Planner refusal phases and Memory event custody

All work is local-first, FREE-ONLY, disconnected and reversible on
[Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).
No real tool backend, model training, consent authentication, Candidate
weights, GPU compute, notifications, UI work or frozen V2 evaluation was run.

## Work basis and direct failure evidence

- Incoming checkpoint HEAD: `0039b23be1c6b611bf2a9aaccdfd6c5a4e5af9e4`,
  Run696, [CI #42423014899](https://github.com/Iam-2squared/ark-ai/actions/runs/42423014899).
- The incoming exact-head CI was independently observed **6/6 FAIL**.
  Ubuntu Python 3.11 log identified **three** erroneous assertions in
  `tests/test_mock_cycle_receipt_constructor_custody_run618.py` after
  **10,676 PASS / 1 SKIP**. The assertions conflated two very different
  refusal boundaries:
  1. A **preinstalled** forged receipt constructor/class is rejected
     *before* Planner commits RUNNING: root stays **PENDING**, no
     occurrence reservation, no audit, no backend.
  2. A SHA-256 replacement detected by the occurrence store is rejected
     *after* Planner commits RUNNING: root stays **UNKNOWN/RUNNING**,
     no occurrence reservation, no audit, no backend and **NO automatic
     retry**. Neither branch can treat a local mock marker as consent.
- Package A, commit
  `041a3e612a69f8ba676f35af14ee64bc9e04f047`, corrects exactly
  those three assertions and comments via the **ordinary GitHub Contents
  API**. It neither changes production behavior nor relaxes the refusal.
  [CI #42426161800](https://github.com/Iam-2squared/ark-ai/actions/runs/42426161800)
  validates that exact test fix; not inferred GREEN from an earlier head.

## Package B: independent WAL/CAS event-prefix regressions

- Initial test file commit
  `91c2706b1804d4c46f5107147f826024a4afc44d`:
  `tests/test_memory_cas_global_event_custody_run697.py`, **5 new
  parametrized cases** (2 independent-row coexistence, 3 whole-DB event-gap).
- The two valid cases share one SQLite database across two owner/scope
  identities, including equal source IDs. A second store advances the
  foreign record with its own exact CAS token. The first record's retained
  per-row token remains valid; a later update of the first row does not
  overwrite or attribute the second writer's work.
- The three negative cases delete the first, middle or final SQLite v1 event
  in a **disposable local fixture database**, then require opt-in generation
  observation and update to reject the inconsistent global event
  `COUNT/MIN/MAX/sqlite_sequence` high-water. The target row's old
  bytes are unchanged and cannot be treated as a valid independent event
  witness.
- The first exact-head [CI #42426245276](https://github.com/Iam-2squared/ark-ai/actions/runs/42426245276)
  **6/6 FAIL** at Ruff **E731**, before pytest, because the new fixture
  assigned a lambda instead of declaring a function. Package B correction,
  commit `5f5e59c8ff28a973f5dd4e580ec13bb0e9c3c69e`, changed only
  `clock = lambda: 100` to `def clock(): return 100` without changing
  test semantics. [CI #42426343426](https://github.com/Iam-2squared/ark-ai/actions/runs/42426343426)
  belongs to the corrected HEAD and remains to be attested independently.
- An event-gap check is **not** an authenticated event ledger, a signature,
  or protection from coordinated replacement/reindexing of both rows and
  event tables. A matching row cannot identify its writer or authorize a
  COMMIT-UNKNOWN replay. This test intentionally changes only disposable
  local SQLite fixtures; production storage and frozen Memory v1 are unchanged.

## Evidence limits and next work

All run IDs above are observed actual CI identifiers, never PASS projections.
The report and canonical checkpoint writes each generate separate CI HEADs;
the latest result must be checked independently and Windows/Ubuntu Python
3.11-3.13 must all be GREEN before declaring exact-head validation.

1. Confirm corrected Planner refusal and five Memory cases on their exact
   CI HEADs; diagnose any further failure from actual logs.
2. Continue coherent CAS/ABA/WAL/COMMIT-UNKNOWN and privacy-veto
   continuity; no ambiguous WRITE replay.
3. Extend Planner independent per-step durable READ evidence, restart
   UNKNOWN isolation, ToolRegistry-bound audit-before-action using only
   disconnected never-execute fixtures until lower-layer GREEN.
4. Keep PR #5 (V3), #8 (foundation), #9 (UI) Draft/unmerged.
   **ALL NEW UI/FRONTEND WORK PAUSED.** Protected V2 final evaluation,
   frozen V1/V2/Local UI/Launcher contracts, real Candidate generation,
   paid external services, new credentials and main merges remain blocked
   absent their separate authorized gates. Overall JARVIS/V3 **NOT_PASSED**.
