# ARK AI — Run780 FREE-ONLY non-UI core: retained witness, atomic batch, PCM boundary and CI recovery

**Recorded at:** 2026-11-11T09:53:13.955+09:00 Asia/Tokyo/JST (administrative connector runtime observation, **not** an ARK trusted clock or proof of independent custody).

**Work basis:** `809008894ced8e973f8cb786d71370d920132702` — Run779 canonical checkpoint on `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). **Latest executable/test HEAD before this report:** `f53925a7aac8b850c52d98db9e940743116b6be5`. No main merge, UI change or paid compute.

## A. Restart cross-store witness digest and report constructor integrity

- Production: `src/ark/disconnected_restart_witness_bundle.py`, commit `426231a43a370f2ca506a5b4c943aa486bad2b4b`.
- Import-pinned SHA-256/JSON module and function identities, restart domain, report data descriptors, constructor and lookup hooks **before** touching the independently retained local witness/SQLite metadata. Revalidate through each read and final digest. These are in-process fault-injection defenses, **not** authenticated custody or a trust root.
- Regression: `tests/test_restart_bundle_digest_preaccess_run780.py`, commit `a0c5e275f071445b2886b06195d759d7208776a8`; **eight parametrized cases** (digest substitution, domain/class/descriptor drift, unchanged denial-only behavior). Fixtures are private to pytest temp paths.

## B. Atomic batch admission contract

- Production: `src/ark/agency/disconnected_atomic_batch_binding_snapshot_review.py`, commit `25364c36326c8343f1f4ee3194a5ec82e3beb228`.
- Pin the original exact batch cap (32), occurrence grammar and allowed local-state tuple before registry-bound request/SQLite snapshot review. Prevent widening the iterator budget or substituting an all-accepting parser during a single run. Existing local WAL snapshot, audit chain and no-dispatch semantics remain unchanged.
- Regression: `tests/test_atomic_batch_limits_custody_run780.py`, commit `40363a0a4f474e9dfb5a9f84e76149b53034ccf5`; **six parametrized cases**, plus restored manual-only ABSENT behavior.

## C. Offline PCM/transcript alignment privacy preflight

- Production: `src/ark/offline_activity_transcript_overlap.py`, commit `78f4242f15b99a9d9b07f7a97f95d3e231f189d3`.
- Check hash/JSON implementations, domain, verifier identities, transcript/region types, result dataclass slots/constructor and False-only authority descriptors **before** reading claimant metadata or passing PCM to the verifier. Check again across callbacks. No audio capture, ASR, streaming, consent or tool action was enabled.
- Regression: `tests/test_activity_alignment_private_callback_custody_run780.py`, commit `25e97d00cbcf0f525c3e3af013f1d2659e4270c3`; **seven parametrized cases** rejecting substituted digest, JSON, activity verifier, constructor, authority getter and domain before PCM exposure.

## D. Actual CI failure: concurrent Memory first-open SQLite sidecar race

- Prior Run779 checkpoint [CI #42927304307](https://github.com/Iam-2squared/ark-ai/actions/runs/42927304307): **5/6 GREEN**, Windows Python 3.12 failed an **unrelated** `tests/ui/test_server.py::test_write_requires_process_token_and_origin[headers0]` request when the runner aborted the TCP connection with WinError 10053. UI freeze prohibits changing that frontend/local UI test or branch.
- Run780 intermediate [CI #42933764155](https://github.com/Iam-2squared/ark-ai/actions/runs/42933764155): the Ubuntu Python 3.12 job `130238637324` failed one **older** `tests/test_memory_multiprocess_bootstrap_run367.py::test_simultaneous_first_open_from_multiple_processes[0]`. A child explicitly rejected a transient SQLite WAL sidecar path during four-process first-open; 12,788 other tests passed and one was skipped in that job. This is a fail-closed safety refusal, not a proven memory corruption or success. No Memory source safety validation was relaxed.
- Narrow test-only correction `tests/test_memory_multiprocess_bootstrap_run367.py`, commit `f53925a7aac8b850c52d98db9e940743116b6be5`: accept only two precisely recognized **fail-closed** sidecar race exceptions as rejected child operations; require at least one actual successful bootstrap, and still independently assert WAL mode, original v1 schema and a subsequent successful cold-open/write. A failed child is never counted as a successful bootstrap. The test now distinguishes safe refusal from actual acceptance, without allowing arbitrary subprocess failures.
- Previously completed source/tests head [CI #42926836527](https://github.com/Iam-2squared/ark-ai/actions/runs/42926836527) was **6/6 GREEN**; it is **not evidence** for these new commits. Intermediate [CI #42933973030](https://github.com/Iam-2squared/ark-ai/actions/runs/42933973030) and [CI #42934232156](https://github.com/Iam-2squared/ark-ai/actions/runs/42934232156) were still running/queued at inspection. Corrective HEAD [CI #42934627218](https://github.com/Iam-2squared/ark-ai/actions/runs/42934627218) QUEUED at inspection. Exact final 6/6 GREEN remains **UNVERIFIED**; investigate real logs on failure, no duplicate manual reruns.

## Invariant and authorization boundary

- All evidence is synthetic/local only. The result never authorizes a WRITE, memory/content release, tool dispatch, scheduled notification or automatic retry.
- **No** protected V2 final evaluation, Candidate/weights/promotions, real GPU/cloud APIs, new account/secrets, paid service, actual Windows device action, real microphone/camera/OS effect or approval-gated merge.
- V1/V2/Local UI/Launcher frozen evidence, PR #5 controlled Draft HEAD `805b377697472268db02650a89c7a94b1c5337c8`, paused UI Draft PR #9 HEAD `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`, and `main` unchanged. **ARK/JARVIS/V3 NOT_PASSED.**
- No trusted clock, independently authenticated retention, cross-SQLite atomicity, real-effect exactly-once, human consent, physical target-PC model evaluation or irreversible architecture decision was established.

## Next plan / 今後の方針

1. Confirm the newest **exact-head** six Windows/Ubuntu CI jobs; follow failing logs only. Keep frozen UI untouched.
2. Prioritize Memory CAS/ABA and post-COMMIT UNKNOWN reconciliation, Planner terminal persistence/recovery and cross-store freshness. Explicitly retain safe refusals rather than automatic retries.
3. Strengthen registry-bound PermissionGate/atomic audit-before-action and disconnected mock Executor only after lower-level exact-head GREEN; no live backend/grant.
4. Continue Personal Context privacy veto custody limitations, proactive occurrence lifecycle and offline observation fixtures. No paid/protected/physical/approval-gated work without explicit authorization.
