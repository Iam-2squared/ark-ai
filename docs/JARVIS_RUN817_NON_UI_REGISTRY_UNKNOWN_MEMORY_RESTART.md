# ARK AI Run817 — Non-UI registry-bound UNKNOWN and coherent Memory restart

## Scope and safety boundary

This invocation is **FREE-ONLY**, **non-UI**, and limited to disconnected, read-only local diagnostic integration on Draft PR #8 (`research/jarvis-foundations`). It does **not** authorize external effects, human consent, trusted time, model training, paid services, Memory deletion, V2 evaluation, Candidate promotion, UI changes, or main merge. Frozen V1/V2/Local UI/Launcher contracts and evidence are unchanged. PR #5 and #9 remain separate, Draft and unmerged.

Work basis: prior Run816 checkpoint HEAD `513893e2c3608cdbfbad4d8c59914a9a40564b27`.

## Package A: registry identity → audited preaction COMMIT-UNKNOWN

- New `src/ark/agency/disconnected_registered_unknown_bridge.py` and `tests/test_registered_unknown_outcome_run817.py`.
- Derives a synthetic WRITE intent via the existing immutable `ToolRegistry` binding and compares it to the existing SQLite preaction audit reviewer. Inspects retained caller-provided prefix and exact occurrence/bound-action/request identities.
- Reports only `UNCHANGED`, `PREEXISTING`, `LOCALLY_RECORDED`, or `ADVANCED_OTHER`; records a domain-separated digest of non-sensitive identities and local observations.
- Refuses READ reclassification, malformed occurrence, forged retained prefix, corrupted audit history, altered bound action, re-bound helper, patched result authority getter, and unexpected local effect authority.
- **13** new test cases, including `NeverExecute` backend, no replay and no externally-effectful calls.

**Limitations:** Registry resolution and SQLite read are *separate epochs*, not a distributed transaction; this bridge does not establish independent custody, user approval, exactly-once real-world execution, or a valid retry. A local row is **not** proof that the requested external action happened.

## Package B: coherent Memory expiry snapshot → retained restart receipt

- New `src/ark/memory/coherent_expiry_restart_bridge.py` and `tests/test_coherent_expiry_restart_bridge_run817.py`.
- Recalculates the retained prior coherent snapshot digest from its cohort and pages, checks scope order/count and retention bounds, reads fresh multi-scope due candidates in the existing *single SQLite read transaction*, then validates the previous/current page transition with the existing restart receipt reviewer.
- Rejects truncated expiry pages rather than silently presenting them as complete coverage; fails on clock rollback, mismatched read limit, mutated retained hashes, changed scope owner, substituted reviewer/helper, and false authorization properties.
- Returns content-free counts and digests; **14** new test cases.
- No removal of expiry candidates, retrieval of plaintext into the result, owner consent, verified wall clock or cross-epoch atomicity.

**Limitations:** Retained data and requested scopes originate with the caller; neither is authenticated historical custody. The fresh SQLite observation can become stale immediately after its read transaction; no automatic purge or policy transition is justified.

## CI and evidence handling

- Prior Run816 checkpoint `513893e2c3608cdbfbad4d8c59914a9a40564b27`: [CI #43203510842](https://github.com/Iam-2squared/ark-ai/actions/runs/43203510842) **GREEN all six jobs** (Windows and Ubuntu, Python 3.11–3.13; jobs separately inspected).
- Initial new-work [CI #43211445184](https://github.com/Iam-2squared/ark-ai/actions/runs/43211445184) **FAIL** because Ruff E501 found a 101-character parametrization line in the new registry test (actual Ubuntu 3.12 log). Subsequent intermediate [#43211646193](https://github.com/Iam-2squared/ark-ai/actions/runs/43211646193) and [#43211746246](https://github.com/Iam-2squared/ark-ai/actions/runs/43211746246) have the same pre-fix E501 issue, not evidence of runtime failure.
- Test-only formatting correction commits `7f22a067816bf4b8c802bcdb3d6cfc2ef9a40b99` and `9fea3e711ee07d74a2779e039b3ac147bb1c9565`; the latter also repairs literal newline separators inadvertently introduced during the first correction. No safety condition or test assertion was weakened.
- New source + test commits: `2c02e109f66e2abcf24b2dbec415a2154bea8bc6`, `52af88bce35f7f8894b783be61fd654983c03f85`, `f8dec3c8d242bd3d203f9c08faeae188a943f2f8`, `91fd999d930e064d461c0a4a75806b253737163a`.
- [Post-fix CI #43211924069](https://github.com/Iam-2squared/ark-ai/actions/runs/43211924069) **IN PROGRESS** when prepared. Do **not** claim final checkpoint-result 6/6 GREEN until that exact SHA's six jobs have been inspected.
- No local pytest or Ruff execution was performed; remote CI is the execution evidence. No manual duplicate workflow was dispatched.

## Integration gates / next plan

1. Confirm all six jobs of the post-fix exact-head CI; inspect and correct any further failures from actual logs, without weakening the legacy privacy/authority tests.
2. Ensure registry descriptors and exact ToolCall fields are checked before any potential third-party dynamic getter in the *composed* entrypoint; this is an identified integration-hardening consideration, not an approval grant.
3. Test simultaneous WAL writer / restart epoch behavior and check result-carrier drift across all callbacks before any higher-level integration.
4. Build the next *independent* read-only Planner UNKNOWN quarantine and Memory CAS/ABA package, using lower-layer GREEN evidence; keep mock execution disconnected.
5. Maintain free-only boundaries, UI pause, frozen contracts, PR #5 Draft gate and all human-confirmation conditions. Overall ARK/JARVIS **NOT_PASSED**.

## Post-submission regression triage (observed before final checkpoint)

The first post-formatting Python matrix reached pytest and exposed two **new code/test mistakes**, rather than a change to the frozen authorization policy: (1) the registry bridge used `AtomicPreactionWitness.chain_sha256` although the actual existing ledger carrier has `tip_sha256`; (2) the Memory test referenced a nonexistent `SQLiteMemoryStore.query` method. Corrections used the real ledger field (`415cb131403f25001acad03b7d011088ed623ea3`) and asserted the real coherent snapshot still contains three candidates after review (`d299e2f6e6e66d392c6712d55367644c4de6c793`). No source authorization or policy was relaxed.

[CI #43212649275](https://github.com/Iam-2squared/ark-ai/actions/runs/43212649275) then revealed a third issue: the `ToolCall.request_id` digest is a computed `str` and need not preserve Python object identity across reads. The bridge initially compared this value with `is`, causing four legitimate read-only cases to reject. Commit `bbd78dd810f2f895a46459a14bba8c5bdd455e99` now pins the actual four input carriers by identity but compares the derived request digest by **value**, as the preexisting registry binding does. The integrity/authority checks, SQLite audit validation, and prohibition of automatic replay remain unchanged.

For [CI #43213234759](https://github.com/Iam-2squared/ark-ai/actions/runs/43213234759) at `bbd78dd810f2f895a46459a14bba8c5bdd455e99`, Ubuntu 3.11/3.12/3.13 were observed individually **GREEN**, Windows 3.11/3.12/3.13 **IN PROGRESS**. This is intermediate evidence only, not final checkpoint-result 6/6 GREEN. No local test runner or paid compute was used.
