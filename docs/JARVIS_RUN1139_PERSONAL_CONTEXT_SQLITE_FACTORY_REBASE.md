# Run1139 — Personal Context replay SQLite factory rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Parent basis HEAD: `1d80a2ac00d6f00669f1d3f2940556e77ac31cad`.
- Prior source child: Draft PR #325, exact HEAD `15faa5c235dc61b193f0812233b938232a7d98d6`.
- Prior source-child CI: [45088953623](https://github.com/Iam-2squared/ark-ai/actions/runs/45088953623), FAIL (two legacy tests).
- Rebased child branch: `research/run1139-personal-context-sqlite-factory-rebase`.

## Finding

The disconnected Personal Context replay ledger validated its hash/JSON/DDL protocol and path preflight, but it called the live `sqlite3.connect` module attribute directly. The protocol guard did not pin the SQLite module, connection factory, connection type or `IntegrityError` class. A substituted factory could therefore return a non-native connection or redirect the supposedly durable reservation path before the ledger's transaction and hash-chain checks ran.

## Change

- Capture the import-original SQLite module, `connect` callable, `Connection` type and `IntegrityError` class.
- Pin the live module attributes and captured identities in the replay protocol guard.
- Route schema probing, startup validation and read/write opens through one guarded connection helper.
- Recheck the protocol after connection creation and require an exact native SQLite connection.
- Use the captured `IntegrityError` class for duplicate-identity handling and pin the helper identity itself.
- Add synthetic regressions for module replacement, live/captured factory substitution, connection/error type replacement, helper replacement and normal exact connection creation.
- Repair two existing read-only restart tests that instrumented `sqlite3.connect`. Those tests now exercise the production read-only open directly and prove that a reserved writer can coexist with a read-only restart, without replacing the factory whose identity is now intentionally pinned.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. The prior Run1137 CI failure was two compatibility-test failures on all matrix jobs; this rebased branch has not yet been validated. No local pytest/Ruff or child CI PASS is claimed. Tests use disposable local SQLite files only.

This does not establish power-loss/fsync durability, independent storage custody, trusted time, consent, revocation freshness, disclosure authority or exactly-once external effects. The ledger remains synthetic and non-dispatching. No Personal Context contract, schema/DDL, request identity, retention or revocation semantics are changed. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, frozen-contract change, UI/frontend work or main merge is included. PR #5 remains Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
