# Run578 — Non-UI Memory CAS and disconnected Planner recovery authority

## Scope and saved source

This run is strictly free-only and non-UI. UI Draft PR #9 and protected contracts/evidence are untouched. ARK/JARVIS/V3 remain **NOT_PASSED**. All work stays in Draft PR #8 or Draft PR #5; no main merge.

### Package 1 — generation CAS token carrier-epoch validation

- Source `src/ark/memory/generation_fenced_cas.py` at commit `78465a7a556352aee819a6bab828b819f6583ca2`.
- Regression `tests/test_memory_generation_token_carrier_epoch_run578.py` at commit `4e02bb233155def9794cd618cabab56d75426c3b`: 3 authored cases, two field-specific clock callback substitutions plus one unmodified local CAS.
- Previously, a reentrant synthetic clock could rebind a `MemoryGenerationCASToken` field to a different but equal-valued string, and the write's input-stability check compared value equality only. This change also checks the **same retained field carriers** across the write epoch. An in-transaction rejection must not alter the record or event log.
- This local SQLite comparison neither proves trusted clock nor grants consent; a COMMIT-uncertain return is never authority for automatic retry.

### Package 2 — Planner synthetic recovery denial identity

- Source `src/ark/agency/planner_journal_review.py` at commit `b80a77dd08615ceda92aa3abeff1daaeb3b83c77`.
- Regression `tests/test_planner_journal_original_denials_run578.py` at commit `76785227cf0da1ff4cda8bacd8a93405e2bccc7e`; scoped callback fixture correction `64c89a9594ca1ca9b4691277805254abcf3bbae6`: 7 authored cases (four early preinstalled False-only replacement probes; two mid-snapshot reentrant replacement probes; one intact FAILED terminal replay).
- Pin the imported synthetic recovery result class and its two False-only denial property descriptors. Reject replacement **before journal database access** on `recover`/`append`, and repeat original-denial checks during synthetic result assembly, including after each property getter. A receipt remains a replay-only witness, not dispatch/retry authorization.
- This covers neither live ToolRegistry/PermissionGate execution nor independent trust of the journal writer, hardware actions, trusted time, or external exactly-once effects.

### Package 3 — V3 free-only test-import correction

- PR #5 only, `tests/v3/test_passive_shape_oracle_original_run577.py`, fixes Ruff `I001` observed in the previous exact-head six-job CI [#41615111987](https://github.com/Iam-2squared/ark-ai/actions/runs/41615111987).
- First correction commit `2c3941488cb26b78bf8d1b7aee888c983fa77343` was also rejected by all six CI jobs on `I001` [#41622081901](https://github.com/Iam-2squared/ark-ai/actions/runs/41622081901). Second correction `b502675cfe0e38d77a2f5526fdb48d09ff142fe1` groups sibling imports in one canonical block. It does not modify model logic, approval rules or protected V3 evaluation.

## Evidence / safety limits

- At the beginning of the run, PR #8 checkpoint HEAD `431bfda41d382264c240b801bc3991699fbdfc77` was independently observed **six/six GREEN** [#41614983874](https://github.com/Iam-2squared/ark-ai/actions/runs/41614983874). That is **prior-head evidence only**.
- Updated code/test **exact-head six-job GREEN is not assumed**. Inspect the latest CI after this note; if any job fails, review its real logs and correct with the normal GitHub Contents API only. Authored pytest case counts are not claims of independent local execution.
- Verified existing frozen PR #8 Memory contract blob `b6e93821ecd69270a7634aceb20775dc36e9953c`, Planner contract `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`, PR #5 Contract blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`. V1/V2/Local UI/Launcher evidence is not modified.
- **No** paid/billable compute or APIs, external GPU, new credentials/secrets, protected V2 final-evaluation opening, real Candidate/model training/export/promotion, real tool execution, destructive effects, physical-PC action, or main merge.
- PR #9 Command Center UI remains completed, **Draft and entirely untouched**. No new frontend work until explicitly resumed.

## Next / 今後の方針

1. Resolve PR #8 and #5 exact-head six-job CI without assuming prior-head success; fix only observed failures.
2. Expand generation-CAS post-COMMIT ambiguity and independently retained receipts, privacy expiry/revocation; freeze schema and non-authorization intact.
3. Integrate disconnected Planner FAILED/BLOCKED recovery with immutable registry-identity and exact PermissionGate proofs only when lower-level HEADs are GREEN.
4. Continue scheduler occurrence replay, privacy-safe Personal Context, local observation fixtures and V3 free-only guards. No UI work.
