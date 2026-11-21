# ARK AI — Run411: Offline recovery archive, registry subject, proactive freshness custody

**Scope:** three independent, reversible, local-only security hardening packages on the existing Draft JARVIS foundations branch. All local artifacts are diagnostic. No backend call, live notification, real device, credentials, paid compute, human authorization, candidate training, PR merge, or protected evaluation opening.

**Starting checkpoint:** Run410 branch HEAD `7be8cfeaf219921e5a96e9b31de34a69d316d3f7`. Its CI #981 / `40160539009` completed **SUCCESS** on Ubuntu/Windows Python 3.11–3.13, as independently re-read at the start. Main remains `7a843f17eb96ed13d66f23b58b06406b3002e405`; V3 PR #5 remains Draft/unmerged/NOT_PASSED.

## New work (3 packages; +18 parametrized pytest cases)

### 1. Retained recovery archive source and UNKNOWN continuity (+8 cases)

- Source: `src/ark/agency/synthetic_recovery_archive_review.py`, source commit `43d35ca6296b9b6220feea4b074c645c0bade8fc`.
- Tests: `tests/test_recovery_archive_capture_epoch_run411.py`, initial test commit `51be44af7ffaadf54c87903d72391f5fe8788004`, narrow fixture-call-order correction `b72c8803972345d5085db2168f1031e9d166845a`.
- Preserve all first-seen nested frozen review/witness field **carriers**, not just value-equal metadata, across JSON serialization, digest creation, detached archive structural validation and final return. Equal-value archive digest replacement fails closed. A retained `RUNNING` / `UNKNOWN` synthetic WRITE may not become known merely because the later local journal claims terminal success/failure.
- Explicitly NOT proven: external result truth, custody of caller-retained archives against coordinated adversary, cross-DB atomicity or exactly-once external effects.
- CI #983 / `40163263861` **FAIL** with three test-only errors: the new fixture passed state in the wrong positional order to the archive rechecker (Ubuntu3.13: 2190 passed, 3 failed; Ruff PASS). Fixed only the new test fixture; subsequent CI #986 / `40163399862` Ubuntu 3/3 GREEN, including Python3.13 Ruff PASS and 2198 pytest PASS. Windows jobs were still in progress when first checked. Preserve #983 failure history.

### 2. Cross-store recovery must bind the original ToolCall and registry entry (+5 cases)

- Source: `src/ark/agency/synthetic_recovery_triage.py`, commit `93041747ef28518a8510aa2967528332c1b0d17d`.
- Tests: `tests/test_recovery_registry_subject_run411.py`, commit `292d084ce55e49e3a78631743fecaf76818f67b2`.
- Require exact `BoundAction`, the same original `ToolCall` object, the exact registry registration and its revision on the first binding. On final rebind require the identical caller object and registration again. Equivalent cloned ToolCalls, copied registry entries and spoofed revisions cannot silently underwrite a cross-store diagnosis.
- This remains a **disconnected** test-time registry, not an authenticated issuer or real ToolBackend authorization mechanism.

### 3. Proactive freshness read-phase carrier integrity (+5 cases)

- Source: `src/ark/proactive_synthetic_freshness_review.py`, commit `2f97fb6f48b26f01da0da2356939540b8566f7f9`.
- Tests: `tests/test_proactive_freshness_carrier_epoch_run411.py`, commit `7a78c0b2fa5ba7a19845f42e9d9a774c79acaaf3`.
- Extend pre-existing value/type checks to **first-seen identity carriers** for receipt, every policy field and optional retained row-hash/digest witness. A local hash callback that swaps equal-valued strings or row tuples cannot evade the post-callback rejection.
- No actual notification, subscription, clock attestation, sensor access or external side effect.

## Validation matrix and limits

- All file writes use ordinary GitHub Contents on the existing Draft PR branch, with a fresh branch-HEAD read immediately before each write; no force push, raw Git objects, hidden write routes or manual CI rerun.
- CI #982 / `40163203000`: SUCCESS all six, source-only archive change.
- CI #983: FAILED for three wrongly ordered new test helper calls, then corrected.
- CI #986 / `40163399862`: Ubuntu Python 3.11/3.12/3.13 GREEN; Ubuntu3.13 2198 pytest passed, Ruff PASS; Windows outcomes must be checked separately.
- Final 3-package source+test HEAD `7a78c0b2fa5ba7a19845f42e9d9a774c79acaaf3` / CI #988 `40163498149`: **IN PROGRESS** at drafting time. Do not claim an all-six PASS or 2203 tests PASS until GitHub confirms exact-head results.
- The original V1/V2/Local UI/Launcher evidence, protected V2 evaluation, frozen V3 Contract 1, Memory v1 and ActionAudit v1 schemas are unchanged. None of these local continuity checks provides attested time, signed human approval, OS-handle custody, real-world external outcome evidence or cross-store transactions.

## Failure cases explicitly exercised

| Boundary | Fixture fault | Expected behavior |
| --- | --- | --- |
| Archive canonicalization | Cached plan-tail status changes | Reject archive capture |
| Archive hashing | Original request changes (including equal-value replacement) | Reject archive capture |
| Archive validation | Nested audit witness or detached digest changes | Reject archive capture |
| Archive restart | A retained UNKNOWN is rewritten into local SUCCEEDED/FAILED | Reject alleged resolution; never retry |
| Recovery registry bind | Equal-valued ToolCall or copied entry returned | Reject original-subject mismatch |
| Recovery final bind | Second bind returns a cloned action | Reject before delivering review |
| Proactive freshness | Receipt, policy or retained witness replaced during hashing | Reject, never notify |
| Baseline | Stable valid synthetic fixture | Review is deterministic, never authorizes an external action |

## Next plan / 今後の方針

1. Read the exact-head final source CI #988 including each Ubuntu/Windows job; diagnose any FAIL via the smallest source/test correction on a freshly read HEAD. Never duplicate equivalent workflow runs.
2. Extend restart uncertainty to retained pending reservations, audit-link history and dependency descendants; require independently held witnesses before any cross-store reconciliation. Remain deny-by-default.
3. Continue Memory v1 CAS, expiry and coherent snapshot / Personal Context privacy lifecycle as independent reversible lanes, preserving frozen SQL schemas.
4. Harden synthetic clock / authenticated-issuer/audit-before-action **interfaces** only; do not treat local hash chains or mock statuses as external proof.
5. Preserve PR #5 Draft/NOT_PASSED and PR #8 Draft/unmerged; no paid compute, Candidate promotion, protected evaluation, live tool execution, secrets, private-data disclosure, destructive actions or main merge without explicit user authorization.
