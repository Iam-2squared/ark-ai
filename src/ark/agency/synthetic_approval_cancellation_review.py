"""Local-only approval-claim cancellation journal with retained-prefix review.

This isolated fixture is not linked to any live PermissionGate or ToolBackend.
Caller identities, approval IDs, cancellation issuers and times are untrusted;
a missing cancellation marker is NOT consent or a dispatch authorization.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

_MAX = 2**63 - 1
_LIMIT = 10_000
_APPROVAL = re.compile(r"approval_[0-9a-f]{64}\Z")
_HASH = re.compile(r"cancel_[0-9a-f]{64}\Z")
_TABLE = """CREATE TABLE synthetic_claim_cancellations(
    seq INTEGER PRIMARY KEY CHECK(seq >= 1),
    approval_id TEXT NOT NULL UNIQUE,
    cancelled_at_ms INTEGER NOT NULL CHECK(cancelled_at_ms >= 0),
    previous_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL
)"""


class SyntheticCancellationRejected(RuntimeError):
    """A synthetic cancellation record/history cannot be trusted."""


def _hash(label: str, fields: object) -> str:
    payload = json.dumps(
        fields, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return "cancel_" + hashlib.sha256(label.encode("utf-8") + b"\0" + payload).hexdigest()


_GENESIS = _hash("ARK-synthetic-cancellation-genesis-v1", ())


@dataclass(frozen=True, slots=True)
class SyntheticCancellationWitness:
    event_count: int
    tail_hash: str
    last_cancelled_at_ms: int

    def assert_shape(self) -> None:
        if (
            type(self.event_count) is not int or not 0 <= self.event_count <= _LIMIT
            or type(self.tail_hash) is not str or not _HASH.fullmatch(self.tail_hash)
            or type(self.last_cancelled_at_ms) is not int
            or not -1 <= self.last_cancelled_at_ms <= _MAX
            or (self.event_count == 0) != (self.last_cancelled_at_ms == -1)
            or self.event_count == 0 and self.tail_hash != _GENESIS
        ):
            raise SyntheticCancellationRejected("invalid synthetic cancellation witness")


@dataclass(frozen=True, slots=True)
class SyntheticCancellationState:
    approval_id: str
    cancelled: bool
    witness: SyntheticCancellationWitness

    @property
    def human_consent_verified(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


def _objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    return tuple(
        tuple(row) for row in conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        )
    )


def _replay(conn: sqlite3.Connection) -> tuple[SyntheticCancellationWitness, ...]:
    if conn.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise SyntheticCancellationRejected("synthetic cancellation schema version changed")
    with sqlite3.connect(":memory:") as expected:
        expected.execute(_TABLE)
        if _objects(conn) != _objects(expected):
            raise SyntheticCancellationRejected("synthetic cancellation schema changed")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise SyntheticCancellationRejected("synthetic cancellation storage invalid")
    prefixes = [SyntheticCancellationWitness(0, _GENESIS, -1)]
    for row in conn.execute(
        """SELECT seq,approval_id,cancelled_at_ms,previous_hash,event_hash
           FROM synthetic_claim_cancellations ORDER BY seq"""
    ):
        previous = prefixes[-1]
        if previous.event_count >= _LIMIT:
            raise SyntheticCancellationRejected("synthetic cancellation budget exceeded")
        seq, claim, at_ms, parent, digest = row
        fields = (seq, claim, at_ms, parent)
        if (
            type(seq) is not int or seq != previous.event_count + 1
            or type(claim) is not str or not _APPROVAL.fullmatch(claim)
            or type(at_ms) is not int or not 0 <= at_ms <= _MAX
            or at_ms < previous.last_cancelled_at_ms
            or type(parent) is not str or parent != previous.tail_hash
            or type(digest) is not str
            or digest != _hash("ARK-synthetic-cancellation-event-v1", fields)
        ):
            raise SyntheticCancellationRejected("synthetic cancellation history changed")
        prefixes.append(SyntheticCancellationWitness(seq, digest, at_ms))
    return tuple(prefixes)


def _retained(value: SyntheticCancellationWitness | None) -> None:
    if value is None:
        return
    if type(value) is not SyntheticCancellationWitness:
        raise SyntheticCancellationRejected("retained cancellation witness has wrong type")
    value.assert_shape()


def _retained_epoch(
    value: SyntheticCancellationWitness | None,
) -> tuple[int, str, int] | None:
    """Pin scalar history evidence before callbacks and SQLite reads."""
    _retained(value)
    if value is None:
        return None
    return (value.event_count, value.tail_hash, value.last_cancelled_at_ms)


def _assert_retained_epoch(
    value: SyntheticCancellationWitness | None,
    pinned: tuple[int, str, int] | None,
) -> None:
    if value is None:
        if pinned is not None:
            raise SyntheticCancellationRejected("retained witness changed")
        return
    value.assert_shape()
    if (
        pinned is None
        or (value.event_count, value.tail_hash, value.last_cancelled_at_ms) != pinned
    ):
        raise SyntheticCancellationRejected("retained witness changed during review")


def _assert_prefix(
    prefixes: tuple[SyntheticCancellationWitness, ...],
    retained: SyntheticCancellationWitness | None,
) -> None:
    if retained is not None and (
        retained.event_count >= len(prefixes)
        or prefixes[retained.event_count] != retained
    ):
        raise SyntheticCancellationRejected("retained cancellation history changed")


class SyntheticCancellationLedger:
    """Append-only identity-only local veto journal, never permission issuance."""

    def __init__(self, path: Path) -> None:
        if not isinstance(path, Path):
            raise TypeError("cancellation path must be a pathlib.Path")
        self.path = path
        self._initial_path = path
        with closing(self._connect(create=True)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if _objects(conn):
                        raise SyntheticCancellationRejected(
                            "unversioned cancellation database is not empty"
                        )
                    conn.execute(_TABLE)
                    conn.execute("PRAGMA user_version=1")
                _replay(conn)
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _assert_path_epoch(self, expected: Path) -> None:
        if (
            type(self.path) is not type(expected)
            or self.path is not expected
            or self._initial_path is not expected
        ):
            raise SyntheticCancellationRejected("cancellation source path changed")

    def _connect(
        self, *, create: bool = False, readonly: bool = False,
    ) -> sqlite3.Connection:
        self._assert_path_epoch(self._initial_path)
        if create:
            return sqlite3.connect(self.path, timeout=10, isolation_level=None)
        mode = "ro" if readonly else "rw"
        return sqlite3.connect(
            self.path.resolve().as_uri() + "?mode=" + mode,
            uri=True, isolation_level=None, timeout=10,
        )

    def read_witness(
        self, *, retained: SyntheticCancellationWitness | None = None,
    ) -> SyntheticCancellationWitness:
        pinned = _retained_epoch(retained)
        path_epoch = self.path
        with closing(self._connect(readonly=True)) as conn:
            conn.execute("BEGIN")
            try:
                prefixes = _replay(conn)
                _assert_retained_epoch(retained, pinned)
                self._assert_path_epoch(path_epoch)
                _assert_prefix(prefixes, retained)
                result = prefixes[-1]
                _assert_retained_epoch(retained, pinned)
                self._assert_path_epoch(path_epoch)
                conn.commit()
                return result
            except BaseException:
                conn.rollback()
                raise

    def cancel_synthetic(
        self,
        approval_id: str,
        *,
        at_ms: int,
        retained: SyntheticCancellationWitness | None = None,
    ) -> SyntheticCancellationWitness:
        if (
            type(approval_id) is not str or not _APPROVAL.fullmatch(approval_id)
            or type(at_ms) is not int or not 0 <= at_ms <= _MAX
        ):
            raise SyntheticCancellationRejected("invalid synthetic approval cancellation")
        pinned = _retained_epoch(retained)
        path_epoch = self.path
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                prefixes = _replay(conn)
                _assert_retained_epoch(retained, pinned)
                self._assert_path_epoch(path_epoch)
                _assert_prefix(prefixes, retained)
                previous = prefixes[-1]
                if previous.event_count >= _LIMIT or at_ms < previous.last_cancelled_at_ms:
                    raise SyntheticCancellationRejected(
                        "synthetic cancellation capacity or clock regression"
                    )
                seq = previous.event_count + 1
                fields = (seq, approval_id, at_ms, previous.tail_hash)
                digest = _hash("ARK-synthetic-cancellation-event-v1", fields)
                try:
                    conn.execute(
                        "INSERT INTO synthetic_claim_cancellations VALUES(?,?,?,?,?)",
                        (*fields, digest),
                    )
                except sqlite3.IntegrityError as exc:
                    raise SyntheticCancellationRejected(
                        "synthetic approval cancellation already persisted"
                    ) from exc
                _assert_retained_epoch(retained, pinned)
                self._assert_path_epoch(path_epoch)
                conn.commit()
                return SyntheticCancellationWitness(seq, digest, at_ms)
            except BaseException:
                conn.rollback()
                raise

    def review_state(
        self,
        approval_id: str,
        *,
        retained: SyntheticCancellationWitness | None = None,
    ) -> SyntheticCancellationState:
        """Read-only exact local status; false does NOT mean genuine approval."""
        if type(approval_id) is not str or not _APPROVAL.fullmatch(approval_id):
            raise SyntheticCancellationRejected("invalid synthetic approval identity")
        pinned = _retained_epoch(retained)
        path_epoch = self.path
        with closing(self._connect(readonly=True)) as conn:
            conn.execute("BEGIN")
            try:
                prefixes = _replay(conn)
                _assert_retained_epoch(retained, pinned)
                self._assert_path_epoch(path_epoch)
                _assert_prefix(prefixes, retained)
                row = conn.execute(
                    "SELECT 1 FROM synthetic_claim_cancellations WHERE approval_id=?",
                    (approval_id,),
                ).fetchone()
                current = prefixes[-1]
                _assert_retained_epoch(retained, pinned)
                self._assert_path_epoch(path_epoch)
                conn.commit()
                return SyntheticCancellationState(
                    approval_id, row is not None, current,
                )
            except BaseException:
                conn.rollback()
                raise
