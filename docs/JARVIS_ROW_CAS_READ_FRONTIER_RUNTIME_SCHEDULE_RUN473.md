# Run473 — exact-row Memory CAS, detached READ frontier, scheduler receipts and free-only V3 runtime custody

**Scope:** Four independent, reversible, local-first implementation/test packages. No protected evaluation, real Tool, OS, GPU, Candidate, data import, paid service, credential, notification, promotion, or main merge. This is new technical evidence, not an approval or full JARVIS PASS.

## Work basis and source/test HEADs

- PR #8 `research/jarvis-foundations` started from `22bba5ddd8e96d8ef9b550194ca412c925757edd`, finished source/test at `477ac60f01ff543ffd480184e3c0d3d8e7ba52b9`.
- PR #5 `research/v3-learning-evaluation` started from `b8cd2ca0c8668b52677af2668689569afaca7a8f`, finished source/test at `05e82f883ffa40c80e406db372afee2007f29ab3`.
- Both PRs remained Draft/open/unmerged when inspected immediately before this document write. No frozen V1/V2/UI/Launcher/Memory v1 DDL/Action Audit or frozen V3 Contract 1 was changed.

## 1. Memory v1 bounded expiry — exact selected row-image CAS

- Source `src/ark/memory/sqlite_store.py`, verified Blob `0aba6392b39563df520aa8b378d0b313f0cc0a0d`.
- Test `tests/test_memory_expiry_exact_row_cas_run473.py`, verified Blob `e43f7553504f10dc834b2232b2a153eb70c76711`. Eight authored pytest cases.
- Previous bounded DELETE matched selected ID/scope/revision and `expires_at_ms<=now`; a synthetic callback could alter an *already expired* row without changing revision and still satisfy the DELETE predicate.
- The mutation now requires exact original memory_id, owner, namespace, source, content, canonical metadata JSON, SHA256, create/update timestamps, revision and **exact original expiry** (plus eligibility <=now). The audit event occurs only after rowcount=1; mismatch raises conflict and rolls back the transaction. Tests exercise same-transaction row changes and rollback of a prior deletion when the later row changes. This does not attest external writers, or eliminate filesystem/connection TOCTOU.
- Initial #1526 / `41015488388` at its own source/test HEAD `635ecc4a4a527ab5d29fa259ef1136b4cd613439` completed SUCCESS as independently observed. Do not relabel this as proof for later READ/scheduler changes.

## 2. Detached READ cycle — independently recomputed wave membership

- Source `src/ark/agency/disconnected_read_cycle.py`, verified Blob `2264e2807ca2cebd139a2af4fc4b502faeeb2151`.
- Test `tests/test_disconnected_read_cycle_frontier_run473.py`, verified Blob `aa95c6abea5e1dd71bc6ca315c02b535393318d1`. Twelve authored cases.
- Validates exact caller clock and grant types, retains grant identity epoch across callbacks, independently recalculates the full shadow DAG ready frontier, and re-binds each expected ToolRegistry READ identity. Forged exact-type preflight receipts cannot omit/reorder ready steps or substitute bound IDs.
- Only a shadow plan changes; no ToolBackend, consent, external receipt, authorization or automatic replay is enabled.

## 3. Detached proactive schedule — exact cursor/result scalar types

- Source `src/ark/disconnected_schedule_preview.py`, verified Blob `2c45568c4f62411c0a72b4033527b7b3d947648a`.
- Final test `tests/test_schedule_preview_result_exact_types_run473.py`, verified Blob `8685f88cee54cd4de56bcb955a3cd71923b7666d`. Seven authored cases.
- Requires the preview constructor to preserve the original state, integer next index, occurrence identity, due timestamp and fingerprint carriers. Prevents `True == 1`, `False == 0` or `10000.0 == 10000` from laundering invalid cursor/time types into an inert schedule receipt.
- No trusted clock, durable occurrence cursor, notification, consent or external Tool authority exists.

## 4. V3 free-only exact runtime identity carriers

- Source `src/ark/learning/runtime_guard.py`, verified Blob `f94b50959dfbc791f0f349380ea6e1a67644796c`.
- Final test `tests/v3/test_runtime_identity_exact_carriers_run473.py`, verified Blob `4a346fb4b6b654acd1d96e9a8909a5ee68c6d3bc`. Twenty-three authored cases.
- Requires an exact `RuntimeIdentity`, exact built-in string fields, exact frozen snapshot/container mappings and exact frozen string fields. Prevents string subclasses with forged `__eq__` and runtime subclasses with overridden `validate` from spoofing the GPU/software manifest.
- Intermediate #1530 / `41015872732` failed Ruff I001 in a new test import; corrected via an ordinary Contents API test edit, without weakening assertions. **Exact final PR #5 source/test HEAD** `05e82f883ffa40c80e406db372afee2007f29ab3` CI #1531 / `41016073075` completed SUCCESS in **all six** standard Ubuntu/Windows Python 3.11–3.13 jobs. No compute, training, Candidate or provider contacted.

## Validation boundaries and next work

All eight changed source/test Git blobs above were independently read from the appropriate exact source/test HEAD and matched. Fifty focused synthetic pytest cases were authored in total, not claimed as locally executed. The working container has no GitHub DNS access for local clone; independently observed GitHub CI is the validation authority for its associated HEAD only.

At first inspection, PR #8 latest source/test #1534 / `41016303125` was IN_PROGRESS, **not full GREEN yet**; previous #1528 / `41015699311` was a distinct historical in-progress READ+Memory build. CI may settle after this evidence is saved. Do not confuse future docs-only check results with the exact source/test check.

**Next:** check exact-head PR #8 #1534 jobs, fix any actual failure without weakening tests, then continue Memory event/CAS integrity, Planner journal/UNKNOWN WRITE quarantine, trusted audit-before-action and privacy-safe scheduler/observation contracts. V3 immutable byte identities, provenance/contamination review, cost/provider approval/caps and physically measured authorized runtime remain blocked without explicit user authorization. No protected V2 evaluation or Candidate promotion.
