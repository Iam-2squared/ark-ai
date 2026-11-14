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
from pathlib import Path

from .proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerRejected,
    _validate,
)

_HEX = re.compile(r"[0-9a-f]{64}\Z")
_MAX_WITNESS_ROWS = 10_000  # Bound row hashing even after schema/row validation.
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


# Keep the original integrity validator when a synthetic callback substitutes
# the public method. We still call the public method for reentrant fault
# coverage, but it may not silently skip the actual local digest validation.
_ORIGINAL_WITNESS_VALIDATOR = SyntheticTriggerWitness.assert_integrity
# _validate receives a live private SQLite handle. A swapped validator,
# including one installed reentrantly after the first source observation,
# must be denied before any private rows are passed into it.
_ORIGINAL_SCHEMA_VALIDATE = _validate
# Private trigger rows are serialized and SHA-256 hashed under an exact local
# codec. Accept a smaller test-only row budget, never a larger production one.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_ROWS = _ROWS
_ORIGINAL_MAX_WITNESS_ROWS = _MAX_WITNESS_ROWS
# A frozen witness can still acquire executable class descriptors and lookup
# hooks. Capture the ORIGINAL slots before untrusted caller code can replace
# them, and check them before reading retained private history or opening
# SQLite. The validator remains patchable for fault-injection tests, but its
# original implementation is still called independently.
_WITNESS_TYPE = SyntheticTriggerWitness
_WITNESS_FIELDS = ("row_hashes", "digest")
_WITNESS_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_WITNESS_FIELDS = tuple(
    vars(_WITNESS_TYPE)[name] for name in _WITNESS_FIELDS
)
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(name) for name in _WITNESS_HOOKS
)


