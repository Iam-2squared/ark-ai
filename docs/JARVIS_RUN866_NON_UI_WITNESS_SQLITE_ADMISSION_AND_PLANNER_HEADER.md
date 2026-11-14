# ARK AI Run866 — Disconnected Memory witness SQLite admission and Planner recovery header

Scope: **only non-UI, local-first, zero-cost, reversible synthetic foundations**.
No real backend/tool dispatch, consent, credential, training, model evaluation,
external action, protected/frozen contract change, Candidate promotion or merge.

## Package A — Memory local witness ledger

- Source commit: `d2dd86466dade40ac0cbcc412b057e741222ecf8`.
- New regression commit: `2c22ea5d4d3b36e67faf40616f1af957e0826e34` (**13 parameterized cases authored**).
- Files: `src/ark/memory/disconnected_witness_ledger.py`,
  `tests/test_memory_witness_sqlite_ingress_run866.py`.
- Refuses NUL paths and native-encoded paths whose longest SQLite journal
  sibling breaches 4096 bytes *before any filesystem inspection*. Refuses
  orphan, symlinked, nonregular and multiply linked `-wal/-shm/-journal`
  companion files during cold open or create. These are **lstat observations**,
  not a race-free directory-descriptor/SQLite-open identity guarantee.
- Inside the same SQLite transaction, count the exact one schema object and
  cap its SQL DDL at 4096 bytes **before Python catalog hydration**; retain
  exact original table DDL comparison. Inspect at most two quick-check
  diagnostics and fail closed on anything except one `ok` row.
- Legacy witness rows, digest domain, CAS behavior, schema version, max
  epochs, genesis and denial-only capability properties are unchanged.
- New tests include invalid path pre-lstat, orphan and nonregular sidecar
  fixtures, synthetic schema injection/oversized DDL and a deliberately
  bounded fake quick-check cursor. They are **authored, not physical-PC
  evidence**.

## Package B — Planner cold-recovery header

- Source commit: `a448ee745d0d782e03a7d6f6999a36f28cf3233e`.
- New regression commit: `00bab249231698a07675b626cd41f1579f97c4dd`
  (**4 parameterized cases authored**).
- Files: `src/ark/agency/planner_journal_review.py`,
  `tests/test_planner_header_bounded_recovery_run866.py`.
- Retained exact one-row header schema, but replaced unbounded
  `fetchall()` with `fetchmany(2)`: two rows suffice to reject ambiguity,
  while ordinary one-row recovery reconstructs the same durable DAG and
  event-history tail. Synthetic cursor tests cover zero, one, two and
  three offered header rows; no backend is executed and recovered RUNNING
  remains manual-only UNKNOWN.

## Evidence boundary, limitations and safety

- First observed work-basis HEAD: Run865 checkpoint
  `8c18d0805640f38fb30e3286781f9a22264d8406`.
- Run865 checkpoint CI `#43568663822`: Windows/Ubuntu, Python 3.11–3.13,
  **GREEN 6/6** observed before these source writes. Its GREEN cannot be
  transferred to new commits.
- New tests were authored through normal GitHub Contents API. A separate
  local SQLite-only probe confirmed an original Memory witness table
  has one schema object, 139 SQL bytes and a single `ok` diagnostic.
  **The probe is not full pytest/Ruff nor a six-job CI result.**
- Autonomous reattempt after COMMIT-UNKNOWN is forbidden. A clean local
  SQLite result does not prove independent custody, source authenticity,
  stable pathnames between lstat and SQLite open, the final WAL/SHM close,
  exactly-once external effects or trusted time. No real file erasure,
  imported private content or external tool execution.
- Frozen V1/V2/Local UI/Launcher interfaces/evidence unchanged. PR #5
  and PR #9 remain untampered; UI/Frontend work is paused.

## Follow-on priority queue

1. Certify *exact resulting HEAD* across six CI jobs; fix any failing
   diagnostic/fixture without weakening fail-closed behavior.
2. Strengthen witness row **prehydration** shape/size admission and
   adversarial SQLite sidecar race fixtures, but do not assert independent
   custody or authorize replay from local evidence.
3. Deepen Memory/ActionAudit COMMIT-UNKNOWN and WAL/SHM last-close tests;
   require manual disposition for uncertain external effects.
4. Continue Planner UNKNOWN terminal propagation, privacy expiry/revocation,
   proactive scheduling and observation offline contracts.
5. Integrate ToolRegistry → exact PermissionGate → durable occurrence →
   preaction audit → disconnected Mock Executor only after each lower-level
   exact-head GREEN; do not connect live actions.
