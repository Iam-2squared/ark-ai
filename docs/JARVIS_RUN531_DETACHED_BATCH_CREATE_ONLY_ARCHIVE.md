# Run531 — restart-safe, create-only detached Planner batch cycle archive

**Branch:** \`research/jarvis-foundations\`, Draft PR #8, unmerged. **Initial work basis:** \`2c93a7ef06408511b6a766908e6da8c0a8867471\`. Source \`2be12608a6fecda84b218e2f3ade2b31417b96a8\`; source + focused tests \`b6664cbf0dc1426886e69dfac23a97d040061bc8\`; Ruff-only wrapped-signature fix \`8a2c3779a9f3096b00361bf3218e7c049952ad07\`.

## New reversible capability

\`src/ark/agency/disconnected_batch_cycle_archive.py\` introduces a **real create-only local-file persistence path** for *deterministic mock* Planner DAG wave results. It is intentionally separate from the real ToolBackend, action/consent/PermissionGate, Memory writes, scheduler dispatch, external effects and UNKNOWN WRITE recovery.

- \`archive_disconnected_batch_fixture_cycle\` independently verifies the caller's existing synthetic plan, schedule and fixture cycle; serializes only request IDs, plan/schedule/step hashes, and the cycle hash. **No raw fixture arguments, private context or result contents** are archived.
- It writes a bounded canonical JSON archive with an exclusive create operation (\`O_CREAT | O_EXCL\`), refuses an existing path rather than overwriting it, flushes and fsyncs the new handle, and reopens the archived data to compare against an independently recomputed mock cycle.
- \`review_disconnected_batch_fixture_cycle_archive\` is a restart-safe **read-only** verifier requiring the prior plan digest and a separately retained archive-file SHA-256; it checks safe regular-file properties/aliases and two exact reads, re-runs detached fixture steps, and compares canonical bytes and file epochs before returning a non-authorizing digest witness.
- Failures after the file has been created **do not auto-delete, overwrite, retry or roll back** it. A partial or ambiguous file is quarantined for manual review; fsync and matching bytes are not a universal durability guarantee on all filesystems.

**Focused tests:** \`tests/test_disconnected_batch_cycle_archive_run531.py\` has ten test functions with parametrized cases for cross-object/restart review, no raw private fixture argument leakage, existing-file safety, modified/stale archive digests, path aliases, symlinks/hardlinks, mutation during a second read, ambiguous fsync, concurrent exclusive-create winner and no granted authority.

## Verification and hard stops

- Initial source-only [CI 41312502403](https://github.com/Iam-2squared/ark-ai/actions/runs/41312502403) and source+test [CI 41312592885](https://github.com/Iam-2squared/ark-ai/actions/runs/41312592885) both **FAILED** all six matrix jobs at Ruff E501: \`disconnected_batch_cycle_archive.py:170\` 102-character helper signature. Exactly that signature was wrapped at \`8a2c3779...\`, with no runtime logic or denial policy change.
- The corrected commit's distinct CI needs to be checked; **do not infer GREEN** from earlier heads. Ten test functions were authored, not independently run locally because \`github.com\` did not resolve in the local container.
- No model/GPU/API, real Tool execution, external READ/WRITE, consent, trusted-clock attestation, secret, physical PC or paid service was accessed. This archive records only a deterministic synthetic result. It cannot establish real execution success or grant automatic replay. No frozen v1/v2/UI/Launcher/evaluation contracts were modified; ARK/JARVIS remains **NOT_PASSED**.

**Next:** confirm corrected exact-head CI; investigate and fix any focused-test mismatch without relaxing safety; then integrate this synthetic persistence witness only behind separately validated ToolRegistry/PermissionGate and trusted audit boundaries. Keep PR #8 Draft/unmerged and main unchanged.
