# ARK AI Run768 — three non-UI free-only safety packages

**Work basis:** `83e4658d1c0ea7d8b25da95a5469e93a669dcd41` (previous Run767 checkpoint).
**Branch:** `research/jarvis-foundations` / Draft PR #8, OPEN, unmerged.
**Scope:** two opt-in backend ingress changes and three new regression test files, all local/synthetic. **No UI work.**

## A — Observation identity ingress: NUL labels

- Source `src/ark/observations.py`: `50c6d70c748e2bb3507b9f78e39eb9db57b50497`; corrected Python escape semantics at `fdfb1826864c72c4f16d2337a81c8c0860a509a2`.
- Directly constructed `ObservationEnvelope` now denies embedded NUL in `source_id`, `adapter_id`, `privacy_scope`, before identifier digest work. This closes a mismatch with the existing disconnected fixture-adapter label preflight. Does not acquire image/audio/camera/screen data.
- `tests/test_observation_direct_nul_identity_run768.py` commit `16e884c37cbed00be9051e3f13adf4fd05bdf420`: 3 direct-admission cases, 3 reflective-mutation / `observation_id` cases, 1 valid Unicode/deterministic-hash case = **7 cases**.
- Intermediate CI `42849260230` for test commit **FAILED 3 Ubuntu jobs (six assertion failures each)** because preceding source commit `50c6d70` mistakenly used a double-escaped literal `"\\\\x00"` rather than the actual NUL character predicate. **The mistake was fixed by the normal Contents API** at `fdfb182` before the final registry changes. Intermediate failure is not evidence of final code failure or success.

## B — Two-row WAL interruption and COMMIT-UNKNOWN reservation

- `tests/test_atomic_preaction_two_row_wal_crash_run768.py`, commit `55201f61216097c6da0f7cabfa3f9be8b76527bc`: **3 tests**; a child Python process dies with a second reservation uncommitted after inserting (1) only an intent or (2) intent and pre-action audit; a separate child commits the second reservation and dies before its caller receives its result.
- Read-only recovery checks retained hash-tip / occurrence sequence, rejects old witnesses and automatic replay, and asserts locally consistent rollback. This does **not** claim that a local COMMIT proves a real external tool effect.
- No production atomic-ledger logic changed; no backend `execute()` invoked.

## C — Registry identity ingress: NUL before backend inspection

- `src/ark/agency/registry.py`, commit `036a6663ecace9821c19af20e78ef119c5d4c660`, rejects embedded NUL labels at the existing exact-type, byte-bounded `_text()` ingress for registration name, capability and backend ID.
- `tests/test_registry_nul_identity_run768.py`, commit `b15489ba33b92efb2367df529d7299e1fea7cbe0`: **4 cases** — 3 invalid fields with a descriptor trap, 1 valid Unicode identity/revision and no backend execution.
- This is a local identity hardening, not backend attestation, permission granting, or a new connector.

## CI status, evidence and limits

- Previous exact basis `83e4658d1c0ea7d8b25da95a5469e93a669dcd41`: GitHub Actions [#42839474821](https://github.com/Iam-2squared/ark-ai/actions/runs/42839474821) **6/6 completed success** for Ubuntu and Windows × Python 3.11–3.13. This does not validate new changes.
- Source CI [#42848695875](https://github.com/Iam-2squared/ark-ai/actions/runs/42848695875) and atomic crash-test CI [#42849081745](https://github.com/Iam-2squared/ark-ai/actions/runs/42849081745): Ubuntu 3/3 GREEN, Windows 3 still in progress at inspected sample.
- Intermediate observation-test CI [#42849260230](https://github.com/Iam-2squared/ark-ai/actions/runs/42849260230): Ubuntu 3/3 **FAIL** at old SHA; fixed source afterward. Do not mask the failure or assume it applies to final SHA.
- Last source/test HEAD `b15489ba33b92efb2367df529d7299e1fea7cbe0`: [#42849914931](https://github.com/Iam-2squared/ark-ai/actions/runs/42849914931) **IN PROGRESS** at inspected sample. Final post-report/post-checkpoint exact-HEAD six-job GREEN **NOT YET VERIFIED**.
- Total new parameterized cases: **14** (7 observation + 3 crash + 4 registry); two backend files changed; three new test modules. Exact remote CI can establish regression status only once all six jobs complete. Local Python test invocation was unavailable because the GitHub repository could not be cloned from the container (DNS isolation); no local PASS claim.

## Boundaries and next actions

- Unchanged: main `7a843f17eb96ed13d66f23b58b06406b3002e405`, Draft PR #5 `805b377697472268db02650a89c7a94b1c5337c8`, paused Draft UI PR #9 `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`, frozen V1/V2/Local UI/Launcher contracts/evidence. All three PRs remain Draft and unmerged.
- No paid compute/API/subscription, external GPU, Candidate generation/promotion, protected V2 evaluation, new credentials or accounts, hardware operation, real notification, real ToolBackend WRITE, destructive action, or main merge.
- Still unproven: independent consent/provenance, trusted clock, immutable custody, cross-SQLite transaction atomicity, authenticated approval, and exactly-once real-world action effects. Ambiguous external WRITE remains UNKNOWN/manual quarantine, NEVER auto-retry.
- **Next:** (1) inspect final exact-head CI and correct any actual failures via the permitted Contents API; (2) expand Memory generation CAS/ABA and coherent retained snapshots; (3) Planner crash recovery and terminal propagation; (4) registry-bound PermissionGate, trusted audit-before-action and disconnected/mock executor; (5) Personal Context privacy, proactive startup clock, observation contracts and free-only V3 read-only guard review. No UI until user resumes it.
