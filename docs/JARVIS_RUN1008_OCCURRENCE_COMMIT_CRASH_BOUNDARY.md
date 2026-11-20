# Run1008 — durable occurrence survives a process crash before audit

**Work basis:** Draft PR #31 exact head \`e228d599dc78fe635fbaa596169d9a035fe0c07b\`. This is a test-only child of the Planner/mock authorization chain. The new regression is \`tests/test_mock_executor_occurrence_commit_crash_run1008.py\`.

## Crash boundary exercised

The spawned child constructs fresh local registry, PermissionGate, Action Audit, occurrence store and exact \`MockToolBackend\`. It then executes one synthetic WRITE. A process-local SQLite connection wrapper observes the occurrence INSERT and calls the native SQLite \`commit()\`; immediately after that commit returns, the child writes a disposable test marker and terminates with \`os._exit(0)\`.

The crash therefore occurs after the durable occurrence reservation but before \`reserve_synthetic\` returns, before the separate Action Audit append, and before the only mock backend call.

The parent verifies:

1. the child exited at the intended post-COMMIT boundary;
2. the occurrence row survived cold reopen and contains only the domain-separated token digest, not the plaintext token ID;
3. the separate Action Audit remains empty;
4. a fresh process-local PermissionGate cannot make the same token reusable;
5. retrying with either the same occurrence ID or a different occurrence ID is denied by the durable token reservation before audit append or mock execution.

## Interpretation and limits

This deliberately records the non-atomic boundary between the existing occurrence and Action Audit databases: a crash can leave a committed occurrence with no pre-action audit row. The safe behavior is quarantine/no retry, not repair, release, or inferred dispatch. The test does **not** make the two databases atomic.

Only disposable local SQLite, synthetic identifiers/time, and the exact in-process mock backend are used. It does not prove trusted time, authenticated consent, independent custody, power-loss durability, a real external effect, or exactly-once real-world execution. No real ToolBackend, credentials, network, shell, device, paid service, GPU, Candidate, protected V2 evaluation, frozen contract, UI branch, or main branch is changed.

**Validation:** authored test only. Exact-head six-job CI is pending after the Draft child PR is opened; no PASS is claimed. Overall ARK/JARVIS remains NOT_PASSED.
