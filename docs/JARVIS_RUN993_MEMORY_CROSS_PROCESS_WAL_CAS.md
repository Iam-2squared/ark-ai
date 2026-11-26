# Run993 — Memory cross-process pinned-WAL CAS

**Work basis:** Draft PR #8 exact checkpoint HEAD `326001af654078227641546a8f30c6954fcea4a3`.

**Isolated branch:** `research/memory-cross-process-wal-reader-run993`, proposed as a Draft child of `research/jarvis-foundations`. No Memory schema or frozen contract is changed.

## Scenario

A spawned read-only process pins a SQLite WAL snapshot containing one synthetic Memory row and its create event. Two other spawned processes start together and attempt a generation-fenced update using the same retained pre-write token.

The regression requires:

- The WAL reader does not prevent the independent writer processes from completing.
- Exactly one writer commits revision 2; the competing writer receives a CAS conflict.
- The pinned reader continues to see the original revision and event prefix until it rolls back.
- A fresh read after rollback sees the single committed update and matching event.
- Reusing the retained pre-write token after restart is denied.
- SQLite quick_check remains `ok`.

## Safety and limits

All paths, owners, namespaces and content are synthetic temporary fixtures. The test dispatches no tool and performs no external effect. The generation token is a local CAS witness, not consent, trusted time, writer attribution or external-action authorization. This is a cross-process storage regression, not proof of independent custody or protection against offline database rollback.

**Exact-head CI:** pending; no PASS claim is made in this report.