def _require_original_witness_carrier() -> None:
    if (
        SyntheticTriggerWitness is not _WITNESS_TYPE
        or _validate is not _ORIGINAL_SCHEMA_VALIDATE
        or hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _ROWS is not _ORIGINAL_ROWS
        or type(_MAX_WITNESS_ROWS) is not int
        or not 0 <= _MAX_WITNESS_ROWS <= _ORIGINAL_MAX_WITNESS_ROWS
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for names, originals in (
                (_WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS),
                (_WITNESS_HOOKS, _ORIGINAL_WITNESS_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticTriggerRejected(
            "proactive witness carrier changed before private history access"
        )


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
    _require_original_witness_carrier()
    # A direct caller may have no enclosing ledger/witness custody fence.
    # Capture both exact carriers *before* either reentrant integrity method.
    retained_rows = retained.row_hashes
    current_rows = current.row_hashes
    retained_digest, current_digest = retained.digest, current.digest
    retained_carriers = tuple(retained_rows)
    current_carriers = tuple(current_rows)

    def assert_epoch() -> None:
        _require_original_witness_carrier()
        if (
            retained.row_hashes is not retained_rows
            or current.row_hashes is not current_rows
            or retained.digest is not retained_digest
            or current.digest is not current_digest
            or any(now is not first for now, first in zip(
                retained.row_hashes, retained_carriers, strict=True,
            ))
            or any(now is not first for now, first in zip(
                current.row_hashes, current_carriers, strict=True,
            ))
        ):
            raise SyntheticTriggerRejected(
                "proactive history witness changed during continuity check"
            )

    assert_epoch()
    retained.assert_integrity()
    assert_epoch()
    _ORIGINAL_WITNESS_VALIDATOR(retained)
    assert_epoch()
    current.assert_integrity()
    assert_epoch()
    _ORIGINAL_WITNESS_VALIDATOR(current)
    assert_epoch()
    if not set(retained.row_hashes).issubset(current.row_hashes):
        raise SyntheticTriggerRejected("retained proactive trigger history changed")
    assert_epoch()


def read_proactive_witness(
    ledger: SyntheticProactiveLedger, *, retained: SyntheticTriggerWitness | None = None,
) -> SyntheticTriggerWitness:
    """Read one snapshot without creating or changing the existing database."""
    if type(ledger) is not SyntheticProactiveLedger:
        raise SyntheticTriggerRejected("exact synthetic proactive ledger required")
    if retained is not None and type(retained) is not SyntheticTriggerWitness:
        raise SyntheticTriggerRejected("exact retained trigger witness required")
    _require_original_witness_carrier()
    # Bind both source identity and retained values before even the FIRST
    # reentrant retained.assert_integrity() callback, not only before SQLite.
    # any injectable validation/row-hydration callback. An equal-path object
    # replacement and a different valid retained witness are both drift.
    path_epoch = ledger.path
    if not isinstance(path_epoch, Path):
        raise SyntheticTriggerRejected("proactive witness requires a Path source")
    retained_rows_carrier = None if retained is None else retained.row_hashes
    retained_digest = None if retained is None else retained.digest
    retained_carriers = () if retained is None else tuple(retained_rows_carrier)

    def assert_epoch() -> None:
        _require_original_witness_carrier()
        if (
            ledger.path is not path_epoch
            or retained is not None
            and (
                retained.row_hashes is not retained_rows_carrier
                or retained.digest is not retained_digest
                or any(now is not first for now, first in zip(
                    retained.row_hashes, retained_carriers, strict=True,
                ))
            )
        ):
            raise SyntheticTriggerRejected(
                "proactive witness source or retained history changed during review"
            )

    assert_epoch()
    if retained is not None:
        retained.assert_integrity()
        assert_epoch()
        _ORIGINAL_WITNESS_VALIDATOR(retained)
        assert_epoch()

    # Path resolution, URI construction, SQLite handle creation and BEGIN
    # are distinct reentrant boundaries. The next callback must not be able
    # to restore a transiently retargeted source or retained witness.
    resolved = path_epoch.resolve()
    assert_epoch()
    uri = resolved.as_uri() + "?mode=ro"
    assert_epoch()
    with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
        assert_epoch()
        conn.execute("BEGIN")
        assert_epoch()
        try:
            _validate(conn)
            assert_epoch()
            # Per-row hashing is observable/reentrant Python. An earlier
            # ledger path or retained witness must not drift temporarily and
            # then be restored by a later row's digest callback.
            row_hashes = []
            for index, row in enumerate(conn.execute(_ROWS)):
                assert_epoch()
                if index >= _MAX_WITNESS_ROWS:
                    raise SyntheticTriggerRejected(
                        "proactive witness row scan budget exceeded"
                    )
                row_hashes.append(_digest("ARK-trigger-row-v1", row))
                assert_epoch()
            hashes = tuple(sorted(row_hashes))
            assert_epoch()
            witness = SyntheticTriggerWitness(
                hashes, "synthetic_triggers_" + _digest(
                    "ARK-trigger-witness-v1", hashes,
                ),
            )
            witness_rows = witness.row_hashes
            witness_digest = witness.digest
            witness_carriers = tuple(witness_rows)

            def assert_witness_epoch() -> None:
                _require_original_witness_carrier()
                if (
                    type(witness) is not SyntheticTriggerWitness
                    or witness.row_hashes is not witness_rows
                    or witness.digest is not witness_digest
                    or any(now is not first for now, first in zip(
                        witness.row_hashes, witness_carriers, strict=True,
                    ))
                ):
                    raise SyntheticTriggerRejected(
                        "proactive result witness changed during review"
                    )

            assert_epoch()
            assert_witness_epoch()
            witness.assert_integrity()
            assert_epoch()
            assert_witness_epoch()
            _ORIGINAL_WITNESS_VALIDATOR(witness)
            assert_epoch()
            assert_witness_epoch()
            if retained is not None:
                assert_proactive_history_continues(retained, witness)
                assert_epoch()
                assert_witness_epoch()
            conn.commit()
            assert_epoch()
            assert_witness_epoch()
        except BaseException:
            conn.rollback()
            raise
    assert_epoch()
    assert_witness_epoch()
    return witness
