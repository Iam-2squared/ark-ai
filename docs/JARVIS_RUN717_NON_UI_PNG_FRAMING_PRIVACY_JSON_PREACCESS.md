# ARK AI — Run717: disconnected PNG framing and private JSON callback preaccess

**Scope:** Two independent reversible **FREE-ONLY NON-UI** security packages on Draft PR #8. No UI, live tool, private data, microphone/camera, paid compute, external GPU, real V3 Candidate, protected V2 evaluation, main merge or user-consent inference.

## Work basis / prerequisite

- Exact initial PR #8 HEAD: `97d07a79ab5df703ea195e286b7679132770a6f0` (Run716 checkpoint).
- Exact-head [CI #42502790410](https://github.com/Iam-2squared/ark-ai/actions/runs/42502790410) completed **6/6 GREEN** on Windows and Ubuntu, Python 3.11–3.13, independently checked at this invocation's start.
- Exact current code/report-prewrite branch HEAD: `627003aa9d1a2f4011fd0f402f8e82f61add65f3`. The final checkpoint write will create a new commit; do not describe this as its result SHA.

## Package A — PNG CRC/struct original callbacks must precede raw fixture bytes

- [Source `f59a7dfa`](https://github.com/Iam-2squared/ark-ai/commit/f59a7dfa5d44bf4421dd950638cd56c21dba922e): `src/ark/offline_png_inventory.py` pins import-time `zlib.crc32`, `struct.unpack`, and `struct.unpack_from` and rejects substituted CRC/framing callbacks in the existing `_require_original_png_authority()` gate, **before even a valid request's PNG data can be passed to the foreign implementation**. Existing SHA-256 and frozen class-carrier/deny-only checks remain.
- [Seven authored regression cases `8f07e6ec`](https://github.com/Iam-2squared/ark-ai/commit/8f07e6ec886073fd0a8ef138ca56a4d0c2b28479), `tests/test_offline_png_framing_preaccess_run717.py`: all three callback identities with matching/mismatched source digest (6 cases), and a valid CRC-checked inert PNG (1).
- [Inherited synthetic corruption test `b0bb32ab`](https://github.com/Iam-2squared/ark-ai/commit/b0bb32ab74dd2ed9e554d526dc5fdae61ca9ddbf) now demands that a poison CRC callback **never executes or mutates a request**, rather than a later reflected mutation being detected. [Isolated class-carrier fixture `2eaff6ad`](https://github.com/Iam-2squared/ark-ai/commit/2eaff6adc7060b0e91d72bee54bc234cd9b0386c) updates its expected error to early framing-denial. Other carrier/authority checks are untouched.
- Limitations: A process-local callable identity is **not** a sandbox, signed sensor provenance, authentic CRC, verified compressed pixels or consent. No camera access, decoder activation or original user image is introduced.

## Package B — private redaction cannot call a replaced JSON serializer/parser

- [Source `0797329b`](https://github.com/Iam-2squared/ark-ai/commit/0797329b60c7034e4fb940ed3115249b4e047a15): `src/ark/offline_context_redaction.py` requires that module-level `json.dumps` and `json.loads` still equal import-time originals in the existing early `_require_original_denials()` and recurrent epoch check. A partial mask may retain private substrings; neither a malicious serializer nor a malicious parser may be reached with that payload.
- [Five authored cases `f16e6557`](https://github.com/Iam-2squared/ark-ai/commit/f16e6557afb08b9598530b2158111e914ffee90e), `tests/test_offline_redaction_json_preaccess_run717.py`: both substituted callback families in complete and partial masking (4 cases) must receive **zero** invocations, plus valid fully masked non-authorizing output (1).
- [Existing serializer-negative cases `627003aa`](https://github.com/Iam-2squared/ark-ai/commit/627003aa9d1a2f4011fd0f402f8e82f61add65f3) now require **pre-access** denial rather than expecting a malicious callback to execute first. A malicious callback cannot mutate a retained span, and its original label must stay unchanged. No production validation of canonical JSON or source digest removed.
- Limitations: The original canonical round-trip still checks accidental serialization mismatch, but a substituted module callback is now denied at the earlier original-identity gate. Local-only masking is **not** irreversible erasure, legal consent, authenticated source custody or external export permission.

## Independent safe audit while CI queued

- Reviewed unchanged PR #5 `docs/v3/PRE_PAID_COMPUTE_GATE.md` plus `training_cli.py`, `runtime_guard.py`, `authorization.py`. The V3 branch still requires separate preflight and Candidate permissions, verified local Git and code manifest identities, exact runtime evidence and user-approved cost ceilings. Required immutable HF bytes/revision, approved 120/30 provenance and human decisions, GPU identity and cost approval remain blockers. This review did **not** open protected final evaluation or perform runtime/training/computation; no gate was modified.
- Invariants to keep separate: process-local identity checks versus authenticated event/file custody; synthetic mock outcomes versus actual dispatch; a successful offline test versus trusted wall-clock and user approval; SHA-256 binding versus privacy erasure/consent.

## Evidence / checks

- **12 new regression cases authored, not yet all-environment-certified**; 2 non-UI production modules, 2 new test files, and 3 existing test files modified. Tests use only in-memory synthetic data.
- Earlier Run716 exact-head CI #42502790410 **6/6 GREEN**. At the mid-session query, the new final source/test HEAD [CI #42506769899](https://github.com/Iam-2squared/ark-ai/actions/runs/42506769899) was **QUEUED**. No local full pytest/Ruff or target-PC GGUF test, and **no Run717 final exact-head six-job GREEN claim**.
- All writes use GitHub's standard Contents API after an immediately preceding PR HEAD check; never raw Git objects, force-push, unknown credential, bypass or unrelated branch. PR #5 and paused UI PR #9 remain Draft/unmerged; frozen V1/V2/Local UI/Launcher evidence unmodified.

## Next plan / 今後の方針

1. Inspect final exact-head CI jobs (Windows and Ubuntu 3.11–3.13). On real FAIL, use the log to repair only the failing invariant/fixture with minimal semantics-preserving changes; work on another non-UI module while CI runs.
2. Memory: independenly retained live-row commitments, CAS/ABA and post-COMMIT-UNKNOWN reconciliation; never convert local witness into automatic retry permission.
3. Planner: independent exact per-step READ input manifests, persistent terminal/UNKNOWN evidence and restart-safe mock-only recovery; do not claim real tool invocation.
4. Registry-bound PermissionGate, durable occurrence authorization, trusted-clock audit-before-action; only then consider safe disconnected cross-module mock integration.
5. Keep UI paused, PR #5/#8/#9 Draft/unmerged, official freezes and V3 protected gates untouched, and all paid/external GPU/credentials/hardware/human-approval/main-merge boundaries closed. ARK/JARVIS/V3 still **NOT_PASSED**.
