# Run1137 — Personal Context replay ledger SQLite factory custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Parent basis HEAD: `776d6d791dc2fc76b3778ee2fa77b6e5f4727ba2`.
- Child branch: `research/run1137-personal-context-sqlite-factory-custody`.

## Finding

The disconnected Personal Context replay ledger validated its hash/JSON/DDL protocol and path preflight, but it called the live `sqlite3.connect` module attribute directly. The protocol guard did not pin the SQLite module, connection factory, connection type or `IntegrityError` class. A substituted factory could therefore return a non-native connection or redirect the supposedly durable reservation path before the ledger's transaction and hash-chain checks ran.

## Change

- Capture the import-original SQLite module, `connect` callable, `Connection` type and `IntegrityError` class.
- Pin the live module attributes and captured identities in the replay protocol guard.
- Route schema probing, startup validation and read/write opens through one guarded connection helper.
- Recheck the protocol after connection creation and require an exact native SQLite connection.
- Use the captured `IntegrityError` class for duplicate-identity handling and pin the helper identity itself.
- Add synthetic regressions for module replacement, live/captured factory substitution, connection/error type replacement, helper replacement and normal exact connection creation.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff or child CI PASS is claimed until that run completes. Tests use disposable local SQLite files only.

This does not establish power-loss/fsync durability, independent storage custody, trusted time, consent, revocation freshness, disclosure authority or exactly-once external effects. The ledger remains synthetic and non-dispatching. No Personal Context contract, schema/DDL, request identity, retention or revocation semantics are changed. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, frozen-contract change, UI/frontend work or main merge is included. PR #5 remains Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
