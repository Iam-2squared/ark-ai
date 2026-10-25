"""Offline retained-witness comparison for synthetic occurrence reservations.

An independently retained earlier witness detects deletion/rewrite of rows in
a later local fixture snapshot. This is not an authenticated ledger, credential
store, user consent, or real dispatch authorization.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .durable_occurrence_review import SyntheticReplayRejected, _validate

_HEX = re.compile(r"[0-9a-f]{64}\\Z")
_MAX_WITNESS_ROWS = 10_000
_COLUMNS = """SELECT token_digest, occurrence_id, registry_revision,
                     bound_action_id, request_id, reserved_at_ms, expires_at_ms
              FROM synthetic_occurrence_reservations"""


def _digest(label: str, data: object) -> str:
    encoded = json.dumps(
        data, ensure_ascii=True, separators=(",", ":"), sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(label.encode("utf-8") + b"\\0" + encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class SyntheticLedgerWitness:
    """Content-minimized review witness requiring independent retention."""

    row_hashes: tuple[str, ...]
    digest: str

    def assert_integrity(self) -> None:
        if (
            type(self.row_hashes) is not tuple
            or len(self.row_hashes) > _MAX_WITNESS_ROWS
            or any(type(item) is not str or not _HEX.fullmatch(item) for item in self.row_hashes)
            or self.row_hashes != tuple(sorted(set(self.row_hashes)))
            or type(self.digest) is not str
            or self.digest != "synthetic_ledger_" + _digest("ARK-ledger-v1", self.row_hashes)
        ):
            raise SyntheticReplayRejected("synthetic retained witness integrity failed")


def assert_synthetic_history_continues(
    retained: SyntheticLedgerWitness, current: SyntheticLedgerWitness,
) -> None:
    """Require every retained row to remain intact in a later snapshot.

    Additional reservations are allowed. An earlier witness must have been
    retained outside the mutable DB; two locally recomputed witnesses are NOT
    an independent audit trail, and both can be forged by a storage adversary.
    """
    if type(retained) is not SyntheticLedgerWitness or type(current) is not SyntheticLedgerWitness:
        raise SyntheticReplayRejected("synthetic continuity requires exact witnesses")
    # Integrity checks hash Python-held tuples: a reflected mutation of the
    # *other* witness during one check must not become the comparison baseline.
    previous_rows, current_rows = retained.row_hashes, current.row_hashes
    previous_epoch = (previous_rows, retained.digest)
    current_epoch = (current_rows, current.digest)

    def assert_epoch() -> None:
        if (
            retained.row_hashes is not previous_rows
            or current.row_hashes is not current_rows
            or (retained.row_hashes, retained.digest) != previous_epoch
            or (current.row_hashes, current.digest) != current_epoch
        ):
            raise SyntheticReplayRejected(
                "synthetic continuity witness changed during comparison"
            )

    assert_epoch()
    retained.assert_integrity()
    assert_epoch()
    current.assert_integrity()
    assert_epoch()
    if not set(retained.row_hashes).issubset(current.row_hashes):
        raise SyntheticReplayRejected("synthetic retained reservation history changed")
    assert_epoch()


def read_synthetic_ledger_witness(
    path: Path, *, retained: SyntheticLedgerWitness | None = None,
) -> SyntheticLedgerWitness:
    """Observe one read-only SQLite snapshot with optional retained history.

    Retention is checked in the *same* transaction as the new witness read.
    This never creates a missing database or retains plaintext token IDs.
    A local digest cannot establish external authenticity, inode custody,
    real user permission, backend results or atomic multi-store consistency.
    """
    if not isinstance(path, Path):
        raise TypeError("synthetic witness path must be a pathlib.Path")
    if retained is not None and type(retained) is not SyntheticLedgerWitness:
        raise SyntheticReplayRejected("exact synthetic retained witness required")
    retained_rows = None if retained is None else retained.row_hashes
    retained_epoch = None if retained is None else (retained_rows, retained.digest)

    def assert_epoch() -> None:
        if retained is not None and (
            retained.row_hashes is not retained_rows
            or (retained.row_hashes, retained.digest) != retained_epoch
        ):
            raise SyntheticReplayRejected(
                "synthetic retained witness changed during ledger read"
            )

    assert_epoch()
    if retained is not None:
        retained.assert_integrity()
        assert_epoch()
    resolved = path.resolve()
    assert_epoch()
    uri = resolved.as_uri() + "?mode=ro"
    assert_epoch()
    with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
        assert_epoch()
        conn.execute("BEGIN")
        try:
            _validate(conn)
            assert_epoch()
            hashes = []
            for row in conn.execute(_COLUMNS):
                assert_epoch()
                if len(hashes) >= _MAX_WITNESS_ROWS:
                    raise SyntheticReplayRejected("synthetic ledger witness scan budget exceeded")
                hashes.append(_digest("ARK-reservation-row-v1", row))
                assert_epoch()
            row_hashes = tuple(sorted(hashes))
            assert_epoch()
            witness = SyntheticLedgerWitness(
                row_hashes, "synthetic_ledger_" + _digest("ARK-ledger-v1", row_hashes),
            )
            assert_epoch()
            witness.assert_integrity()
            assert_epoch()
            if retained is not None:
                assert_synthetic_history_continues(retained, witness)
                assert_epoch()
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
    assert_epoch()
    return witness
