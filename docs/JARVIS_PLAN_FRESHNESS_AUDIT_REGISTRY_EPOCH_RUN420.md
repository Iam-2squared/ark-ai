# ARK AI — Run420: final-epoch integrity in Planner, Proactive, Audit and ToolRegistry

**Scope:** `Iam-2squared/ark-ai`, branch `research/jarvis-foundations`, Draft PR #8. Four isolated and reversible disconnected/mock-only hardening packages. **No real ToolBackend execution, issuer consent, trusted time, multi-store atomicity, automatic replay, external action, real model training or JARVIS PASS.**

**Exact Run420 work-basis HEAD:** `bf68a172a4b67ff35a82447e58aa100fb42e267f` (Run419 recovery archive source+tests; #1098 / 40183656398 completed SUCCESS). The canonical `docs/PROJECT_STATUS.md` still began at Run418 on entry; Run419 technical evidence exists independently as `docs/JARVIS_LINEAGE_PRIVACY_STARTUP_MEMORY_ARCHIVE_RUN419.md`. No prior checkpoint is silently rewritten.

## Four source + test packages (34 new parametrized pytest cases)

| Lane | Source HEAD | Test HEAD | New cases | Fail-closed invariant |
| --- | --- | --- | ---: | --- |
| PlanGraph | `cc1f8cfee3b9427258b575620e5e84131f091871` | `adcf8364d6cc9a886ddeb2b062f10fa27064163f` | 8 | Topology and status digests recheck exact original PlanStep/status epochs **after** hash callbacks; detached `statuses()` rechecks after constructing copies. Prevents a pre-mutation witness from being returned after late, reflected step/status retargeting. |
| Proactive freshness | `a5f7ba1b261fef5657a6ee12294c53f20709cfeb` | `7aef3da7f12ee23dae3e24e099eefb4d3b95869e` | 9 | Read-only prepared-trigger review pins the newly created SyntheticTriggerWitness through continuity callbacks, SQLite COMMIT and result construction. Rejects forged review fields, equal-valued witness swaps and altered history. |
| ActionAudit continuity | `e88cb6f145b85e12ff65ad770534e36b76b70073` | `05a9cdfb30e95b325d973f6c02288259f69415d4` | 8 | Read-only audit continuity pins exact retained witness types/carriers and rechecks original SQLite source plus final constructed witness. No replay authority or event rewriting. |
| ToolRegistry | `a13a73e0d0c20ceb468ba397582a0dad8f43b2b7` | `fb540870726d411c023cdb13470c7f9a39eece91` | 9 | `bind()` revalidates ToolCall, immutable registration epoch and exact returned BoundAction carriers **after** result construction. Equal-valued replacement and backend/effect identity drift fail closed before any dispatch. |

All fault hooks run entirely within synthetic pytest fixtures; mocks do not execute tools, use hardware, send notifications or read private user data. The additional checks cannot detect adversarial coordinated replacement of all independent evidence, nor establish authentic user permission or a real external exactly-once side effect. Existing deterministic witness inputs and frozen SQL schemas are unchanged.

## CI / exact HEAD fidelity (sample at engineering-document preparation)

- Baseline Run419 final source+tests **#1098 / 40183656398 SUCCESS** (all jobs).
- PlanGraph test HEAD **#1100 / 40184295779**: 6/6 GREEN, 0 FAILED, 0 IN PROGRESS/QUEUED. Ubuntu Python 3.13 log at job `121141701678` reported **Ruff PASS / 2490 passed, 1 skipped**.
- Proactive test HEAD **#1102 / 40184522102**: 6/6 GREEN, 0 FAILED, 0 IN PROGRESS/QUEUED. Ubuntu Python 3.13 job `121142373663`: **Ruff PASS / 2499 passed, 1 skipped**.
- ActionAudit test HEAD **#1104 / 40184676699**: 4/6 GREEN, 0 FAILED, 2 IN PROGRESS/QUEUED. Ubuntu Python 3.13 job `121142836430`: **Ruff PASS / 2507 passed, 1 skipped**.
- ToolRegistry final four-package test HEAD **#1106 / 40184830259**: 3/6 GREEN, 0 FAILED, 3 IN PROGRESS/QUEUED. **2516 passed, 1 skipped is an arithmetic expectation only, NOT a verified result** until its exact Ubuntu 3.13 pytest log reports it. No all-six GREEN claim before every job completes.
- Automatically started GitHub CI is the only CI used; no duplicate workflow dispatch, local GPU or paid runtime was launched. Intermediate HEAD results are not substituted for a newer HEAD.

## Guardrails / preserved evidence

Frozen V1/V2/Local UI/Launcher and V3 Contract 1 unchanged; **Memory v1 and ActionAudit v1 SQL DDL unchanged**. `main` untouched. PR #5 remains Draft/unmerged/NOT_PASSED, PR #8 Draft/unmerged. No paid/external compute, additional credentials, protected V2 evaluation, Candidate weight/adapter generation, promotion, personal-data export/erasure or irreversible action. In particular, **UNKNOWN/RUNNING and reserved-PENDING WRITE have no automatic replay authority**.

## Next plan / 今後の方針

1. Verify final ToolRegistry source+test **#1106** and this distinct document/checkpoint HEAD in every Ubuntu and Windows Python 3.11–3.13 job; inspect and correct only genuine failures via normal GitHub Contents writes.
2. Expand multi-WRITE Planner/PermissionGate/Occurrence/ActionAudit/AuditLink reserved-PENDING/UNKNOWN crash/restart triage, with independently retained history and negative replay tests. No external effects.
3. Strengthen Memory CAS/concurrent update, expiry, coherent snapshot and privacy revocation; do not modify frozen DDL or perform irreversible private-data actions.
4. Continue fixture-only trusted-clock/issuer readiness, Observation/Scheduler correlation and V3 free-only provenance/path/reproducibility approval guards. Stop individual paid/protected/approval-gated lanes pending explicit authorization.
