# Run574 — Non-UI ARK Core: retained privacy veto, Memory event clocks, V3 passive identity regression

**Scope:** opt-in, free-only, local synthetic backend and review-only work. This is not a completed JARVIS capability or official gate PASS. The separate UI foundation on Draft PR #9 is explicitly paused and not modified.

## 1. Detached proactive attention under retained privacy veto (PR #8)

`src/ark/offline_attention_revocation_review.py` joins a caller-retained `SyntheticRevocationWitness` and `SyntheticContextRevocationLedger` with `preview_proactive_attention`.

1. Validate original class/function identities, exact bounded local hashes and callback-denial implementation before accessing the ledger.
2. Reconcile all retained revocation markers via an independent caller-held prefix. On a visible scope-digest veto, emit `LOCAL_REVOCATION_VETO` without evaluating an attention candidate.
3. For a locally non-revoked scope, retain the detached attention disposition (e.g., `REVIEW_ONLY`), **never** converting it into user consent or permission to notify.
4. Bind scope/trigger/occurrence/observation/time and revocation witness to a domain-separated, content-free SHA-256 review digest. Reject carrier or authority drift.

`tests/test_offline_attention_revocation_gate_run574.py` covers inert candidates, veto precedence, unrelated revocation, retained-marker rollback, pre-read malformed input, dependency class replacement and timestamp-dependent hashes (**10 authored cases**).

**Boundaries:** the scope digest comes from a synthetic caller-supplied policy; the ledger is not an authenticated consent source. An absent local veto is not a grant. A new veto may race with use outside this review. Neither the result nor its SHA proves cross-SQLite atomicity, human approval, trusted clock, notification delivery, external effect or a ToolRegistry/PermissionGate authorization.

## 2. Memory retained row/event temporal reconciliation (PR #8)

`src/ark/memory/sqlite_retained_row_delta_review.py` now checks each *live* memory row's `created_at_ms` and `updated_at_ms` against the corresponding complete local event lifecycle in the **same** read transaction. On delete then recreate, the newly observed `create` resets the row creation epoch. For an individual memory ID, later event timestamps must not precede that memory's preceding event; independent memory IDs do not require a shared global event clock.

`tests/test_memory_row_delta_temporal_lifecycle_run574.py` tests two first-event timestamp mismatches, a retrospectively backdated update, valid update/delete/recreation, equal timestamps and a different memory with an earlier timestamp (**6 authored cases**). One existing test `tests/test_memory_retained_row_delta_run512.py` was updated to accept earlier fail-closed timestamp rejection rather than expecting only the old event-prefix error text. No v1 schema, frozen contract, CAS mutation, expiry policy or writer attribution is changed.

**Boundaries:** a self-consistent forged row **and** forged event history is still not authenticated without external retained evidence. Local clock values remain untrusted; this is a structural temporal consistency check only. It grants neither writing nor erasure/replay/disclosure.

## 3. V3 passive local identity hardening tests (Draft PR #5)

`tests/v3/test_identity_artifact_final_bytes_denial_run574.py` adds a same-size/mtime-restored local JSON mutation probe requiring final byte reread to catch it, plus four false-valued authority-descriptor replacement tests. There are **5 authored cases**, no runtime source modifications, no frozen V3 contract change, no real model/Hub bytes, no protected evaluation, no Candidate, no training and no external compute.

## Validation and integration ordering

- PR #8 initial basis `c8a720380887705824cf27880d6383a3481d2137` had exact-head CI `#41587191820` **6/6 GREEN**.
- Initial attention + privacy source/test CI `#41592395217` failed Ruff import ordering; the **import-only correction** was saved, and later CI `#41592635222` separately validated earlier code revisions (refer to GitHub for its final state).
- The temporal Memory CI `#41592849235` exposed a pre-existing test that expected a later error despite the new earlier timestamp veto; only its diagnostic expectation was updated. Inspect the CI on the latest exact-head before asserting all-green.
- V3 new tests' exact-head CI `#41592520213` **6/6 GREEN** (Ubuntu and Windows, Python 3.11–3.13).
- Cross-component connection remains **diagnostic only**. Real consent, trusted-clock audit-before-action, restart-safe exactly-once authorization, external-memory provenance, production notification/tool execution and physical-PC validation must be independently reviewed before any action-enabling integration.

## Next plan / 今後の方針

1. Confirm PR #8's post-fix exact-head six-job CI, repair only concrete failures and keep unrelated work independent while it runs.
2. Extend Memory generation-CAS, retention/expiry, ambiguous-COMMIT and coherent snapshots with independently retained witnesses; protect privacy and avoid automated retries.
3. Advance Planner FAILED/BLOCKED recovery plus registered mock READ receipts, occurrence/replay custody and trusted-clock/audit-before-action.
4. Preserve all frozen V1/V2/Local UI/Launcher and V3 contracts; keep PR #5/#8/#9 Draft/unmerged, and keep **all UI development paused**.

**No paid/API/GPU/new service, real Candidate/training, protected V2 evaluation, source credentials, physical PC action, ToolBackend dispatch, destructive migration or main merge. ARK/JARVIS/V3 NOT_PASSED.**
