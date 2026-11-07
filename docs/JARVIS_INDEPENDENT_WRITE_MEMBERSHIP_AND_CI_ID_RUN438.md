# Run438 — Independent Expected WRITE Membership and Pytest Node-ID Guard

**Status:** Draft PR #8, isolated local-first proof / test changes; complete JARVIS **NOT_PASSED**.
**Work basis:** Run437 checkpoint HEAD \`71870e40d9b8a89c86bef9b121934a6ac2edcc99\`.
**Source implementation HEAD:** \`fb4c912415aa492e57b1e1cc6f84404ab64f1b96\`.
**Membership regression HEAD:** \`da9820c259ddef3f32f9a639f140387581fc13b2\`.
**CI-guard regression HEAD:** \`7f819a32227093cf91c315793933a3372a8768a7\`.
No real ToolBackend, authorization, protected evaluation, training, subscription or paid compute was used.

## Package A: genuinely independent complete-WRITE list witness

New \`src/ark/agency/synthetic_expected_write_membership_review.py\` provides
\`capture_expected_write_membership\` and \`assert_expected_write_membership\`.
It operates **without importing the still-unvalidated Run434 detached bundle**,
SQLite, a clock, a registry or an executor. The caller must retain a complete,
sorted tuple of WRITE step IDs and a \`plan_[0-9a-f]{64}\` topology digest
**from the independently held original plan**, not from the recovery archive.

The witness uses explicit SHA-256 domain separation, exact types, a maximum of
128 steps, a 256-character per-ID limit, and a 40 kB canonical representation
budget. The comparison rejects missing, extra, unordered, duplicated or
cross-topology WRITE IDs. A fabricated digest or reflected witness replacement
during validation is rejected. Returned witnesses explicitly expose
\`dispatch_authorized=False\`, \`automatic_replay_authorized=False\` and
\`external_outcome_known=False\`. The local digest detects accidental evidence
drift; it does **not** authenticate an independently trusted plan author.

The Run437 audit noted a detached archive could omit an entire WRITE entry
and recompute its own bundle digest. This independent expected-list primitive
addresses the **prerequisite** for recognizing such an omission, but no
integration into \`restore_synthetic_write_plan_bundle\` has occurred: Run434
bundle's exact-head CI is still pending. Nor does this primitive prove that the
caller's claimed list is complete. That must be established at the original
PlanGraph/topology boundary and retained outside the SQLite/archive failure
domain before any later production integration.

New \`tests/test_synthetic_expected_write_membership_run438.py\` adds
**21 pytest parameter-expanded cases**. A disconnected, locally staged copy of
the standalone module and its test file ran under Python 3.13.5:
**21 passed**. This is *not* a full repository or GitHub Actions PASS;
the working container cannot resolve github.com to clone the repository.

## Package B: fixed oversized fixture ID regression guard

The previous \`test_fixture_rejects_oversized_payload\` parametrization
caused ~4 MiB of repeated \`a\` to appear in Windows pytest failure reports.
Run437 added short fixed IDs without reducing the payload or skipping tests.

New \`tests/test_ci_fixture_param_id_guard_run438.py\` adds **two AST-only
tests** for that exact regression. The guard checks both payload multipliers
remain **4,194,305 bytes**, the fixture cases retain two short, unique explicit
parameter IDs, and the function still uses \`pytest.raises(...,
match="byte budget exceeded")\` without a skip marker. AST inspection does
not instantiate the huge payloads. The guard itself ran locally against a
*representative copied decorator/body fixture* (not a mounted repo checkout):
**2 passed**. The exact current repository HEAD has not passed CI.

This is a test-only guard; the GitHub CI workflow, test behavior, and
frozen V1/V2/Local UI/Launcher evidence were not modified.

## Independent read-only CI forensic inspection

At this invocation's actual GitHub inspection:
- #1255 / \`40251633322\`, source HEAD \`fb4c9124...\`: **QUEUED**;
- #1256 / \`40251731215\`, membership test HEAD \`da9820c2...\`: **QUEUED**;
- #1257 / \`40252121935\`, ID guard HEAD \`7f819a32...\`: **QUEUED**;
- #1252 / \`40246195602\`, Run437 final source/test HEAD: **QUEUED**;
- Earlier #1221 / \`40223600447\`: Ubuntu 3/3 SUCCESS,
  Windows 3/3 **CANCELLED** in the latest per-job read; this does *not*
  imply final GREEN or prove the underlying setup error was fixed;
- #1222 / \`40223781720\`, #1223 / \`40224110645\`,
  #1224 / \`40227265210\`: Ubuntu 3/3 SUCCESS per run,
  Windows 3/3 still **IN PROGRESS**, with \`Run pytest\` still active.

Read-only logs for Windows jobs \`121260770970\`, \`121261741097\`
and \`121271173411\` each returned approximately **4.2 million
characters** and ended in a giant \`ERROR at setup\` report containing
the large parametrized fixture ID, with no completed traceback or final test
summary visible. That is corroborating evidence for pathological pytest
reporting, *not* proof of the precise original fixture error or of a fix.

The GitHub Actions queue must not be treated as successful evidence.
No duplicate workflow was dispatched, no run was manually cancelled, and
no old failure or cancellation was reclassified as GREEN.

## Next dependencies / 今後の方針

1. Await exact-head CI #1252 and #1257 plus this invocation's final
   executable/test and checkpoint-result HEAD. Diagnose failure steps/logs;
   do not weaken tests or manually launch equivalent duplicate workflows.
2. Only after the detached Run434 bundle is GREEN, add a separate **recovered
   bundle ↔ independently retained original-plan full WRITE-membership**
   check and a recomputed-digest omission negative test. Preserve no-replay,
   no-dispatch, and no external-effect-success constraints.
3. Continue orthogonal free-only Memory CAS/expiry event integrity, privacy
   revocation, issuer/trusted-clock deny-only interfaces and offline Observation
   fixtures. Keep frozen DDL/contracts and all protected evaluation gates.
4. Leave PR #5 and PR #8 Draft/unmerged. No paid/external GPU or API,
   Candidate generation/promotion, user hardware action, credential connection,
   protected V2 final opening, destructive action or main merge.

**Important evidence limit:** a locally recomputed hash and a caller-claimed
expected list do not make separate SQLite files atomic or provide human
consent, signed timing, a verified registry/backend identity, or a real-world
exactly-once outcome. UNKNOWN/RUNNING and reserved PENDING WRITEs remain
non-replayable.
