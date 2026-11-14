# ARK AI — Run708 Non-UI Free-Only Safety and CI Recovery

**Basis:** PR #8 `research/jarvis-foundations`, exact initial HEAD
`5bdfc3941a97dd1a167d72c8cdd993bec39291ba`.
**Report-write-basis HEAD:** `46b792e8e0f9fa4c66fd4eb9ef475b77c8bfb3e6`.
All operations are synthetic/disconnected. No UI, external executor,
physical computer action, paid compute, V2 protected evaluation, V3 Candidate,
frozen contract, or main merge was touched.

## Package A — Memory optional generation-CAS Windows test handle lifecycle

At [CI #42461995306](https://github.com/Iam-2squared/ark-ai/actions/runs/42461995306),
all three Ubuntu jobs succeeded, while all three Windows jobs failed.
Windows Python 3.11 output includes `25 failed, 10947 passed, 60 skipped`,
with actual `PermissionError: [WinError 32]` during
`tempfile.TemporaryDirectory.__exit__`: a test-owned SQLite
`mem.sqlite` remained open at immediate directory removal.
A SQLite `with sqlite3.connect(...) as connection` transaction context
**does not itself close the connection**.

[Commit `570c1c8`](https://github.com/Iam-2squared/ark-ai/commit/570c1c8f477e5f69887e287c471daacaa5df7322)
adds `contextlib.closing` around the explicit test readback connection
in `tests/test_generation_cas_input_carrier_preaccess_run706.py`.
This preserves every hostile class-carrier rejection and stored-row assertion.
It does **not** weaken the production Memory CAS guard or suppress cleanup
errors with `ignore_cleanup_errors`.

## Package B — Due-reservation Windows test handle lifecycle

The same real Windows CI showed **12** failing parameterizations in
`tests/test_due_reservation_carrier_preaccess_run706.py` due to an open
test-created `due.sqlite` readback connection during temporary-directory
cleanup. [Commit `11ba9c7`](https://github.com/Iam-2squared/ark-ai/commit/11ba9c79706c7c623d01ecb2cd3223278fc5fce1)
uses the same deterministic `contextlib.closing` pattern.
No change to `DisconnectedDueReservations`, scheduler policy,
occurrence permissions, replay controls, or frozen contracts.

## Package C — Audit's paged read must verify unseen historical rows

The existing `SQLiteActionAudit.append()` checked the entire committed
local prefix under its SQLite writer transaction; `events()` validated
dense event IDs and the requested page plus predecessor, so an intact page
could conceal earlier/later malformed but dense rows.
[Commit `8ee0523`](https://github.com/Iam-2squared/ark-ai/commit/8ee0523d040bc2d4d6dceb598d04070d0ab7fd98)
reuses the same full historical local identity/chronology validation inside
the **existing paged read's SQLite snapshot**. Existing paged-event error
messages are retained by deferring the historical-prefix exception until
after selected-page validation. Returned pages cannot be certified by
looking only at their own well-formed rows.

[Commit `46b792e`](https://github.com/Iam-2squared/ark-ai/commit/46b792e8e0f9fa4c66fd4eb9ef475b77c8bfb3e6)
adds **five** synthetic test cases: unseen first identity corruption,
unseen final identity corruption, hidden earlier time rollback, empty page
with older corruption, and healthy read-only pagination. Tests require
no mutation of local rows or AUTOINCREMENT high-water. These are **authored
cases, not claimed PASS** until exact-head CI completes.

**Limitations:** Full prefix verification has O(N) read cost per `events()`
call in addition to existing O(N) append cost. This is a local consistency
gate; a privileged actor can jointly rewrite SQLite rows and metadata. It
is **not independently authenticated custody**, cryptographic provenance,
trusted clock/consent attestation, or external exactly-once execution.
Do not replace it with an unreviewed cache or promote it to action authority.

## Exact evidence and next integration gates

- Original Run707 checkpoint [CI #42462272165](https://github.com/Iam-2squared/ark-ai/actions/runs/42462272165): Ubuntu 3/3 GREEN and Windows 3 running at initial review. Earlier Windows failures were reproduced via the concrete logs of #42461995306 and #42462126180. Different commits' results must not be conflated.
- This invocation's new CI was automatically queued by the ordinary PR push. The final corrected combined head's six-job result **remains UNVERIFIED** until all Windows/Ubuntu Python 3.11–3.13 jobs complete. No local full-repo pytest/Ruff result or autonomous action PASS is claimed.
- PR #5 V3 and PR #9 UI remain Draft/unmerged; UI work is stopped. V1/V2/Local UI/Launcher and frozen evaluation contracts remain unchanged. No real backend, external notification, training, paid service, new credentials, protected V2 evaluation, irreversible erasure or physical-PC operation.
- Next: read the newest source/test and final checkpoint CI results; investigate actual remaining errors, if any. Continue Memory COMMIT-UNKNOWN and WAL/CAS reviews, Planner persisted per-step READ identity, registry-bound authorization and durable audit-before-action via disconnected mocks. Revisit audit prefix performance only with an independently reviewed custody design.
