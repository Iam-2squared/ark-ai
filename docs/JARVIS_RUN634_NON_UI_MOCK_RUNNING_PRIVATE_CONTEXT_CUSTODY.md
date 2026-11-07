# Run634 — Non-UI durable mock RUNNING readback and private context report custody

## Scope / provenance

- Repository: `Iam-2squared/ark-ai`; Draft PR #8 `research/jarvis-foundations`, unmerged.
- Work-basis HEAD: `4c4b70f6f7a51ef1a2e4dcebc80e5f4debd3cd23`.
- Baseline CI [#42023898088](https://github.com/Iam-2squared/ark-ai/actions/runs/42023898088): six GitHub Actions jobs completed **success** (Ubuntu/Windows, Python 3.11–3.13). This establishes **baseline only**, not the modifications below.
- No local repository checkout or full local pytest/Ruff proof: container GitHub DNS resolution failed. GitHub Contents API was used for guarded, ordinary file updates, and sources were fetched again to verify persisted paths and Blob SHAs. Test cases are **authored**, not counted as PASS until exact-head CI completes.

## 1. Mock WRITE must confirm durable RUNNING before occurrence reservation

**Why:** a journal append is a callback boundary. Previously the mock cycle ignored its return value and proceeded to a separate SQLite occurrence reservation even if the journal append had been replaced with a no-op or was followed by a terminal transition. This could create orphan cross-store fixture state before the final append rejected it.

**Change:** `src/ark/agency/synthetic_mock_action_cycle_review.py`, commit `29d5dd43d75300e69d091cf9818d026cca3e3808`, Blob `1e0c21b53e7732dd18529ad3c0206b9629b3e2cc`. After `PENDING -> RUNNING`, the cycle performs a new read-only `journal.recover(retained=pre_run_tail)`, rechecks already-pinned input identities, and requires the exact target step `RUNNING` revision 1, inclusion in ambiguous-running steps and precisely one new event **before** touching the occurrence ledger. Failure leaves the action non-replayable; it does not assert rollback.

**Tests:** `tests/test_mock_cycle_durable_running_readback_run634.py`, commit `7cd8615cf9e0295692a31cf6e289289fbae86781`, Blob `4350aacee6a100bd183e46bf608d666960c74014`. Three explicit cases: forged/no-op append, committed RUNNING immediately advanced to FAILED, and valid disconnected mock cycle with restart replay denial. All expect no real backend invocation; both negative cases require zero occurrence reservations and zero audit records.

## 2. Private context verifier pins the *original* detached report

**Why:** `verify_offline_context_preview` previously rebuilt a private fixture preview before pinning its caller-retained report fields. A digest callback could therefore mutate/repair a forged report or replace an equal-valued field carrier while verification was in progress, and value comparisons alone would not reveal the changed report epoch.

**Change:** `src/ark/personal_context_offline_preview.py`, commit `46f7918ee658aee212c251500b15fcbffa4cec17`, Blob `541b60e51e05db01928f4293a781ba4b8f82018c`. Capture exact original report field carrier identities before the rebuild. Recheck them alongside the fixture epoch after callbacks and later review phases; reject changed report receipts without exposing private content.

**Tests:** `tests/test_private_context_retained_report_epoch_run634.py`, commit `fad16d409c04246eea640265fea5bb235c39145b`, Blob `439e685db29459940eda5e640d9900d6e33f8002`. Three authored cases: hash-time repair of a previously forged digest, equal-valued replacement of record-ID tuple, and unchanged local-only verification.

## 3. Coherent Memory snapshot validates UTF-8 before private SQLite reads

**Why:** a lone surrogate in a valid-looking Python `str` can pass the previous bounded request validator and then fail at UTF-8 query-digest encoding **after** scanning Memory rows. Reject malformed owner, namespace, or query text at the request boundary.

**Change:** `src/ark/memory/coherent_snapshot_review.py`, commit `b120a967a1b2496a859dfbbaab2c9c63c1b6d3f0`, Blob `19b078638d2950cd19ec028115ce57a2768c708f`. Strict UTF-8 encoding validation in the **nonfrozen coherent-snapshot request only**, no Memory v1 schema or contract changes. No database access from request validation.

**Tests:** `tests/test_coherent_memory_utf8_inputs_run634.py`, commit `45b7b0a686551aa797d6a779e9be4dc684546695`; three invalid surrogate positions and one valid Japanese/Arabic multilingual request. Four authored cases; no local PASS claim.

## Evidence and boundaries

- Latest source/test HEAD before this report update: `45b7b0a686551aa797d6a779e9be4dc684546695`. The exact source/test CI [#42030554587](https://github.com/Iam-2squared/ark-ai/actions/runs/42030554587) was **IN PROGRESS** at the last recorded check: Ubuntu Python 3.11 GREEN; five other jobs not yet completed. No 6/6 GREEN claim.
- The two work packages are independent: the private-context changes did not touch the mock action cycle's code or its running CI path.
- No UI/frontend changes; PR #9 stays untouched. PR #5 remains Draft/unmerged. No frozen V1/V2/Local UI/Launcher or V3 Contract 1 edits; no main merge, physical-PC actions, real ToolBackend, actual side-effect attestation, user consent, export, retention grant, authenticated clock, cross-database atomicity, paid API/GPU/compute, candidate training, promotion or protected final evaluation.
- **Not a JARVIS PASS.** SQLite re-read can improve local persistence diagnosis but cannot prove external exactly-once delivery, authenticated identity, or user permission. UNKNOWN WRITE/COMMIT remains manual-only; never auto-retry.

## Next / 今後の方針

1. Confirm latest exact-head Ubuntu/Windows 6-job CI; inspect any failed job log and repair only the implicated source/tests via ordinary guarded GitHub paths.
2. Review independent post-audit mock receipt readback (audit-before-action) and cross-store UNKNOWN reconciliation once current mock path CI is GREEN.
3. Continue Memory CAS row/event/expiry integrity, Planner restart-terminal propagation, PermissionGate and ToolRegistry exact identities, disconnected-only observation and free-only V3 guard reviews.
4. Keep UI paused, drafts unmerged, frozen evaluation and spending boundaries intact.
