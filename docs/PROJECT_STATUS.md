# ARK AI Project Status

**LATEST**

Saved at: **2026-09-26 19:49:03 JST (+09:00)**

## Checkpoint identity

- Canonical checkpoint branch: `research/v3-learning-evaluation`
- PR #5: **Draft / unmerged**
- Exact checkpoint work-basis HEAD: `d6d4c1954a85fc716b1c593ac55c85417912418f`
- Previous checkpoint result HEAD: `d6d4c1954a85fc716b1c593ac55c85417912418f` — superseded by this status update.
- Long-term-memory foundation branch HEAD: `1cfcd7adaedcb495b0ac799247d911f2af57dad8`
- Tool/planning/action-safety foundation branch HEAD: `c268bfb73bcca720528e8bbf1851287f42510b4c`
- The resulting checkpoint commit cannot be embedded in this file; record it in the next checkpoint.
- Overall state: **V1/V2/Local UI/Launcher PASS/frozen; V3 Draft/NOT_PASSED; later foundations isolated/not PASS**

## Current state / 現在の状況

ARK remains on the frozen V1/V2/Local UI/Launcher baseline for released behavior. V3 Contract 1
and all protected evaluation boundaries remain unchanged. PR #5 is still Draft and latest code
HEAD `d6d4c1954a85fc716b1c593ac55c85417912418f` has GREEN CI #151.

Independent reversible groundwork now exists outside the V3 workstream for local long-term
memory and for tool/planning/action safety. These branches do not assume Candidate results and
are not integrated into main or declared roadmap PASS.

## Work completed in this session

### NEW — local-first memory foundation

On `research/long-term-memory-foundation`:

- Completed the previously incomplete memory package with explicit scope isolation and
  deterministic SHA-256 memory identities.
- Added SQLite schema versioning, compare-and-swap revisions, expiration visibility,
  physical expiry purge and revision-guarded physical deletion.
- Added content-free lifecycle audit records so content/metadata are not copied into the audit log.
- Added deterministic lexical retrieval with NFKC normalization and CJK/Japanese bigram support.
- Added 9 focused tests for identity, scope isolation, CAS conflicts, expiration/purge,
  deterministic ranking, Japanese retrieval, deletion and future-schema fail-closed behavior.
- New work commit: `1cfcd7adaedcb495b0ac799247d911f2af57dad8`.

### NEW — tool/planning/action-safety foundation

On `research/tool-planning-action-foundation`:

- Added stable tool-call/capability/scope contracts with canonical argument digests and
  deterministic action request IDs.
- Added fail-closed exact-scope capability grants and expiring, exact-request one-shot
  authorization for write-effect operations.
- Added deterministic DAG planning state with dependency validation, optimistic revision
  guards and transitive blocking after failed prerequisites.
- Added SQLite action-audit storage that records argument hashes rather than raw arguments
  and fails closed on unsupported future schema versions.
- Added 10 committed focused tests covering permission, one-shot, DAG, revision and audit
  safety boundaries.
- New work commit: `c268bfb73bcca720528e8bbf1851287f42510b4c`.

### Existing V3 work retained

Candidate-run create-only evidence, byte re-verification, strict training-metrics schema,
runtime/source identity gates and Pre-Paid-Compute boundaries remain unchanged in this session.

## Tests / CI / evidence

- PR #5 HEAD `d6d4c1954a85fc716b1c593ac55c85417912418f`:
  CI #151 / run `36223644908` — **GREEN / completed successfully**.
- Memory foundation: focused offline prototype-equivalent test set was exercised before commit
  with **9 passed**; the isolated branch does not yet have a GitHub PR/CI result.
- Agency foundation: a local prototype superset was exercised with **11 passed** before the
  executable registry portion was intentionally omitted from the committed safety-only scope.
  The committed 10-test branch does not yet have a GitHub PR/CI result.
- No foundation branch is represented as CI-validated or integration-ready until GitHub CI
  actually runs on its exact committed HEAD.

## Frozen contracts / evidence unchanged

- V1 reviewed freeze and OFFICIAL PASS evidence.
- V2 fixed suite/scorer/policy, reviewed 11/12 baseline and known `math-02` format-only failure.
- Local UI v1 and Launcher/Gate Runner reviewed/frozen evidence.
- V3 Contract 1/hash and Experiment-001 semantics.
- Protected V2 final evaluation and its opening budget.
- No external paid compute, Candidate generation, Validation/V2 opening, promotion,
  Contract mutation or main merge occurred.

## Unresolved blockers / authorization boundaries

1. V3 still requires immutable/materialized model and tokenizer identity evidence,
   provenance-complete human-approved 120/30 data, exact runtime/tool identities and
   authorized hardware/budget evidence before any external-compute preflight.
2. External/paid compute, real Candidate generation, protected evaluation opening,
   Candidate promotion, frozen-contract changes and main merge remain explicit hard stops.
3. The memory and agency foundations are isolated research branches; PR creation/CI wiring
   remains pending and no integration/PASS claim is made.
4. Automatic personal-data ingestion, semantic/vector memory, real tool execution and
   computer-control backends are deliberately not connected until their permission,
   privacy and compatibility boundaries are proven.

## Next plan / 今後の方針

1. Keep PR #5 Draft; continue free V3 reproducibility/export/identity closure without
   weakening frozen gates.
2. Run exact-HEAD CI for the memory and agency foundation branches when a safe PR/CI path is
   available; fix ordinary lint/test issues minimally.
3. Extend isolated foundations with privacy/retention migration tests, durable plan state,
   typed tool-result/audit correlation and mock-only orchestration before any real action backend.
4. Prepare reversible voice/vision input and computer-action interfaces that reuse the same
   capability/audit boundary without granting device control.
5. Re-read every target branch HEAD immediately before writes; reconcile concurrent changes
   and never force-push.
