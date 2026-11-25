"""Local-only V3 attempt and finalization receipts; never starts training.

The ledger reserves one attempt per execution snapshot before any caller-owned
work, then appends one finalization receipt only after the caller has already
published its evidence bundle. An interrupted STARTED attempt requires manual
review. This module is not wired into the training CLI and grants no execution,
compute, Candidate, evaluation, or promotion authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

_SCHEMA_VERSION = 1
_MAX_SQLITE_INT = (1 << 63) - 1
_MAX_ATTEMPTS = 128
_MAX_EVENTS = _MAX_ATTEMPTS * 2
_MAX_PATH_BYTES = 4096
_ATTEMPT_ID = re.compile(r"attempt_[0-9a-f]{64}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_EVENT_DOMAIN = b"ARK-v3-local-attempt-event-v1\0"
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_JSON_DUMPS = json.dumps
_GENESIS = _ORIGINAL_SHA256(b"ARK-v3-local-attempt-genesis-v1\0").hexdigest()
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _require_original_codec() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_JSON_DUMPS
    ):
        raise AttemptLedgerSchemaError("attempt ledger digest or JSON codec changed")

_META_SQL = """
CREATE TABLE attempt_meta (
    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
    schema_version INTEGER NOT NULL CHECK(schema_version = 1),
    last_sequence INTEGER NOT NULL CHECK(last_sequence >= 0),
    last_event_sha256 TEXT NOT NULL CHECK(length(last_event_sha256) = 64)
) STRICT
"""

_RESERVATIONS_SQL = """
CREATE TABLE attempt_reservations (
    attempt_id TEXT PRIMARY KEY CHECK(length(attempt_id) = 72),
    execution_sha256 TEXT NOT NULL UNIQUE CHECK(length(execution_sha256) = 64),
    authorization_packet_sha256 TEXT NOT NULL
        CHECK(length(authorization_packet_sha256) = 64),
    started_at_ms INTEGER NOT NULL CHECK(started_at_ms >= 0)
) STRICT
"""

_EVENTS_SQL = """
CREATE TABLE attempt_events (
    sequence INTEGER PRIMARY KEY CHECK(sequence >= 1),
    attempt_id TEXT NOT NULL REFERENCES attempt_reservations(attempt_id),
    execution_sha256 TEXT NOT NULL CHECK(length(execution_sha256) = 64),
    authorization_packet_sha256 TEXT NOT NULL
        CHECK(length(authorization_packet_sha256) = 64),
    state TEXT NOT NULL CHECK(state IN ('STARTED', 'FINALIZED')),
    occurred_at_ms INTEGER NOT NULL CHECK(occurred_at_ms >= 0),
    artifact_manifest_sha256 TEXT,
    evidence_bundle_sha256 TEXT,
    previous_event_sha256 TEXT NOT NULL CHECK(length(previous_event_sha256) = 64),
    event_sha256 TEXT NOT NULL UNIQUE CHECK(length(event_sha256) = 64),
    UNIQUE(attempt_id, state),
    CHECK(
        (state = 'STARTED'
            AND artifact_manifest_sha256 IS NULL
            AND evidence_bundle_sha256 IS NULL)
        OR
        (state = 'FINALIZED'
            AND length(artifact_manifest_sha256) = 64
            AND length(evidence_bundle_sha256) = 64)
    )
) STRICT
"""

_DDL = _META_SQL + ";" + _RESERVATIONS_SQL + ";" + _EVENTS_SQL


class AttemptLedgerError(RuntimeError):
    """Base error for the local V3 attempt ledger."""


class AttemptLedgerSchemaError(AttemptLedgerError):
    """The local ledger schema, event chain, or retained rows are invalid."""


class AttemptLedgerConflictError(AttemptLedgerError):
    """An attempt was already reserved or cannot make this transition."""


class AttemptLedgerNotFoundError(AttemptLedgerError):
    """The requested attempt does not exist."""


class AttemptLedgerCommitUnknown(AttemptLedgerError):
    """SQLite did not acknowledge COMMIT; cold recovery is required."""


@dataclass(frozen=True, slots=True)
class AttemptReceipt:
    attempt_id: str
    execution_sha256: str
    authorization_packet_sha256: str
    state: str
    event_sequence: int
    event_sha256: str
    started_at_ms: int
    occurred_at_ms: int
    artifact_manifest_sha256: str | None
    evidence_bundle_sha256: str | None

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_compute_authorized(self) -> bool:
        return False

    @property
    def candidate_generation_authorized(self) -> bool:
        return False

    @property
    def protected_v2_authorized(self) -> bool:
        return False

    @property
    def promotion_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class AttemptRecovery:
    receipt: AttemptReceipt
    manual_review_required: bool

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_compute_authorized(self) -> bool:
        return False

    @property
    def candidate_generation_authorized(self) -> bool:
        return False

    @property
    def protected_v2_authorized(self) -> bool:
        return False

    @property
    def promotion_authorized(self) -> bool:
        return False


def _require_sha(value: object, label: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be an exact lowercase SHA-256 digest")
    return value


def _require_attempt_id(value: object) -> str:
    if type(value) is not str or _ATTEMPT_ID.fullmatch(value) is None:
        raise ValueError("attempt_id must be attempt_ followed by 64 lowercase hex digits")
    return value


def _require_time(value: object) -> int:
    if type(value) is not int or not 0 <= value <= _MAX_SQLITE_INT:
        raise ValueError("occurred_at_ms must be a non-negative SQLite integer")
    return value


def _canonical_event(
    sequence: int,
    attempt_id: str,
    execution_sha256: str,
    authorization_packet_sha256: str,
    state: str,
    occurred_at_ms: int,
    artifact_manifest_sha256: str | None,
    evidence_bundle_sha256: str | None,
    previous_event_sha256: str,
) -> bytes:
    _require_original_codec()
    payload = [
        sequence,
        attempt_id,
        execution_sha256,
        authorization_packet_sha256,
        state,
        occurred_at_ms,
        artifact_manifest_sha256,
        evidence_bundle_sha256,
        previous_event_sha256,
    ]
    return json.dumps(
        payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")


def _event_hash(*values: object) -> str:
    _require_original_codec()
    return _ORIGINAL_SHA256(_EVENT_DOMAIN + _canonical_event(*values)).hexdigest()


def _is_reparse_point(info: os.stat_result) -> bool:
    attributes = getattr(info, "st_file_attributes", 0)
    return type(attributes) is not int or bool(attributes & _REPARSE_POINT)


def _safe_path(path: Path, *, create: bool) -> None:
    """Reject obvious local path aliases before SQLite opens the ledger.

    Rechecking path metadata narrows accidental aliasing but is not atomic
    dirfd custody or protection against a concurrent owner-controlled rename.
    """
    if (
        type(path) is not type(Path()) or ".." in path.parts
        or not path.name or "\x00" in str(path)
    ):
        raise AttemptLedgerSchemaError("attempt ledger path is invalid")
    try:
        target = path.absolute()
        if len(os.fsencode(target)) + len(b"-journal") > _MAX_PATH_BYTES:
            raise AttemptLedgerSchemaError("attempt ledger path exceeds its byte budget")
        for ancestor in target.parents:
            info = ancestor.lstat()
            if (
                not stat.S_ISDIR(info.st_mode)
                or stat.S_ISLNK(info.st_mode)
                or _is_reparse_point(info)
            ):
                raise AttemptLedgerSchemaError("attempt ledger ancestor is not a plain directory")
        try:
            info = target.lstat()
        except FileNotFoundError:
            if not create:
                raise AttemptLedgerSchemaError("attempt ledger database is unavailable") from None
            main_exists = False
        else:
            main_exists = True
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_ISLNK(info.st_mode)
                or info.st_nlink != 1
                or _is_reparse_point(info)
            ):
                raise AttemptLedgerSchemaError("attempt ledger is not a single regular file")
        for suffix in ("-journal", "-wal", "-shm"):
            sidecar = target.with_name(target.name + suffix)
            try:
                sidecar_info = sidecar.lstat()
            except FileNotFoundError:
                continue
            if not main_exists or (
                not stat.S_ISREG(sidecar_info.st_mode)
                or stat.S_ISLNK(sidecar_info.st_mode)
                or sidecar_info.st_nlink != 1
                or _is_reparse_point(sidecar_info)
            ):
                raise AttemptLedgerSchemaError("attempt ledger SQLite sidecar is unsafe")
    except OSError as exc:
        raise AttemptLedgerSchemaError("attempt ledger path cannot be verified") from exc


def _schema_objects(connection: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    rows = connection.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    return tuple(tuple(row) for row in rows)


def _validate_schema(connection: sqlite3.Connection) -> None:
    quick = connection.execute("PRAGMA quick_check").fetchall()
    if len(quick) != 1 or tuple(quick[0]) != ("ok",):
        raise AttemptLedgerSchemaError("attempt ledger SQLite quick_check failed")
    foreign = connection.execute("PRAGMA foreign_key_check").fetchmany(1)
    if foreign:
        raise AttemptLedgerSchemaError("attempt ledger foreign-key integrity failed")
    with closing(sqlite3.connect(":memory:")) as expected:
        expected.executescript(_DDL)
        if _schema_objects(connection) != _schema_objects(expected):
            raise AttemptLedgerSchemaError("attempt ledger schema differs from frozen v1 DDL")


def _validate_history(
    connection: sqlite3.Connection,
) -> tuple[dict[str, tuple[tuple[object, ...], ...]], int, str]:
    meta = connection.execute(
        "SELECT singleton, schema_version, last_sequence, last_event_sha256 "
        "FROM attempt_meta"
    ).fetchall()
    if (
        len(meta) != 1
        or tuple(meta[0])[:2] != (1, _SCHEMA_VERSION)
        or type(meta[0][2]) is not int
        or type(meta[0][3]) is not str
        or _SHA256.fullmatch(meta[0][3]) is None
    ):
        raise AttemptLedgerSchemaError("attempt ledger metadata is invalid")

    reservations = connection.execute(
        "SELECT attempt_id, execution_sha256, authorization_packet_sha256, started_at_ms "
        "FROM attempt_reservations ORDER BY attempt_id"
    ).fetchall()
    events = connection.execute(
        "SELECT sequence, attempt_id, execution_sha256, authorization_packet_sha256, "
        "state, occurred_at_ms, artifact_manifest_sha256, evidence_bundle_sha256, "
        "previous_event_sha256, event_sha256 "
        "FROM attempt_events ORDER BY sequence"
    ).fetchall()
    if len(reservations) > _MAX_ATTEMPTS or len(events) > _MAX_EVENTS:
        raise AttemptLedgerSchemaError("attempt ledger exceeds its retained row budget")

    grouped: dict[str, list[tuple[object, ...]]] = {}
    previous = _GENESIS
    for expected_sequence, row in enumerate(events, start=1):
        (
            sequence, attempt_id, execution_sha256, authorization_sha256,
            state, occurred_at_ms, manifest_sha256, evidence_sha256,
            previous_hash, event_sha256,
        ) = tuple(row)
        if (
            type(sequence) is not int or sequence != expected_sequence
            or type(attempt_id) is not str or _ATTEMPT_ID.fullmatch(attempt_id) is None
            or type(execution_sha256) is not str or _SHA256.fullmatch(execution_sha256) is None
            or type(authorization_sha256) is not str
            or _SHA256.fullmatch(authorization_sha256) is None
            or state not in ("STARTED", "FINALIZED")
            or type(occurred_at_ms) is not int or not 0 <= occurred_at_ms <= _MAX_SQLITE_INT
            or type(previous_hash) is not str or previous_hash != previous
            or type(event_sha256) is not str or _SHA256.fullmatch(event_sha256) is None
        ):
            raise AttemptLedgerSchemaError("attempt ledger event shape or chronology is invalid")
        if state == "STARTED":
            if manifest_sha256 is not None or evidence_sha256 is not None:
                raise AttemptLedgerSchemaError("STARTED event contains finalization digests")
        elif (
            type(manifest_sha256) is not str or _SHA256.fullmatch(manifest_sha256) is None
            or type(evidence_sha256) is not str or _SHA256.fullmatch(evidence_sha256) is None
        ):
            raise AttemptLedgerSchemaError("FINALIZED event digests are invalid")
        expected_hash = _event_hash(
            sequence, attempt_id, execution_sha256, authorization_sha256,
            state, occurred_at_ms, manifest_sha256, evidence_sha256, previous_hash,
        )
        if event_sha256 != expected_hash:
            raise AttemptLedgerSchemaError("attempt ledger event hash mismatch")
        grouped.setdefault(attempt_id, []).append(tuple(row))
        previous = event_sha256

    if (
        type(meta[0][2]) is not int
        or meta[0][2] != len(events)
        or meta[0][3] != previous
    ):
        raise AttemptLedgerSchemaError("attempt ledger event frontier mismatch")

    reservation_ids: set[str] = set()
    execution_ids: set[str] = set()
    for reservation in reservations:
        attempt_id, execution_sha256, authorization_sha256, started_at_ms = tuple(reservation)
        if (
            type(attempt_id) is not str or _ATTEMPT_ID.fullmatch(attempt_id) is None
            or type(execution_sha256) is not str or _SHA256.fullmatch(execution_sha256) is None
            or type(authorization_sha256) is not str or _SHA256.fullmatch(authorization_sha256) is None
            or type(started_at_ms) is not int or not 0 <= started_at_ms <= _MAX_SQLITE_INT
            or attempt_id in reservation_ids or execution_sha256 in execution_ids
        ):
            raise AttemptLedgerSchemaError("attempt reservation identity is invalid")
        reservation_ids.add(attempt_id)
        execution_ids.add(execution_sha256)
        attempt_events = grouped.get(attempt_id, [])
        if (
            len(attempt_events) not in (1, 2)
            or attempt_events[0][4] != "STARTED"
            or attempt_events[0][2] != execution_sha256
            or attempt_events[0][3] != authorization_sha256
            or attempt_events[0][5] != started_at_ms
            or (len(attempt_events) == 2 and (
                attempt_events[1][4] != "FINALIZED"
                or attempt_events[1][2] != execution_sha256
                or attempt_events[1][3] != authorization_sha256
            ))
        ):
            raise AttemptLedgerSchemaError("attempt reservation and event history disagree")

    if set(grouped) != reservation_ids:
        raise AttemptLedgerSchemaError("attempt event has no matching reservation")
    return {key: tuple(value) for key, value in grouped.items()}, len(events), previous


class SQLiteAttemptLedger:
    """Append-only local attempt ledger with no retry or execution authority."""

    __slots__ = ("_path",)

    def __setattr__(self, name: str, value: object) -> None:
        if name == "_path":
            try:
                object.__getattribute__(self, "_path")
            except AttributeError:
                pass
            else:
                raise AttributeError("attempt ledger path is immutable")
        object.__setattr__(self, name, value)

    def __init__(self, path: str | Path) -> None:
        if type(path) not in (str, type(Path())):
            raise AttemptLedgerSchemaError("attempt ledger requires an exact local path")
        source = Path(path)
        if ".." in source.parts:
            raise AttemptLedgerSchemaError("attempt ledger path traversal is refused")
        self._path = source.absolute()
        _safe_path(self._path, create=True)
        self._initialize()

    def _connect(self, *, create: bool = False) -> sqlite3.Connection:
        _safe_path(self._path, create=create)
        if create:
            connection = sqlite3.connect(
                self._path, timeout=5, isolation_level=None,
            )
        else:
            uri = self._path.resolve().as_uri() + "?mode=rw"
            connection = sqlite3.connect(
                uri, uri=True, timeout=5, isolation_level=None,
            )
        try:
            connection.execute("PRAGMA busy_timeout=5000")
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA synchronous=FULL")
            _safe_path(self._path, create=False)
            return connection
        except Exception:
            connection.close()
            raise

    def _initialize(self) -> None:
        with closing(self._connect(create=True)) as connection:
            connection.execute("PRAGMA journal_mode=DELETE")
            connection.execute("BEGIN IMMEDIATE")
            names = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            if not names:
                for statement in _DDL.split(";"):
                    if statement.strip():
                        connection.execute(statement)
                connection.execute(
                    "INSERT INTO attempt_meta VALUES (1, ?, 0, ?)",
                    (_SCHEMA_VERSION, _GENESIS),
                )
            _validate_schema(connection)
            _validate_history(connection)
            connection.execute("COMMIT")

    @staticmethod
    def _append_event(
        connection: sqlite3.Connection,
        *,
        attempt_id: str,
        execution_sha256: str,
        authorization_packet_sha256: str,
        state: str,
        occurred_at_ms: int,
        artifact_manifest_sha256: str | None = None,
        evidence_bundle_sha256: str | None = None,
    ) -> tuple[int, str]:
        row = connection.execute(
            "SELECT last_sequence, last_event_sha256 FROM attempt_meta WHERE singleton=1"
        ).fetchone()
        if (
            row is None or type(row[0]) is not int or type(row[1]) is not str
            or row[0] >= _MAX_EVENTS
        ):
            raise AttemptLedgerSchemaError("attempt ledger event frontier is invalid or full")
        sequence = row[0] + 1
        previous_hash = row[1]
        event_sha256 = _event_hash(
            sequence, attempt_id, execution_sha256, authorization_packet_sha256,
            state, occurred_at_ms, artifact_manifest_sha256,
            evidence_bundle_sha256, previous_hash,
        )
        connection.execute(
            "INSERT INTO attempt_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                sequence, attempt_id, execution_sha256, authorization_packet_sha256,
                state, occurred_at_ms, artifact_manifest_sha256,
                evidence_bundle_sha256, previous_hash, event_sha256,
            ),
        )
        updated = connection.execute(
            "UPDATE attempt_meta SET last_sequence=?, last_event_sha256=? "
            "WHERE singleton=1 AND last_sequence=? AND last_event_sha256=?",
            (sequence, event_sha256, row[0], previous_hash),
        )
        if updated.rowcount != 1:
            raise AttemptLedgerConflictError("attempt ledger frontier compare-and-swap failed")
        return sequence, event_sha256

    def begin_attempt(
        self,
        attempt_id: str,
        execution_sha256: str,
        authorization_packet_sha256: str,
        *,
        now_ms: int,
    ) -> AttemptReceipt:
        attempt_id = _require_attempt_id(attempt_id)
        execution_sha256 = _require_sha(execution_sha256, "execution_sha256")
        authorization_packet_sha256 = _require_sha(
            authorization_packet_sha256, "authorization_packet_sha256",
        )
        now_ms = _require_time(now_ms)
        with closing(self._connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                _validate_schema(connection)
                _validate_history(connection)
                connection.execute(
                    "INSERT INTO attempt_reservations VALUES (?, ?, ?, ?)",
                    (attempt_id, execution_sha256, authorization_packet_sha256, now_ms),
                )
                sequence, event_sha256 = self._append_event(
                    connection,
                    attempt_id=attempt_id,
                    execution_sha256=execution_sha256,
                    authorization_packet_sha256=authorization_packet_sha256,
                    state="STARTED",
                    occurred_at_ms=now_ms,
                )
                try:
                    connection.execute("COMMIT")
                except sqlite3.Error as exc:
                    raise AttemptLedgerCommitUnknown(
                        "attempt reservation COMMIT outcome is unknown; cold recovery required"
                    ) from exc
            except AttemptLedgerCommitUnknown:
                raise
            except sqlite3.IntegrityError as exc:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise AttemptLedgerConflictError(
                    "execution snapshot or attempt identity was already reserved"
                ) from exc
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        return AttemptReceipt(
            attempt_id, execution_sha256, authorization_packet_sha256,
            "STARTED", sequence, event_sha256, now_ms, now_ms, None, None,
        )

    def finalize_attempt(
        self,
        attempt_id: str,
        execution_sha256: str,
        authorization_packet_sha256: str,
        *,
        artifact_manifest_sha256: str,
        evidence_bundle_sha256: str,
        now_ms: int,
    ) -> AttemptReceipt:
        attempt_id = _require_attempt_id(attempt_id)
        execution_sha256 = _require_sha(execution_sha256, "execution_sha256")
        authorization_packet_sha256 = _require_sha(
            authorization_packet_sha256, "authorization_packet_sha256",
        )
        artifact_manifest_sha256 = _require_sha(
            artifact_manifest_sha256, "artifact_manifest_sha256",
        )
        evidence_bundle_sha256 = _require_sha(
            evidence_bundle_sha256, "evidence_bundle_sha256",
        )
        now_ms = _require_time(now_ms)
        with closing(self._connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                _validate_schema(connection)
                grouped, _, _ = _validate_history(connection)
                events = grouped.get(attempt_id)
                if not events:
                    raise AttemptLedgerNotFoundError("attempt reservation was not found")
                started = events[0]
                if (
                    started[4] != "STARTED"
                    or started[2] != execution_sha256
                    or started[3] != authorization_packet_sha256
                ):
                    raise AttemptLedgerConflictError(
                        "finalization does not match the reserved attempt"
                    )
                if len(events) != 1:
                    raise AttemptLedgerConflictError("attempt was already finalized")
                sequence, event_sha256 = self._append_event(
                    connection,
                    attempt_id=attempt_id,
                    execution_sha256=execution_sha256,
                    authorization_packet_sha256=authorization_packet_sha256,
                    state="FINALIZED",
                    occurred_at_ms=now_ms,
                    artifact_manifest_sha256=artifact_manifest_sha256,
                    evidence_bundle_sha256=evidence_bundle_sha256,
                )
                try:
                    connection.execute("COMMIT")
                except sqlite3.Error as exc:
                    raise AttemptLedgerCommitUnknown(
                        "attempt finalization COMMIT outcome is unknown; cold recovery required"
                    ) from exc
            except AttemptLedgerCommitUnknown:
                raise
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        return AttemptReceipt(
            attempt_id, execution_sha256, authorization_packet_sha256,
            "FINALIZED", sequence, event_sha256, started[5], now_ms,
            artifact_manifest_sha256, evidence_bundle_sha256,
        )

    def recover(self, attempt_id: str) -> AttemptRecovery:
        attempt_id = _require_attempt_id(attempt_id)
        with closing(self._connect()) as connection:
            try:
                connection.execute("PRAGMA query_only=ON")
                connection.execute("BEGIN")
                _validate_schema(connection)
                grouped, _, _ = _validate_history(connection)
                events = grouped.get(attempt_id)
                if not events:
                    raise AttemptLedgerNotFoundError("attempt reservation was not found")
                started = events[0]
                latest = events[-1]
                finalized = latest[4] == "FINALIZED"
                receipt = AttemptReceipt(
                    attempt_id,
                    started[2],
                    started[3],
                    latest[4],
                    latest[0],
                    latest[9],
                    started[5],
                    latest[5],
                    latest[6],
                    latest[7],
                )
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        return AttemptRecovery(receipt, manual_review_required=not finalized)


__all__ = [
    "AttemptLedgerCommitUnknown",
    "AttemptLedgerConflictError",
    "AttemptLedgerError",
    "AttemptLedgerNotFoundError",
    "AttemptLedgerSchemaError",
    "AttemptReceipt",
    "AttemptRecovery",
    "SQLiteAttemptLedger",
]
