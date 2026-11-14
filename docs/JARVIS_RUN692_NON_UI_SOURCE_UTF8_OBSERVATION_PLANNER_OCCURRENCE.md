# ARK Run692 — offline identity, observation, Planner and occurrence regressions

**Status:** FREE-ONLY, non-UI, synthetic fixture/test work in Draft PR #8. No production module, frozen contract, PR #5, PR #9, `main`, real action, protected evaluation or Candidate runtime changed.

## Exact basis and packages

Initial basis: PR #8 `6062c1cb5a43ee184d8b07f0affab3409c5dcaca` (Run691 checkpoint). All four packages are on `research/jarvis-foundations`, without UI/frontend changes or new services.

1. **Memory generation source identity**, `a91efb7aa2da54404b86a896f3fec5413db8fba9`, `tests/test_memory_generation_source_identity_run692.py`: **21** cases. Six mutated/bad UTF-8 or oversized source IDs fail before generation snapshot SQLite; six fail before opt-in write SQLite without spending the retained CAS token; six fail before private post-COMMIT manual review; three exact 512-byte multibyte identities work across SQLite handles while review remains non-authorizing. No Memory v1 public identity contract change.
2. **Observation request labels**, `86a98816ee83cc0a5d5b39d18129c183316d271d`, `tests/test_observation_request_label_utf8_run692.py`: **20** cases. Twelve invalid query source/privacy labels (surrogates, whitespace, UTF-8 byte overflow) fail before private fixture identity hashing. Eight valid exact 1024-byte labels retain deterministic one-envelope result and explicit denial of consent, source authentication and dispatch. No media capture.
3. **Planner canonical READ evidence**, `bdfa25703ba8ddb585a34a7a08d85b75a91befc9`, `tests/test_planner_read_bundle_canonical_order_run692.py`: **30** cases. All 24 permutations of four detached per-step receipts and six permutations for a three-SUCCEEDED/one-PENDING DAG must produce the same canonical local bundle, without dispatch/replay. The missing fourth success receipt is never inferred. Synthetic digest equality is not independent execution custody.
4. **Durable synthetic occurrence replay**, `1dec0702396beea612234b4c18a66729fdff8892`, `tests/test_synthetic_occurrence_token_replay_run692.py`: **6** cases. On a newly opened SQLite reservation store reject reused token/occurrence across same or different requests, backward caller clock and expired one-shot token. A subsequent independent reservation remains possible; the mock backend must remain uncalled.

**Total: 77 new parametrized cases, four new test modules.** Production source and schemas remain unchanged this run. These are offline safety regressions, **not** authenticated consent, trusted time, external exactly-once effects, action authorization, or a JARVIS completion PASS.

## CI chronology and observed limitations

- Incoming Run691 checkpoint at `6062c1cb5a43ee184d8b07f0affab3409c5dcaca`, [CI #42398792060](https://github.com/Iam-2squared/ark-ai/actions/runs/42398792060): **6/6 GREEN** (Ubuntu/Windows, Python 3.11–3.13), observed through exact commit workflow and job results.
- Early A [#42403182683](https://github.com/Iam-2squared/ark-ai/actions/runs/42403182683), B [#42403227224](https://github.com/Iam-2squared/ark-ai/actions/runs/42403227224) and C [#42403291059](https://github.com/Iam-2squared/ark-ai/actions/runs/42403291059): all 6 jobs FAIL on **Ruff import-block spacing** in the new Memory test module; **pytest not reached** on these ancestor HEADs.
- Minimal import-spacing correction to the Memory test only: `239e4d9f8fe8d22f54d73ec5f2357eb354fdbfa1`. Correction [#42403403955](https://github.com/Iam-2squared/ark-ai/actions/runs/42403403955) and four-package [#42403498647](https://github.com/Iam-2squared/ark-ai/actions/runs/42403498647) were **IN PROGRESS** at sampling. Do not infer final 6/6 GREEN or 77/77 passing until exact-head CI is observed.
- The later report/status commits create distinct HEADs and associated automatic CI runs. They must not be asserted GREEN based on ancestor runs.

## Preserved hard boundaries

PR #5 V3 learning/evaluation remains Draft/unmerged and blocked on actual immutable local base/runtime hashes, legally reviewed provenance/contamination/rights decisions, cost/compute identity, and separate approvals. Protected V2 final evaluation remains unopened. PR #9 UI remains Draft/unmerged and untouched, all new UI/frontend work paused. V1/V2/Local UI/Launcher freezes and `main` stay unchanged. No paid API, external GPU/compute, credentials, new account connection, real Candidate/export, physical-PC action, authenticated review, destructive migration, actual backend dispatch or main merge.

## Next plan / 今後の方針

1. Confirm latest four-package **and checkpoint-result** CI six jobs; when a failure exists, inspect its exact job logs and perform only semantics-preserving correction via ordinary Contents API, using independent non-UI work while CI runs.
2. Close the opt-in Memory CAS **metadata UTF-8 preaccess** guard gap only after matching code/tests are reviewed; hold COMMIT-UNKNOWN as manual-only, preserve privacy revocation and coherent WAL snapshots, never automatically retry.
3. Add independent durable Planner READ custody/recovery; distinguish deterministic local digest from authenticated source evidence. No UNKNOWN WRITE auto-replay.
4. Advance disconnected ToolRegistry/PermissionGate + occurrence/audit-before-action readiness, Personal Context privacy and proactive scheduler contracts, without enabling actual execution; maintain the separate free-only V3 approval boundary.
