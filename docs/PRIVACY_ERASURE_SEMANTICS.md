# ARK Privacy Erasure Semantics

Work basis: `7a3171527a7e422a8e53af79936dd9893711c59f`

This document distinguishes logical data deletion from storage-byte reclamation for ARK's local-first SQLite state. It is foundation guidance only. It changes no frozen V1/V2/Local UI/Launcher/V3 evidence or authorization boundary.

## Definitions

ARK must use precise language for deletion:

- **logical deletion** — a row is no longer addressable through normal application queries;
- **row deletion** — the SQLite row has been removed from the live table;
- **reclamation** — free pages/WAL frames containing obsolete bytes have been recycled, truncated, or overwritten;
- **forensic erasure** — ARK has evidence that obsolete plaintext bytes are not recoverable from the storage surfaces covered by the erasure procedure.

These are not interchangeable guarantees.

## SQLite WAL finding

Local prototype testing reproduced the following sequence with Python SQLite:

1. database in WAL mode;
2. plaintext sentinel inserted and committed;
3. a reader begins and keeps a snapshot open;
4. writer deletes the row and commits;
5. sentinel is absent from the live table but remains present in the WAL bytes;
6. `wal_checkpoint(TRUNCATE)` reports busy while the reader holds the old snapshot;
7. after the reader ends, TRUNCATE succeeds and the WAL reaches zero bytes.

This confirms that a successful application-level delete does not imply immediate byte reclamation from WAL storage.

## `secure_delete` finding

The same local experiment was repeated with `PRAGMA secure_delete=OFF` and `ON`.

With an active reader, both modes retained the obsolete sentinel in WAL frames until the reader released its snapshot.

After the reader ended and a truncating checkpoint completed:

- with `secure_delete=OFF`, the obsolete sentinel was still observable in the main database file in the tested build;
- with `secure_delete=ON`, the obsolete sentinel was not observable in the main database file in the tested build.

Five repeated local rounds per mode reproduced the same result. This is prototype evidence only; filesystem, journal, SQLite build, backup, swap, crash, and storage-device behavior can introduce additional surfaces.

Therefore ARK must not document `secure_delete=ON` alone as universal forensic-erasure proof.

## Application contract

Normal Memory deletion guarantees only the application-level contract that is explicitly implemented and tested.

At minimum, a normal delete should guarantee:

- exact owner/namespace match;
- exact expected revision;
- persisted-row integrity validation;
- atomic row removal;
- lifecycle event only for a row actually removed;
- immediate exclusion from normal retrieval.

It must not claim that every historical byte has already disappeared from WAL, free pages, backups, filesystem snapshots, swap, crash dumps, or storage-device remanence.

## Explicit erasure operation

If ARK later exposes a stronger local erasure operation, it must be separate from ordinary `delete()` and must return evidence rather than silently upgrading the guarantee.

A local SQLite erasure procedure may include, as applicable:

1. stop or drain readers holding old snapshots;
2. perform revision-guarded logical/row deletion;
3. use a documented `secure_delete` policy;
4. complete an appropriate checkpoint/reclamation step;
5. verify checkpoint completion rather than ignoring a busy result;
6. verify the covered database/WAL surfaces according to the declared threat model;
7. record any surfaces that cannot be proven erased.

The operation must fail closed or report incomplete erasure when a reader, lock, filesystem limitation, or other condition prevents the declared guarantee.

## Reader and snapshot rule

A long-lived reader can delay reclamation of deleted content.

Therefore higher-level Personal Context, UI, scheduler, and observability code must not keep unnecessary SQLite read transactions open. Read transactions should be scoped narrowly and closed promptly.

An erasure request must account for active readers rather than assuming a delete commit makes obsolete WAL frames immediately reclaimable.

## Retention language

Documentation and APIs should use terms such as:

- `deleted from active memory`;
- `row removed`;
- `reclamation pending`;
- `erasure incomplete`;
- `erasure verified for declared local SQLite surfaces`.

Avoid unqualified phrases such as "permanently erased" unless the implementation has explicit evidence for the threat model being claimed.

## Required tests before stronger erasure claims

Repository tests for any future explicit erasure API should cover at least:

- active-reader checkpoint blocking;
- successful reclamation after reader release;
- secure-delete policy verification;
- WAL truncation result checking;
- no stale revision deletion;
- no deletion across owner/namespace boundaries;
- recovery after interrupted erasure;
- clear incomplete-erasure result when reclamation cannot finish;
- no false claim that backups/snapshots/external copies were erased.

## Integration rule

This clarification does not authorize destructive cleanup outside the application's controlled local store. It does not authorize filesystem-wide shredding, backup deletion, external service deletion, paid compute, new credentials, Candidate generation, protected evaluation opening, promotion, frozen-contract changes, physical-PC actions unavailable through authorized tools, or main merge.
