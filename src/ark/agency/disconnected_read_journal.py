"""Detached SQLite evidence journal for synthetic READ results only.

An independent retained tip/count detects truncation or rewrite. Neither SQLite
nor SHA-256 authenticates a model, human, tool dispatch, or real-world effect.
No executor, model, ToolRegistry, MemoryStore or external service is accessed.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import stat
from dataclasses import dataclass
from pathlib import Path

_REQUEST = re.compile(r"req_[0-9a-f]{32}\Z")
_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_OPS = frozenset(("math.sum", "text.stats", "text.find", "json.inspect"))
_DOMAIN = b"ARK-detached-synthetic-read-journal-v1\0"
_GENESIS = hashlib.sha256(_DOMAIN + b"genesis").hexdigest()
_MAX_ROWS = 128
_SCHEMA = "ark.synthetic.read.journal.v1"
_MARKER_DDL = "CREATE TABLE marker (revision TEXT NOT NULL)"
_RECEIPT_DDL = (
    "CREATE TABLE receipts ("
    "seq INTEGER PRIMARY KEY, request_id TEXT NOT NULL, "
    "step_id TEXT NOT NULL, operation TEXT NOT NULL, "
    "input_digest TEXT NOT NULL, result_digest TEXT NOT NULL, "
    "previous_sha TEXT NOT NULL, chain_sha TEXT NOT NULL, "
    "UNIQUE(request_id, step_id))"
)


class ReadJournalRejected(ValueError):
    """The detached READ receipt stream is unsafe, stale, or inconsistent."""


@dataclass(frozen=True, slots=True)
class ReadReceipt:
    request_id: str
    step_id: str
    operation: str
    input_digest: str
    result_digest: str


@dataclass(frozen=True, slots=True)
class ReadJournalWitness:
    count: int
    tip_sha256: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def effect_proven(self) -> bool:
        return False

    @property
    def replay_authorized(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False


def genesis_witness() -> ReadJournalWitness:
    """The single valid starting witness for a new, empty local journal."""
    return ReadJournalWitness(0, _GENESIS)


def _check_witness(witness: ReadJournalWitness) -> None:
    if (
        type(witness) is not ReadJournalWitness
        or type(witness.count) is not int or not 0 <= witness.count <= _MAX_ROWS
        or type(witness.tip_sha256) is not str
        or _SHA.fullmatch(witness.tip_sha256) is None
    ):
        raise ReadJournalRejected("invalid retained witness")


def _check_receipt(row: ReadReceipt) -> None:
    if (
        type(row) is not ReadReceipt
        or type(row.request_id) is not str or _REQUEST.fullmatch(row.request_id) is None
        or type(row.step_id) is not str or _STEP.fullmatch(row.step_id) is None
        or type(row.operation) is not str or row.operation not in _OPS
        or type(row.input_digest) is not str or _SHA.fullmatch(row.input_digest) is None
        or type(row.result_digest) is not str or _SHA.fullmatch(row.result_digest) is None
    ):
        raise ReadJournalRejected("invalid synthetic READ receipt")


def _chain(previous: str, index: int, row: ReadReceipt) -> str:
    payload = json.dumps(
        {"index": index, "previous": previous, "request_id": row.request_id,
         "step_id": row.step_id, "operation": row.operation,
         "input_digest": row.input_digest, "result_digest": row.result_digest},
        ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(_DOMAIN + payload.encode("ascii")).hexdigest()


def _safe_path(path: Path, *, must_exist: bool) -> None:
    if (
        type(path) is not type(Path("."))
        or not path.is_absolute()
        or ".." in path.parts
    ):
        raise ReadJournalRejected("explicit absolute local Path required")
    # path.parent.is_symlink() misses a symbolic GRANDPARENT. Reject all
    # non-directory/symbolic ancestors before any open("x") or SQLite access.
    # Ancestry inspection is not an atomic open-handle/path custody proof.
    try:
        for parent in path.parents:
            info = parent.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise ReadJournalRejected("journal ancestor is not a real directory")
    except OSError as exc:
        raise ReadJournalRejected("journal ancestor unavailable") from exc
    if path.is_symlink() or (must_exist and not path.exists()):
        raise ReadJournalRejected("missing or symbolic journal path")
    if path.exists() and not stat.S_ISREG(path.stat(follow_symlinks=False).st_mode):
        raise ReadJournalRejected("journal must be a regular file")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise ReadJournalRejected("journal parent must be an existing directory")


def _verify_schema(connection: sqlite3.Connection) -> None:
    """No foreign tables, triggers, views or changed constraints permitted."""
    expected = sqlite3.connect(":memory:")
    try:
        expected.execute(_MARKER_DDL)
        expected.execute(_RECEIPT_DDL)
        query = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(connection.execute(query)) != tuple(expected.execute(query)):
            raise ReadJournalRejected("synthetic READ journal schema changed")
    finally:
        expected.close()


class DisconnectedReadJournal:
    """SQLite-only append/CAS ledger; stores digests, never raw result contents."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @classmethod
    def create(cls, path: Path) -> DisconnectedReadJournal:
        """Create only a NEW local database; never overwrite an existing path."""
        _safe_path(path, must_exist=False)
        try:
            with path.open("x", encoding="utf-8"):
                pass
            connection = sqlite3.connect(path, timeout=10, isolation_level=None)
            connection.execute("PRAGMA busy_timeout=10000")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(_MARKER_DDL)
            connection.execute("INSERT INTO marker VALUES (?)", (_SCHEMA,))
            connection.execute(_RECEIPT_DDL)
            connection.execute("COMMIT")
            return cls(connection)
        except (FileExistsError, OSError, sqlite3.Error) as exc:
            raise ReadJournalRejected("cannot create new local journal") from exc

    @classmethod
    def open(cls, path: Path) -> DisconnectedReadJournal:
        """Reopen an existing marked journal without migrating any schema."""
        _safe_path(path, must_exist=True)
        try:
            connection = sqlite3.connect(path, timeout=10, isolation_level=None)
            connection.execute("PRAGMA busy_timeout=10000")
            rows = connection.execute("SELECT revision FROM marker").fetchall()
            if rows != [(_SCHEMA,)]:
                raise ReadJournalRejected("foreign journal marker")
            _verify_schema(connection)
            cls(connection)._scan()
            return cls(connection)
        except sqlite3.Error as exc:
            raise ReadJournalRejected("unreadable journal schema") from exc

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> DisconnectedReadJournal:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _scan(self) -> ReadJournalWitness:
        """Scan in the caller's transaction, enforcing contiguous hash linkage."""
        _verify_schema(self._connection)
        marker = self._connection.execute("SELECT revision FROM marker").fetchall()
        if marker != [(_SCHEMA,)]:
            raise ReadJournalRejected("foreign journal marker")
        rows = self._connection.execute(
            "SELECT seq, request_id, step_id, operation, input_digest, "
            "result_digest, previous_sha, chain_sha FROM receipts ORDER BY seq"
        ).fetchall()
        if len(rows) > _MAX_ROWS:
            raise ReadJournalRejected("journal row budget exceeded")
        tip = _GENESIS
        seen: set[tuple[str, str]] = set()
        for i, (seq, request, step, op, inp, out, previous, stored) in enumerate(rows, 1):
            row = ReadReceipt(request, step, op, inp, out)
            _check_receipt(row)
            identity = (request, step)
            if seq != i or identity in seen or previous != tip:
                raise ReadJournalRejected("missing, reordered, or duplicated receipt")
            if type(stored) is not str or _SHA.fullmatch(stored) is None:
                raise ReadJournalRejected("invalid stored chain digest")
            tip = _chain(tip, i, row)
            if stored != tip:
                raise ReadJournalRejected("receipt chain altered")
            seen.add(identity)
        return ReadJournalWitness(len(rows), tip)

    def verify(self, retained: ReadJournalWitness) -> ReadJournalWitness:
        """Verify a stable SQLite read snapshot against caller-retained state."""
        _check_witness(retained)
        try:
            self._connection.execute("BEGIN")
            actual = self._scan()
            if actual != retained:
                raise ReadJournalRejected("external witness disagrees with journal")
            self._connection.execute("COMMIT")
            return actual
        except BaseException:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    def append(self, row: ReadReceipt, retained: ReadJournalWitness) -> ReadJournalWitness:
        """Append one synthetic READ digest with transaction-scoped CAS."""
        _check_receipt(row)
        _check_witness(retained)
        # Retain the caller's exact dataclass fields before entering SQLite.
        fields = (row.request_id, row.step_id, row.operation,
                  row.input_digest, row.result_digest)
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            actual = self._scan()
            if actual != retained or actual.count >= _MAX_ROWS:
                raise ReadJournalRejected("stale or exhausted journal witness")
            if any(current is not earlier for current, earlier in zip(
                (row.request_id, row.step_id, row.operation,
                 row.input_digest, row.result_digest), fields, strict=True,
            )):
                raise ReadJournalRejected("receipt mutated before append")
            next_index = actual.count + 1
            next_tip = _chain(actual.tip_sha256, next_index, row)
            self._connection.execute(
                "INSERT INTO receipts VALUES (?,?,?,?,?,?,?,?)",
                (next_index, *fields, actual.tip_sha256, next_tip),
            )
            if any(current is not earlier for current, earlier in zip(
                (row.request_id, row.step_id, row.operation,
                 row.input_digest, row.result_digest), fields, strict=True,
            )):
                raise ReadJournalRejected("receipt mutated before commit")
            self._connection.execute("COMMIT")
            return ReadJournalWitness(next_index, next_tip)
        except sqlite3.IntegrityError as exc:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise ReadJournalRejected("duplicate synthetic receipt") from exc
        except BaseException:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise
