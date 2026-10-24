"""Independent retained-prefix diagnosis for synthetic Context revocations.

A local hash witness is only useful when retained outside the mutable SQLite
ledger. It is not authenticated consent, trusted storage, or an erasure proof.
This reader never repairs, removes or implicitly creates a revocation store.
"""

from __future__ import annotations

import hashlib
import json
import re
from contextlib import closing
from dataclasses import dataclass

from .personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    _validate,
)

_SHA = re.compile(r"rvk_[0-9a-f]{64}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_MAX = 2**63 - 1


def _hash(rows: tuple[tuple[str, int], ...]) -> str:
    encoded = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode()
    return "rvk_" + hashlib.sha256(
        b"ARK-context-revocation-continuity-v1\0" + encoded
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class SyntheticRevocationWitness:
    rows: tuple[tuple[str, int], ...]
    witness_id: str

    def assert_integrity(self) -> None:
        if (
            type(self.rows) is not tuple or len(self.rows) > 10_000
            or type(self.witness_id) is not str
            or not _SHA.fullmatch(self.witness_id)
        ):
            raise SyntheticContextRevocationRejected("retained revocation shape invalid")
        last = ""
        for row in self.rows:
            if type(row) is not tuple or len(row) != 2:
                raise SyntheticContextRevocationRejected("retained revocation row malformed")
            digest, time_ms = row
            if (
                type(digest) is not str or not _DIGEST.fullmatch(digest)
                or digest <= last or type(time_ms) is not int
                or not 0 <= time_ms <= _MAX
            ):
                raise SyntheticContextRevocationRejected(
                    "retained revocation order/identity invalid"
                )
            last = digest
        if _hash(self.rows) != self.witness_id:
            raise SyntheticContextRevocationRejected("retained revocation digest mismatch")


def review_revocation_continuity(
    ledger: SyntheticContextRevocationLedger,
    *, retained: SyntheticRevocationWitness | None = None,
) -> SyntheticRevocationWitness:
    """Compare all previously witnessed veto markers in one SQLite snapshot.

    New markers are allowed. Removing or rewriting any independently retained
    marker fails closed. Unwitnessed deletions cannot be detected by hashes.
    """
    if type(ledger) is not SyntheticContextRevocationLedger:
        raise SyntheticContextRevocationRejected("exact revocation ledger required")
    if retained is not None and type(retained) is not SyntheticRevocationWitness:
        raise SyntheticContextRevocationRejected("exact retained witness required")
    source_path = ledger.path
    # Capture the caller's exact retained evidence BEFORE its first integrity
    # callback. A frozen dataclass can be reflectively mutated from inside
    # assert_integrity(), including replacement with value-equal tuple clones.
    pinned = None
    retained_rows = None
    retained_row_carriers = ()
    if retained is not None:
        retained_rows = retained.rows
        if type(retained_rows) is not tuple or len(retained_rows) > 10_000:
            raise SyntheticContextRevocationRejected("retained revocation shape invalid")
        retained_row_carriers = tuple(retained_rows)
        pinned = (retained_rows, retained.witness_id)

    def assert_epoch() -> None:
        ledger._assert_source_path(source_path)
        if retained is not None and (
            retained.rows is not retained_rows
            or (retained.rows, retained.witness_id) != pinned
            or any(
                row is not original for row, original in zip(
                    retained.rows, retained_row_carriers, strict=True,
                )
            )
        ):
            raise SyntheticContextRevocationRejected(
                "retained revocation evidence changed during review"
            )

    # Check source and retained inputs together before invoking either
    # validator; source validation itself can be a reentrant test callback.
    assert_epoch()
    if retained is not None:
        retained.assert_integrity()
        assert_epoch()

    with closing(ledger._connect(readonly=True)) as conn:
        conn.execute("BEGIN")
        try:
            assert_epoch()
            _validate(conn)
            assert_epoch()
            rows = tuple(
                (digest, time_ms) for digest, time_ms in conn.execute(
                    """SELECT scope_digest,revoked_at_ms
                       FROM synthetic_context_revocations ORDER BY scope_digest"""
                )
            )
            assert_epoch()
            witness = SyntheticRevocationWitness(rows, _hash(rows))
            assert_epoch()
            witness.assert_integrity()
            assert_epoch()
            if retained is not None:
                retained.assert_integrity()
                assert_epoch()
                current = dict(witness.rows)
                if any(current.get(digest) != at for digest, at in retained.rows):
                    raise SyntheticContextRevocationRejected(
                        "retained revocation history changed"
                    )
            assert_epoch()
            conn.commit()
            assert_epoch()
            return witness
        except BaseException:
            conn.rollback()
            raise
