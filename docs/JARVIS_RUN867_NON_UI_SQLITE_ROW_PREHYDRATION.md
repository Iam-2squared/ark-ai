# ARK AI Run867 — non-UI SQLite persisted-row prehydration fences

Scope: zero-new-cost, disconnected, reversible non-UI ARK core. **NOT_PASSED**.
This report covers *three independent synthetic SQLite read-admission packages*.
No external side effects, real Personal Context, UI/frontend edits, Candidate
training/evaluation, paid resources, new credentials, protected gate opening,
frozen contract change or main merge.

## Verified repository basis and source commits

- Initial work basis: `3588e2fd124c5ab5fae9cff777179154311b33ba`
  (Run866 latest checkpoint; [CI #43573518079](https://github.com/Iam-2squared/ark-ai/actions/runs/43573518079),
  Windows/Ubuntu x Python 3.11-3.13 **GREEN 6/6** confirmed before work).
- Memory witness source: `573fba22a4feaa2a91b96294ab899e542111622c`,
  test commit `cb667c9c1d74f25bb66314c56ba9264c8d665cc4`.
  Source `src/ark/memory/disconnected_witness_ledger.py`, tests
  `tests/test_memory_witness_sqlite_row_admission_run867.py`.
  SQLite-side aggregate count, total/maximum payload native bytes,
  status/chain widths, and exact storage classes reject oversized or
  mistyped rows *before* the Python `SELECT seq,payload_json...` stream.
  **9 authored parameterized tests** cover UTF-8 byte-vs-character growth,
  overlong status/digest, BLOB variants, 257 rows and intact genesis.
- Planner recovery source: `5089269cdd75466779286f1504adbede9aa5dd7c`,
  test commit `4104ca215deab512432f5fb69631fee1e3372141`.
  Source `src/ark/agency/planner_journal_review.py`, tests
  `tests/test_planner_sqlite_header_event_preflight_run867.py`.
  In the same recovery transaction, reject incorrect persisted header
  hash widths or SQLite numeric types and oversized/mistyped event fields
  using SQL-side predicate probes. Check true event count <=10,000 before
  streaming event rows. Step ID byte ceiling derives from the *already
  admitted graph*, rather than inventing a new public PlanStep limit.
  **14 authored tests** include 6 malformed header and 7 malformed
  event variants plus unchanged RUNNING/UNKNOWN no-auto-replay behavior.
- Scheduler quarantine source: `3246a73e9f1d13f2802f71285c8321715b8b0171`,
  test commit `d0f8e40a6baca19f73c8fcd5138bb7d3b1ee2978`.
  Source `src/ark/disconnected_schedule_quarantine_ledger.py`, tests
  `tests/test_schedule_policy_sqlite_admission_run867.py`.
  A two-row SQLite cursor limits row count but not individual value size;
  SQL-side policy width/storage-class probe now denies oversized hash or
  malformed numeric columns before reading the policy row. **7 authored
  tests** cover six malicious columns and a normal restart.

**30 test cases AUTHORED, not yet claimed PASS at latest HEAD.**
Source and test blobs were independently fetched from GitHub after writes;
Python source line lengths remain <=100 on all three modified modules,
and new tests have line lengths <=100. This is a static review, **not**
full pytest, Ruff, host-Windows or model/GGUF verification.

## Trust boundaries retained

These checks protect Python hydration of *one local SQLite snapshot*.
They do **not** authenticate pathnames, WAL/SHM last-close continuity,
in-process callbacks, independent retained witness custody, trust the
wall clock, grant user consent, authorize context disclosure, restore
uncertain external effects, or prove exactly-once execution across stores.
No underlying SQLite schema, durable digest domain, Planner graph transition,
frozen V1/V2/Local UI/Launcher evidence, or approval rule changed.
Recovered RUNNING remains UNKNOWN requiring manual disposition. Quarantine
remains a denial-only preview; no notification or scheduled dispatch occurs.

## CI and evidence chronology

- Prior exact checkpoint HEAD `3588e2fd`: #43573518079 **GREEN 6/6**.
- New source/test CI auto-started for each ordinary Contents API commit;
  no duplicate or manual equivalent workflow dispatch.
- At report creation, incomplete/new exact-HEAD CI **is not inherited**
  from earlier source/test commits. Inspect each exact SHA and its six
  Windows/Ubuntu x Python jobs. The final report/checkpoint writes will
  each create additional CI and must be assessed separately.

## Next plan / 今後の方針

1. Inspect latest six-job exact-head CI and minimize any regressions
   without weakening prehydration gates. Keep independent lanes active.
2. Expand COMMIT-UNKNOWN and WAL/SHM last-client-close discontinuity
   probes for Memory and ActionAudit with disposable fixtures; no blind retry.
3. Strengthen coherent Memory CAS/expiry and Planner UNKNOWN terminal lineage.
4. Continue Personal Context retention/revocation and observation fixture
   backend privacy without exporting real sensitive data.
5. Connect registry-bound Tool identity, PermissionGate, audit-before-action
   and Mock Executor only after prerequisites are GREEN on exact HEAD,
   always with no live effect or automatic promotion.
