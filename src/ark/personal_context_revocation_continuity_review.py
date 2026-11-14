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
_DOMAIN = b"ARK-context-revocation-continuity-v1\0"


def _hash(rows: tuple[tuple[str, int], ...]) -> str:
    encoded = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode()
    return "rvk_" + hashlib.sha256(
        _DOMAIN + encoded
    ).hexdigest()


# Local retained witnesses depend on these exact hash/JSON primitives.
# A substituted digest callback could certify a false privacy-veto prefix.
# Check the implementation before reading retained fields or private SQLite.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_HASH = _hash
# Schema validation runs against a private SQLite connection: a substituted
# validator must never receive it, even when its eventual result looks valid.
_ORIGINAL_VALIDATE = _validate
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_DIGEST_PATTERN = _DIGEST
_ORIGINAL_MAX = _MAX


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


# Reject a preinstalled or reentrant replacement of the validator itself.
# Merely calling a mutable method cannot establish even local witness shape.
_WITNESS_TYPE = SyntheticRevocationWitness
_ORIGINAL_WITNESS_VALIDATOR = vars(_WITNESS_TYPE)["assert_integrity"]
_WITNESS_FIELDS = ("rows", "witness_id")
_WITNESS_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_WITNESS_FIELDS = tuple(vars(_WITNESS_TYPE)[key] for key in _WITNESS_FIELDS)
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(key) for key in _WITNESS_HOOKS
)


def _require_original_witness_carrier() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _hash is not _ORIGINAL_HASH
        or _validate is not _ORIGINAL_VALIDATE
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _SHA is not _ORIGINAL_SHA_PATTERN
        or _DIGEST is not _ORIGINAL_DIGEST_PATTERN
        or type(_MAX) is not int or _MAX != _ORIGINAL_MAX
    ):
        raise SyntheticContextRevocationRejected(
            "revocation digest implementation changed"
        )
    # A forged slotted field/constructor is executable even if the retained
    # witness's digest and validator still look correct. Read class dicts,
    # never those potentially hostile instance attributes, at ingress.
    if (
        SyntheticRevocationWitness is not _WITNESS_TYPE
        or vars(_WITNESS_TYPE).get("assert_integrity") is not _ORIGINAL_WITNESS_VALIDATOR
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for names, originals in (
                (_WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS),
                (_WITNESS_HOOKS, _ORIGINAL_WITNESS_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticContextRevocationRejected(
            "revocation integrity validator changed"
        )


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
    _require_original_witness_carrier()
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
        _require_original_witness_carrier()
        ledger._assert_source_path(source_path)
        if retained is not None and (
            retained.rows is not retained_rows
            or retained.witness_id is not pinned[1]
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
            digest = _hash(rows)
            assert_epoch()
            witness = SyntheticRevocationWitness(rows, digest)
            assert_epoch()
            # The freshly constructed witness is also a reflected-mutable
            # carrier. An integrity or COMMIT callback must not retarget the
            # result after its digest was checked and before it is returned.
            witness_rows = witness.rows
            witness_id = witness.witness_id
            witness_row_carriers = tuple(witness_rows)

            def assert_witness_epoch() -> None:
                if (
                    type(witness) is not SyntheticRevocationWitness
                    or witness.rows is not witness_rows
                    or witness.witness_id is not witness_id
                    or type(witness.rows) is not tuple
                    or len(witness.rows) != len(witness_row_carriers)
                    or any(
                        now is not before
                        for now, before in zip(
                            witness.rows, witness_row_carriers, strict=True,
                        )
                    )
                ):
                    raise SyntheticContextRevocationRejected(
                        "revocation result witness changed during review"
                    )

            assert_epoch()
            assert_witness_epoch()
            witness.assert_integrity()
            assert_epoch()
            assert_witness_epoch()
            if retained is not None:
                retained.assert_integrity()
                assert_epoch()
                current = dict(witness.rows)
                if any(current.get(digest) != at for digest, at in retained.rows):
                    raise SyntheticContextRevocationRejected(
                        "retained revocation history changed"
                    )
            assert_epoch()
            assert_witness_epoch()
            conn.commit()
            assert_epoch()
            assert_witness_epoch()
            return witness
        except BaseException:
            conn.rollback()
            raise
