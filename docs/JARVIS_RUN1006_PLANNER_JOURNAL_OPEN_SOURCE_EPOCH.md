# Run1006 — Planner journal source epoch and no-recreate open

**Work basis:** Draft PR #36 exact head `e8f89704b3de5d55daaf58463a11aee140ca9cca`; exact-head CI #44622369804 was observed GREEN 6/6. This isolated child does not modify PR #36 or PR #18/#19 ancestors.

## Gap

Planner journal path admission already performed a post-open `lstat()` check and closed the connection on rejection. The connector nevertheless derived a local `Path` from `self._path` and later passed `self._path` again to SQLite. A reentrant callback could change that source string between the preflight and SQLite open; the post-open check would still inspect the earlier local Path while the connection could target a different path. In addition, a non-create open used plain `sqlite3.connect(path)`, which can create a replacement file if the main database disappears after preflight.

## Change

- Pin the exact source string and derived Path object before preflight.
- Open non-create connections with SQLite URI `mode=rw`, preventing silent recreation after a raced deletion while preserving literal special path characters through `Path.as_uri()`.
- Recheck the same Path object after open and reject a changed `self._path` before any PRAGMA.
- Close the just-opened handle when source identity or path admission fails.
- Preserve Planner journal schema v1, append/CAS semantics, topology binding, terminal propagation and RUNNING-step quarantine.

## Regression coverage

Two synthetic tests cover source rebinding during SQLite open (including closed-handle verification) and deletion after preflight. The latter requires SQLite `mode=rw` to fail without recreating the missing database.

## Limits and safety

These are local pathname/source-epoch checks, not atomic dirfd custody, authenticated storage or protection against hostile filesystem-owner TOCTOU. No recovered RUNNING step is replayed. No ToolBackend dispatch, trusted clock, consent, paid service, external compute, credentials, Candidate, protected V2 evaluation, frozen-contract change, UI work or main merge is involved.

**Exact-head CI is pending for this child. No PASS is claimed. Overall ARK/JARVIS remains NOT_PASSED.**
