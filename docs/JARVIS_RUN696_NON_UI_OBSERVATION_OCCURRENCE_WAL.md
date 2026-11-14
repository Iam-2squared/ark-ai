# ARK AI — Run696: non-UI observation, synthetic occurrence and Memory WAL

This is a **free-only, disconnected and reversible** development record for
[Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).
It is not a V2/V3/JARVIS PASS, human authorization, independent provenance
record, physical-PC result, or evidence of any live action.

## Work basis and packages

- Incoming work-basis HEAD: `47ad5dc927327d320b97d6533e66f3d98923aa3f` (Run695 checkpoint).
- Incoming exact-head [CI #42418419606](https://github.com/Iam-2squared/ark-ai/actions/runs/42418419606):
  **6/6 FAIL**, with the same two legacy Observation diagnostic expectations
  differing from the new import-time pre-access digest rejection.
  Ubuntu Python 3.11 log reports **10,670 PASS / 1 SKIP / 2 FAIL**.
  Windows Python 3.13 log reports **10,611 PASS / 60 SKIP / 2 FAIL**.
  This failure is real and must not be represented as GREEN.
- **A — Observation compatibility correction**, commit
  `c7e11e3a8fe88059dae9b99a58004488ec0c9eb6`:
  `tests/test_observation_envelope_validator_slot_custody_run649.py`.
  The two affected reentrant-hash scenarios now require the *earlier*
  `digest implementation changed` refusal, assert the substituted digest
  callback was never called, and assert no executable envelope accessor
  executed. No Observation production guard was weakened.
- **B — Synthetic occurrence private-token digest preflight**, production commit
  `6a27fba4e6949b59292452cb80669b585d961aa6`:
  `src/ark/agency/durable_occurrence_review.py` pins the SHA-256 module/function
  identity at import-time, rejects replacement before reading one-shot token
  fields or entering synthetic registry/SQLite work, and rechecks across
  registry/transaction callback boundaries. This is an in-process *fixture*
  integrity check, not signed authorization or an external exactly-once guarantee.
  Legacy fault-injection tests in
  `tests/test_occurrence_input_commit_epoch_run410.py` updated at commit
  `c6272ac450b45567ed52cb8eb731cc6285682cc8` to require prehash
  refusal and zero substituted callbacks rather than relying on a substituted
  digest to mutate a private token.
  Three new parametrized cases at
  `tests/test_synthetic_occurrence_digest_preaccess_run696.py`, commit
  `289640235b52af6388c846166d4c8cf47e6a62ce`, cover direct SHA
  substitution, module replacement, and registry-reentrant replacement,
  followed by an independent valid fixture-only reservation.
- **C — Memory foreign-writer/WAL COMMIT-UNKNOWN classification**, four new
  parametrized cases in `tests/test_memory_cas_foreign_writer_wal_outcome_run696.py`,
  commit `6402dc0775103fa7aa64a424934f6259f8811464`.
  Two distinct SQLiteMemoryStore handles operate against the same disposable WAL
  database. A second writer updates the row with matching content/metadata/expiry,
  or one of three divergences; the first writer's retained stale CAS cannot
  replay and the manual read-only review never attributes matching bytes to the
  caller or supplies consent/retry/external-dispatch authority. Frozen Memory v1
  schema and public put/delete contracts are unchanged.

## Compatibility CI failures and semantics-preserving corrections

- Production occurrence prehash guard triggered **three** previously valid
  fault-injection scenarios at a *different, earlier* boundary. The pre-fix
  [CI #42422227996](https://github.com/Iam-2squared/ark-ai/actions/runs/42422227996)
  had three Ubuntu failures when last inspected: legacy mock audit marker
  injection, mock receipt-constructor injection, and a synthetic receipt
  class injection during token hashing. [#42422306207](https://github.com/Iam-2squared/ark-ai/actions/runs/42422306207)
  inherited those same three failures while other jobs were pending. These
  are **real failures**, not PASS evidence.
- Corrected through ordinary GitHub Contents API updates:
  `tests/test_mock_cycle_audit_receipt_epoch_run400.py` at commits
  `cfcc11ef334055c18b1b514c9018d86847eec289`,
  `55fb32f715becb36ecc430c660e622eef9a9bf24`;
  `tests/test_mock_cycle_receipt_constructor_custody_run618.py` at
  `ae1e2ed56a48ce23668e6cb4a4c9f59d6fb73146`,
  `e0cfec2295405e8f34d1773870b5e42671d7c7b0`;
  and `tests/test_synthetic_reservation_receipt_class_custody_run607.py`
  at `82ab196f8a4df30a42a350ed0b006b5c2e9081e6`.
- Mock Planner RUNNING is durably appended **before** one-shot occurrence
  reservation. The corrected tests therefore require a retained ambiguous
  RUNNING step with **zero** occurrence rows and **zero** audit rows after
  early digest refusal; the injected digest or receipt constructor never
  runs. A failed mock cycle never automatically retries UNKNOWN WRITE.
  The post-COMMIT forged-receipt scenario continues to require one retained
  reservation and rejection of replay. **No production guard was relaxed.**
- The corrected-source CI is independent from failed earlier HEADs and
  remains to be attested **6/6 GREEN**. Do not infer success from test edits.

## CI evidence / known limitations

- After A: [#42421918089](https://github.com/Iam-2squared/ark-ai/actions/runs/42421918089)
  observed Ubuntu **3/3 GREEN** and Windows **3 in progress** at report planning.
- After B: [#42422227996](https://github.com/Iam-2squared/ark-ai/actions/runs/42422227996)
  observed **6 in progress** at report planning.
- After C: [#42422306207](https://github.com/Iam-2squared/ark-ai/actions/runs/42422306207)
  observed **1 in progress / 5 queued** at report planning.
- The final report and checkpoint each trigger separate CI runs; results are
  tied to exact commit SHAs and must never be inferred from earlier GREEN.
  Source/test changes may require a narrow fix if actual CI exposes other
  diagnostic mismatches. No duplicate manual workflow runs were started.
- All tests use only local/disposable SQLite, synthetic token strings, fixture
  clocks, and disconnected never-execute backends. The synthetic reservations
  cannot prove human approval, global exactly-once external effects, or
  trusted-clock security. Matching Memory rows cannot prove writer identity,
  and uncertain WRITEs must not be auto-replayed.

## Frozen and authorization boundaries

`main`, frozen V1/V2/Local UI/Launcher contracts and protected V2 evaluation
are not modified. [V3 Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5)
is unmerged and requires independently verifiable provenance/identity/license,
contamination/reproducibility and explicit budget/compute/review gates.
[UI Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) remains
untouched, Draft/unmerged; **ALL NEW UI/FRONTEND WORK IS PAUSED**.
No paid/external GPUs/APIs/services, candidate adapters/weights, protected
evaluation, new accounts/secrets, live tool dispatch, physical-PC work,
destructive operations, real notifications or main merge were performed.

## Next plan / 今後の方針

1. Verify exact-head CI 6/6 for corrected Observation, occurrence digest and
   Memory WAL tests. Investigate any actual failures and correct only the
   relevant isolated source/test path using permitted GitHub Contents updates.
2. Deepen Memory CAS/ABA/COMMIT-UNKNOWN, WAL/coherent row+event snapshot and
   privacy veto continuity. No UNKNOWN WRITE automatic replay.
3. Validate Planner per-step independent durable READ receipts and cold-restart
   terminal/UNKNOWN behavior before registry-bound audit-before-action join.
4. Continue local-first replay-safe ToolRegistry/PermissionGate, Personal
   Context privacy, proactive/observation fixture contracts and free-only V3
   reproducibility/identity checks, without resuming UI development.
