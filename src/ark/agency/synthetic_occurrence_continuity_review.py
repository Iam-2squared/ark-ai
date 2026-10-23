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

_HEX = re.compile(r"[0-9a-f]{64}\Z")
_COLUMNS = """SELECT token_digest, occurrence_id, registry_revision,
                     bound_action_id, request_id, reserved_at_ms, expires_at_ms
              FROM synthetic_occurrence_reservations"""


def _digest(label: str, data: object) -> str:
    encoded = json.dumps(
        data, ensure_ascii=True, separators=(",", ":"), sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(label.encode("utf-8") + b"\0" + encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class SyntheticLedgerWitness:
    """Content-minimized review witness requiring independent retention."""

    row_hashes: tuple[str, ...]
    digest: str

    def assert_integrity(self) -> None:
        if (
            type(self.row_hashes) is not tuple
            or any(type(item) is not str or not _HEX.fullmatch(item) for item in self.row_hashes)
            or self.row_hashes != tuple(sorted(set(self.row_hashes)))
            or type(self.digest) is not str
            or self.digest != "synthetic_ledger_" + _digest("ARK-ledger-v1", self.row_hashes)
        ):
            raise SyntheticReplayRejected("synthetic retained witness integrity failed")


def read_synthetic_ledger_witness(path: Path) -> SyntheticLedgerWitness:
    """Observe one committed, read-only fixture snapshot without dispatch.

    This never creates a missing database or retains plaintext token IDs.
    The resulting digest is local and cannot establish external authenticity.
    """
    if type(path) is not Path:
        raise TypeError("synthetic witness path must be an exact pathlib.Path")
    uri = path.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
        conn.execute("BEGIN")
        try:
            _validate(conn)
            row_hashes = tuple(sorted(
                _digest("ARK-reservation-row-v1", row)
                for row in conn.execute(_COLUMNS)
            ))
            witness = SyntheticLedgerWitness(
                row_hashes, "synthetic_ledger_" + _digest("ARK-ledger-v1", row_hashes),
            )
            witness.assert_integrity()
            conn.commit()
            return witness
        except BaseException:
            conn.rollback()
            raise


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
    retained.assert_integrity()
    current.assert_integrity()
    if not set(retained.row_hashes).issubset(current.row_hashes):
        raise SyntheticReplayRejected("synthetic retained reservation history changed")
