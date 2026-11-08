# ARK AI — Run712: exact-log CI repair, offline context prefix digest custody, post-COMMIT quarantine

**Recorded at:** 2026-11-08T21:51:52.245+09:00 (administrative runtime clock sampled before this report write; not an authenticated trusted clock). **UTC:** 2026-11-08T12:51:52.245Z. **Branch:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), OPEN/Draft/UNMERGED. **Initial inspected work-basis HEAD:** `209a1dfd161bef3d47863e6f6c24deef643295d4`. **Pre-report HEAD:** `d1f657a0122c9bc1490c2c02aa5e7310179783f7`.

## Changes saved in this invocation

### A. Six previously failing CI cases — semantics-preserving repair

The exact Run711 checkpoint [CI #42478257222](https://github.com/Iam-2squared/ark-ai/actions/runs/42478257222) completed **FAIL in all six Python 3.11–3.13 / Ubuntu and Windows jobs**. Actual Ubuntu 3.11 and Windows 3.11 job logs identify **six** legacy assertions inconsistent with new earlier fail-closed checks, not a previously confirmed GREEN. Changes are confined to legacy tests:

- [`65e0812`](https://github.com/Iam-2squared/ark-ai/commit/65e0812ef0153e3218dfe5ff4dc61164d50434a1): a substituted SHA-256 fixture binding callback is rejected at the earlier "fixture recomputation rejected" boundary, before any counterfeit binding constructor executes. The test retains its zero-constructor-calls invariant.
- [`e1869b2`](https://github.com/Iam-2squared/ark-ai/commit/e1869b21af6d8fb78972b7453a91281c32a20941): the three tool result denial cases no longer substitute the newly pinned SHA-256 primitive (which would intentionally trigger an earlier unrelated guard). Instead, they install a forbidden JSON-stage callback and verify that authority descriptor mutation is rejected before fixture JSON processing. The authority-denial expectation remains unchanged.
- [`1a5d7d0`](https://github.com/Iam-2squared/ark-ai/commit/1a5d7d02213d487e0ed5e42ae940e297e70cba24): the two old quarantine tests now assert **pre-COMMIT** denial of a rebound receipt constructor, zero injected constructor calls, **zero persisted quarantine rows**, and an unchanged retained witness, instead of falsely asserting that a new preflight rejection occurred after COMMIT. Production quarantine logic is unchanged.

### B. Privacy-safe Context retained-prefix review — one optional backend source and seven regressions

- [Source `4c6d238`](https://github.com/Iam-2squared/ark-ai/commit/4c6d23811629efca71200bfeb382f83adc1b7141) pins the import-original SHA-256, JSON serialization, module identities and domain separation **before accessing retained witness data or SQLite**, and rechecks the same identities at existing stable boundaries. These digests concern synthetic but **linkable** Context request metadata; no context text or real disclosure permission is generated.
- [Tests `2373f93`](https://github.com/Iam-2squared/ark-ai/commit/2373f933c4b21751160633715303a1aa87487358) add **7 tests**: five preinstalled hostile SHA/JSON/domain mutations denied before SQLite or injected callback; one mutation during retained SQLite observation denied before hashing; one healthy genesis-prefix review retaining all seven deny-only properties.
- This is **not** cryptographic independent custody or a trusted witness; callers must still retain history independently. No existing frozen Memory/Context schema changes.

### C. Genuine quarantine post-COMMIT denial — two new tests

- [Tests `d1f657a`](https://github.com/Iam-2squared/ark-ai/commit/d1f657a0122c9bc1490c2c02aa5e7310179783f7) add **2** new tests on an actual **after-COMMIT read boundary**, covering SQLite history tampering detected by chain validation and runtime policy-epoch carrier drift after durability. Each verifies the row was **already committed** before the injected failure; a rejection does **not** imply rollback, safe retry, notification, or dispatch.
- This restores coverage of the true late-denial semantics distinct from the two corrected **pre-COMMIT** constructor-rebinding tests; only synthetic local SQLite is exercised.

## CI evidence / limits

- Base exact-head [#42478257222](https://github.com/Iam-2squared/ark-ai/actions/runs/42478257222): **6/6 FAIL** (six documented legacy cases), based on actual Ubuntu/Windows logs. Not GREEN.
- Observed automatic workflow runs at last review: [#42481675466](https://github.com/Iam-2squared/ark-ai/actions/runs/42481675466) **IN PROGRESS** (first repair), [#42481768500](https://github.com/Iam-2squared/ark-ai/actions/runs/42481768500) **IN PROGRESS** (all legacy repairs), [#42481983065](https://github.com/Iam-2squared/ark-ai/actions/runs/42481983065) **IN PROGRESS** (Context source/tests), and [#42482125383](https://github.com/Iam-2squared/ark-ai/actions/runs/42482125383) **QUEUED** (post-COMMIT tests). Other intervening pushes also auto-triggered standard CI; **no duplicate manual workflows** were launched. All are observations before this report/checkpoint, **not** final latest-HEAD six-job proof.
- **New tests:** 9 (7 Context + 2 Quarantine). **Existing failing cases revised:** 6 (one binding, three Toolbox, two Quarantine). **Production paths:** one optional Context backend module; **no local full pytest or Ruff was run**. Final six-environment GREEN **NOT VERIFIED**; latest changes may require additional log-driven fixes.

## Hard boundaries and priorities

PR #5 (V3 paid/approval gate), PR #9 (UI paused), main and frozen V1/V2/Local UI/Launcher contracts/evidence remain untouched and unmerged. No paid/potentially billable compute, external API/GPU, real tool backend, physical PC, credentials, sensors, real Candidate weights/adapter, protected V2 evaluation, approval inference, automatic retry/promotion or destructive work.

**Next:** (1) inspect all six exact-head CI job results and fix genuine log-proven failures without relaxing safety; (2) independently strengthen Memory COMMIT-UNKNOWN/CAS/ABA and Planner step-specific durable READ recovery; (3) advance Registry + durable authorization + audit-before-action + disconnected mock integration only after lower-layer exact-head GREEN; (4) review local audit O(N) history cost without sacrificing tamper detection; (5) continue free-only privacy/observation/V3 guard reviews. **ARK/JARVIS/V3 NOT_PASSED.**
