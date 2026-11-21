# ARK AI Run914 — CI compatibility repair + Memory/Planner SQLite catalog metadata admission

**Recorded at (JST): 2026-11-16T16:02:45+09:00.** Work basis: `77a9250232fa973365db8aa5e51d3eff99cfc66e`. Complete source+test HEAD: `fcb62ed61366598394e67fcc6cb62e91c69b4788` (pre-report). Branch: `research/jarvis-foundations` / Draft PR #8. **ARK/JARVIS NOT_PASSED.** No UI code touched.

## A. Confirmed Run913 regression and normal-path correction

[Run913 checkpoint CI #43813106625](https://github.com/Iam-2squared/ark-ai/actions/runs/43813106625) failed all six Windows/Ubuntu × Python 3.11–3.13 pytest jobs. An Ubuntu 3.11 log recorded **22 FAIL / 16,377 PASS / 1 SKIP**. The 2026-11-16 Run913 pinned-source addition introduced two new ledger `__dict__` fields (`_source_path_epoch`, `_source_policy_epoch`) but the read-only quarantine triage expected exactly the previous two fields; this incorrectly rejected legitimate detached restart reviews. Another old post-COMMIT regression expected the previous rejection string although the new pin now refuses earlier at the SQLite opener.

- [`893ab8c7`](https://github.com/Iam-2squared/ark-ai/commit/893ab8c7b21a8a213a631cb960cf2f37856574f6): read-only triage admits **exactly four** pinned ledger fields and verifies source/policy **object identity**, before policy use and across every pre/post-open snapshot check. Extra instance state, value-equal replacement, or altered original carriers still fail closed. The result retains `execution_authorized=False`, `notification_authorized=False`, `automatic_replay_authorized=False` and manual-review-only status.
- [`6b0384d2`](https://github.com/Iam-2squared/ark-ai/commit/6b0384d2460a9e379c809e96e28b002f41046557): update one old regression's exception-message regex to accept the **new earlier** exact source-identity refusal as well as its former carrier refusal; its actual durable-row and no-replay assertions remain intact. No frozen persisted schema or runtime policy was changed.

This is a confirmed compatibility repair, **not** a statement that all six current jobs are GREEN. Earlier `#43819539166` showed Ubuntu 3/3 GREEN while Windows remained in progress at an observed point.

## B. SQLite Memory v1 schema metadata budget

- [`0cdb65cf`](https://github.com/Iam-2squared/ark-ai/commit/0cdb65cf61dca5ea104f2faf3988639f2ff48b65): `memory.sqlite_store._schema_objects` SQL-side preflight now bounds aggregate UTF-8/BLOB bytes in `sqlite_master.type`, `name`, and `tbl_name` as well as the existing SQL DDL budget and object count before hydrating the catalog. Metadata aggregate ceiling **16,384 bytes**; frozen v1 DDL unchanged.
- [`c7e09e58`](https://github.com/Iam-2squared/ark-ai/commit/c7e09e5882c6257bdc04b729ca58022a2e913ca6): **4 synthetic tests** authored: over-budget name/table-name/type and a valid in-memory catalog. [`96bc5e36`](https://github.com/Iam-2squared/ark-ai/commit/96bc5e367a085273afffceff83b74777fbe796c1) fixes the authored test's import order after Ruff I001 was detected on intermediate CI. A disposable local SQLite-only probe showed altered name/table-name metadata totals of 16,399 bytes despite 25-byte SQL; it is **not an ARK pytest suite PASS**.

## C. SQLite Planner synthetic journal schema metadata budget

- [`2d252213`](https://github.com/Iam-2squared/ark-ai/commit/2d252213544aa6e64c3af7c2b06e35b570678ac3): `agency.planner_journal_review._schema_check` now bounds catalog `type`/`name`/`tbl_name` alongside DDL bytes before `_objects` materializes rows. Existing two-object and 4,096-byte DDL constraints remain; new metadata aggregate ceiling **4,096 bytes**. Journal schema/hash-chain/COMMIT-UNKNOWN semantics unchanged.
- [`fcb62ed6`](https://github.com/Iam-2squared/ark-ai/commit/fcb62ed61366598394e67fcc6cb62e91c69b4788): **4 synthetic tests** authored for huge name/table-name/type and the normal schema. Local isolated SQLite probes reported malformed metadata aggregate 4,170–4,186 bytes with DDL total 579 bytes. No protected evaluation opened.

**Total new regression cases authored: 8 (4 Memory + 4 Planner), plus one legacy test corrected.** No standalone full ARK suite was run locally; exact-head CI is the authoritative verification. No duplicate manual workflow launched. Intermediate pre-Ruff-fix CI failures are preserved rather than mislabeled green.

## CI snapshot and outstanding gates

- Previous `77a92502`: [#43813106625](https://github.com/Iam-2squared/ark-ai/actions/runs/43813106625) **FAIL 6/6** as above.
- Quarantine correction `6b0384d2`: [#43819539166](https://github.com/Iam-2squared/ark-ai/actions/runs/43819539166) **IN PROGRESS** at last observation (Ubuntu 3/3 GREEN; Windows in progress except one already GREEN).
- Memory authored-test intermediate `c7e09e58`: [#43820044912](https://github.com/Iam-2squared/ark-ai/actions/runs/43820044912) **FAIL**, Ruff import order; later corrected.
- Planner source intermediate `2d252213`: [#43820443308](https://github.com/Iam-2squared/ark-ai/actions/runs/43820443308) **FAIL 6/6**, same pre-fix Ruff issue inherited from memory test.
- Memory import fix `96bc5e36`: [#43820497522](https://github.com/Iam-2squared/ark-ai/actions/runs/43820497522) **IN PROGRESS** at last observation.
- Latest complete source/test HEAD `fcb62ed6`: [#43820540642](https://github.com/Iam-2squared/ark-ai/actions/runs/43820540642) **IN PROGRESS** at last observation. Final latest-head Windows/Ubuntu × 3.11–3.13 **6/6 GREEN not yet certified**. A subsequent report/checkpoint creates further HEADs/runs; report the result precisely.

## Frozen contracts, safety and next work

V1/V2/Local UI/Launcher contracts and frozen evidence, protected V2 evaluation, V3 Candidate/provenance/human approval gate and protected Draft PR #5, paused UI Draft PR #9, main, Planner/Memory v1 persisted schema, trusted-clock/permission boundaries and UNKNOWN no-automatic-replay all unchanged. No real/private user data, GPU, model training, paid/external API or compute, credentials, new service, physical PC, candidate weight, promotions, real tool writes or notifications, destructive operation, main merge or force push.

**Unresolved:** Windows/Ubuntu cross-process WAL/SHM last-close sidecar race; independent custody and history; Planner cross-store COMMIT-UNKNOWN/effect exactly-once proof; Memory full CAS/expiry/event atomicity under adversarial concurrency; trusted consent/audit clock, real GGUF gate and V3 runtime approvals.

**Next:** verify full latest HEAD matrix; minimal semantics-preserving fixes to any actual failures; isolate WAL/SHM phase with disposable tests; advance Memory/Planner custody and only then registry-bound PermissionGate/audit-before-action/disconnected mock integration. Keep all three PRs Draft/unmerged and UI paused.
