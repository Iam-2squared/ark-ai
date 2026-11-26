# Run1050 — Personal Context replay process-crash and proactive race fixture rebase

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact parent HEAD `aa6e47284fbba6f45845274531defdeb5a974252` (Run1047 ToolRegistry custody integration). This child is test-only and based on that exact parent.

## Personal Context COMMIT process-crash regression

A spawned child exits immediately after native SQLite COMMIT and before `reserve()` can construct or return its local receipt. Cold recovery verifies one hash-only reservation, stale/duplicate denial, SQLite integrity and absence of synthetic private fixture text from durable bytes.

This is a synthetic local fixture, not independent custody, consent, revocation freshness, disclosure permission, trusted time, authenticated provenance or exactly-once external action evidence.

## Proactive two-process fixture stabilization

The prior PR #145 exact head failed CI #44855740615 on Ubuntu Python 3.11 because a concurrent DELETE-journal sidecar unlink was observed by the proactive path-custody preflight. The guard correctly failed closed.

This rebase keeps a parent SQLite anchor connection in WAL mode while child preparations race, so legitimate WAL/SHM sidecars remain linked and stable. Production path checks, alias rejection and the actual two-process preparation race are unchanged. No uncertain-COMMIT retry or production-source relaxation is introduced.

## Evidence and limits

Previous PR #149 exact head `e284e8209f9b1765e10b292def33b79475d351c6` passed CI #44858550158 (6/6) on older parent `a6529d15c78cb9341e2ff97bc886f1b771ad05bd`. That evidence does not transfer to this new parent `aa6e47284fbba6f45845274531defdeb5a974252`; fresh exact-head CI is required. No local pytest/Ruff PASS is claimed.

Synthetic fixtures, spawned local processes and disposable SQLite only. No live personal data, disclosure, ToolBackend, external effect, trusted clock, independent custody, frozen contract, paid service, external compute, Candidate, protected V2 evaluation, UI work or main merge is involved. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
