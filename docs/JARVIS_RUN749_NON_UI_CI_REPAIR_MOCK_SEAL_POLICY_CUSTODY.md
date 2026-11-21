# ARK AI — Run749 free-only non-UI core custody and CI repair

## Scope and verified basis

- **Branch:** `research/jarvis-foundations`, Draft [PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), unmerged. Initial independently retrieved source HEAD: `3a0bf1a52097ae2c9bcd11f66b4cc1a033a6e6c5` (Run748 checkpoint). Last source/test HEAD before this report: `8525f57395bbe3513e9cd82de059f263e6f5fda5`.
- **Run748 CI #42697737030** on `3a0bf1a...`: **COMPLETED FAIL in 6/6 jobs**. Inspected actual Ubuntu Python 3.11 job log (#129433964950): 12,157 passed, 1 failed, 1 skipped. Sole failure was `tests/test_context_recovery_result_original_slots_run658.py::test_reentrant_report_slot_replacement_rejected_without_getter[digest]`: expected message `review result gained authority`, actual `context replay digest implementation changed`. The actual existing early SHA/JSON callback guard denied the substituted digest first. No authorization gate was relaxed.
- **CI repair** [`6c8438c`](https://github.com/Iam-2squared/ark-ai/commit/6c8438c877d525cb59ea038e812e5c4be22ca2a2): the one affected fixture now expects the earlier digest guard in the digest phase; witness/durable-read phases retain their previous assertions. Injected authority getter must never execute.

## Package A — Disconnected mock arithmetic dependency custody

- Production [`1cb03c7`](https://github.com/Iam-2squared/ark-ai/commit/1cb03c7f457f7b0266dc2ab94c7e2d764f39be2d) pins the import-time `builtins` module and `sum` implementation before parsing caller-private canonical JSON. A process-local forged `sum` must not observe mock arguments or influence a synthetic result, whether the requested operation is `math.sum` or another tool.
- Test [`1de2e10`](https://github.com/Iam-2squared/ark-ai/commit/1de2e1024f3153759e7cd0ad2fb78e7bf550bae3) adds **6 parametrized cases**: process-wide substituted `sum` across three operations, substituted toolbox module across two operations, and a normal deterministic `math.sum` identity/deny-only baseline.
- The tool remains intentionally disconnected, in-memory and non-authorizing. Neither this pin nor a mock receipt is a real ToolBackend, sandbox or action grant.

## Package B — Local file-seal result/retained carrier boundary

- Production [`5756ed9`](https://github.com/Iam-2squared/ark-ai/commit/5756ed9e574a8dc1bc8f08a08bba3615d4d97260) captures import-original `DisconnectedFileSeal` slot descriptors, authority-denial properties, constructor/lookup hooks, frozen field vectors and `dataclasses.fields` identity.
- Public capture/review reject forged carriers **before the local file is opened**. Reentrant handle/path callback changes are rechecked before constructing/returning a seal. Review uses the pinned field names rather than a potentially replaced reflected field enumerator.
- Test [`e451854`](https://github.com/Iam-2squared/ark-ai/commit/e451854e1103fec7b68aea6d9d958e606b214baf) adds **26 cases**: 20 preinstalled field/deny/constructor hooks across capture and review; three protocol-vector replacements; one replaced field-reflection helper; one reentrant path-parent mutation; and one healthy seal/review baseline.
- This protects only local in-process shape admission. Source path races, POSIX/Windows handle identity changes after inspection, WAL consistency, retained-witness independence and authenticated ownership are **not proven**.

## Package C — Registry-bound policy static inspection

- Production [`95b41ae`](https://github.com/Iam-2squared/ark-ai/commit/95b41ae86cc034c4024d0e437433ac3516df0cfe) captures the import-original `inspect` module and `inspect.getattr_static`. The registered PermissionGate refuses a replaced static lookup **before** asking it to inspect a potentially token-bearing gate object.
- Test [`8525f57`](https://github.com/Iam-2squared/ark-ai/commit/8525f57395bbe3513e9cd82de059f263e6f5fda5) adds **5 cases**: READ and WRITE, module and lookup substitutions, zero forged lookup executions, a rejected WRITE token remaining usable, and a normal read-only registry-bound mock baseline.
- Still only process-local diagnostics; this does not authenticate token issuer/time, prevent restart replay, create audit-before-real-action, or enable external tools.

## CI status and immutable gates

- New authored regression cases: **37 total** (6+26+5), plus one repaired existing fixture; no full local pytest claimed. Each write used ordinary GitHub Contents API with the contemporaneous PR HEAD and current file blob, with no force-push/raw Git bypass.
- Separate automatic PR CI jobs were launched for source/test commits. Known run IDs: [#42705157469](https://github.com/Iam-2squared/ark-ai/actions/runs/42705157469) on `6c8438c`, [#42705557037](https://github.com/Iam-2squared/ark-ai/actions/runs/42705557037) on `1de2e10`, [#42705995601](https://github.com/Iam-2squared/ark-ai/actions/runs/42705995601) on `e451854`, and [#42706347959](https://github.com/Iam-2squared/ark-ai/actions/runs/42706347959) on `8525f57`. At report preparation these were **QUEUED/IN PROGRESS**; no exact newest HEAD six-platform GREEN proven. An automatic report/checkpoint CI will apply to its own later HEAD and must be judged independently.
- main `7a843f17eb96ed13d66f23b58b06406b3002e405`, V3 Draft PR #5 `805b377697472268db02650a89c7a94b1c5337c8` and paused UI Draft PR #9 `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` were inspected and not modified. Frozen V1/V2/Local UI/Launcher contracts/evidence untouched.
- No UI/frontend, paid GPU/API/compute, real Candidate/adapter, protected V2 evaluation, real sensor, external action, physical-PC change, destructive migration, user grant, external account/secret, main merge or automatic promotion. **ARK/JARVIS/V3 NOT_PASSED.**
- Independent V3 [pre-paid-compute gate](https://github.com/Iam-2squared/ark-ai/blob/805b377697472268db02650a89c7a94b1c5337c8/docs/v3/PRE_PAID_COMPUTE_GATE.md) still requires immutable HF revision/file hashes, human-approved and provenance-cleared 120/30, exact tools/runtime/GPU identities, bounded explicit JPY/wall-clock approval and GREEN before any external work. No such approval is inferred from a local checksum.

## Next plan / 今後の方針

1. Verify **latest checkpoint-result SHA** six-job CI, inspect actual failed job steps and make minimal fail-closed fixes; never duplicate runs.
2. Continue Memory CAS/ABA expiry, authoritative row/event/WAL snapshot, manual-only COMMIT-UNKNOWN; improve Windows handle/TOCTOU proof rather than interpreting lexical seals as file identity.
3. Continue Planner persisted READ/terminal restart recovery and registry-bound authorization occurrence/audit sequence; keep disconnected mock until independent exact-head lower-level GREEN.
4. Complete Personal Context privacy/revocation/retention/erasure review; build proactive/observation synthetic contracts. Retain separate frozen V2/V3, UI pause and approval gates.
