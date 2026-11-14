# ARK AI Run862 — bounded non-UI SQLite catalogs and process-level Planner terminal CAS

## Scope and evidence boundaries

- Repository: `Iam-2squared/ark-ai`
- Work basis: `0de0ab5d138e0d3eadc77ba14af0b2aa764dac18` (Run861 checkpoint).
- Development branch: `research/jarvis-foundations` / Draft PR #8, no main merge.
- Prior independently checked basis CI: [#43549199600](https://github.com/Iam-2squared/ark-ai/actions/runs/43549199600) — **6/6 GREEN** for the Run861 checkpoint only. Source, test and final checkpoint commits below are **NOT** certified by that earlier run.
- **Overall ARK/JARVIS: NOT_PASSED.** All new UI/frontend development remains paused.

## New implementation — SQLite pre-materialization admission

1. **Disconnected synthetic scheduler quarantine** — source commit `9b65955b52039da17ef66afac32b886e1bb6f043`: within the existing SQLite validation transaction, bound `sqlite_master` object count (8) and SQL DDL bytes (8192) before creating a Python schema tuple. Replace an unbounded integrity-result fetch with a two-row probe. Reject more than 512 stored quarantine rows and non-integer event columns, non-TEXT or wrong-width occurrence/digest columns via SQL `typeof`/`length` before Python event iteration. These are local storage validation rules, **not** trusted provenance.
2. **Memory v1 schema inspection** — `e94a8a71339abe131b2e053feba1e04e13c32355`: before unbounded `sqlite_master` hydration in the *existing* schema validator, require at most 16 schema objects / 16,384 SQL bytes inside the same snapshot. Original V1 SQL schema and historical evidence were not modified. No disk repair or automatic retry.
3. **ActionAudit v1 schema inspection** — `eca3f175f8c6daf219253f59b99cea5d6b2338d0`: same scoped, bounded catalog preflight for audit v1 startup; original DDL remains intact. No external action, authenticated issuer, audit authority, or exactly-once guarantee is inferred.

These checks protect the Python boundary against oversized or malformed catalogs within SQLite's own query execution, but cannot attest a historical writer, solve path-to-open races, or prove sidecar custody. They intentionally fail closed.

## New independent process and negative fixtures

4. **Planner terminal CAS race** — `7e3894f3a5e05e4d0a12f84b8e9d4104cf431484`: two new parametrized cases race spawned independent Python interpreters, one committing FAILED/CANCELLED and one SUCCEEDED from the same RUNNING revision. Expected local SQLite CAS outcome: exactly one terminal winner, one stale loser; the dependent step is either BLOCKED or still pending based on the committed root, while an independent root remains pending. Cold restart checks journal equality and never grants dispatch or replay. This is **not** external effect exactly-once.
5. **Bounded SQL catalog and persisted-data fixtures** — `05deef0ca20deb1e643c967da21f0c319243d68a`: eight authored tests, six from three stores × (excess catalog objects, oversized synthetic DDL), plus two scheduler persisted-row negative cases (BLOB occurrence metadata and 513 rows). Each uses disposable SQLite paths. Tests ensure early fail-closed rejection and leave evidence physically inspectable; they do not grant private disclosure, schedule execution, repair or replay.

**Total new test cases authored this invocation: 10 (2 Planner + 8 catalog).** Exact-head CI verification is required before labeling these tests PASS.

## CI attribution

The following CI workflows were started automatically by distinct GitHub commits. No manually duplicated equivalent workflows were launched.

- Scheduler source `9b65955b`: [#43553171669](https://github.com/Iam-2squared/ark-ai/actions/runs/43553171669).
- Memory source `e94a8a71`: [#43553318061](https://github.com/Iam-2squared/ark-ai/actions/runs/43553318061).
- Planner fixture `7e3894f3`: [#43553393002](https://github.com/Iam-2squared/ark-ai/actions/runs/43553393002).
- Audit source `eca3f175`: [#43553444701](https://github.com/Iam-2squared/ark-ai/actions/runs/43553444701).
- Final executable source/tests `05deef0c`: [#43553580770](https://github.com/Iam-2squared/ark-ai/actions/runs/43553580770).

**As last observed while composing this report:** source CI runs were in progress or queued; final executable-head and future checkpoint-head **6/6 GREEN NOT YET VERIFIED**. Do not extrapolate Run861 green. Full local pytest/Ruff, physical Windows PC and GGUF gates not executed. Fix any GitHub CI regression without loosening the SQL preflight, Planner CAS or denial flags.

## Frozen boundaries, blockers and next plan

Frozen V1/V2/Local UI/Launcher contracts and evidence unchanged. Draft PR #5 protected V3 final-evaluation gate and Draft UI PR #9 untouched, unmerged; no UI feature/test/integration changes. No paid/external GPU/API, subscription, new credentials, Candidate adapter/training/promotion, protected V2 final evaluation, actual backend dispatch, notification, deletion, real PC action or main merge.

Unsolved: Memory and ActionAudit WAL/SHM last-close and pathname-to-open races; independently authenticated COMMIT-UNKNOWN causal witness; Planner recovered RUNNING stays UNKNOWN/manual; cross-store atomicity; restart-safe approval with trusted issuer/clock/audit-before-action; exactly-once external side effects.

**Next plan / 今後の方針:** (1) determine exact final HEAD six-job CI and repair any failures; (2) independently review bounded SQLite catalog admission and detect schema/query collateral effects; (3) pursue sidecar final-close and COMMIT-UNKNOWN causal witnesses on fresh disposable databases; (4) strengthen Planner/Privacy restart cases; (5) only then prepare disconnected ToolRegistry/PermissionGate/Audit/Mock Executor integration without claiming authority.
