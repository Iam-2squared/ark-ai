# ARK AI — Run586: non-UI deny-only custody across epoch, registered READ, and persisted READ receipts

**Saved at (untrusted host timestamp):** 2026-11-04T01:52:35.961+09:00 Asia/Tokyo/JST. This is a development note, not authentication, consent, a trusted clock or model quality evidence.

## Scope / custody

- Work-basis branch HEAD: `c69182b5f9d0df2af821dcb8ac71519fd3c9d4d0`; [previous exact-head CI #41668995856](https://github.com/Iam-2squared/ark-ai/actions/runs/41668995856) **6/6 GREEN** on Ubuntu/Windows Python 3.11–3.13.
- Current source/test write-basis HEAD: `c2701abdc46d82b414010d1e6a957d9e6505588e`. The note commit and any checkpoint commit are separate result HEADs. Do not report them as included in earlier CI.
- All writes went through the normal GitHub Contents API with file blob SHA and fresh branch HEAD checks. No raw Git object write, force push, merge or UI change.

## NEW implementation packages

1. **Cross-store epoch vector** — `src/ark/disconnected_epoch_vector.py` blob `d04901cb8fc7f6c27993e460e2a1a1ee5a623d9f`: capture original deny-only vector property descriptors at import; reject substituted False-looking definitions and reflectively changed result digest/stores after any callback. `tests/test_disconnected_epoch_vector_denial_custody_run586.py` blob `a1d235f290c9cfeaca4de7f7541a7292cb7ca90e`: 13 authored parametrized cases. No coherent cross-store transaction, authenticated custodian, grant or clock.
2. **Registered READ-only preflight** — `src/ark/agency/disconnected_registered_read_preflight.py` blob `82e2938e57766893cf39b1e7c0590e8f5c66e228`: pin original five nonauthorizing report descriptors at import and verify before registry binding and after each report getter, rejecting callback mutations. `tests/test_registered_read_preflight_report_custody_run586.py` blob `ef07206c74131004149048812ae6a4db814a1787`: 13 authored parametrized cases. This never executes a registered ToolBackend, consumes a WRITE authorization, or proves trusted time.
3. **Retained registered READ receipt** — `src/ark/agency/disconnected_registered_receipt_review.py` blob `6fad9ccd0d9d622eb97514faeea0d41202def9f3`: pin original retained-link and output review denial definitions and recheck around local SQLite recovery. `tests/test_registered_receipt_original_denials_run586.py` final blob `29f061d84261c271816c43ee8e2a3a56c878ce3b`: 11 authored parametrized cases, with a follow-up line-length correction. This does not prove an external READ happened, origin identity or replay authority.

**Test count:** 14 new pytest function definitions, 37 parametrized test cases (13 + 13 + 11) authored on GitHub; counts are NOT an independent local pytest PASS result. No physical-PC or model execution was attempted.

## Latest sampled CI — exact HEAD is the test boundary

- [#41678290151](https://github.com/Iam-2squared/ark-ai/actions/runs/41678290151) HEAD `c2701abdc46d82b414010d1e6a957d9e6505588e`: **QUEUED / NOT YET DETERMINED** (sampled 2026-11-04T01:52:35.961+09:00)
- [#41678143713](https://github.com/Iam-2squared/ark-ai/actions/runs/41678143713) HEAD `36bf82b0447f027db7f191c4d107bdad11a0ee9e`: **QUEUED / NOT YET DETERMINED** (sampled 2026-11-04T01:52:35.961+09:00)
- [#41678042310](https://github.com/Iam-2squared/ark-ai/actions/runs/41678042310) HEAD `f54cea6ccf131ac27916c8e258b899e12054eb25`: **QUEUED / NOT YET DETERMINED** (sampled 2026-11-04T01:52:35.961+09:00)
- [#41677830455](https://github.com/Iam-2squared/ark-ai/actions/runs/41677830455) HEAD `6eb2ca2a31080fc90b3c40a6ae72bdd2543bad7a`: **IN_PROGRESS / NOT YET DETERMINED** (sampled 2026-11-04T01:52:35.961+09:00)
- [#41677751094](https://github.com/Iam-2squared/ark-ai/actions/runs/41677751094) HEAD `c296a2b1cc9649f2ec8ce2b4272cb0134a50fd3c`: **IN_PROGRESS / NOT YET DETERMINED** (sampled 2026-11-04T01:52:35.961+09:00)
- [#41677634880](https://github.com/Iam-2squared/ark-ai/actions/runs/41677634880) HEAD `be6f767e5c6c55e1cc0e842eff83eef3b6423511`: **IN_PROGRESS / NOT YET DETERMINED** (sampled 2026-11-04T01:52:35.961+09:00)
- [#41677533200](https://github.com/Iam-2squared/ark-ai/actions/runs/41677533200) HEAD `ca752fa56b9cd5c8fbbfe0f0371ae9866216f603`: **IN_PROGRESS / NOT YET DETERMINED** (sampled 2026-11-04T01:52:35.961+09:00)

No duplicate workflow was manually dispatched. Older GREEN verifies ONLY its precise older commit. An in-flight run is neither GREEN nor FAIL until its jobs finish.

## Frozen evidence / irreversible boundaries

- Frozen PR #8 Memory contract `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c`; Planner `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`. Frozen PR #5 `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`; unchanged after re-read.
- PR #5 `805b377697472268db02650a89c7a94b1c5337c8` Draft/unmerged; PR #9 UI `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` untouched Draft/unmerged; main `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged.
- No paid service, external GPU/compute, real Candidate, protected V2 final evaluation, automatic promotion, real tool dispatch, actual private export/consent, physical PC action, irreversible operation, frozen-contract change or merge. JARVIS/V3 remain **NOT_PASSED**.

## Next plan / 今後の方針

1. Determine six-job exact-head CI on the newest source/test package and subsequent note/checkpoint. For any FAIL inspect job logs and apply a semantics-preserving minimal fix, then work a different non-UI lane while CI starts.
2. Integrate registry-bound identity, restart-safe one-shot audit-before-action and occurrence/replay quarantine only after lower-level exact-HEAD GREEN, with all real backends disconnected.
3. Continue Memory event/generation-CAS/expiry/coherent snapshots and COMMIT-UNKNOWN manual-only reconciliation; Planner terminal/FAILED/BLOCKED recovery; Personal Context consent/revocation, Proactive Scheduler duplicate prevention, offline Observation lineage, and free-only V3 provenance/approval gates.
