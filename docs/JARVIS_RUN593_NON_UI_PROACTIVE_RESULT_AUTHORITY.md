# ARK AI — Run593 non-UI proactive authority custody (free-only)

This note documents **three isolated local-fixture hardening packages** on Draft PR #8. The source remains disconnected from real notifications, tools, accounts, clocks, user permissions and external side effects. It does not make proactive scheduling operational.

## A. Read-only prepared-trigger freshness result

- Source: `src/ark/proactive_synthetic_freshness_review.py`, source commit `e60d1cfbe1181fb949c8d71709607f9fa34eec4b`.
- Tests: `tests/test_proactive_freshness_original_denial_run593.py`, test commit `91f2894e29cfa981689e5b57d9236c66bba86146` (5 authored pytest cases, including three parametrized original-descriptor substitutions).
- The result has three deny-only fields: notification, dispatch and automatic replay. An unreviewed replacement `property(lambda _: False)` is **not** the original immutable authority definition. After every getter the read-only result and source epochs are checked; after the last getter all original descriptor identities are rechecked, preventing a late callback from replacing an earlier getter.
- SQLite remains read-only for this review; success is structural fixture coherence, not authentic provenance, current human consent or trusted wall time.

## B. Persisted synthetic preparation receipt

- Source: `src/ark/proactive_synthetic_review.py`, source commit `a4690caacefbfd5079acd791e63b73fe05a0bff8`.
- Tests: `tests/test_proactive_receipt_original_authority_run593.py`, test commit `2d19acb01165c5c0581fbf566000fb3cfbee5a76` (9 authored pytest cases: three False descriptor substitutions, three True grants, a reentrant earlier-descriptor substitution, a reflected receipt carrier mutation and an untouched control).
- After the **local SQLite COMMIT**, the returned receipt must have exactly the original result type, field carriers and three original deny-only descriptors. Each getter may be reentrant, so the receipt and policy are checked again after every call. A forged output is rejected rather than returned as a permission token.
- **Critical crash/COMMIT caveat:** an exception from these checks occurs after the marker may already be durable. It does not roll back that marker, prove that any external action occurred, or permit automatically retrying the preparation. The tests verify the local row count remains one following post-COMMIT denial.

## C. Manual-only Memory post-COMMIT CAS triage

- Source: `src/ark/memory/postcommit_uncertainty_review.py`, source commit `06920c17c04e7ddedaa7bbfa13340422870026ad`.
- Tests: `tests/test_memory_triage_retained_carrier_run593.py`, test commit `0a031a2711113f66a2c79c24b7bf752be8e9b8d8` (4 authored pytest cases, including three field-carrier substitution scenarios).
- The independently retained generation-CAS token is captured before the first SQLite snapshot. Manual triage now checks the **original identity** of every token field after snapshot/reentrant callbacks rather than accepting a newly substituted but equal-valued digest. This rejects an unreviewed change of retained evidence with no database mutation, retry or claimed writer attribution.
- The caller must still retain the original token independently; local matching digests cannot authenticate which process, person or event caused a visible row update.

## CI / verification boundaries

- Pre-work basis PR #8 HEAD `b9f6751f350ed35f40f116f73ba9f8f45c698ad9`: [CI #41735070871](https://github.com/Iam-2squared/ark-ai/actions/runs/41735070871) **six jobs GREEN**; this only attests the earlier baseline.
- New source/test CI runs [#41741792918](https://github.com/Iam-2squared/ark-ai/actions/runs/41741792918), [#41741846186](https://github.com/Iam-2squared/ark-ai/actions/runs/41741846186), [#41741970285](https://github.com/Iam-2squared/ark-ai/actions/runs/41741970285), and [#41742027790](https://github.com/Iam-2squared/ark-ai/actions/runs/41742027790) were **IN PROGRESS / QUEUED** when initially inspected. These must be checked against exact commit HEADs before asserting a six-job pass.
- The 18 authored cases across the three packages are not claimed as independently run local pytest successes: direct public-repository cloning was unavailable in the local execution container owing to DNS resolution failure. GitHub Actions remains the validation gate. No equivalent manual workflow was triggered.

## Still blocked / unchanged

No real notification, durable exactly-once user authorization, consent proof, attested clock, physical hardware integration, paid API/compute, Candidate work, protected V2 final evaluation, automatic promotion, main merge, frozen contract mutation or UI/frontend change. PR #5 and paused PR #9 remain Draft and untouched. Local ledger markers and digest witnesses can be coherently rewritten by a sufficiently privileged local actor; independent signed provenance is outside these fixtures.

**Follow-up:** confirm exact-head CI; then prioritize genuinely durable Planner crash recovery, Memory generation CAS/COMMIT-UNKNOWN and registry-bound audit-before-action in disconnected execution only. All official ARK/JARVIS/V3 final PASS gates remain **NOT_PASSED**.
