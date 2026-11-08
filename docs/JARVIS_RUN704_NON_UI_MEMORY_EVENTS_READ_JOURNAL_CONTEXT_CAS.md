# ARK AI — Run704: global Memory event integrity, READ result custody, Context replay races

**Scope:** free-only, local-first, reversible, non-UI work on Draft PR #8.
**Initial work-basis HEAD:** `5aac6a84323e3c2ee160bb54f21658d0a27af0e6`.
No main merge, frozen contract/DDL revision, UI change, model/GPU action,
real tool dispatch, protected V2 evaluation, consent claim or Candidate promotion.

## Package A — Memory v1 scoped event reads

- [Source `4321df87`](https://github.com/Iam-2squared/ark-ai/commit/4321df8795a3d877c2d534c1c0e619fb45fdad40): add a read-only global append high-water validator to `SQLiteMemoryStore.events`, executed in its **existing SQLite read transaction** immediately after frozen v1 schema validation and before any scoped SELECT is disclosed.
- Verify global `COUNT/MIN/MAX(event_id)` plus SQLite `sqlite_sequence` tail: empty untouched journal or exact contiguous 1..N with sequence=N. Missing first/middle/last rows, complete truncation and altered tail are rejected even when querying a different owner's empty scope. No new schema, table, persistent metadata, write or cleanup action.
- [Tests `37a60c78`](https://github.com/Iam-2squared/ark-ai/commit/37a60c7808323bee2da4dfe4b8cb6433de232213): **6** new cases, including normal cross-owner pagination and no private foreign content in returned metadata.
- **Limit:** an attacker who can rewrite both all history and SQLite internal sequence consistently may defeat this *local* check. It is neither independently retained provenance nor forensic erasure proof. A concurrent writer after the read snapshot does not invalidate the earlier coherent view.

## Package B — Detached READ result class custody

- [Source `d7877fb6`](https://github.com/Iam-2squared/ark-ai/commit/d7877fb61c729c1a6e17497137423ada18352166): retain import-time `ReadJournalSnapshot` class, exact two result slots, initializer/allocation/getter hooks and four denied-authority properties. Refuse a substituted class **before SQLite recovery access**, re-check across the stable recovery path and immediately around result construction.
- [Tests `6a4b5dac`](https://github.com/Iam-2squared/ark-ai/commit/6a4b5dac69c349e5dedf8f10e6a79ebe35da2b94): **5** subprocess-isolated hostile constructor/new/slot/getter/authority descriptor cases, with a healthy genesis baseline and an intentionally closed handle to prove early refusal. No real READ result or permission inferred.
- **Limit:** Python class descriptor checks do not authenticate a running process against a hostile interpreter or prove independent custody; a fixture journal stores only supplied result digests.

## Package C — Personal Context competing writer/restart safety

- [Tests `b534fc57`](https://github.com/Iam-2squared/ark-ai/commit/b534fc57bd316f7c49b5d89310cd31ef54e9f527): **4** tests exercising same/different hash-only request IDs against two independently reopened SQLite ledgers with the same genesis CAS witness, stale loser recovery, prefix verification after an additional reservation, historically rewritten hashes and restart duplicate denial.
- Each test uses disposable local SQLite and synthetic plaintext which must not appear in the database. A successful local reservation carries only false external disclosure/replay claims. Neither CAS nor a local hash proves global exactly-once side effects, user consent, or physical erasure.

## Actual CI investigation and fixes

- [Pre-invocation exact-head CI `42448499983`](https://github.com/Iam-2squared/ark-ai/actions/runs/42448499983): **6/6 GREEN** at initial `5aac6a84323e3c2ee160bb54f21658d0a27af0e6`, Windows/Ubuntu × Python 3.11–3.13.
- Fresh authored-test HEADs [`42452332790`](https://github.com/Iam-2squared/ark-ai/actions/runs/42452332790) and [`42452412676`](https://github.com/Iam-2squared/ark-ai/actions/runs/42452412676) **6/6 FAIL** at Ruff `I001`, import-block formatting only. This is not a passing test verdict.
- Normal [READ test import fix `06f163a3`](https://github.com/Iam-2squared/ark-ai/commit/06f163a301f598f65cd42e89afce3e8628a2e511) and [Context import fix `5ff8612f`](https://github.com/Iam-2squared/ark-ai/commit/5ff8612f51bdc8fd5f34d86b9faa86c876cbef52) added standard future imports/reorganized imports without changing the test assertions or safety rules.
- Earlier Memory source [`42452240735`](https://github.com/Iam-2squared/ark-ai/actions/runs/42452240735) and tests [`42452259466`](https://github.com/Iam-2squared/ark-ai/actions/runs/42452259466) showed partial Ubuntu GREEN at interim checks; the later READ source [`42452300821`](https://github.com/Iam-2squared/ark-ai/actions/runs/42452300821) was still in progress.
- **The combined corrected exact HEAD has NOT been verified 6/6 GREEN.** Later CI jobs may reveal runtime failures. No local pytest run was performed: this automation's container cannot resolve the public GitHub remote, so no full checkout is available. Actual conclusions must come from GitHub Actions logs, not assumptions.

## Independent free-only V3 review

Read-only inspection of frozen [PR #5 HEAD `805b377697472268db02650a89c7a94b1c5337c8`](https://github.com/Iam-2squared/ark-ai/pull/5) `src/ark/learning/training_cli.py` confirms code paths for `run_preflight` and `run_training` first call scoped `validate_experiment_001` and evidence verification before `_verify_actual_runtime` imports torch, with full training additionally verifying a previous preflight report. **No execution, authorization, GPU, Candidate or approval was performed**. This source-level ordering is not an independent runtime/pass attestation and PR #5 remains frozen Draft/unmerged.

## Prioritized next work

1. Verify CI for corrected exact PR #8 HEAD; if actual tests fail, inspect each job and make the smallest semantics-preserving correction. Do not misattribute older green jobs to later commits.
2. Check Memory event paging under coherent WAL snapshots and cross-owner truncation, including any existing legacy diagnostics affected by the earlier high-water rejection.
3. Expand durable detached READ per-step input binding and crash-safe recovery using retained witnesses, and continue audit-before-action / PermissionGate on disconnected-only paths after exact-head proof.
4. Retain Personal Context data minimization, proactive observation and V3 free-only boundary review. UI paused; PR #5/#8/#9 remain Draft/unmerged; ARK/JARVIS/V3 **NOT_PASSED**.
