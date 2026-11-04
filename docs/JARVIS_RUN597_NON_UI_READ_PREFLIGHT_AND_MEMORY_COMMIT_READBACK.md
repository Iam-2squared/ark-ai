# ARK AI — Run597 non-UI: READ preflight authority and Memory COMMIT readback

**Scope:** Draft PR #8 `research/jarvis-foundations`; local, disconnected and reversible groundwork only. This note is not a gate approval, an assertion of all-platform CI GREEN, or evidence of a real external action. UI/front-end work remains paused.

## Package A — disconnected plan READ preflight

- `src/ark/agency/disconnected_read_preflight.py` was changed in commit `603693619b25eb7e75bfa2f0256e66dc680db63d`; the regression file `tests/test_read_plan_preflight_authority_run597.py` was added in `c1f765e4dad9e1a9acaba2b2a1eb2123697343bb` (**14 authored pytest cases**, not independent local PASS counts).
- The four non-authorizing receipt properties (`dispatch_authorized`, `external_result_verified`, `authenticated_clock_or_consent`, `automatic_replay_authorized`) are compared with import-time descriptors before review and after every result getter. Even an injected getter that returns `False` is not an original denial proof; result field carriers, grant/plan epochs and bound action carriers are rechecked at return.
- A swapped class/instance `PermissionGate.authorize_registered` method can no longer mint a valid-looking `BoundAction` response in this disconnected preview: original method identity is independently checked after authorization and at final return. This is **process-local diagnostic drift detection**, not executable code attestation or safe execution of arbitrary monkeypatched code.
- The original registry, plan, PermissionGate, immutable grant definitions and frozen contracts remain unchanged. The backend is not called; grants and caller-observed time confer no live permission.
- Original regression suite tests may report a safe denial **earlier** than their previous downstream error messages. CI [#41768900892](https://github.com/Iam-2squared/ark-ai/actions/runs/41768900892) confirmed Ubuntu 3.12 **8 FAIL / 7,851 PASS / 1 SKIP** from these older diagnostic expectations. No source security check was removed: expectation-only repair commits `aabe23ab5b96b177039139f6722d9ff78a43e78c`, `d850a27b084c7f2c0d8c8860771b5b4ab279bca5`, `ba72087279be98a585bc58d66ecda84d839a3947` accept the observed earlier fail-closed paths. Fresh final-HEAD CI still required.

## Package B — generation-fenced Memory v1 CAS readback

- `src/ark/memory/generation_fenced_cas.py` was changed in commit `faeed309c14d06234542ddbf05c12e36490b45a4`; regression file `tests/test_memory_generation_postcommit_readback_run597.py` was added in commit `34eb42e55b7e8e9870136fd66965e6188b2b9df9` (**5 authored pytest cases**, not independent local PASS counts).
- After the transaction commits and the original result is checked, the writer opens a new **read-only SQLite snapshot** and revalidates the exact generation token, complete per-memory event history, and row digest. It rechecks input identity and result carrier identity following the readback callback. Readback disagreement, missing history, local SQLite I/O failure, or post-readback carrier mutation rejects with an **uncertain COMMIT / manual review** error.
- Synthetic test fixtures inject read I/O failures, post-COMMIT row/history corruption, same-value new object identity, and an ordinary successful path. A failed post-COMMIT review **does not undo a COMMIT** and **does not authorize retry**. Reopen/read comparison is not an atomic cross-process guarantee, independent audit custody, consent proof, or trusted time. A legitimate concurrent later update can also produce an uncertainty rejection.
- Frozen `src/ark/memory/contracts.py` and Memory v1 database schema are unchanged.

## Evidence and security boundaries

- **Last verified prior exact-head CI:** [#41764124518](https://github.com/Iam-2squared/ark-ai/actions/runs/41764124518) at `fa046246aa47786f8f81e6c9b86d56bd794a7935`: six Ubuntu/Windows Python 3.11/3.12/3.13 jobs **COMPLETED SUCCESS**. That GREEN predates the new source/test changes.
- New CI runs [#41768845571](https://github.com/Iam-2squared/ark-ai/actions/runs/41768845571), [#41768900892](https://github.com/Iam-2squared/ark-ai/actions/runs/41768900892), [#41769067160](https://github.com/Iam-2squared/ark-ai/actions/runs/41769067160), [#41769140876](https://github.com/Iam-2squared/ark-ai/actions/runs/41769140876), and [#41769367293](https://github.com/Iam-2squared/ark-ai/actions/runs/41769367293) are **intermediate or pending** evidence at note authoring; do not promote a partial or older GREEN to final-head evidence.
- Contract Blob SHA checks: Memory `b6e93821ecd69270a7634aceb20775dc36e9953c`, Planner `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`, PR #5 protected V3 `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`.
- PR #5 remains Draft/unmerged under its training and evaluation gate; PR #9 UI remains Draft/unmerged/PAUSED. No production ToolBackend, model Candidate, external GPU, paid API/service, final protected V2 evaluation, human-approval fabrication, frozen artifact update, external consent/identity claim or main merge.
- **Overall:** ARK/JARVIS/V3 **NOT_PASSED**.

## Next plan / 今後の方針

1. Confirm **the final checkpoint-result HEAD** on all six jobs. If FAIL, inspect the precise job logs and apply only the minimal source-/test-semantics-preserving change through normal GitHub Contents API; avoid parallel duplicate reruns.
2. Keep preflight result authority pinned across downstream detached READ-cycle reviews and test fail-closed branches, without dispatching a backend.
3. Verify generation CAS post-COMMIT readback continuity against concurrent writes, failures and restart; treat ambiguous outcomes as manual-only.
4. Once exact lower-layer GREEN evidence exists, prototype disabled-by-default registry-bound durable authorization plus audit-before-mock-action/occurrence replay quarantine in a separate disconnected lane. Maintain privacy-safe Personal Context and proactive fixtures without opening real integrations.
