# Run559 — Passive packet-file open: final symlink race guard

**Scope:** V3 Draft PR #5, locally saved review packets only. No GPU,
preflight/training execution, billable service, real Candidate generation,
protected V2 evaluation, promotion, or main merge is authorized by this work.

## Change

- [Source 72f6466d](https://github.com/Iam-2squared/ark-ai/commit/72f6466dd462d7d92223a09eb2d7a61953bf7dd4):
  `src/ark/learning/authorization_packet_file_review.py` now opens a
  previously `lstat`-checked file through `os.open` with
  `O_RDONLY | O_NOFOLLOW` where the platform exposes `O_NOFOLLOW`, plus
  binary/close-on-exec flags if available. It retains existing bounded reads,
  `fstat`/path `lstat` identity comparisons, canonical JSON and packet-byte
  digest revalidation, and final post-verifier reread.
- [Tests a3998aa7](https://github.com/Iam-2squared/ark-ai/commit/a3998aa7920c688d9a26c456f22f496ba5de9b01):
  `tests/v3/test_packet_file_nofollow_open_run559.py` adds two POSIX
  regression cases (skipped where `O_NOFOLLOW` is unavailable): kernel-open
  flags on both reads, and replacing an ordinary packet path with a symlink
  to a byte-identical synthetic file between `lstat` and `open`. The swap
  must fail before opening the redirected target on supported platforms.

CI [41479385376](https://github.com/Iam-2squared/ark-ai/actions/runs/41479385376)
was **IN PROGRESS** at last inspection; do not report full GREEN until the
exact source/test HEAD's six jobs are complete.

## What this does not establish

- `O_NOFOLLOW` guards the **final path component** only and is unavailable
  on some platforms (including conventional Windows Python). Existing parent
  symlink checks can still race; there is no anchored directory-fd walk or
  independently authenticated immutable copy.
- A file digest, local inode and symlink check cannot authenticate the reviewer,
  local source ownership, provider billing cap or compute authorization.
- Frozen V3 Experiment 001 settings, immutable contract, provenance and V2
  final evaluation gate are unchanged; real compute remains blocked.

Next free work: a separately reviewed Windows path-handle strategy and
immutable/local-byte staging before any runtime import or model load. These
require explicit design/provenance checks and cannot be replaced by this
best-effort offline packet verifier.
