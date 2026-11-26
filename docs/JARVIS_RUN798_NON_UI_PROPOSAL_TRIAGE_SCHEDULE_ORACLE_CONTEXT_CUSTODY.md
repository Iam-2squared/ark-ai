# Run798 — Non-UI proposal COMMIT-UNKNOWN triage, schedule oracle, Context custody

Date: 2026-11-12 JST. **DRAFT / FREE ONLY / NO LIVE EXECUTION**.
Initial work-basis HEAD: `5f57e1f56048e90a758ca3c3424a4d28ba6ac3b1` (Run797; CI #43071826276 subsequently individually verified 6/6 GREEN). Draft PR #8 only. Frozen V1/V2/Local UI/Launcher, PR #5 Contract 1 and protected evaluation, and paused UI PR #9 untouched.

## A. Manual-only unknown synthetic proposal commit triage

Source `src/ark/agency/disconnected_proposal_unknown_commit_review.py` commit `eda0725ceadd57d2435855f9e8a1a62672a7210a`; tests `tests/test_disconnected_proposal_unknown_commit_review_run798.py` commit `ffc71b2fcac403f7cf1569ca9a70d0442a5a23b6`. **19 submitted cases**.

Given a pre-attempt global CAS witness and expected tip, derives the next deterministic event and global hash without writing, then asks the existing store for a coherent SQLite read-only snapshot with retained-prefix checking.

Classifications: `OBSERVED_UNCHANGED` (current observed state only; **NEVER a retry permit**), `OBSERVED_EXACT_APPEND` (one exact candidate event on the observed global prefix), `MANUAL_REVIEW_REQUIRED` (interleaving/later events). Every disposition requires manual reconciliation. Missing/modified schema or rollback is rejected rather than interpreted as unchanged. Tests cover genesis, multiple revisions, lost commit receipt, cross-proposal interleaving, nonzero prefix, later same-proposal changes, malformed inputs, rollback, schema corruption and permanent denial flags.

**Limits:** a local SHA or caller witness is not signed, independently authenticated, trusted time, verified external effect, human permission, or proof a valid database was never rolled back. No dispatch, automatic retry, training or Candidate operations.

## B. Independent synthetic scheduler boundary oracle

Tests `tests/test_disconnected_schedule_oracle_run798.py` commit `de4afee500f9bb15a520d2c223c6b19486ec86db`, **109 submitted cases**. Independently derives occurrence IDs and preview SHA-256 across four recurrence policies, all cursor positions including exhausted, and six offsets at due/grace/expiry boundaries; also forged cursor and nonexact/out-of-range clock tests. Source unchanged. Never grants notification, execution, trusted-clock, consent or replay.

## C. Context metadata carrier preaccess safety

Source `src/ark/offline_context_membership_guard.py` commit `8a1cb701baf51a0cda6b5e498d28cd523f7aa69b`; tests `tests/test_context_membership_carrier_custody_run798.py` commit `73fecdf50a632d6a0581c166a9bbbedb764eeff1`, **21 submitted cases**. Pins original record/veto/result dataclass field slots, constructors, attribute lookup hooks before reading untrusted metadata or producing an admission digest. Existing hash-driven reentrant drift checks retained unchanged to avoid invalidating earlier fault-injection tests. This is metadata-only, deny-only; no live Memory text, consent attestation, external export or ToolBackend.

## CI evidence and limitations

- Baseline Run797 exact HEAD `5f57e1f56048e90a758ca3c3424a4d28ba6ac3b1`, [CI #43071826276](https://github.com/Iam-2squared/ark-ai/actions/runs/43071826276): **GREEN 6/6**, Ubuntu/Windows Python 3.11–3.13, individual jobs checked.
- Run798 A source [#43081482954](https://github.com/Iam-2squared/ark-ai/actions/runs/43081482954), tests [#43081654083](https://github.com/Iam-2squared/ark-ai/actions/runs/43081654083).
- Run798 B tests [#43081938985](https://github.com/Iam-2squared/ark-ai/actions/runs/43081938985).
- Run798 C source [#43082232510](https://github.com/Iam-2squared/ark-ai/actions/runs/43082232510), tests [#43082340512](https://github.com/Iam-2squared/ark-ai/actions/runs/43082340512).
- **149 submitted cases**, NOT verified six-job exact-HEAD GREEN at document preparation; no local integrated pytest/Ruff or real target-PC model evidence claimed. Normal GitHub CI does not open GPU/Candidate/Tool runtime.

## D. Planner durable WRITE restart denial descriptor custody

Source `src/ark/agency/disconnected_write_restart_binding.py` commit `101ba90e419b90725bbccff139f79cc8689a5466`; tests `tests/test_write_restart_original_denials_run798.py` commit `7627272eef5ed6c64299107ec6c2c2e56902ed5e`, **13 submitted cases**. A preexisting restart path captured denial properties only after interacting with the persisted ledger. This package pins the original six denial property descriptors at import and checks them BEFORE ledger inspection. Substituted True- or False-returning executable getters are rejected without invoking the getter or opening a WRITE effect. Existing complete reservation, exact witness, UNKNOWN quarantine and mock-only invariants unchanged; this still proves neither an external WRITE outcome nor cross-store atomicity.

## CI failure triage (new Run798 work only)

The C test HEAD [#43082340512](https://github.com/Iam-2squared/ark-ai/actions/runs/43082340512) had **6/6 Ruff E501 FAIL**, each caused by the same four overlong test assertion lines. No source security condition failed in that run because pytest was not reached. Those four lines were wrapped without changing assertions (fix commit `843e0563bb652600b6bb05009dcd3fd8d49562a4`). Corrected CI [#43082784274](https://github.com/Iam-2squared/ark-ai/actions/runs/43082784274) was still **IN PROGRESS** when rechecked; do not claim its GREEN. D code/tests CI likewise not yet certified.

**Revised Run798 total: 162 submitted cases (19 + 109 + 21 + 13), NOT 162 proven PASS.**

## Next plan / 今後の方針

1. Verify individual six CI jobs on the exact latest HEAD and correct only actual failures via the normal GitHub safety path.
2. Continue Memory CAS/ABA/coherent expiry and Planner terminal/UNKNOWN WRITE recovery; maintain manual COMMIT-UNKNOWN quarantine, never replay automatically.
3. Improve proposal retained witness custody and path-swap review; then connect Registry-bound PermissionGate, durable occurrence, audit-before-action solely through disconnected mock fixtures after GREEN.
4. Keep PRs #5/#8/#9 Draft/unmerged; PR #9 UI paused. No paid compute, new credentials, real Candidate, protected evaluation, destructive operations or main merge. ARK/JARVIS **NOT_PASSED**.
