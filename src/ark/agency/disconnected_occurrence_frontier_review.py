"""Read-only coherent frontier for the disconnected occurrence fixture.

The digest summarizes all *currently retained* valid synthetic reservations in
one SQLite read transaction. It is not an append-proof, signed checkpoint,
human approval, external outcome, or permission to dispatch/retry a WRITE.
The input database can be replaced by its owner; retain a frontier elsewhere.
No token digests, tool identities or private request IDs leave this API.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
    _require_safe_occurrence_path,
    _validate,
)

_DOMAIN = b"ARK-disconnected-occurrence-frontier-v1\0"
_MAX_ROWS = 10_000
_MAX_CLOCK = 2**63 - 1
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SQLITE3 = sqlite3
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_STORE_CLASS = SyntheticOccurrenceStore
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_VALIDATE = _validate
_ORIGINAL_PATH_CHECK = _require_safe_occurrence_path


@dataclass(frozen=True, slots=True)
class SyntheticOccurrenceFrontier:
    row_count: int
    commitment_sha256: str
    latest_reserved_at_ms: int

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def human_approval_authenticated(self) -> bool:
        return False

    @property
    def external_outcome_proven(self) -> bool:
        return False


_FRONTIER = SyntheticOccurrenceFrontier
_FIELDS = ("row_count", "commitment_sha256", "latest_reserved_at_ms")
_DENIALS = (
    "dispatch_authorized", "automatic_replay_authorized",
    "human_approval_authenticated", "external_outcome_proven",
)
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_DESCRIPTORS = tuple(
    vars(_FRONTIER).get(name) for name in _FIELDS + _DENIALS + _HOOKS
)


def _protocol() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or sqlite3 is not _ORIGINAL_SQLITE3
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _SHA is not _ORIGINAL_SHA_PATTERN
        or SyntheticOccurrenceStore is not _ORIGINAL_STORE_CLASS
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _validate is not _ORIGINAL_VALIDATE
        or _require_safe_occurrence_path is not _ORIGINAL_PATH_CHECK
        or SyntheticOccurrenceFrontier is not _FRONTIER
        or type(_MAX_ROWS) is not int or _MAX_ROWS != 10_000
        or type(_MAX_CLOCK) is not int or _MAX_CLOCK != 2**63 - 1
        or any(
            vars(_FRONTIER).get(name) is not original
            for name, original in zip(
                _FIELDS + _DENIALS + _HOOKS, _ORIGINAL_DESCRIPTORS, strict=True,
            )
        )
    ):
        raise SyntheticReplayRejected("occurrence frontier review contract changed")


def _image(witness: SyntheticOccurrenceFrontier) -> tuple[int, str, int]:
    _protocol()
    if type(witness) is not _FRONTIER:
        raise SyntheticReplayRejected("invalid retained occurrence frontier type")
    image = (
        witness.row_count, witness.commitment_sha256, witness.latest_reserved_at_ms,
    )
    if (
        type(image[0]) is not int or not 0 <= image[0] <= _MAX_ROWS
        or type(image[1]) is not str or _SHA.fullmatch(image[1]) is None
        or type(image[2]) is not int or not -1 <= image[2] <= _MAX_CLOCK
        or (image[0] == 0) != (image[2] == -1)
    ):
        raise SyntheticReplayRejected("invalid retained occurrence frontier")
    return image


def review_synthetic_occurrence_frontier(
    store: SyntheticOccurrenceStore,
    *,
    retained: SyntheticOccurrenceFrontier | None = None,
) -> SyntheticOccurrenceFrontier:
    """Reconcile a complete bounded row-set, with no implicit retry authority.

    Unlike comparing only row counts, a valid-looking in-place SQLite rewrite
    or equal-count substitution changes the digest. Ordering by token digest
    makes a stable *set* commitment, not a prefix or append-order witness.
    """
    _protocol()
    if type(store) is not SyntheticOccurrenceStore:
        raise SyntheticReplayRejected("exact synthetic occurrence store required")
    expected = _image(retained) if retained is not None else None
    source = store._path
    if type(source) is not type(Path()) or ".." in source.parts:
        raise SyntheticReplayRejected("synthetic occurrence source invalid")

    def assert_epoch() -> None:
        _protocol()
        if store._path is not source:
            raise SyntheticReplayRejected("synthetic occurrence source changed")
        if retained is not None and _image(retained) != expected:
            raise SyntheticReplayRejected("retained occurrence frontier changed")

    assert_epoch()
    _require_safe_occurrence_path(source, create=False)
    assert_epoch()
    uri = source.resolve().as_uri() + "?mode=ro"
    assert_epoch()
    try:
        with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
            assert_epoch()
            conn.execute("BEGIN")
            try:
                _validate(conn)
                assert_epoch()
                cursor = conn.execute(
                    "SELECT token_digest,occurrence_id,registry_revision,"
                    "bound_action_id,request_id,reserved_at_ms,expires_at_ms "
                    "FROM synthetic_occurrence_reservations "
                    "ORDER BY token_digest LIMIT ?",
                    (_MAX_ROWS + 1,),
                )
                rows = cursor.fetchall()
                assert_epoch()
                if len(rows) > _MAX_ROWS:
                    raise SyntheticReplayRejected("synthetic frontier exceeds row budget")
                latest = max((row[5] for row in rows), default=-1)
                raw = json.dumps(
                    rows, ensure_ascii=True, separators=(",", ":"),
                    allow_nan=False,
                ).encode("ascii")
                digest = hashlib.sha256(
                    _DOMAIN + len(rows).to_bytes(4, "big") + raw,
                ).hexdigest()
                assert_epoch()
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
    except sqlite3.DatabaseError as exc:
        raise SyntheticReplayRejected(
            "synthetic occurrence frontier storage cannot be reviewed"
        ) from exc

    result = _FRONTIER(len(rows), digest, latest)
    assert_epoch()
    if (
        type(result) is not _FRONTIER
        or _image(result) != (len(rows), digest, latest)
        or any(getattr(result, name) is not False for name in _DENIALS)
    ):
        raise SyntheticReplayRejected("synthetic frontier result gained authority")
    assert_epoch()
    if expected is not None and _image(result) != expected:
        raise SyntheticReplayRejected(
            "retained occurrence frontier differs from current SQLite snapshot"
        )
    return result
