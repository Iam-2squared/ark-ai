# Run561 — Passive V3 packet ctime custody (zero-cost, no authorization)

This note documents an **unapproved, read-only** local packet integrity hardening on
Draft PR #5. It does not authorize a GPU/API call, preflight training, Candidate,
protected V2 evaluation, promotion, or main merge.

## Exact change and limitations

- Original baseline HEAD: `7b75f12be085e1c142512941121a4bd7aefb59d3`.
- `src/ark/learning/authorization_packet_file_review.py`: the file epoch used
  on both opens now includes **POSIX `st_ctime_ns`** in addition to dev,
  inode, size and mtime. A same-byte rewrite that restores `st_mtime_ns`
  may still advance inode change time. The review rejects inconsistent
  snapshots **before** accepting an inert witness; no external action follows.
- Source commit `783aca8abebb4e583ae292b51977e79c0dda65ef`;
  synthetic tests `3837ffa721eb9b2e370efb77e112a964d0da2ede`.
- Initial source-only CI [41493707431](https://github.com/Iam-2squared/ark-ai/actions/runs/41493707431)
  **FAILED on Windows 3.12/3.13** because Windows path.stat/fstat ctime
  semantics did not preserve the new epoch equality even for unchanged files.
  This is a real compatibility issue, **not** evidence of file tampering.
- Focused correction `e1ff72a7e3587518b36894c9894c61b5be83c6f4`
  applies the ctime check **only on POSIX**, retaining the previous Windows
  four-field guarantee with a constant fifth placeholder.
  Corresponding test correction HEAD `3186e2af3fe15901d002fe297cba194562083ea4`.
  The corrected exact-head full CI result must be checked independently;
  initial failure is not retroactively GREEN.

## Test intent

`tests/v3/test_packet_file_ctime_custody_run561.py` exercises the platform
epoch shape and a POSIX same-byte rewrite with deliberately restored mtime.
The latter is skipped on Windows and on a filesystem where no distinguishable
ctime change can be observed. Existing nonregular/FIFO and final symlink
barriers remain intact.

**Not proven:** authenticated writer/retained hash, durable immutable file
custody, ancestor-path race exclusion, atomic third-party state, provider
identity, clock trust or any real paid authorization. Never infer provenance
or approval from local file metadata, even on POSIX.
