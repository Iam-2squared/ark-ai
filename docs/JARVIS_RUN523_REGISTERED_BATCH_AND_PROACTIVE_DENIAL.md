# Run523 — disconnected registered READ / DAG correlation and proactive startup denial

**Branch:** `research/jarvis-foundations`, Draft PR #8, unmerged. **Latest source/test basis HEAD:** `20422e2aaac89f77c5f38a76709a1ccca96d4eb1`. **ARK/JARVIS state:** NOT_PASSED.

## Package A — Planner DAG → immutable ToolRegistry → retained READ journal

New `src/ark/agency/disconnected_registered_batch_receipt_review.py` correlates one exact disconnected batch step and its deterministic dependency wave with one original registered `act_` ToolCall, separately retained `act_`→`req_` fixture link, and an SQLite READ-journal witness. The plan digest is independently supplied; plan and schedule are reverified before and after receipt inspection. The existing registered receipt reviewer validates the registry, exact READ grant, fixture request/result binding and journal contents without ever calling the ToolBackend; the journal is read again at the end. The new output contains only bounded IDs and hashes plus explicit false-valued authority flags.

**Important limits:** Plan wavefront position is not proof dependencies ran, journal hashes are not authenticated historic execution, `act_` linkage is a caller-retained assertion, and the SQLite snapshot cannot be made atomically consistent with separately supplied DAG, registry and grant carriers. Neither a READ backend nor a WRITE backend is dispatched; no replay, permission escalation or implicit consent.

`tests/test_registered_batch_receipt_run523.py` covers the positive diagnostic-only path with a dependent DAG; wrong step, unknown step, mismatched retained plan digest, expired grant, mutated DAG operation/args, altered wavefront, forged output after a false authority getter, and locally modified journal rows. All are disconnected fixtures; no external action occurs.

The original exact-source CI [41285955208](https://github.com/Iam-2squared/ark-ai/actions/runs/41285955208) failed Ruff I001 on new imports (6/6 jobs). The import formatting was corrected without semantics changes on `20422e2aaac89f77c5f38a76709a1ccca96d4eb1`; **do not inherit an earlier run's GREEN** for that new HEAD.

## Package B — Scheduler + Startup Readiness final denial

`src/ark/proactive_startup_fence_review.py` now verifies all four last-mile no-authority properties on `SyntheticProactiveStartupReview` (`startup_authorized`, `notification_authorized`, `dispatch_authorized`, `automatic_replay_authorized`) as **exact False**, rechecks original source/receipt/policy/requirement/snapshot witnesses after each property callback, then rechecks snapshot integrity and output scalar carriers before returning. A synthetic READY/trigger marker remains diagnostic, never notification or Tool execution permission. `tests/test_proactive_startup_final_denial_run523.py` checks True/1 authority forgery and late false-valued getter mutations of the output and source carriers.

The initial proactive CI [41286204490](https://github.com/Iam-2squared/ark-ai/actions/runs/41286204490) ran before the import fix in the independent READ module and therefore failed shared Ruff I001. This is not evidence against the proactive semantics; current combined-head CI must still pass all environments before asserting the final source is GREEN.

## Frozen boundaries and honest limits

Main, frozen V1/V2/Local UI/Launcher evidence, Memory v1 schema, Agency contracts, frozen V3 Contract and protected V2 final scorer were not modified. All authorizing real-world actions, provider/billing identities, clock attestation, consent, human-review decisions, durable cross-store atomicity, and externally authenticated provenance remain unproven. No paid/external GPU, credentials, subscriptions, real Candidate generation, protected V2 opening, ToolBackend action, deletion, automatic WRITE replay or main merge.

## Next

1. Resolve any exact-HEAD CI failures, then require GREEN across Ubuntu/Windows Python 3.11–3.13 for the latest combined code.
2. Extend durable Memory CAS and Planner UNKNOWN WRITE **manual-only** recovery, avoiding replay after uncertain COMMIT.
3. Continue scheduler occurrence/restart deduplication, trusted-clock audit-before-action, privacy-safe Personal Context and offline Observation without conflating diagnostic evidence with authority.
