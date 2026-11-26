# ARK AI Run612 — Non-UI memory event-log custody, disconnected startup, and WRITE-slot witness guards

**Scope:** Draft PR #8 `research/jarvis-foundations`, based on prior checkpoint `c13c827bbaec50c8e2d4e97c72ca630650bc7e9a`. The eight-commit implementation and test basis is `2ca89d8e393a1656752b3b909a81c26a86744fd9`. This report does not claim physical-PC verification, actual tool execution, paid compute, or a JARVIS PASS.

## Log-supported previous CI repair

Prior exact Run611 CI [#41881607221](https://github.com/Iam-2squared/ark-ai/actions/runs/41881607221) finished **6/6 FAIL**, with eight pytest failures: three cases in `test_proactive_freshness_authority_run513.py` expected one forged getter call but stronger original-descriptor checks reject **before** that call; five cases in `test_read_bridge_postauthority_receipt_epoch_run499.py` expected receipt-construction failure after a forged callback, but the new binding epoch guard rejects before receipt construction with `fixture rebinding failed`. Source enforcement was not weakened. Test-only commits `1f8959fc4282550d76c72c90d8c61ec1d99bda85` and `6c8c268330feadfbf469d16a951c0bbadad7c199` assert **zero** injected getter/constructor calls, with exact early-denial messages. Repair-head CI [#41889676028](https://github.com/Iam-2squared/ark-ai/actions/runs/41889676028) was **Ubuntu 3/3 GREEN, Windows 3 jobs IN PROGRESS** at last observed checkpoint evidence read; not yet a complete 6/6 PASS.

## NEW package 1 — Memory generation CAS global append integrity (8 new authored cases)

Source `src/ark/memory/generation_fenced_cas.py` commit `62261e04c59150480d30cfca0a2d5a1f6d77199e`; tests `tests/test_memory_generation_global_tail_run612.py` commit `1b7cedce558f6fe8a44cf47cc0a285f373360413`. A row-local generation token alone does not detect deletion of an *unrelated* row's event history. `_snapshot` now verifies the entire local `memory_events` sequence count/min/max and `sqlite_sequence` high-water **inside its existing SQLite read or write transaction**, before accepting the row-local token and before a fenced write. Seven synthetic corruption fixtures cover unrelated earlier/later deletion, removed terminal lifetime, complete event removal, and modified/missing high-water. One normal two-row fixture confirms a valid update remains possible. The extra global query is O(number of events), a deliberate fail-closed local consistency cost; it is **not** writer authentication or independent custody. Coordinated rewrites of both history and the local sequence may remain undetectable.

## NEW package 2 — startup readiness original deny-only authority (5 new authored cases)

Source `src/ark/disconnected_local_readiness.py` commit `312ed5cead77aa5fc191f8ba3265e309a13b696c`; tests `tests/test_disconnected_readiness_pregetter_run612.py` commit `3b63f2b0bab8ea1b38fc0316f7125847f84d7a7d`. Revalidate original schema, READ-preflight, and report authority descriptors **before and after each getter**, so a preceding dynamic read cannot install a False-looking executable property without detection at the next boundary. Use the pinned import-time report constructor rather than a mutable global class reference. Three synthetic reentrancy fixtures, one post-hash constructor replacement fixture, and one normal query-only startup fixture. No backend dispatch or actual approval.

## NEW package 3 — persisted WRITE reservation retained witness denial (6 new authored cases)

Source `src/ark/agency/disconnected_write_slot_ledger.py` commit `40235e9585deaa8c74ea0d41a1c5e5895ac97126`; tests `tests/test_write_slot_original_witness_denial_run612.py` commit `2ca89d8e393a1656752b3b909a81c26a86744fd9`. An injected `independently_authenticated` property returning either True or False is refused **before invocation**, including after a synthetic SQLite inspection callback. Four paired direct inspect/reserve cases, a late-injection pre-COMMIT rollback case, and a normal inert reservation/reopen case. SQLite reservation uniqueness does not prove an exactly-once external effect. Unknown COMMIT is **not** retry authorization.

## Evidence / non-claims

Independent compare `c13c827...2ca89d8...` returned **eight paths only**: three non-UI sources, three new test files, and two old test assertion files; main, UI branch, and frozen contracts were not in the change set. **19 parameter-expanded new cases authored (8 + 5 + 6); not a claim of 19 local pytest PASS**. No local checkout was possible because container DNS could not resolve `github.com`; GitHub Actions is the verification source, and queued/in-progress results are never asserted GREEN. Memory and startup diagnostics are local, disconnected, read-only where declared, and fail closed; no independently signed witness, authenticated user consent, trusted clock, remote write provenance, physical exactly-once guarantee, or protected evaluation claim.

Strict zero-cost boundary respected: no paid service/API/GPU, no real Candidate generation, no actual notifications, no external tool backend, no private export, no destructive action, no protected V2 final evaluation, no contract changes, no Candidate promotion, and no approval-required main merge. PR #5 and paused UI PR #9 remain Draft/unmerged and untouched. Overall ARK/JARVIS/V3 **NOT_PASSED**.

## Next plan / 今後の方針

1. Check the exact final checkpoint HEAD CI on Ubuntu/Windows Python 3.11–3.13; repair only real failures with normal Contents writes.
2. Continue generation CAS ambiguity/manual-only recovery and global memory event/row coherence without confusing a matching state with commit ownership.
3. Advance Planner crash recovery + registry-bound PermissionGate + audited occurrence mock handoff **only after the dependent exact-head CI is GREEN**.
4. Keep privacy/retention and proactive/observation provenance fixtures independent; maintain V3 free-only gates and UI pause.
