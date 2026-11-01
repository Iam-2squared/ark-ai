# Run526 — Registered READ batch child receipt custody (free-only)

**Scope:** disconnected Planner DAG, immutable ToolRegistry, PermissionGate and SQLite synthetic READ witness. No actual ToolBackend dispatch, WRITE, audio, notifications, autonomous retry, human consent or external effect. PR #8 remains Draft/unmerged; ARK/JARVIS overall is **NOT_PASSED**.

## Source and exact basis

- Initial PR #8 work-basis HEAD `6ccf4789bf3e322403d2a9b3c2ce9f28209dacf6` (Run525 canonical status).
- Source guard: `src/ark/agency/disconnected_registered_batch_receipt_set.py`, commit `ab8085c5ab597550138a488c8f4fb63bdf52bb6f`.
- Regression tests: `tests/test_registered_batch_receipt_set_run524.py`, first test commit `5ab4267e965091da970cf66e21fb863f03042907`, test-only Ruff I001 import correction `400577ff456f2e07b23da056838c325ed1222cb0`. **9 authored pytest cases**: seven forged child receipt fields, one forged child authority flag, one false-valued late getter that mutates the child digest.
- First exact test-head CI [41294787361](https://github.com/Iam-2squared/ark-ai/actions/runs/41294787361) failed in all six jobs **at Ruff I001**, before pytest, due an import ordering mistake; corrected without changing production semantics. The corrected CI must independently reach GREEN before any PASS statement; no local full pytest/Ruff due container GitHub DNS unavailability.

## Independent parent-boundary invariants

Each nested `RegisteredBatchReceiptReview` is now checked again by the complete-DAG reviewer before aggregation: exact child type; step ID and `act_`/`req_` identities; parent plan and schedule digests; correct schedule wave; independently carried `RegisteredFixtureLink.link_sha256`; retained journal count/tip; lowercase 64-character child review checksum; all five strict-False non-authority flags; and stable child fields after those getter callbacks. The aggregate still independently rechecks every step and retained local journal multiple times.

A matching hash is local diagnostic evidence, not authentic consent, actual historical execution, a single transaction across multiple journals, or a right to retry after uncertain COMMIT. Existing READ journal DDL and frozen agency/Memory contracts are unchanged. No new credentials, paid or external compute, protected V2 evaluation or main merge.

## Next safe work

1. Complete exact-head CI for the corrected test commit and its successor documentation/checkpoint heads; on FAIL inspect logs and repair only the identified defect.
2. Keep future Planner recovery, CAS, registered call permissions, UNKNOWN WRITE and scheduler integration read-only/mock until independent lower-layer GREEN and explicit authorization for effects.
