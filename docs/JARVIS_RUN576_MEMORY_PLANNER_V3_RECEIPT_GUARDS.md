# ARK AI Run576 — Memory child receipts, Planner restart failure, V3 passive authority

This technical note records **free-only, non-UI, reversible** work on the Draft branches of PR #8 and PR #5. No backend dispatch, real Memory write outside synthetic tests, paid compute, V3 Candidate generation, protected V2 evaluation, approval, or main merge was performed. **ARK/JARVIS/V3 NOT_PASSED.**

## Memory — dual-read COMMIT ambiguity custody (PR #8)

- Source commit: `5219cd8743e11e08c38f270cb2a525fb1c3f7f8b`; test commit: `eb0af848dc26504e86f5a63bf4546e02c4edcfcc`.
- `src/ark/memory/ambiguous_commit_pair_review.py` now snapshots the first child review receipt *before* invoking the second reviewer. It checks identity of all child field carriers after each false-only denial callback and recomputes the two children's distinct domain-separated SHA-256 receipts from their declared fields. A forged, syntactically valid SHA, or a reflected rewrite during a nested callback, fails closed rather than being rebound into the parent pair digest.
- `tests/test_memory_ambiguous_child_integrity_run576.py`: **6 authored parameter-expanded cases** covering forged first/second digests, reentrant rewrites, and unchanged/matching manual-only observations.
- Prior existing tests correctly expected refusal but expected *later* disagreement/drift messages. CI `41605105521` observed three such FAILs. Two **test-only** normal API corrections at `572ab02b5096ab92a133bb9de9ace6a486d51eac` and `6dc9422aee1073c1915243b54f4fdb06b3781f49` assert the new earlier child-digest diagnostic without removing assertions or loosening the source check.
- Local receipt digests are **not** signed, do not identify writers or prove a COMMIT, and **never** permit automatic retry. Two SQLite reads remain non-atomic.

## Planner — failed-step dependency consistency (PR #8)

- Source commit: `2ae4b5073133556a4d8473e123da12b42b85eabd`; test commit: `130d7a7365c3437f894f83d66608835da521e1b8`.
- `src/ark/agency/disconnected_write_recovery_fence.py`: a synthetic `FAILED` step, like `RUNNING`/`SUCCEEDED`, can claim prior execution only after **all** its dependencies are `SUCCEEDED`. A `BLOCKED` or `CANCELLED` child still may be an unstarted terminal diagnostic; unresolved UNKNOWN WRITEs remain quarantined.
- `tests/test_mixed_failed_dependency_guard_run576.py`: **12 authored cases** (8 contradictory dependency/effect combinations, 3 legitimate unstarted successors, 1 failure after valid predecessor). No live Planner state transitions or ToolBackend invocation.

## V3 — import-time pinned child snapshot denial (PR #5)

- Source commit: `97aa92414f1b6b12904a0df760f9315a9ce91215`; test commit: `df7e78c531792f0c1aaf3a035e636ac5526da79f`.
- `src/ark/learning/offline_readiness_transition.py` now captures **original source shape report denial descriptors at module import**, before processing either unapproved snapshot. A preinstalled false-only replacement fails before JSON tree inspection, instead of becoming the new post-callback baseline. Existing path, digest, and output restrictions remain unchanged.
- `tests/v3/test_passive_transition_child_denials_run576.py`: **7 authored cases** covering all 6 denial descriptors and unmodified passive syntax-only behavior. No model loading, local identity fabrication, approval, training, export or paid runner.

## Evidence and limits

- Previous exact-head CI: PR #8 `16e934529e5de90851786f1e6cd3e71f0ad35ec0` run [41599463055](https://github.com/Iam-2squared/ark-ai/actions/runs/41599463055), **6/6 GREEN**; PR #5 `882d72d4180b58f6979b7c374c26c934df78fa6b` run [41599787593](https://github.com/Iam-2squared/ark-ai/actions/runs/41599787593), **6/6 GREEN**.
- PR #8 intermediate run [41605105521](https://github.com/Iam-2squared/ark-ai/actions/runs/41605105521) **FAIL (3 inherited error-message expectations)**, corrected subsequently. Latest corrected source/test HEAD [41605745535](https://github.com/Iam-2squared/ark-ai/actions/runs/41605745535) **QUEUED at direct sample**. PR #5 latest source/test [41605638463](https://github.com/Iam-2squared/ark-ai/actions/runs/41605638463) **IN PROGRESS at direct sample**. **Do not inherit old GREEN for new HEADs.**
- **25 authored cases** are test definitions, not a locally verified 25 PASS. Local clone/pytest is unavailable due to container DNS, so exact commit CI is execution evidence only after each run completes.
- Frozen Memory `b6e93821ecd69270a7634aceb20775dc36e9953c`, Planner `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`, and V3 Contract `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` Blob SHAs remain unchanged.
- UI/Frontend paused; PR #9 stays Draft/unmerged at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`. PR #5/#8 stay Draft/unmerged; main remains `7a843f17eb96ed13d66f23b58b06406b3002e405`.

## Next plan / 今後の方針

1. Confirm the new exact-head six-job CI; repair only actual failures using normal Contents API, switching immediately to an independent non-UI lane.
2. Advance generation-CAS uncertainty with independently retained witnesses, consent/revocation fences and coherent local snapshots (no auto retry).
3. Advance Planner FAILED/BLOCKED restart chains, Registered READ partial success receipts, exact registry-bound PermissionGate, and durable audit-before-action in disconnected mock mode.
4. Continue non-UI proactive/observation backend, privacy retention, and free-only V3 identity/approval guard reviews. Leave PR #9 untouched until UI work is explicitly resumed.
