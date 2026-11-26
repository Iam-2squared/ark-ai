# Run590 — Non-UI provenance, source epoch, and privacy veto capacity

**Evidence collected:** 2026-11-03T20:51:52.029Z UTC (ordinary host clock; not authenticated time).
**Work-basis HEAD:** `6a7366ce9efa4de2c9532c0c4eb1764b1cedb038`.
**Last source/test HEAD before this note:** `1e3f429d38b1260eef61a2e4bcc81fddb27dc4fd`.
**PR:** [#8 Draft JARVIS foundations](https://github.com/Iam-2squared/ark-ai/pull/8) on `research/jarvis-foundations`. UI work remains paused.

## Package 1 — Synthetic proactive freshness preflight custody

- Source HEAD `8a0f6ba41348b767f7b9cf763a30d341434c1882` changes `src/ark/proactive_synthetic_freshness_review.py`.
- A caller-supplied retained witness integrity method is reentrant Python. Its original placement before source/receipt/policy capture could cause a new path/receipt/policy epoch to be accepted as the baseline. Pin exact carriers first, check after the callback, and invoke the independently captured original validator so a substituted no-op hook does not bless a corrupted witness.
- Test HEAD `dbf6ac084da2e6a2467964db48e08feeacc86a03` introduces 7 parameter-expanded offline cases: five preflight source/receipt/policy/retained drift attempts, one substituted-validator corrupted digest, one ordinary read-only/non-authorizing control.
- **Real CI failure observed**, not hidden: initial #41715585849 and #41715687310 failed Ruff I001 because the new import was unsorted. Corrected via normal Contents API at `bc72169fadbd695e11413c1c137ad77042168e2e`. This is a style-only, semantics-preserving repair; [CI #41715945371](https://github.com/Iam-2squared/ark-ai/actions/runs/41715945371) started for that fix. No duplicate manual workflow launch.

## Package 2 — Observation chain result input anchor

- Source HEAD `edb9d4a90c5f554bfdc0f94b263edc66ff95bb32`, `src/ark/observation_fixture_chain_review.py`, removes a constructor-result trust bootstrap: the expected output must come from the already validated source/privacy/envelope observations rather than fields read *from* a potentially mutated result.
- The exact-type/value/object-carrier check now runs immediately after construction and before/after each denial-only property callback.
- Test HEAD `f8f25c4f1eec9c99f405381684751a1a2528aa88` adds 7 synthetic cases: six reflected constructor carrier substitutions and one ordinary closed-chain control. This is not authenticated media capture, microphone/camera access, consent or backend integration.

## Package 3 — Personal Context revocation SQLite capacity

- Source HEAD `e9628b0fac1a16e60fccaf2a01e13b2c95b41c5e`, `src/ark/personal_context_revocation_review.py`, introduces shared `_MAX_REVOCATION_ROWS` for the existing validator and SQLite admission.
- Admission checks existing row count **inside the same `BEGIN IMMEDIATE` writer transaction** before inserting a new synthetic veto. Prevents 10,001st row from committing and stranding the next `_validate()` / restart, including racing writers.
- Test HEAD `1e3f429d38b1260eef61a2e4bcc81fddb27dc4fd`, `tests/test_personal_context_revocation_capacity_run590.py`, adds 3 synthetic cases: bound exhausted with retained/restart reconciliation, zero capacity, and two competing writers for the final slot. Revocation is still a *veto fixture*, not a user consent ledger, real deletion or data disclosure permission.

## CI/evidence and safety claims

- Prior exact work-basis [#41707766890](https://github.com/Iam-2squared/ark-ai/actions/runs/41707766890): **6/6 SUCCESS** at `6a7366ce9efa4de2c9532c0c4eb1764b1cedb038`. This green does **not** validate the new changes.
- New CI auto-launched by normal source/test pushes. [#41716234424](https://github.com/Iam-2squared/ark-ai/actions/runs/41716234424) corresponds to the third package test HEAD. **Record its actual final status separately; do not infer GREEN from previous runs.**
- 17 *authored parameter-expanded pytest cases* across three new test files, **not** 17 separately locally executed passes. No local full-repository environment was available in this invocation.
- Frozen Memory contract `b6e93821ecd69270a7634aceb20775dc36e9953c`, Planner contract `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`, and V3 Contract 1 `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` were checked unchanged. `main`, Draft PR #5, and paused UI Draft PR #9 remain untouched.
- **No** paid/external GPU, new paid API/service, real Candidate generation, protected V2 evaluation, UI/frontend changes, physical-PC work, ToolBackend execution, automatic replay or promotion, destructive operation or main merge. Hashes, SQLite rows and caller clocks are only local consistency signals. They are not independent signatures, trusted time, actor identity, user consent or external exactly-once execution.

## Next plan / 今後の方針

1. Read latest exact-head six-job Ubuntu/Windows CI, inspect any failure logs; fix only true source/test errors while preserving fail-closed behavior. Avoid equivalent manual reruns.
2. Continue restart-safe Memory CAS/COMMIT-UNKNOWN and Planner persisted FAILED/BLOCKED recovery on independent source paths.
3. Bind immutable registry identities to exact PermissionGate claims and audit-before-action occurrence fencing without enabling any live executor.
4. Preserve detached Personal Context privacy/retention guards and observation fixtures; V3 source/path approvals remain validation-only until separately authorized.
