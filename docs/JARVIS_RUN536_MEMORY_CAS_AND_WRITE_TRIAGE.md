# Run536 — Memory ambiguous-CAS observation and UNKNOWN WRITE manual fence

**Scope:** two independent **free-only**, disconnected/reversible JARVIS foundation packages, plus exact-test correction and safety review. No real ToolBackend, network service, GPU, trusted clock, secret, human consent or protected V2 evaluation. Main and frozen contracts remain untouched.

## Work bases and saved changes

- PR #8 `research/jarvis-foundations`, Draft/unmerged, started this run at `8789f9539c3f2154f7eb78514bb53c7d1e83e567`.
- Memory source `src/ark/memory/generation_cas_outcome_review.py`: initial `d701be4cc2376ac145661e39666f5a3a9b8085b3`, updated in `49aee79bca0dfbb2cd1064d234289626b159533a`, Ruff import-only correction `06af4f6386e2ce3fce5511b625ae5a0b2b904c22`.
- Memory tests `tests/test_memory_generation_cas_outcome_run536.py`: `3221a199ff0c3afe163308ad2dac2b31d26ab795`, **13 authored pytest cases** including parametrized cases. The initial test CI [41338071925](https://github.com/Iam-2squared/ark-ai/actions/runs/41338071925) identified **one real rejection gap** for a stale-but-valid-length row hash; first patch closed same-revision row and historical-prefix checks, and subsequent CI [41338559487](https://github.com/Iam-2squared/ark-ai/actions/runs/41338559487) failed Ruff import-order only. Latest corrective import CI [41338975568](https://github.com/Iam-2squared/ark-ai/actions/runs/41338975568) was **IN PROGRESS** at this record's composition; do not label the latest HEAD GREEN without reading all six job conclusions.
- Manual WRITE source `src/ark/agency/offline_write_manual_triage.py`: digest-custody patch `fc03700f4b56514142ec68b5498dc06225f67dc6`, exact canonical NUL-domain escape correction `7063d3b4dc2ace4bb048f5b5dd6b9f9d9df6732d`. Tests `tests/test_offline_write_triage_fence_digest_run536.py` in `7e238ffd862359685cb9e47ed9e4f86b0ddcc72d`, **10 authored pytest cases** including parametrized adversarial child-forgery cases. [Prior CI 41338809221](https://github.com/Iam-2squared/ark-ai/actions/runs/41338809221) failed Ruff in the *independent Memory module*, which was subsequently fixed; this run does **not** prove the WRITE code failed semantically.

## Memory generation CAS: ambiguous post-COMMIT report

The new opt-in `review_memory_generation_cas_outcome(store, proposed, retained=...)` is a read-only investigation aid. It makes two coherent row/event reads in one SQLite snapshot and a second snapshot-based inspection after checking all report-denial callbacks. It checks the exact existing row identity, retained lifetime `create_event_id`, monotone revision/event head, and the independently retained event-prefix digest rederived from the persisted **prefix** (not just the current live head). A stale same-version row SHA is rejected even when it is syntactically valid.

It emits **only**:
- `UNCHANGED_OBSERVED`: retained row/history still match; not permission to retry.
- `ONE_MATCHING_UPDATE_OBSERVED`: next revision visibly matches requested content/metadata/expiry; **does not attribute that update to this invocation**. An independent writer could have committed identical bytes.
- `DIVERGED_OBSERVED`: current live same-generation row differs or has more than one update.
- Deleted, recreated, missing, malformed, reindexed, corrupted, unbounded or unsafely changing lifetimes are **rejected for manual review**, never silently re-created or retried.

The report denies `commit_attributed_to_caller`, `automatic_retry_authorized`, `consent_authenticated`, `trusted_clock_verified`, and `external_action_authorized` with exact `False` values. Event prefix binding is **not a signature**, authentic writer identity, WAL erasure proof or physical storage crash guarantee. Frozen Memory v1 `put/delete` API and schema are unchanged. This is diagnostic-only, no permission to extend retention or reveal private text.

## Manual UNKNOWN WRITE child provenance

The existing read-only `build_offline_write_triage_packet` still requires a complete local reservation ledger and independently retained witness. This update independently verifies that its returned recovery fence and nested dispositions are exact types, that source claim ordering and every `(step_id,effect,deps,state,result,reservation,code)` tuple is unchanged, and that the **domain-separated SHA-256** of the full canonical claims+decisions equals the returned child's digest. It repeats a false-authority denial sweep and rechecks frozen carriers before returning.

A child returning plausible step IDs or a 64-hex fake digest cannot silently remove UNKNOWN/RUNNING WRITE quarantine. The validated output is still a **human investigation checklist only**: no dispatch, replay, automatic confirmation, actual external outcome, consent, or WRITE permission is created. A claimed `SUCCEEDED` WRITE remains unauthenticated until independently reviewed.

## Next safe integration

1. Confirm six-platform CI on the latest corrected Memory and manual-WRITE code; fix actual failures with the smallest semantics-preserving change using the normal GitHub Contents API.
2. For Memory: consider stable independent persistence of a retained generation witness without claiming secret signatures, and a fail-closed manual triage path for ambiguous outcomes, not automatic retry.
3. For Planner: connect offline terminal `FAILED/BLOCKED` archival evidence to registered READ receipts only after exact-head verified invariants, without backends or external actions.
4. For V3: maintain fully separate approval, immutable artifact, provenance and GPU/spend gates.

**HARD STOPS:** PR #5 and #8 stay Draft/unmerged; no paid/external compute, no actual Candidate/adapter generation, no model/file hashes invented, no protected final V2 evaluation, no automatic promotion, no frozen-contract changes and no main merge.
