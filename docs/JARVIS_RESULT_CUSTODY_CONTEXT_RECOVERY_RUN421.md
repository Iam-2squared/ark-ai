# ARK AI — Run421: Memory, Startup, Privacy and Recovery final-carrier custody

**Scope:** `Iam-2squared/ark-ai`, `research/jarvis-foundations`, Draft PR #8. These four packages are isolated, reversible, and **disconnected/mock-only**. They neither enable a real ToolBackend nor create authentic consent, trusted time, multi-SQLite atomicity, external exactly-once semantics, live device access, network calls, model training or automatic execution.

**Exact work-basis HEAD:** `71c330dd95a854be3ac0d375536ac2e0ec47f059` (Run420 canonical checkpoint; CI #1108 / `40185240920` completed SUCCESS). The frozen V1/V2/Local UI/Launcher and V3 PR #5 contracts are untouched.

## Four independent implementation + regression packages

| Lane | Source commit | Test commit | Added pytest cases | Safety invariant |
| --- | --- | --- | ---: | --- |
| Memory Snapshot | `806ba1a53d37ef057833271d1984267f4686dc17` | `4dc4405c58c004d83b77e5738f55f8856c3bc8d9` | 9 | Recheck original request/path/hydrated records **after** construction of the detached `CoherentSnapshotReview`; reject forged outer record tuple, digest carrier, read timestamp or result type. Do not change Memory v1 DDL or raw-content-free witness format. |
| Startup Readiness | `97f674435e8631c2412aa79d74d184b245eeb1bf` | `5ce459827389ca27da036a013314a85b7530f31f` | 10 | After `StartupSnapshot` construction, recheck the original probes, exact `ComponentResult` scalar carriers and graph digest/result identity. Synthetic READY does not authorize activation. |
| Privacy Context Reuse | `e71adb2f2fef0fec2a461ad37725ebc1a5ecd14f` | `6e8157e95950ad39a568c82bcd3c0215681b4e65` | 7 | Keep the separately re-projected `SyntheticContextBundle` nested carriers and previously retained veto witness fixed through receipt construction. Detect equal-valued carrier replacement; disclose no content and grant no consent. |
| Multi-WRITE Recovery | `f5985917b1490d940012152483ecfb0576191b98` | `1a39448ae02527c046df75a646ad8cb00a23b883` | 5 | Pin `PlanStep.step_id` and `ToolCall` scalar string identities (not only value equality) across registry binding and independent SQLite diagnosis; preserve UNKNOWN/reserved-PENDING non-replay. |

**Total new regression cases:** 9 + 10 + 7 + 5 = **31**. All tests are local and synthetic. The four test files are `tests/test_memory_snapshot_result_epoch_run421.py`, `tests/test_startup_result_constructor_epoch_run421.py`, `tests/test_context_reuse_fresh_result_epoch_run421.py`, and `tests/test_recovery_plan_scalar_carrier_run421.py`.

## Evidence integrity and CI scope

- Opening exact checkpoint `71c330dd95a854be3ac0d375536ac2e0ec47f059`: #1108 / `40185240920` SUCCESS.
- First coherent Memory package `4dc4405c58c004d83b77e5738f55f8856c3bc8d9`: CI #1110 / `40186142948` SUCCESS at initial verification.
- Startup package `5ce459827389ca27da036a013314a85b7530f31f`: CI #1112 / `40186228426` initially IN PROGRESS; re-evaluate exact jobs before any GREEN claim.
- Privacy package `6e8157e95950ad39a568c82bcd3c0215681b4e65`: CI #1114 / `40186364274` initially IN PROGRESS; re-evaluate exact jobs before any GREEN claim.
- Full four-package source + tests HEAD `1a39448ae02527c046df75a646ad8cb00a23b883`: CI #1116 / `40186515531` initially QUEUED; **no GREEN claim without six exact-head jobs**.
- Nontruncated Git tree comparison at the four-package HEAD against unchanged main `7a843f17eb96ed13d66f23b58b06406b3002e405`: main 94 blobs, branch 514 blobs, **420 added / 0 main files modified / 0 removed**. The engineering document and later checkpoint are additional branch-only files.

## Open safety boundaries / next work

Local digests and mock receipts are not independently authenticated. Genuine user consent/issuer verification, signed trusted-clock evidence, coordinated cross-store snapshot atomicity, external WRITE result receipts and exactly-once semantics remain **NOT_PASSED**. Never replay a durable reserved-PENDING or UNKNOWN WRITE automatically. Later work should target cross-store reconciliation, Memory CAS/expiry/multiprocess races, revocation monotonicity, Observation/Proactive fixture boundaries and V3 free-only provenance/approval controls. Keep PR #5 Draft/unmerged and do not open protected V2 final evaluation, promote a Candidate, train weights, provision GPU/API/services, use paid compute, or merge main without explicit authorization.
