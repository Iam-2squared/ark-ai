"""Disconnected, policy-bound quarantine history for *expired* scheduled slots.

This stores only synthetic overdue classifications. Caller time, schedule identity
and retained witnesses are not authenticated. Recording quarantine never grants
execution, notification, consent, automatic replay, or trusted-clock authority.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import stat
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_SLOT = re.compile(r"slot_[0-9a-f]{64}\Z")
_MAX_MS = 2**63 - 1
_MAX_ROWS = 512
_MAX_OCCURRENCES = 4096
_MAX_INTERVAL_MS = 366 * 24 * 60 * 60 * 1000
_DOMAIN = b"ARK-disconnected-quarantine-ledger-v1\0"
_DDL = (
    "CREATE TABLE policy (policy_sha256 TEXT PRIMARY KEY, first_ms INTEGER NOT NULL, "
    "interval_ms INTEGER NOT NULL, count INTEGER NOT NULL, grace_ms INTEGER NOT NULL)",
    "CREATE TABLE quarantines (seq INTEGER PRIMARY KEY, occurrence_id TEXT NOT NULL "
    "UNIQUE, due_ms INTEGER NOT NULL, observed_ms INTEGER NOT NULL, "
    "chain_sha256 TEXT NOT NULL)",
)


class ScheduleQuarantineRejected(ValueError):
    """An invalid or stale synthetic occurrence/storage epoch was supplied."""


@dataclass(frozen=True, slots=True)
class QuarantinePolicy:
    policy_sha256: str = field(repr=False)
    first_ms: int
    interval_ms: int
    count: int
    grace_ms: int


@dataclass(frozen=True, slots=True)
class QuarantineWitness:
    count: int
    chain_sha256: str

    @property
    def independently_authenticated(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class QuarantineReceipt:
    witness: QuarantineWitness
    quarantined_index: int

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

    @property
    def consent_verified(self) -> bool:
        return False


def _digest(payload: tuple[object, ...]) -> str:
    data = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(_DOMAIN + data).hexdigest()


def _policy_epoch(policy: object) -> tuple[str, int, int, int, int]:
    if type(policy) is not QuarantinePolicy:
        raise ScheduleQuarantineRejected("exact synthetic policy required")
    values = (policy.policy_sha256, policy.first_ms, policy.interval_ms,
              policy.count, policy.grace_ms)
    sha, first, interval, count, grace = values
    if (type(sha) is not str or _SHA.fullmatch(sha) is None
            or any(type(n) is not int for n in (first, interval, count, grace))
            or not 0 <= first <= _MAX_MS
            or not 1_000 <= interval <= _MAX_INTERVAL_MS
            or not 1 <= count <= _MAX_OCCURRENCES
            or not 0 <= grace < interval or grace > 60_000
            or first + (count - 1) * interval > _MAX_MS):
        raise ScheduleQuarantineRejected("invalid bounded synthetic schedule")
    return values


def genesis_quarantine_witness(policy: QuarantinePolicy) -> QuarantineWitness:
    return QuarantineWitness(0, _digest(("genesis", _policy_epoch(policy))))


def derive_quarantined_occurrence(policy: QuarantinePolicy, index: int) -> str:
    sha, first, interval, count, _ = _policy_epoch(policy)
    if type(index) is not int or not 0 <= index < count:
        raise ScheduleQuarantineRejected("invalid occurrence index")
    due = first + index * interval
    payload = json.dumps((sha, index, due), separators=(",", ":")).encode("ascii")
    # Match the independent deterministic preview identifier without importing
    # or trusting a preview result object as authority.
    return "slot_" + hashlib.sha256(
        b"ARK-disconnected-schedule-preview-v1\0" + b"occurrence\0" + payload
    ).hexdigest()


def _path(value: object, *, create: bool) -> Path:
    if (type(value) is not type(Path(".")) or not value.is_absolute()
            or ".." in value.parts or len(str(value)) > 4096
            or value.name in ("", ".", "..")):
        raise ScheduleQuarantineRejected("absolute exact fixture path required")
    try:
        for parent in value.parents:
            info = parent.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise ScheduleQuarantineRejected("unsafe quarantine ancestor")
        try:
            info = value.lstat()
        except FileNotFoundError:
            if not create:
                raise ScheduleQuarantineRejected("missing quarantine ledger") from None
        else:
            if create or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ScheduleQuarantineRejected("aliased or existing quarantine ledger")
    except OSError as exc:
        raise ScheduleQuarantineRejected("quarantine path unavailable") from exc
    return value


def _validate(conn: sqlite3.Connection, epoch: tuple[str, int, int, int, int]) -> QuarantineWitness:
    if conn.execute("PRAGMA user_version").fetchone() != (1,):
        raise ScheduleQuarantineRejected("quarantine schema version changed")
    with closing(sqlite3.connect(":memory:")) as expected:
        for statement in _DDL:
            expected.execute(statement)
        q = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(conn.execute(q)) != tuple(expected.execute(q)):
            raise ScheduleQuarantineRejected("quarantine schema drift")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise ScheduleQuarantineRejected("quarantine SQLite integrity failure")
    if tuple(conn.execute("SELECT * FROM policy")) != (epoch,):
        raise ScheduleQuarantineRejected("stored schedule policy changed")
    witness = QuarantineWitness(0, _digest(("genesis", epoch)))
    last_observed = -1
    for seq, occurrence, due, observed, chain in conn.execute(
        "SELECT seq,occurrence_id,due_ms,observed_ms,chain_sha256 "
        "FROM quarantines ORDER BY seq"
    ):
        if (witness.count >= _MAX_ROWS or type(seq) is not int
                or seq != witness.count + 1 or seq > epoch[3]
                or type(due) is not int or type(observed) is not int
                or type(chain) is not str or _SHA.fullmatch(chain) is None
                or type(occurrence) is not str or _SLOT.fullmatch(occurrence) is None):
            raise ScheduleQuarantineRejected("invalid quarantine history row")
        wanted_due = epoch[1] + (seq - 1) * epoch[2]
        policy = QuarantinePolicy(*epoch)
        wanted_slot = derive_quarantined_occurrence(policy, seq - 1)
        if (due != wanted_due or occurrence != wanted_slot
                or not due + epoch[4] < observed <= _MAX_MS
                or observed < last_observed):
            raise ScheduleQuarantineRejected("quarantine occurrence or clock changed")
        wanted = _digest(("row", witness.chain_sha256, seq, occurrence, due, observed))
        if chain != wanted:
            raise ScheduleQuarantineRejected("quarantine chain altered")
        last_observed = observed
        witness = QuarantineWitness(seq, chain)
    return witness


class DisconnectedScheduleQuarantineLedger:
    """Ordered expiry quarantine journal, never a scheduler or dispatcher."""

    def __init__(self, path: Path, *, policy: QuarantinePolicy, create: bool = False) -> None:
        if type(create) is not bool:
            raise ScheduleQuarantineRejected("exact create flag required")
        self._path = _path(path, create=create)
        self._epoch = _policy_epoch(policy)
        mode = "rwc" if create else "rw"
        with closing(sqlite3.connect(
            self._path.as_uri() + "?mode=" + mode, uri=True,
            isolation_level=None, timeout=10,
        )) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if create:
                    if (conn.execute("PRAGMA user_version").fetchone() != (0,)
                            or tuple(conn.execute("SELECT name FROM sqlite_master"))):
                        raise ScheduleQuarantineRejected("nonempty quarantine ledger")
                    for statement in _DDL:
                        conn.execute(statement)
                    conn.execute("INSERT INTO policy VALUES(?,?,?,?,?)", self._epoch)
                    conn.execute("PRAGMA user_version=1")
                _validate(conn, self._epoch)
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _open(self, *, read_only: bool) -> sqlite3.Connection:
        path = _path(self._path, create=False)
        return sqlite3.connect(
            path.as_uri() + ("?mode=ro" if read_only else "?mode=rw"),
            uri=True, isolation_level=None, timeout=10,
        )

    def inspect(self, *, retained: QuarantineWitness) -> QuarantineWitness:
        self._check_witness(retained)
        original = (retained.count, retained.chain_sha256)
        with closing(self._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                actual = _validate(conn, self._epoch)
                if actual != retained or original != (retained.count, retained.chain_sha256):
                    raise ScheduleQuarantineRejected("stale or changed quarantine witness")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        return actual

    @staticmethod
    def _check_witness(value: object) -> None:
        if (type(value) is not QuarantineWitness
                or type(value.count) is not int or not 0 <= value.count <= _MAX_ROWS
                or type(value.chain_sha256) is not str
                or _SHA.fullmatch(value.chain_sha256) is None):
            raise ScheduleQuarantineRejected("invalid retained quarantine witness")

    def quarantine_expired(
        self, *, index: int, occurrence_id: str, observed_ms: int,
        retained: QuarantineWitness,
    ) -> QuarantineReceipt:
        """Record one *already expired* synthetic occurrence in order, without dispatch."""
        self._check_witness(retained)
        original = (retained.count, retained.chain_sha256)
        if (type(index) is not int or type(observed_ms) is not int
                or not 0 <= observed_ms <= _MAX_MS
                or type(occurrence_id) is not str
                or _SLOT.fullmatch(occurrence_id) is None):
            raise ScheduleQuarantineRejected("invalid synthetic expiry claim")
        policy = QuarantinePolicy(*self._epoch)
        if index >= self._epoch[3] or index < 0:
            raise ScheduleQuarantineRejected("occurrence index outside policy")
        due = self._epoch[1] + index * self._epoch[2]
        if (occurrence_id != derive_quarantined_occurrence(policy, index)
                or observed_ms <= due + self._epoch[4]):
            raise ScheduleQuarantineRejected("occurrence is not expired or not policy-bound")
        with closing(self._open(read_only=False)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                current = _validate(conn, self._epoch)
                if current != retained or original != (retained.count, retained.chain_sha256):
                    raise ScheduleQuarantineRejected("stale or rolled-back quarantine witness")
                if index != current.count or current.count >= _MAX_ROWS:
                    raise ScheduleQuarantineRejected("out-of-order or duplicate quarantine")
                if current.count:
                    previous = conn.execute(
                        "SELECT observed_ms FROM quarantines WHERE seq=?", (current.count,)
                    ).fetchone()[0]
                    if observed_ms < previous:
                        raise ScheduleQuarantineRejected("caller clock regressed")
                seq = index + 1
                chain = _digest(("row", current.chain_sha256, seq,
                                 occurrence_id, due, observed_ms))
                conn.execute("INSERT INTO quarantines VALUES(?,?,?,?,?)",
                             (seq, occurrence_id, due, observed_ms, chain))
                result = QuarantineWitness(seq, chain)
                if _validate(conn, self._epoch) != result:
                    raise ScheduleQuarantineRejected("quarantine write lost integrity")
                if original != (retained.count, retained.chain_sha256):
                    raise ScheduleQuarantineRejected("retained witness changed before commit")
                conn.commit()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise ScheduleQuarantineRejected("duplicate quarantine occurrence") from exc
            except BaseException:
                conn.rollback()
                raise
        return QuarantineReceipt(result, index)
