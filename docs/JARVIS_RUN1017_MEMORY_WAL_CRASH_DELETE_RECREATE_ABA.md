# ARK AI Run1017 — Memory WAL crash and delete/recreate ABA

**Work basis:** Draft PR #8 exact head `183324473da6250ab9be853e6c068be19c62d85c`, branch `research/jarvis-foundations`. This is an isolated test-only non-UI child of PR #8.

## Coverage added

The new spawned-process regression composes three already separate local invariants:

1. A WAL reader pins the original row/event snapshot while the writer deletes and recreates the same deterministic Memory ID at revision 1.
2. The child reader exits without closing its SQLite transaction while a second independent reader remains alive; a TRUNCATE checkpoint must remain busy/incomplete until the final reader closes.
3. After last-close checkpoint and cold reopen, the original generation token must still be rejected despite the reused memory ID and revision, while a freshly observed token can update the new lifetime.

The test is parameterized for read-only and read-write child readers. It checks the retained global event sequence, final SQLite quick_check, stale-token denial without row/event mutation, and successful use of a fresh generation token.

## Evidence and limits

This test is authored, not a local pytest PASS. It requires exact-head Windows/Linux × Python 3.11–3.13 CI. It uses only synthetic identifiers and disposable temporary SQLite files.

This does not prove power-loss/fsync durability, authenticated writer provenance, trusted time, independent custody, physical erasure, cross-store atomicity, consent, or external-action authorization. No live personal data, real backend, paid service, external compute, credentials, Candidate, protected V2 evaluation, frozen-contract change, UI, PR #5, PR #9, or main merge is included. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
