# ARK AI — Run626: disconnected WRITE triage, Memory uncertain-COMMIT row epoch and ToolRegistry canonical ToolCall identity

**Status:** Three reversible, non-UI source+test packages saved to Draft PR #8, branch `research/jarvis-foundations`. **28 new parameter-expanded pytest cases authored, NOT 28 local PASS**; four earlier WRITE packet fixture cases revised. Final full HEAD 6/6 CI remains **NOT VERIFIED** at this report's writing. No paid compute, real backend actions, human approval, V3 Candidate or frontend changes. ARK/JARVIS/V3 **NOT_PASSED**.

## Verified starting point

- Work-basis HEAD: `7479957708955a9928bd28c94bb2fb97478dbb72` (Run625 checkpoint), [Actions run 41977746114](https://github.com/Iam-2squared/ark-ai/actions/runs/41977746114) **six jobs GREEN**: Ubuntu/Windows × Python 3.11, 3.12, 3.13.
- No local Git checkout or local pytest/Ruff: `git ls-remote` could not resolve github.com. CI statuses below come only from GitHub API reads, not local success claims.
- Safe GitHub file writes used the ordinary Contents API after freshly re-reading the PR HEAD. No raw Git objects, ref rewrites, force pushes, workflow dispatch, release or merge.

## Package A — manual ambiguous WRITE triage packet must not execute a substituted constructor

- Source `src/ark/agency/offline_write_manual_triage.py`, blob `9202550b4647726783cc3514235833c9ac5adaa2`, source commit `b6a4067ce172aaf949dbd04ad357912ddb849aa4`.
- Pin the original `OfflineWriteTriagePacket.__init__` and check it in the existing static authority-descriptor guard *before* packet construction, including after packet fingerprint callbacks. Denial getters and original nested item initializer remain pinned; no claimed human outcome or external WRITE permission.
- Legacy test `tests/test_manual_write_triage_pregetter_custody_run613.py`, blob `02258d3718aa3ecae58f166f52c553269b49b77d`, corrected in `1a8ecdb7ac1fe8c71b52c38c9b4184348d20bc5a`: four cases now require substituted initializer **never executes** rather than expecting it to install a fake getter.
- New `tests/test_manual_write_packet_original_initializer_run626.py`, blob `1b2a24a269104d3e6e10c4049d1b4f94f4ae4616`, commit `22d2cf83b7c7cdf0b9c3d7844bef90b2e19980fb`: **six** cases (READ/WRITE × preinstalled/fingerprint constructor injection; READ/WRITE inert baseline). Neither case dispatches a tool.
- Early source-only [CI 41982507588](https://github.com/Iam-2squared/ark-ai/actions/runs/41982507588) exposed the **four expected obsolete test assertions**; the updated fixture fixes that precise expectation without relaxing the denial. Corrected tests [CI 41982686368](https://github.com/Iam-2squared/ark-ai/actions/runs/41982686368) observed Ubuntu 3/3 and Windows 3.11/3.12 GREEN, Windows 3.13 IN PROGRESS at last job read. This is not the final HEAD.

## Package B — read-only Memory COMMIT-UNKNOWN row image and reentrant hash

- Source `src/ark/memory/postcommit_uncertainty_review.py`, blob `e22b7570f4982913d79bfc54e3a4d939f558bc34`, commit `e3afa4826ad7f99d3d75c7648ba2dd184118360d`.
- The manual reconciliation now retains exact original `MemoryRecord` field carriers plus a metadata snapshot and checks them **before and after** its synthetic row-hash callback. A digest of the *old* image cannot bless a mutable record changed by the hash callback before disposition classification.
- New `tests/test_memory_commit_triage_reentrant_row_epoch_run626.py`, corrected blob `e1b6dd48d285da01cc933106dd860ab6aef16d0b`: **eight** cases (content/revision/metadata × first/second hash callback; unchanged/matching-update local baselines).
- Initial [CI 41982910171](https://github.com/Iam-2squared/ark-ai/actions/runs/41982910171) Ubuntu 3.11 logged **6 FAIL / 8,746 PASS / 1 SKIP**: the six new fault cases correctly rejected but expected the internal `row image changed after snapshot` message. The existing public wrapper deliberately exposes `Memory triage unavailable; manual review required`, retaining the precise internal error as `__cause__`. Fixed only the test to assert both public fail-closed message and exact nested cause, commit `b66a798782995bffa5c2ca11d4845b3be991a075`; [CI 41983619520](https://github.com/Iam-2squared/ark-ai/actions/runs/41983619520) QUEUED at last job read. No retry or attribution inference.

## Package C — registry-bound identity cannot execute forged ToolCall canonical machinery

- Source `src/ark/agency/registry.py`, blob `3fa9fa11c4b95183005c508e693fe74910705246`, commit `4ce6fd1366ea7727ac00d987e0d5454cce4af09e`.
- Pin original ToolCall constructor, `__post_init__`, `request_id` and `arguments_sha256` descriptors at registry import; check before synthetic canonical ToolCall construction in `resolve`/`bind`, after canonicalization and across registry lookup/revision callbacks. No tool execution, no one-shot token, no effect or approval promotion. This changes neither ToolCall's frozen contract nor its hash domain.
- New `tests/test_registry_toolcall_canonical_descriptor_run626.py`, blob `8ad7c730302a890faf9404b65009cd5cf402cc29`, commit `22c9de6f6e970c58b77d61b3c243b23dc0e48d16`: **14** authored cases (2 operations × 4 preinstalled forged members; 2 × 2 lookup callback injections; 2 inert baseline).
- [CI 41983361913](https://github.com/Iam-2squared/ark-ai/actions/runs/41983361913) and [CI 41983462915](https://github.com/Iam-2squared/ark-ai/actions/runs/41983462915) were in progress at last read. No latest-HEAD success is inferred.

## Authorization/freeze boundaries and follow-up

PR #5 remains Draft, pre-paid-compute blocked, with human-approved dataset/contamination, immutable HF snapshot bytes/revision, exact runtime/device identities, cost authorization and V2 opening unresolved; none were guessed or changed. PR #9 remains Draft and **UI/FRONTEND PAUSED**. PR #8 remains Draft/unmerged. Main, frozen V1/V2/Local UI/Launcher contracts and evidence, V3 Contract 1, and protected evaluation boundaries are unchanged. No new credentials, notifications, service subscriptions, external compute, real WRITE actions, automatic UNKNOWN replay, irreversible erasure or Candidate promotion.

**Next plan / 今後の方針:** (1) inspect exact-head final CI, repair only logged defects while overlapping independent non-UI work; (2) extend Memory CAS/COMMIT-UNKNOWN row/event/prefix and privacy expiry evidence without inferring consent, and Planner crash-recovery no-replay; (3) integrate ToolRegistry, PermissionGate, audit-before-mock-action and occurrence fencing only on exact-head GREEN predecessors; (4) review V3 free-only static approval/path/identity gates; (5) preserve UI pause, Draft PR #5/#8/#9 and frozen evidence.
