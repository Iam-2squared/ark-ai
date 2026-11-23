# Run1162 — Memory cross-process pinned-WAL CAS rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at child creation: `aa466abdf3de9abc9d1560e614952596c7cc8b19`.
- Rebased the test-only cross-process WAL/CAS regression from Draft PR #343 exact child HEAD `7a42e5b62543b5d32a3499360694ae90b2ecb0d4`.
- Source exact-head CI [45120556993](https://github.com/Iam-2squared/ark-ai/actions/runs/45120556993) was GREEN on the source head only; it does not transfer to this rebase.
- New branch: `research/run1162-memory-wal-cas-rebase`.

## Scenario and assertions

A spawned read-only process pins a SQLite WAL snapshot containing one synthetic Memory row and its create event. Two independent spawned writers start together and attempt a generation-fenced update with the same retained pre-write token.

The regression requires exactly one revision-2 winner and one CAS conflict; the pinned reader must continue to see the original row/event prefix until rollback; a fresh read must see the single matching update; the retained token must remain rejected; and SQLite quick_check must remain `ok`.

## Safety and limits

All paths, owners, namespaces and content are synthetic temporary fixtures. No tool is dispatched and no external effect occurs. The generation token is a local CAS witness, not consent, trusted time, writer attribution or external-action authorization. This is a cross-process storage regression, not proof of independent custody or protection against offline database rollback.

Test-only. No Memory production source, v1 DDL/public API, or frozen contract changes. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive operation, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
