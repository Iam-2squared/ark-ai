"""Durable, disconnected due-slot reservations for synthetic scheduler fixtures.

A reservation is NOT execution permission, a trusted-clock reading, consent,
or a notification. A caller must independently retain the returned witness;
SQLite and SHA-256 alone cannot detect a complete storage rollback.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import stat
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"slot_[0-9a-f]{64}\Z")
_MAX_MS = 2**63 - 1
_MAX_ROWS = 512
_MAX_LATENESS_MS = 60_000
_DOMAIN = b"ARK-detached-synthetic-due-slot-v1\0"
_DDL = (
    "CREATE TABLE due_reservations ("
    "seq INTEGER PRIMARY KEY, occurrence_id TEXT NOT NULL UNIQUE, "
    "policy_sha256 TEXT NOT NULL, due_at_ms INTEGER NOT NULL, "
    "reserved_at_ms INTEGER NOT NULL)"
)


class DueReservationRejected(ValueError):
    """A due-slot transition is invalid, stale, or not safe to reserve."""


@dataclass(frozen=True, slots=True)
class DueReservationWitness:
    count: int
    fingerprint: str

    @property
    def independent_custody_proven(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class DueReservationReceipt:
    occurrence_id: str
    due_at_ms: int
    reserved_at_ms: int
    witness: DueReservationWitness

    @property
    def execution_authorized(self) -> bool:
        return False

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False


def _digest(rows: tuple[tuple[object, ...], ...]) -> str:
    payload = json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(_DOMAIN + payload).hexdigest()


def genesis_due_witness() -> DueReservationWitness:
    return DueReservationWitness(0, _digest(()))


def _check_witness(witness: object) -> None:
    if (
        type(witness) is not DueReservationWitness
        or type(witness.count) is not int
        or not 0 <= witness.count <= _MAX_ROWS
        or type(witness.fingerprint) is not str
        or _SHA.fullmatch(witness.fingerprint) is None
    ):
        raise DueReservationRejected("invalid independently retained due witness")


def _check_path(path: object, *, exists: bool) -> Path:
    if type(path) is not type(Path(".")) or not path.is_absolute():
        raise DueReservationRejected("absolute local fixture Path required")
    if path.is_symlink() or (exists and not path.exists()):
        raise DueReservationRejected("missing or symbolic due ledger")
    if path.exists() and not stat.S_ISREG(path.stat(follow_symlinks=False).st_mode):
        raise DueReservationRejected("due ledger must be a regular file")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise DueReservationRejected("due ledger parent must be a real directory")
    return path


def _schema(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone() != (1,):
        raise DueReservationRejected("due ledger schema version changed")
    with closing(sqlite3.connect(":memory:")) as expected:
        expected.execute(_DDL)
        query = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(conn.execute(query)) != tuple(expected.execute(query)):
            raise DueReservationRejected("due ledger schema drift")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise DueReservationRejected("due ledger storage integrity failure")


def _inspect(conn: sqlite3.Connection) -> tuple[DueReservationWitness, int | None]:
    _schema(conn)
    saved: list[tuple[object, ...]] = []
    last_reserved: int | None = None
    for seq, occurrence, policy, due, reserved in conn.execute(
        "SELECT seq,occurrence_id,policy_sha256,due_at_ms,reserved_at_ms "
        "FROM due_reservations ORDER BY seq"
    ):
        if len(saved) == _MAX_ROWS:
            raise DueReservationRejected("due ledger review budget exceeded")
        if (
            type(seq) is not int or seq != len(saved) + 1
            or type(policy) is not str or _SHA.fullmatch(policy) is None
            or type(due) is not int or type(reserved) is not int
            or not 0 <= due <= reserved <= _MAX_MS
            or reserved - due > _MAX_LATENESS_MS
            or last_reserved is not None and reserved < last_reserved
        ):
            raise DueReservationRejected("inconsistent persisted due slot")
        wanted = "slot_" + hashlib.sha256(
            _DOMAIN + (policy + ":" + str(due)).encode("ascii")
        ).hexdigest()
        if type(occurrence) is not str or _ID.fullmatch(occurrence) is None:
            raise DueReservationRejected("invalid persisted slot identity")
        if occurrence != wanted:
            raise DueReservationRejected("due slot identity does not bind its policy")
        saved.append((seq, occurrence, policy, due, reserved))
        last_reserved = reserved
    rows = tuple(saved)
    return DueReservationWitness(len(rows), _digest(rows)), last_reserved


class DisconnectedDueReservations:
    """Fixture SQLite reservations, never an actual autonomous scheduler."""

    def __init__(self, path: Path) -> None:
        self._path = _check_path(path, exists=False)
        with closing(sqlite3.connect(self._path, timeout=10, isolation_level=None)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if tuple(conn.execute("SELECT name FROM sqlite_master")):
                        raise DueReservationRejected("unversioned nonempty due ledger")
                    conn.execute(_DDL)
                    conn.execute("PRAGMA user_version=1")
                _inspect(conn)
                if self._path is not path:
                    raise DueReservationRejected("due ledger path changed")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _open(self, *, read_only: bool) -> sqlite3.Connection:
        path = _check_path(self._path, exists=True)
        mode = "ro" if read_only else "rw"
        return sqlite3.connect(
            path.as_uri() + "?mode=" + mode, uri=True, timeout=10, isolation_level=None,
        )

    def witness(self) -> DueReservationWitness:
        """Read without re-creating deleted storage; caller must retain separately."""
        source = self._path
        with closing(self._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                result, _ = _inspect(conn)
                if self._path is not source:
                    raise DueReservationRejected("due ledger source changed during read")
                conn.commit()
                return result
            except BaseException:
                conn.rollback()
                raise

    def reserve_due(
        self, *, policy_sha256: str, due_at_ms: int,
        observed_now_ms: int, retained: DueReservationWitness,
    ) -> DueReservationReceipt:
        """Persist one synthetic reservation, then return a non-executing receipt."""
        if (
            type(policy_sha256) is not str or _SHA.fullmatch(policy_sha256) is None
            or type(due_at_ms) is not int or type(observed_now_ms) is not int
            or not 0 <= due_at_ms <= observed_now_ms <= _MAX_MS
            or observed_now_ms - due_at_ms > _MAX_LATENESS_MS
        ):
            raise DueReservationRejected("invalid or stale caller-asserted due claim")
        _check_witness(retained)
        prior_epoch = (retained.count, retained.fingerprint)
        path_epoch = self._path
        identity = "slot_" + hashlib.sha256(
            _DOMAIN + (policy_sha256 + ":" + str(due_at_ms)).encode("ascii")
        ).hexdigest()
        if (retained.count, retained.fingerprint) != prior_epoch:
            raise DueReservationRejected("retained witness changed")
        with closing(self._open(read_only=False)) as conn:
            if self._path is not path_epoch:
                raise DueReservationRejected("due source changed before transaction")
            conn.execute("BEGIN IMMEDIATE")
            try:
                current, last = _inspect(conn)
                if current != retained or (retained.count, retained.fingerprint) != prior_epoch:
                    raise DueReservationRejected("stale or rewritten due ledger")
                if last is not None and observed_now_ms < last:
                    raise DueReservationRejected("caller due clock regressed")
                if current.count >= _MAX_ROWS:
                    raise DueReservationRejected("due ledger full")
                conn.execute(
                    "INSERT INTO due_reservations VALUES(?,?,?,?,?)",
                    (current.count + 1, identity, policy_sha256,
                     due_at_ms, observed_now_ms),
                )
                result, _ = _inspect(conn)
                if self._path is not path_epoch:
                    raise DueReservationRejected("due source changed before commit")
                if (retained.count, retained.fingerprint) != prior_epoch:
                    raise DueReservationRejected("retained witness changed before commit")
                conn.commit()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise DueReservationRejected("duplicate synthetic due occurrence") from exc
            except BaseException:
                conn.rollback()
                raise
        return DueReservationReceipt(identity, due_at_ms, observed_now_ms, result)
