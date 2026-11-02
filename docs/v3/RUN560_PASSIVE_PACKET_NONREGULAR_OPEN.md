# Run560 — Passive V3 packet pre-read nonregular-file fence

**State:** free-only, read-only review, with no training, GPU, model access,
external API, provider action, Candidate generation, protected V2 evaluation,
approval, promotion or `main` merge.

The existing detached packet review compared `lstat` and `fstat` file
epochs, final-path non-symlink status, canonical JSON and independently
retained packet SHA-256. It previously read opened bytes **before** checking
whether the opened descriptor was a regular single-link file. A local
path swap from regular file to FIFO between `lstat` and `open` could
therefore block in a read-only FIFO `open` on POSIX; swapping to a device
could cause non-file data to be read before the later type rejection.

In `src/ark/learning/authorization_packet_file_review.py`, the
`os.open` flags now include `O_NONBLOCK` when available. Immediately
after `fstat`, the opened descriptor is required to be a regular,
single-link file with the original device/inode/size/mtime epoch **before**
any byte read. A changed inode fails closed, even if an attacker copied
identical JSON bytes into the substitute file. Existing second-read and
symlink checks remain. No schema or frozen contract has changed.

New `tests/v3/test_packet_file_open_pre_read_fence_run560.py` provides
three synthetic cases: supported-platform nonblocking flag, final-component
FIFO substitution at the open boundary (POSIX-only), and same-byte regular
replacement with a trap that rejects any unverified read. These are three
authored pytest cases, not a claimed local PASS count. CI requires separate
exact-HEAD verification.

Source commit `f279cc79999ec216d44e841bfe7b92da03fd8533`;
new test commit `fbfac51369a9464e6d1664a5e7cae0163bb2ffe0`.

**Residual boundaries:** `O_NONBLOCK` and `O_NOFOLLOW` depend on OS support.
Windows does not receive a matching kernel-level FIFO/symlink guarantee.
Ancestor-directory substitution, privileged filesystem races, cross-machine
identity, upstream Hub revision, immutable model bytes, authenticated human
approval, and provider billing authority are **not** established by local
`lstat/fstat` or matching hashes. Real V3 training remains blocked.
