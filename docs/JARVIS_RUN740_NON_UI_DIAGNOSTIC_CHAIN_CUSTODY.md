# Run740 — FREE-ONLY non-UI diagnostic JSONL writer custody and independent readback

**Saved report at (administrative JST):** 2026-11-09T23:28:51.423+09:00 (not a trusted runtime clock, human approval, or authenticated audit).  
**Branch/PR:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8); OPEN and unmerged.  
**Initial independently read work-basis HEAD:** `d4b99353ad3b48fdce35af6d1e0db68eb46b0b65`.  
**Source + regression-test HEAD before this report:** `aff886bd02c505ead6ecef3e1ca1c6283333a86d`.  
**Overall completion:** ARK/JARVIS/V3 **NOT_PASSED**; private diagnostic chain is *caller asserted, deny-only*, not an independently authenticated audit or action capability.

## Package A — private diagnostic public-code writer preaccess pinning

- [Source `821c357`](https://github.com/Iam-2squared/ark-ai/commit/821c3574a04fc819bc2251a4c7ecd0958662c348), `src/ark/private_diagnostic_ledger.py`.
- Before reading any input event carrier or caller anchor, reject rebound SHA-256/JSON serializer, digest domain, event/public-code allowlists, regex, integer/output budgets, event or output dataclass field/constructor/getter descriptors, and original deny-only authority descriptors.
- Recheck the protocol before and after the inner serialization/hash callback epochs and before reading each resulting false authority property. Retain original canonical byte format, existing public-code allowlist, SHA-256 domain and sequence semantics. No raw private value or file/SQLite I/O.
- This is callback integrity detection inside one Python process; it does **not** create a sandbox, signature, authenticated writer identity, trusted clock, consent, or real audit receipt.

## Package B — bounded independent public diagnostic JSONL verifier

- [New source `d435d04`](https://github.com/Iam-2squared/ark-ai/commit/d435d0458de3af9861eebbaec6331849343018ed), `src/ark/private_diagnostic_ledger_verify.py`.
- Inputs: exact ASCII canonical JSONL bytes represented as a string, caller-retained initial SHA-256, first sequence, expected count, and final SHA-256. Parse only bounded records: max 128 events/50,000 ASCII bytes, valid [1, 2**63-1] sequence span; require newline and exact record count.
- Independently verify exact schema keys (and canonical bytes, ruling out duplicates/unknown keys and alternate JSON representations), public-code allowlists and exact scalar types, every prior-link SHA-256, domain-separated hash and externally retained final hash. Changed count, truncated/reordered records and unknown records fail closed.
- Four permanently false properties (`audit_authenticated`, `cleanup_authorized`, `tool_execution_authorized`, `private_data_export_authorized`). Returned result contains only count/start/end and digest, not diagnostic payload. Checks imported codec/helper identities before any caller bytes reach JSON/SHA callbacks. Verifier and writer are separate modules but share an explicitly matching *public* protocol.
- Caller-held anchor/count/tip can all be forged together. The verifier cannot prove independent storage, timestamp, emitter identity, nonrepudiation, full-history inclusion or permission.

## Tests, CI and workstreams

- [Authored tests `fd45660`](https://github.com/Iam-2squared/ark-ai/commit/fd456600aad1f82745b4f41d55ef4376ed556382), [narrow fixture-constructor correction `aff886b`](https://github.com/Iam-2squared/ark-ai/commit/aff886bd02c505ead6ecef3e1ca1c6283333a86d), `tests/test_private_diagnostic_protocol_run740.py`: **56 authored parameter-expanded cases** covering valid cross-module digest roundtrip, changed protocol and poisoned codec callbacks, changed dataclass/denial descriptors, retained digest/count/anchor binding, tampered/duplicate-key/reordered/noncanonical JSONL, ASCII and size limits.
- The constructor correction makes hostile event-slot tests instantiate the fixture *before* monkeypatching class slots. It is a fixture-only repair and does not relax production code.
- Inherited [Run738 checkpoint CI #42620562317](https://github.com/Iam-2squared/ark-ai/actions/runs/42620562317) on `d55156f...`: Windows/Ubuntu Python 3.11–3.13 **6/6 GREEN**. Run739 pre-run HEAD `d4b9935...` [CI #42631540769](https://github.com/Iam-2squared/ark-ai/actions/runs/42631540769) subsequently confirmed **6/6 GREEN**. Neither baseline can certify this Run740 code.
- Run740 authored-test [CI #42634441577](https://github.com/Iam-2squared/ark-ai/actions/runs/42634441577) and fixture-fix [CI #42634723535](https://github.com/Iam-2squared/ark-ai/actions/runs/42634723535) were **IN PROGRESS** at last inspection; their exact-head 6/6 GREEN is **UNPROVEN**. Any failure must be diagnosed from actual job logs before promotion to a verified baseline. No duplicate workflow dispatch, local full repository pytest or physical-device execution.
- Independent read-only V3 hard-gate check: PR #5 `805b377697472268db02650a89c7a94b1c5337c8` remains Draft/unmerged. `RealTrainingBackend` raises `StopRequired`; preflight authorization is separate from Candidate training and has unresolved immutable model/dataset/runtime/device/JPY/time/human approval gates. No V3 source or protected evaluation was modified.
- Concurrent/frozen refs read: main `7a843f17eb96ed13d66f23b58b06406b3002e405`; Draft PR #5 `805b377697472268db02650a89c7a94b1c5337c8`; stopped UI Draft PR #9 `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`. All unchanged by this work. V1/V2/Local UI/Launcher frozen contracts/evidence untouched.
- No paid/external compute, GPU, accounts, API/service, credentials, actual ToolBackend/sensor, Candidate/weight generation or promotion, V2 final evaluation opening, destructive erasure, main merge, or hidden raw-Git/safeguard bypass.

## Next plan / 今後の方針

1. Obtain exact latest test-fix and report-head Windows/Ubuntu Python 3.11–3.13 CI results; if FAIL, isolate the actual failure trace and make a minimal semantics-preserving fix in normal GitHub Contents API.
2. After exact-head GREEN, integrate the bounded public-code verifier with disconnected-only diagnostic history and retained independent witnesses; never accept a caller-held anchor as authenticated.
3. Prioritize Memory CAS/ABA, row/event snapshot coherence, COMMIT-UNKNOWN manual-only triage and Planner persisted READ evidence/recovery.
4. Only after dependency GREEN, strengthen immutable ToolRegistry/PermissionGate, one-shot occurrence, audit-before-action and mock-only executor. Preserve explicit no-real-WRITE boundary.
5. Continue privacy-safe Personal Context, proactive/observation backend, SQLite Windows/POSIX TOCTOU design, and free V3 guard review without touching frozen contracts, PR #5 or stopped UI #9.


## Additional independent packages — mock recovered READ bound and Memory fixture CI triage

- **C / Recovered READ fixture step-count authority:** [source `2397b5e`](https://github.com/Iam-2squared/ark-ai/commit/2397b5ea9d71e019f1dfb5eda0d095e8df2be228) pins the exact original `_MAX_STEPS=24` budget, including exact integer type, *before* synthetic READ schedule/request data reaches any callback. [20 newly authored parameter-expanded tests `67338ce`](https://github.com/Iam-2squared/ark-ai/commit/67338cea3e32e4af9be418d2c3f303f1fe7f554a) verify refusal of rebound budget, digest/ID parsers, codecs, original recovery/fixture functions and patched binding/output descriptors; deterministic pure-memory sum and false authority remain. No actual ToolBackend, permission grant, dispatch or WRITE replay.
- **D / Inherited cross-process Memory fixture instability:** Actual [Run740 intermediate CI #42634723535](https://github.com/Iam-2squared/ark-ai/actions/runs/42634723535) Ubuntu Python 3.13 job `129219735741`: **11,930 PASS, 1 FAIL, 1 SKIP**, `tests/test_memory_multiscope_cross_process_purge_run435.py` worker unexpectedly exited *before* both workers' release barrier. Original fixture discarded the exited child's stderr, so the concrete process-exit cause is **not proven**, and failure cannot be attributed to the diagnostic changes. The Ubuntu Python 3.11 and 3.12 jobs for this same intermediate HEAD were GREEN at the last read. [Narrow fixture repair `8667207`](https://github.com/Iam-2squared/ark-ai/commit/8667207f45db3673a9fb34a14b8eec279f44da4b) serializes only child SQLite bootstrap and records the real bounded child stderr if a startup failure recurs; both workers still park and race simultaneously on the unchanged shared purge-versus-refresh release gate. No production Memory CAS/expiry behavior, expected race outcomes or security acceptance were relaxed.
- **Revised authored regression count:** 56 diagnostic tests + 20 READ bridge tests = **76 new parameter-expanded test cases**; one existing Memory cross-process fixture corrected diagnostically. **Latest relevant workflow IDs:** `#42635574767` for bridge tests and `#42635746824` for bootstrap fix, **QUEUED** at first observation; exact final-source/checkpoint 6/6 GREEN and 76-test all-platform PASS remain **UNPROVEN**. No duplicate workflows manually dispatched.
- All four packages remain isolated, local/mock/read-only or fixture-only. UI paused, frozen V1/V2/Local UI/Launcher untouched, Draft PR #5/#9 unmerged; no paid services, external GPU, Candidate weights, protected V2 opening, real action or main merge.
