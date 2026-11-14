# ARK local process-concurrency fault matrix — Run435

**Status:** review/test additions only; exact-source GitHub CI is not assumed
GREEN. Repository: `Iam-2squared/ark-ai`, Draft PR #8
(`research/jarvis-foundations`). Starting checkpoint HEAD:
`1d8c78b26463ae823b57d4602674368d68e2147c`.

## Scope and evidence discipline

Three independent Python-subprocess fixtures exercise the existing SQLite
boundaries without connecting a sensor, scheduler service, credential,
notification sink, action backend, trusted clock, or live memory source.
Each test uses pytest's disposable temporary directory. Child processes
initialize their stores, publish a ready marker, and only then cross a shared
filesystem start gate. Child outputs are joined; a timeout or unexpected
exception fails the test. Child processes are always reaped in `finally`.

The intended checks below are **assertions in newly saved tests**, not
validated outcomes until their precise code HEAD passes CI. Runtime host
cannot resolve github.com for a local clone; neither pytest nor Ruff has
been claimed locally for this exact branch.

| Package | File | Independent-process invariant |
| --- | --- | --- |
| Proactive (+4) | `tests/test_proactive_cross_process_preparation_race_run435.py` | Same policy and trigger, or same policy with different observation digest, admits **one** preparation under the minimum interval and rolling budget; different revision or owner remains isolated, admitting both. Inspect durable rows after restart. |
| Memory initial CAS (+4) | `tests/test_memory_cross_process_create_race_run435.py` | Concurrent `expected_revision=0` for an identical owner/namespace/source admits **one** create and **one** conflict; distinct owner, namespace or source permits two creations. Every committed row has one content-free create event, at revision 1. |
| Global expiry/refresh (+2) | `tests/test_memory_multiscope_cross_process_purge_run435.py` | A global purge of two expired namespaces racing an independent refresh of namespace A yields one of two serializable, fully audited outcomes: purge deletes both and refresh conflicts; or refresh commits revision 2 and purge deletes only namespace B. |

## Fail-closed limits

- SQLite `BEGIN IMMEDIATE`, unique indexes and CAS predicates are the tested
  *local* admission authorities. The filesystem barrier only increases
  collision likelihood; it does not prove exhaustive scheduling or fairness.
- Durable scheduler preparation is not a notification. Durable Memory
  creation/expiry is not a general-purpose cross-store transaction,
  personal-data erasure, a user-consent decision, or a known Tool result.
- No signed trusted-clock source, authenticated approval issuer,
  independently attested external outcome or real-world exactly-once WRITE.
  UNKNOWN/RUNNING and previously reserved PENDING WRITEs stay on hold.
- Witness hashes do not authenticate a database against full-file rollback;
  independent retained evidence is mandatory for rollback diagnosis.
- Frozen V1/V2/Local UI/Launcher contracts and evidence, Memory v1 DDL,
  ActionAudit v1 DDL and V3 Contract 1 remain untouched. No main merge, real
  Candidate, protected evaluation, external GPU or paid service is authorized.

## Priority after CI

1. Check GitHub run **for each exact HEAD**, inspect failed logs if needed;
   repair only through normal Contents writes. Do not infer newer GREEN from
   an older run or manually dispatch duplicate workflows.
2. If the fixtures pass, add crash-at-COMMIT test variants and randomized
   *bounded* interleavings for the same stores (not cross-file atomicity).
3. Following exact-head GREEN on the detached plan-wide recovery-bundle
   baseline, independently retain step witnesses and diagnose a restarted
   READ→WRITE→READ→WRITE plan through Planner, Occurrence, ActionAudit and
   AuditLink. Preserve quarantine for ambiguous or reserved successors.
4. Keep PR #5 and PR #8 Draft/unmerged; require separately authorized real
   provenance, time, issuer, billing and hardware evidence for gated lanes.
