# ARK AI — Run670 | non-UI preflight / dual Memory diagnostics / observation request bounds

**Evidence status:** Saved on Draft PR #8, local-only, free-only. This document records authored changes, not a JARVIS PASS or completed cross-platform certification. Sampled administrative time 2026-11-07 06:50:16 Asia/Tokyo/JST; not an authenticated time source.

## Scope and exact work basis

- Branch: `research/jarvis-foundations`, PR #8 Draft/unmerged.
- Initial verified HEAD: `31f106879f54d932329882ddd2691bfda0aa9fbe` (Run669). Run669 CI [#42292848693](https://github.com/Iam-2squared/ark-ai/actions/runs/42292848693) was independently confirmed **completed success in all six Ubuntu/Windows × Python 3.11/3.12/3.13 jobs** before new writes.
- Work HEAD before this report: `fbf0224cb66d6595c6e8b13aac7867c4375d87ef`. The GitHub compare endpoint reported **6 commits ahead, 0 behind, five non-UI changed paths**.
- The report's commit SHA and the later checkpoint SHA can only be observed *after* each ordinary Contents API write. Neither should be preclaimed as evidence.

## Package A — proactive restart authority checks at ingress

`src/ark/offline_schedule_resume_review.py` now checks the import-original result denial descriptors, the original QuarantineWitness authenticity denial descriptor, and all DisconnectedDuePreview authority descriptors in `_require_original_result_carriers()`, **before accessing the private ledger path, schedule cursor or retained quarantine fields**. A substituted getter returning False must not become the authority baseline. Previous later `stable()` checks remain; no notification, dispatch, clock attestation or automatic replay is added.

`tests/test_schedule_resume_prepath_denial_run670.py` adds **4 authored cases**: three separate hostile denial-property replacements with a poison private SQLite path access detector, plus an unmodified deny-only restart. An initial CI run [#42299550923](https://github.com/Iam-2squared/ark-ai/actions/runs/42299550923) failed real Ruff E501 on one too-long test vector (110 > 100); a **test-only line wrapping fix** at `fbf0224cb66d6595c6e8b13aac7867c4375d87ef` preserves the same inputs and rejection expectations. The historical failed CI must remain recorded.

## Package B — two independent COMMIT-UNKNOWN reviews agree without caller attribution

`tests/test_memory_two_diagnostic_no_attribution_run670.py` adds **4 authored cases** for local SQLite handles with an unrelated-owner event and (1) no target update, (2) one externally committed identical update, (3) an externally committed divergent metadata update, or (4) two externally committed identical updates. Both `review_uncertain_memory_commit` and `review_memory_generation_cas_outcome` are compared on retained/observed event digests. Expected classifications differ by API but agree on state: LOCAL_UNCHANGED/UNCHANGED_OBSERVED, ONE_MATCHING_UPDATE_VISIBLE/ONE_MATCHING_UPDATE_OBSERVED, or INDETERMINATE/DIVERGED_OBSERVED. All returned authority flags must remain False; no auto retry, write, consent, source attribution or trusted time. No Memory implementation or frozen v1 schema changed.

A matching row/event after COMMIT-UNKNOWN is **not** proof of the original caller's commit. An independent writer can commit the same bytes, and the two read-only diagnostics cannot independently establish authorship, cross-store atomicity or exactly-once external action.

## Package C — UTF-8 byte budget on observation chain *query* labels

`src/ark/observation_fixture_chain_review.py` previously rejected overlong source/privacy query labels by Python character count only; envelope v1 already restricted each label to 1024 **encoded** bytes. The chain now encodes both request labels strictly and rejects any that exceed 1024 UTF-8 bytes before reading private observation fields or invoking fixture validation. It retains the existing invalid-surrogate rejection and all provenance/chain digest semantics. No hardware device capture, media retention, external source or network action.

`tests/test_observation_chain_query_utf8_run670.py` adds **8 authored cases**: a valid exactly 1024-byte non-ASCII label for each query field, two oversize Unicode forms for both fields, and unpaired surrogate invalidity for both fields. No identities, consent or observation provenance are fabricated.

## CI / verification and allowed boundaries

- Inherited exact-head [Run669 CI #42292848693](https://github.com/Iam-2squared/ark-ai/actions/runs/42292848693) **GREEN 6/6**.
- Source-only [#42298988896](https://github.com/Iam-2squared/ark-ai/actions/runs/42298988896): Ubuntu 3/3 GREEN at the sampled job inspection, Windows IN PROGRESS.
- Memory test [#42299151906](https://github.com/Iam-2squared/ark-ai/actions/runs/42299151906): Ubuntu 3/3 GREEN at sampled inspection, Windows IN PROGRESS.
- Observation source [#42299405204](https://github.com/Iam-2squared/ark-ai/actions/runs/42299405204) and observation cases [#42299486818](https://github.com/Iam-2squared/ark-ai/actions/runs/42299486818): IN PROGRESS at sample.
- Proactive new-test [#42299550923](https://github.com/Iam-2squared/ark-ai/actions/runs/42299550923): genuine Ruff E501 FAIL on Ubuntu Python 3.11/3.13 sampled; corrected via standard Contents API; repair-HEAD [#42299745140](https://github.com/Iam-2squared/ark-ai/actions/runs/42299745140) was QUEUED when sampled. **16 new authored cases and latest exact-HEAD 6/6 GREEN remain UNVERIFIED** until the jobs finish.
- No paid API, GPU, external compute, new credential, protected evaluation, Candidate artifact/promotion, real tool execution, destructive operation or main merge. V1/V2/Local UI/Launcher frozen evidence unchanged. PR #5 and UI PR #9 remain Draft/unmerged; the UI lane was not touched.

## Targeted follow-on work (dependency-aware)

1. Confirm final source/test and checkpoint exact-head CI; inspect real failures and fix only with ordinary GitHub Contents writes, without bypass or weakening the new preaccess guard.
2. Tighten privacy-safe Personal Context return receipt class/field/denial preflight and reentrancy at source, preserving legacy regression intent. This is an **identified next-audit target**, not claimed as implemented here.
3. Continue Memory CAS expiry/ABA/row-event coherent snapshot and Planner success Receipt custody. Keep recovered unreceipted SUCCEEDED blocked, and connect Registry/PermissionGate/audit-first occurrence only in disconnected mock after lower-level exact-head GREEN.
4. Continue V3 local-license/path/reproducibility guards without training, weights, protected final evaluation or automatic promotion. Maintain explicit authorizations, frozen contracts and UI pause.
