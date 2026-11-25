# Run562 — passive V3 packet opened-handle recheck

Work basis: PR #5 `research/v3-learning-evaluation`, `38a4e9d598df0f8715f00c2abbe0e2194a99edce` (prior [CI 41494383671](https://github.com/Iam-2squared/ark-ai/actions/runs/41494383671) completed SUCCESS).

## Scope

[Source `94dc61d2`](https://github.com/Iam-2squared/ark-ai/commit/94dc61d28c99af3a9f26e1a22a85bf0700797103) now performs a second `os.fstat()` **after** the bounded packet-file read but **before closing the opened descriptor**. It compares this handle's regular-file type, single-link requirement and portable inode/size/mtime/OS-specific ctime epoch against the first opened handle and path epoch. Checking the final *path* alone could miss drift of an already-open descriptor when the pathname observation was stale or misleading.

[Test commit `5bea6b88`](https://github.com/Iam-2squared/ark-ai/commit/5bea6b88ad0eaf7ef01b400765766a7548192b2f) adds **four authored fixture cases**: a normal two-fstat read plus synthetic postread handle drift in mtime, inode and link count while path metadata remains unchanged. These are authored pytest cases, not a local PASS count. [CI 41503703692](https://github.com/Iam-2squared/ark-ai/actions/runs/41503703692) was **QUEUED** at last inspection; exact-head green must be checked later.

## Boundaries

This is a passive, bounded, local packet-custody diagnostic, **not** immutable filesystem custody. POSIX ctime does not prove a trusted source; Windows ctime behavior remains the previously documented fallback. A race after the second fstat, a swapped ancestor directory, coordinated metadata spoofing, or an untrusted local process remain outside this narrow guarantee. The underlying packet retains explicit false-only external-compute/Candidate/protected-evaluation/main-merge authority. Frozen V3 Contract and V1/V2 evidence are unchanged. No actual GPU, paid compute, real Candidate, scoring, model weights, approvals, external APIs, or main merge.
