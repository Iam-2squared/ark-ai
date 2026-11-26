# Run660 — Non-UI cross-handle ambiguity and registry-revision replay fences

**Report sampled:** 2026-11-06T20:45:28.980+09:00 (Asia/Tokyo/JST, administrative timestamp only).  
**Work basis:** PR #8 `research/jarvis-foundations` at `d987506b4ff0edaff9c6fd008d7d56c01990b98f`, previously verified with [CI #42207377805](https://github.com/Iam-2squared/ark-ai/actions/runs/42207377805): all six matrix jobs GREEN. PR remains Draft/unmerged.

## Package A — local Memory COMMIT-UNKNOWN, two SQLite observers

Added `tests/test_memory_ambiguous_cross_handle_phase_run660.py` at commit `514cb3107a60155e74693f1744561415b6f701e9` (three parameterized cases). A second `SQLiteMemoryStore` connection mutates **the same target** during (1) the gap between independent child reviews, (2) between full double-observation passes, or (3) a delete/recreate lifetime transition. The pair must reject a split epoch rather than return a purported matching receipt. Each test explicitly distinguishes a synthetic writer's durable mutation from an automatic retry by the reviewer. No writer identity, human consent, clock trust, authentication, or external exactly-once conclusion follows from this diagnostic.

[CI #42212163613](https://github.com/Iam-2squared/ark-ai/actions/runs/42212163613) failed in all six matrix jobs **at Ruff**, before pytest, for one unused import (`F401`). That single test import was removed in the ordinary Contents update `b195d686172a9316f39eb6f5f7399c420ccd6ee5` without modifying reviewer semantics. The intervening [CI #42212275007](https://github.com/Iam-2squared/ark-ai/actions/runs/42212275007) also failed at the same inherited Ruff error. Repair CI [#42212359897](https://github.com/Iam-2squared/ark-ai/actions/runs/42212359897) is not claimed GREEN unless all six jobs at its exact SHA complete successfully.

## Package B — registry revision changes must not erase occurrence history

Added `tests/test_registry_revision_occurrence_isolation_run660.py` at commit `ba32ecd954190e3bd48635c7032f2dfef4d01491` (three cases). The fixture uses two immutable `ToolRegistry` snapshots with the same exact mock tool but different backend identifiers/revisions. It verifies that a persisted SQLite reservation rejects (a) the same one-shot token under a changed registry with a fresh occurrence, and (b) the same occurrence under a changed registry with a fresh token. It also demonstrates that new distinct tokens/occurrences produce **inert** synthetic receipts: `dispatch_authorized=False`, `outcome_known=False`, `automatic_replay_authorized=False`. The backend's `execute` method is never called.

A fresh process-local `PermissionGate` accepting a new mock grant is not a durable human approval and cannot override the SQLite unique constraints. A registry hash does not attest physical backend bytes or external effects. Tests are source-level, not a proof of restart-safe actual execution.

## Package C — Unicode-exact private source custody

Added `tests/test_offline_redaction_unicode_source_custody_run660.py` at `90899473b556c707a725a9bde39ead5937791397` (four cases). Three independently retained source SHA-256 witnesses deliberately distinguish Unicode codepoint sequences which normalize to the **same display text** (NFC): accent composition and the Angstrom sign. Each full-mask preview hides the same surface plaintext, but exact original UTF-8 bytes and privacy-local hashes remain distinct. An old witness must not accept visually similar new input. The fourth case checks an entirely covered joiner/non-BMP/RTL sample and denial of all downstream disclosure/erasure/dispatch claims. This is not automated redaction, a consent proof, or an external export route; only disposable synthetic fixture strings are used.

**Total authored Run660 test cases:** ten (3 Memory + 3 Registry + 4 privacy). No exact-head all-six PASS claim is made until the GitHub matrix for the combined SHA completes GREEN.

## Independent V3 free-only preflight audit

Read existing Draft [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) at `805b377697472268db02650a89c7a94b1c5337c8`, including `docs/v3/CONTRACT.md`, `PRE_PAID_COMPUTE_GATE.md`, and `HF_IDENTITY_REVIEW.md`. The contract requires exact immutable upstream/model/tokenizer identities, traceable 120/30 dataset rights and human contamination review, pinned runtime/export hashes, explicit device/cost/time approval and separate preflight/full-training/evaluation gates. The stated model metadata cannot serve as the materialized immutable revision or byte inventory. **No V3 gate is opened by these two JARVIS tests or this report.** No paid service, model download, GPU operation, Candidate adapter creation, or protected V2 evaluation was attempted.

## Integrity limits and next integration steps

- All tests authored in the three new files: **ten**. Their presence in Git does not mean six passing test cases. The previous checkpoint SHA is GREEN; new exact-head evidence is pending until CI confirms.
- No modifications to PR #5, PR #9, UI/frontend source, frozen V1/V2/Local UI/Launcher contract or main.
- Local diagnostic digests and SQLite row uniqueness detect specific failure classes but never establish externally authenticated consent, a trusted clock, actual effect delivery, or automatic replay permission.
- On CI failure, inspect one failing Ubuntu job first, correct the minimum test defect without weakening integrity code, and let independent work continue. Once six-job GREEN on the exact test HEAD is established, advance audit-before-action / detached ToolRegistry–PermissionGate–Planner mock bridge without connecting real tools.
