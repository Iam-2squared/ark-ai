# Run524 — V3 regular-file source-identity fence (local only)

**Branch:** `research/v3-learning-evaluation`, [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), unmerged. **Source/test basis HEAD:** `09f80e21c03eb2ecf267051e76bca50f567a7ebb`. **Overall V3 status:** NOT_PASSED.

## NEW: refuse nonregular or source-swapped execution snapshots

`src/ark/learning/execution.py` now checks `Path.lstat()` **before opening** the bounded JSON execution snapshot. A symlink, directory, FIFO or other non-regular source is refused. Oversized regular files fail at the path-stat stage, before even opening them. After open, `fstat` identity must match the initial `lstat` source; after JSON parsing, **both** the reopened file identity and the final path-entry `lstat` must still match the original inode/device/size/mtime. Byte equality remains mandatory. This complements Run523's read-open/reopen byte fence, without changing V3 experiment, approval or training semantics.

**Seven new test cases** in `tests/v3/test_execution_snapshot_regular_source_run524.py` exercise normal noncanonical JSON; directory rejection; symlink rejection (skipped only when the runner cannot create symlinks); named-pipe rejection (platform-dependent skip); pre-open byte-budget refusal; inode replacement between path stat and open; and same-inode hard-link retargeting via a symlink during decode (skipped only where link creation is unavailable).

## Evidence

- Source update `4af3f35e10dd337357127f0b9a4cdd58f168d2dd`; combined source/test `09f80e21c03eb2ecf267051e76bca50f567a7ebb`.
- [Exact combined-source CI #41290319534](https://github.com/Iam-2squared/ark-ai/actions/runs/41290319534): **6/6 GREEN** on Ubuntu/Windows Python 3.11–3.13. This is not a separate local pytest claim; permitted platform skips are conditional.
- No actual HF model/tokenizer bytes, upstream revision, adapter, preflight, Candidate run, GPU, billing action, V2 opening or promotion occurred.

## Limits and frozen boundary

These checks make unsafe local file types and **observed** same-file identity drift fail closed. They are not path locks, trusted storage, authenticated provenance or protection from a later modification after return. Filesystem stat precision and link privileges vary by OS; callers must still present exact immutable source identity and explicit human/compute authorizations at later gates. V3 Contract 1, frozen V1/V2/Local UI/Launcher evidence, protected V2 final evaluator and `main` were not modified. PR #5 remains Draft/unmerged. No cost or new credentials.

## Next plan

Continue free-only approval packet/path/identity/provenance reviews without executing training. Any actual provider/GPU spending, protected V2 evaluation, real Candidate generation, irreversible action, contract change or merge remains blocked until separately authorized.
