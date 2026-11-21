# Run944 — disconnected Memory WAL CAS, proactive identity admission, V3 packet cold custody

This document is a **narrow non-UI development and incident analysis**, not a new
architecture authority, freeze, evaluation, human review, or a JARVIS completion claim.
All observed identities are local-process diagnostics, not authenticated provenance.
No paid/external compute, GPU training, live tool backend, notification, new secret,
protected V2 evaluation, Candidate promotion, UI change or main merge is authorized.

## 1. Cross-process Memory WAL test: isolate CAS from last-close unlink

**Prior run's unexpected failure:** [CI #44088190412](https://github.com/Iam-2squared/ark-ai/actions/runs/44088190412) had five successful jobs and a failing Ubuntu/Python 3.11 job. The failing test was
`tests/test_memory_cross_process_cas_run424.py::test_simultaneous_processes_have_one_cas_winner_and_one_audited_update[1]`.
The child failed *before its CAS gate*, while constructing `SQLiteMemoryStore`, with
`MemorySchemaError` for `-shm`, a regular file with `st_nlink == 0`.
The runner reported `1 failed, 17063 passed, 1 skipped`. No unsupported claim
of corrupted Memory rows or an actual double-CAS commit is inferred.

**Why it matters:** independently starting two Python SQLite connections can race
SQLite's last-connection WAL/SHM unlink against another connection's pathname
`lstat`. This is distinct from a durable hardlink/symlink/special-file alias,
which the production guard must continue to refuse. A bounded second pathname
check already existed in `src/ark/memory/sqlite_store.py` but did not eliminate
the transient (a regular inode may be unlinked at both checks).

**Fix scope:** [commit 734b4fe](https://github.com/Iam-2squared/ark-ai/commit/734b4fe0141c73ff06d1348abac1179b3e26b2a6)
keeps a real SQLite read transaction open in the parent while both child
processes start and cross the CAS barrier. Keeping a reader open prevents
unrelated *final-close* sidecar unlink while the test asks a distinct question:
whether concurrent contenders produce one revision-2 winner with exactly one
update event. The existing production custody refusal remains untouched;
the test does not retry a tool, ignore corruption, force open a path, or
weaken an alias check. Separate WAL lifecycle and sidecar-custody tests remain
responsible for startup/last-close behavior; this test no longer conflates
that phenomenon with CAS correctness.

## 2. Proactive synthetic schedule identity NUL protection

[Commit 5a54abf](https://github.com/Iam-2squared/ark-ai/commit/5a54abfcb097c49658844291d24c1db59a764f70)
adds one early, bounded reject to the non-UI synthetic policy text validator:
an exact string containing `U+0000` cannot become an owner, namespace,
definition or revision identity. Length limits and strict UTF-8 admission
remain in force. [Test commit 5cf2be1](https://github.com/Iam-2squared/ark-ai/commit/5cf2be1a9aabf369dc1fb7321c52945bed5a9c24)
introduces 12 field/placement combinations plus one valid Unicode local
SQLite receipt. [Fixture correction d897f02](https://github.com/Iam-2squared/ark-ai/commit/d897f0297c986f2da4e94b2b649a0139d8f37d2b)
uses true NUL characters at Python runtime instead of a literal slash-x
sequence; no production policy was relaxed. These tests do **not** enable
scheduler dispatch, notification, trust in a caller clock, or consent.

## 3. Offline V3 packet reproducibility and rejection in cold interpreters

[Test commit a6ffe78](https://github.com/Iam-2squared/ark-ai/commit/a6ffe7889907ce43f9f40046f7aae5e6758abb80)
adds three Python subprocess checks of exact supplied packet digest,
normalized cross-binding digest, checks and four False-only authority flags,
plus four malformed-packet refusals which must not echo packet data.
[Fixture correction c04a443](https://github.com/Iam-2squared/ark-ai/commit/c04a4433aa4efda9516b2c8a7b182c9bfa17b5e0)
uses an actual newline and NUL byte rather than backslash spellings.
The tests use synthetic in-memory JSON only. They do not open protected
evaluation materials, verify machine identity, run training or obtain approval.

## Integration / validation constraints

- Total new tests authored: **20** (13 proactive + 7 V3), plus one existing
  Memory cross-process test modified. They are **not claimed full six-job GREEN**
  merely because GitHub stored the commits. The latest exact-head workflow
  and the checkpoint-result workflow must be checked independently.
- The production `Memory` SQLite alias guard is unchanged. If the new
  reader fixture still exhibits an unsupported startup refusal, inspect the
  *exact failed job* instead of retrying or weakening the production gate.
- `Proactive` identities and V3 hashes remain synthetic local diagnostics.
  An expiry, CAS result, or packet digest is not human approval, external
  exactly-once execution, independently authenticated source custody, or
  a trusted timestamp.
- V1/V2, Local UI/Launcher, frozen Observation and V3 contract/evaluation
  gates are untouched. UI Draft PR #9 and V3 Draft PR #5 stay unmerged.
- Next independent core gates: Memory coherent snapshot/CAS/event prefix
  failure recovery; Planner COMMIT-UNKNOWN manual-only quarantine; immutable
  ToolRegistry/PermissionGate occurrence-bound authorization; trusted-clock
  audit-before-action; and disconnected/mock integration only after actual
  exact-head GREEN and reviewed dependency contracts.
