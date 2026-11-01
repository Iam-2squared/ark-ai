# Run523 — V3 execution-snapshot local source-epoch custody

**Branch:** `research/v3-learning-evaluation` (Draft PR #5, unmerged). **Source/test basis HEAD:** `21f75a3a6e96ad5d9bb9b5ec1d436b4fce98ded4`. **Status:** safety groundwork only; **NOT_PASSED**.

## Scope, semantics and non-authority

`load_snapshot()` in `src/ark/learning/execution.py` still reads only local, size-bounded JSON and rejects duplicate JSON keys and nonfinite values. Its new read-only source-epoch guard captures the initial opened file identity and bytes, performs the existing JSON parse, then re-opens the same path and compares the full bounded bytes and `st_dev/st_ino/st_size/st_mtime_ns` against the initial open. A changed, deleted, swapped or replaced input is rejected before the parsed dictionary is returned. The input is still not canonically rewritten; legitimate noncanonical JSON remains supported.

This is **not** a filesystem lock, trusted storage, cryptographic provenance, user approval, billable-compute permission, or an atomic guarantee against modifications after this check. The guard never launches a training job, downloads a model, generates an adapter/Candidate, opens frozen V2 scoring, promotes a model or changes Contract 1.

## Executable regressions

`tests/v3/test_execution_snapshot_source_epoch_run523.py` covers a stable valid fixture, differing content written by a parser callback, an oversized replacement, a same-byte **different-inode** replacement and source removal. The initial test mistakenly expected an identical same-byte rewrite to be detected on every platform; Windows precision showed that expectation was not justified. The test was corrected to demand rejection of actually differing bytes, without removing or relaxing any production guard.

The original source/test run [41286107623](https://github.com/Iam-2squared/ark-ai/actions/runs/41286107623) had four passing jobs and two failing Windows jobs because the identical-byte fixture did not always change the observable file identity/timestamp. The correction was saved in `21f75a3a6e96ad5d9bb9b5ec1d436b4fce98ded4`; its exact-head GitHub CI must be inspected separately before declaring GREEN. This documentation itself does not inherit that CI.

## Persistent hard stops

No paid/external GPU/API or new service, credentials, model bytes, actual human approvals, full Candidate/weights, protected V2 final evaluation, contract changes, automatic promotion or main merge. PR #5 remains Draft/unmerged pending its existing controlling gate. Input hashes and local inode checks are *local consistency*, not upstream materialization or authenticated human-review evidence.

## Next

1. Verify exact corrected test-source CI on the saved HEAD across six environments, fixing genuine failures only via normal Contents writes.
2. Preserve free-only model byte/path/identity, audit-provenance and reproducibility guards without opening the protected evaluation or training.
3. Require separately explicit authorization at any paid/physical/human-review/real-Candidate boundary.
