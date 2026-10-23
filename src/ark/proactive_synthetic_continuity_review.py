"""Read-only historical witness for synthetic proactive trigger preparations.

An independently retained older witness can detect row deletion or rewriting
in a later SQLite snapshot. A locally regenerated witness is not an external
attestation, real user consent, notification authorization or execution grant.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from .proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerRejected,
    _validate,
)

_HEX = re.compile(r"[0-9a-f]{64}\Z")
_ROWS = """SELECT trigger_id,scope_digest,policy_digest,source_digest,
                  observation_digest,observed_at_ms,prepared_at_ms
           FROM synthetic_prepared_triggers"""


def _digest(label: str, data: object) -> str:
    encoded = json.dumps(
        data, ensure_ascii=True, separators=(",", ":"), sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(label.encode("utf-8") + b"\0" + encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class SyntheticTriggerWitness:
    row_hashes: tuple[str, ...]
    digest: str

    def assert_integrity(self) -> None:
        if (
            type(self.row_hashes) is not tuple
            or len(self.row_hashes) > 10_000
            or any(
                type(item) is not str or not _HEX.fullmatch(item)
                for item in self.row_hashes
            )
            or self.row_hashes != tuple(sorted(set(self.row_hashes)))
            or type(self.digest) is not str
            or self.digest != "synthetic_triggers_" + _digest(
                "ARK-trigger-witness-v1", self.row_hashes,
            )
        ):
            raise SyntheticTriggerRejected("synthetic trigger witness integrity failed")


def assert_proactive_history_continues(
    retained: SyntheticTriggerWitness,
    current: SyntheticTriggerWitness,
) -> None:
    """Require retained rows to remain in a newer witness; new rows are allowed."""
    if (
        type(retained) is not SyntheticTriggerWitness
        or type(current) is not SyntheticTriggerWitness
    ):
        raise SyntheticTriggerRejected("exact proactive witnesses required")
    retained.assert_integrity()
    current.assert_integrity()
    if not set(retained.row_hashes).issubset(current.row_hashes):
        raise SyntheticTriggerRejected("retained proactive trigger history changed")


def read_proactive_witness(
    ledger: SyntheticProactiveLedger, *, retained: SyntheticTriggerWitness | None = None,
) -> SyntheticTriggerWitness:
    """Read one snapshot without creating or changing the existing database."""
    if type(ledger) is not SyntheticProactiveLedger:
        raise SyntheticTriggerRejected("exact synthetic proactive ledger required")
    if retained is not None:
        if type(retained) is not SyntheticTriggerWitness:
            raise SyntheticTriggerRejected("exact retained trigger witness required")
        retained.assert_integrity()
    uri = ledger.path.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
        conn.execute("BEGIN")
        try:
            _validate(conn)
            hashes = tuple(sorted(
                _digest("ARK-trigger-row-v1", row)
                for row in conn.execute(_ROWS)
            ))
            witness = SyntheticTriggerWitness(
                hashes, "synthetic_triggers_" + _digest(
                    "ARK-trigger-witness-v1", hashes,
                ),
            )
            witness.assert_integrity()
            if retained is not None:
                assert_proactive_history_continues(retained, witness)
            conn.commit()
            return witness
        except BaseException:
            conn.rollback()
            raise
