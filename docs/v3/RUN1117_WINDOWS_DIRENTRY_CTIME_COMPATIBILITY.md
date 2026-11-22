# Run1117 — V3 no-follow traversal: Windows metadata compatibility

## Exact basis

- Parent: Draft PR #294, `research/run1116-v3-code-tree-no-follow-rebase`.
- Parent HEAD at child creation: `48044409d6bc73982ca14f9b8c6d34dabf1b39f8`.
- Child: Draft PR #295, `research/run1117-v3-reparse-fixture-repair`.
- Latest source/test commits before this report: `c91a8ec29132b2e05268c485595e0fe7874df53f`, `73fcdef303e33d0a3e252f88e6d3a6da8187e0a0`, `771926956eb73c67668c7b4865ccf801119a2cd2`.

## Failure evidence and diagnosis

The first child revision's exact-head CI run [45051615687](https://github.com/Iam-2squared/ark-ai/actions/runs/45051615687) completed with all three Ubuntu matrix jobs GREEN and all three Windows jobs FAIL. The inspected Windows Python 3.12 job [137297761142](https://github.com/Iam-2squared/ark-ai/actions/runs/45051615687) reported 38 failures, 1,563 passes and 7 skips. Most failures surfaced as `snapshot entry changed during enumeration` during otherwise stable local directory scans.

The implementation compared `info_epoch[2:]` and `path_epoch[2:]`, which includes `st_ctime_ns`. On Windows, `DirEntry.stat` and `Path.lstat` can expose different ctime semantics (creation time versus change time), as already documented in the file-hashing path. The code comment called these fields portable but the comparison was broader than the portable set.

## Repair

- Add a pure metadata comparison helper.
- On Windows, ignore device/inode and ctime differences between DirEntry and Path observations, but still require mode, size, mtime and link-count agreement.
- On POSIX, retain the complete device/inode/mode/size/mtime/ctime/link-count equality check.
- Keep the separate Path-derived epoch recheck, so the accepted path metadata must remain stable against itself.
- Replace the test's mutable `identity.os` substitution with direct tests of the platform comparison rule.
- Keep the synthetic reparse fixture on the new no-follow `os.scandir`/DirEntry path; reject before Path metadata access or nested enumeration.

## Limits and next evidence

This remains best-effort local filesystem admission, not atomic dirfd custody or protection against a hostile concurrent writer. No model download, GPU, training, Candidate, protected V2 evaluation, paid service, credential, hardware action or main merge. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; this report does not claim PASS. PR #294 and PR #295 remain Draft; PR #5 remains gated Draft/unmerged. ARK/JARVIS remains NOT_PASSED.
