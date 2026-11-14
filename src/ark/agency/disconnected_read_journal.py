"""Detached SQLite evidence journal for synthetic READ results only.

An independent retained tip/count detects truncation or rewrite. Neither SQLite
nor SHA-256 authenticates a model, human, tool dispatch, or real-world effect.
No executor, model, ToolRegistry, MemoryStore or external service is accessed.
"""

from __future__ import annotations

import hashlib
import json
import os
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


# Preserve original, non-authorizing carrier types against injected factories.
_RECEIPT_TYPE = ReadReceipt
_WITNESS_TYPE = ReadJournalWitness


@dataclass(frozen=True, slots=True)
class ReadJournalSnapshot:
    """Digest-only, non-authorizing recovery view of one local SQLite snapshot."""

    witness: ReadJournalWitness
    receipts: tuple[ReadReceipt, ...]

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def effect_proven(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False


_SNAPSHOT_TYPE = ReadJournalSnapshot
_SNAPSHOT_DENIALS = (
    "dispatch_authorized", "effect_proven",
    "automatic_replay_authorized", "independent_custody_proven",
)
_WITNESS_DENIALS = (
    "dispatch_authorized", "effect_proven",
    "replay_authorized", "independent_custody_proven",
)
_ORIGINAL_WITNESS_DENIALS = tuple(
    vars(_WITNESS_TYPE)[name] for name in _WITNESS_DENIALS
)
_ORIGINAL_SNAPSHOT_DENIALS = tuple(
    vars(_SNAPSHOT_TYPE)[name] for name in _SNAPSHOT_DENIALS
)


# Receipt recovery must not call a substituted result constructor/getter.
# Frozen dataclass instances do not freeze their Python class descriptors.
_SNAPSHOT_FIELDS = ("witness", "receipts")
_SNAPSHOT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_SNAPSHOT_FIELDS = tuple(
    vars(_SNAPSHOT_TYPE)[name] for name in _SNAPSHOT_FIELDS
)
_ORIGINAL_SNAPSHOT_HOOKS = tuple(
    vars(_SNAPSHOT_TYPE).get(name) for name in _SNAPSHOT_HOOKS
)


def _require_original_snapshot_class() -> None:
    if (
        ReadJournalSnapshot is not _SNAPSHOT_TYPE
        or any(
            vars(_SNAPSHOT_TYPE).get(name) is not original
            for names, originals in (
                (_SNAPSHOT_FIELDS, _ORIGINAL_SNAPSHOT_FIELDS),
                (_SNAPSHOT_HOOKS, _ORIGINAL_SNAPSHOT_HOOKS),
                (_SNAPSHOT_DENIALS, _ORIGINAL_SNAPSHOT_DENIALS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise ReadJournalRejected(
            "READ recovery result changed: snapshot constructor changed"
        )



# Frozen dataclass instances do not freeze their class descriptors. A patched
# slot/getter/constructor may inspect a private receipt before validation;
# pin import-original carriers and deny-only authority descriptors first.
_RECEIPT_FIELDS = (
    "request_id", "step_id", "operation", "input_digest", "result_digest",
)
_WITNESS_FIELDS = ("count", "tip_sha256")
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RECEIPT_FIELDS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_FIELDS
)
_ORIGINAL_WITNESS_FIELDS = tuple(
    vars(_WITNESS_TYPE)[name] for name in _WITNESS_FIELDS
)
_ORIGINAL_RECEIPT_HOOKS = tuple(
    vars(_RECEIPT_TYPE).get(name) for name in _CARRIER_HOOKS
)
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(name) for name in _CARRIER_HOOKS
)


def _require_original_read_carriers() -> None:
    if ReadReceipt is not _RECEIPT_TYPE or ReadJournalWitness is not _WITNESS_TYPE:
        raise ReadJournalRejected("synthetic READ carrier class changed")
    for cls, names, originals in (
        (_RECEIPT_TYPE, _RECEIPT_FIELDS, _ORIGINAL_RECEIPT_FIELDS),
        (_WITNESS_TYPE, _WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS),
        (_RECEIPT_TYPE, _CARRIER_HOOKS, _ORIGINAL_RECEIPT_HOOKS),
        (_WITNESS_TYPE, _CARRIER_HOOKS, _ORIGINAL_WITNESS_HOOKS),
        (_WITNESS_TYPE, _WITNESS_DENIALS, _ORIGINAL_WITNESS_DENIALS),
    ):
        if any(
            vars(cls).get(name) is not original
            for name, original in zip(names, originals, strict=True)
        ):
            raise ReadJournalRejected(
                "invalid retained witness"
                if cls is _WITNESS_TYPE else "synthetic READ carrier descriptor changed"
            )


def genesis_witness() -> ReadJournalWitness:
    """The single valid starting witness for a new, empty local journal."""
    _require_original_read_carriers()
    return ReadJournalWitness(0, _GENESIS)


def _check_witness(witness: ReadJournalWitness) -> None:
    _require_original_read_carriers()
    if type(witness) is not _WITNESS_TYPE:
        raise ReadJournalRejected("invalid retained witness")
    original_count = witness.count
    original_tip = witness.tip_sha256
    if (
        type(original_count) is not int or not 0 <= original_count <= _MAX_ROWS
        or type(original_tip) is not str or _SHA.fullmatch(original_tip) is None
    ):
        raise ReadJournalRejected("invalid retained witness")
    # A False-valued substitute is still an unreviewed authority descriptor.
    # A getter may also replace an already checked descriptor or frozen field.
    for name, descriptor in zip(
        _WITNESS_DENIALS, _ORIGINAL_WITNESS_DENIALS, strict=True,
    ):
        if (
            vars(_WITNESS_TYPE).get(name) is not descriptor
            or getattr(witness, name) is not False
            or witness.count is not original_count
            or witness.tip_sha256 is not original_tip
            or any(
                vars(_WITNESS_TYPE).get(flag) is not pinned
                for flag, pinned in zip(
                    _WITNESS_DENIALS, _ORIGINAL_WITNESS_DENIALS, strict=True,
                )
            )
        ):
            raise ReadJournalRejected("invalid retained witness")


def _check_receipt(row: ReadReceipt) -> None:
    _require_original_read_carriers()
    if (
        type(row) is not _RECEIPT_TYPE
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
        or not path.name
        or "\x00" in str(path)
    ):
        raise ReadJournalRejected("explicit absolute local Path required")
    # Main SQLite path may fit in characters while its rollback sidecar
    # exceeds the native byte limit. Refuse before any ancestor lstat/open.
    try:
        encoded_size = len(os.fsencode(path))
    except (UnicodeError, ValueError, OSError) as exc:
        raise ReadJournalRejected("READ journal path encoding invalid") from exc
    if encoded_size + len(b"-journal") > 4096:
        raise ReadJournalRejected("READ journal native path byte budget exceeded")
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
    if path.exists():
        info = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ReadJournalRejected("journal requires one regular-file link")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise ReadJournalRejected("journal parent must be an existing directory")


def _verify_schema(connection: sqlite3.Connection) -> None:
    """Bound SQL catalog hydration; require exactly the frozen local schema."""
    # Two tables and the autoindex for UNIQUE(request_id, step_id).
    # Check the count and *encoded* SQL DDL bytes in SQLite's snapshot
    # BEFORE copying foreign DDL text into Python.
    budget = connection.execute(
        "SELECT COUNT(*),COALESCE(SUM(length(CAST(sql AS BLOB))),0) "
        "FROM sqlite_master"
    ).fetchone()
    if (
        type(budget) is not tuple or len(budget) != 2
        or type(budget[0]) is not int or budget[0] != 3
        or type(budget[1]) is not int or not 0 <= budget[1] <= 4_096
    ):
        raise ReadJournalRejected("synthetic READ schema catalog preflight failed (schema changed)")
    expected = sqlite3.connect(":memory:")
    try:
        expected.execute(_MARKER_DDL)
        expected.execute(_RECEIPT_DDL)
        query = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(connection.execute(query)) != tuple(expected.execute(query)):
            raise ReadJournalRejected("synthetic READ journal schema changed")
    finally:
        expected.close()
    quick = connection.execute("PRAGMA quick_check").fetchmany(2)
    if len(quick) != 1 or tuple(quick[0]) != ("ok",):
        raise ReadJournalRejected("synthetic READ journal SQLite integrity failure")


def _require_stored_marker_admission(connection: sqlite3.Connection) -> None:
    """Reject oversized or non-TEXT revision before retrieving marker rows."""
    bad = connection.execute(
        "SELECT 1 FROM marker WHERE typeof(revision)!='text' "
        "OR length(CAST(revision AS BLOB))!=? LIMIT 1",
        (len(_SCHEMA),),
    ).fetchone()
    if bad is not None:
        raise ReadJournalRejected("synthetic READ marker hydration admission failed")


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
            try:
                connection.execute("PRAGMA busy_timeout=10000")
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(_MARKER_DDL)
                connection.execute("INSERT INTO marker VALUES (?)", (_SCHEMA,))
                connection.execute(_RECEIPT_DDL)
                connection.execute("COMMIT")
            except BaseException:
                # A failed creation must not leak the SQLite handle or imply
                # that an incomplete new file is a valid marked journal.
                # Never delete that file automatically: custody is external.
                connection.close()
                raise
            return cls(connection)
        except (FileExistsError, OSError, sqlite3.Error) as exc:
            raise ReadJournalRejected("cannot create new local journal") from exc

    @classmethod
    def open(cls, path: Path) -> DisconnectedReadJournal:
        """Reopen an existing marked journal without migrating any schema."""
        _safe_path(path, must_exist=True)
        try:
            connection = sqlite3.connect(path, timeout=10, isolation_level=None)
            try:
                connection.execute("PRAGMA busy_timeout=10000")
                # Marker, schema and chain must come from ONE SQLite snapshot.
                # No claim of cross-process custody or writer authentication.
                connection.execute("BEGIN")
                _require_stored_marker_admission(connection)
                rows = connection.execute("SELECT revision FROM marker").fetchmany(2)
                if rows != [(_SCHEMA,)]:
                    raise ReadJournalRejected("foreign journal marker")
                _verify_schema(connection)
                cls(connection)._scan()
                connection.execute("COMMIT")
            except BaseException:
                # A rejected or corrupt database must not retain its SQLite
                # handle, including on the custom rejection path.
                connection.close()
                raise
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
        _require_original_read_carriers()
        _verify_schema(self._connection)
        _require_stored_marker_admission(self._connection)
        marker = self._connection.execute("SELECT revision FROM marker").fetchmany(2)
        if marker != [(_SCHEMA,)]:
            raise ReadJournalRejected("foreign journal marker")
        # A bounded number of rows is not a bounded byte allocation.
        # Inspect all stored types and UTF-8 widths inside this same snapshot
        # BEFORE materializing even one potentially huge private receipt.
        count = self._connection.execute(
            "SELECT COUNT(*) FROM receipts"
        ).fetchone()[0]
        if type(count) is not int or not 0 <= count <= _MAX_ROWS:
            raise ReadJournalRejected("journal row budget exceeded")
        malformed = self._connection.execute(
            "SELECT 1 FROM receipts WHERE typeof(seq)!='integer' "
            "OR typeof(request_id)!='text' "
            "OR length(CAST(request_id AS BLOB))!=36 "
            "OR typeof(step_id)!='text' "
            "OR length(CAST(step_id AS BLOB))!=21 "
            "OR typeof(operation)!='text' "
            "OR length(CAST(operation AS BLOB)) NOT BETWEEN 1 AND 32 "
            "OR typeof(input_digest)!='text' "
            "OR length(CAST(input_digest AS BLOB))!=64 "
            "OR typeof(result_digest)!='text' "
            "OR length(CAST(result_digest AS BLOB))!=64 "
            "OR typeof(previous_sha)!='text' "
            "OR length(CAST(previous_sha AS BLOB))!=64 "
            "OR typeof(chain_sha)!='text' "
            "OR length(CAST(chain_sha AS BLOB))!=64 LIMIT 1"
        ).fetchone()
        if malformed is not None:
            raise ReadJournalRejected("journal receipt hydration admission failed")
        rows = self._connection.execute(
            "SELECT seq, request_id, step_id, operation, input_digest, "
            "result_digest, previous_sha, chain_sha FROM receipts ORDER BY seq"
        ).fetchmany(_MAX_ROWS + 1)
        if len(rows) > _MAX_ROWS:
            raise ReadJournalRejected("journal row budget exceeded")
        tip = _GENESIS
        seen: set[tuple[str, str]] = set()
        for i, (seq, request, step, op, inp, out, previous, stored) in enumerate(rows, 1):
            _require_original_read_carriers()
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
        _require_original_read_carriers()
        return ReadJournalWitness(len(rows), tip)

    def verify(self, retained: ReadJournalWitness) -> ReadJournalWitness:
        """Verify a stable SQLite read snapshot against caller-retained state."""
        _check_witness(retained)
        pinned = (retained.count, retained.tip_sha256)

        def stable() -> None:
            _check_witness(retained)
            if (
                type(retained) is not _WITNESS_TYPE
                or retained.count is not pinned[0]
                or retained.tip_sha256 is not pinned[1]
            ):
                raise ReadJournalRejected("retained READ witness changed during verify")

        stable()
        try:
            self._connection.execute("BEGIN")
            actual = self._scan()
            stable()
            if (
                type(actual) is not _WITNESS_TYPE
                or actual.count != pinned[0]
                or actual.tip_sha256 != pinned[1]
                or actual.dispatch_authorized is not False
                or actual.effect_proven is not False
                or actual.replay_authorized is not False
                or actual.independent_custody_proven is not False
            ):
                raise ReadJournalRejected("external witness disagrees with journal")
            self._connection.execute("COMMIT")
            # Read-only COMMIT can still be a synthetic callback boundary.
            stable()
            return actual
        except BaseException:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    def recover_receipts(self, retained: ReadJournalWitness) -> ReadJournalSnapshot:
        """Read bounded digest-only receipts under an independently pinned tip.

        This is a fixture recovery bridge, not evidence that a READ operation
        executed, not a live Planner state, and never authorization to replay.
        The caller must retain the tip outside this local SQLite database.
        """
        _require_original_snapshot_class()
        # Validate original witness slots/getters before reading either field.
        # An injected dataclass descriptor is executable, even if its value
        # resembles the retained count or tip.
        _check_witness(retained)
        retained_fields = (retained.count, retained.tip_sha256)
        connection = self._connection

        def stable() -> None:
            _require_original_snapshot_class()
            _check_witness(retained)
            if (
                type(retained) is not _WITNESS_TYPE
                or retained.count is not retained_fields[0]
                or retained.tip_sha256 is not retained_fields[1]
                or self._connection is not connection
            ):
                raise ReadJournalRejected("READ recovery witness or handle changed")

        stable()
        try:
            connection.execute("BEGIN")
            stable()
            actual = self._scan()
            stable()
            if (
                type(actual) is not _WITNESS_TYPE
                or actual.count != retained_fields[0]
                or actual.tip_sha256 != retained_fields[1]
            ):
                raise ReadJournalRejected("READ recovery retained tip mismatch")
            saved = connection.execute(
                "SELECT request_id,step_id,operation,input_digest,result_digest "
                "FROM receipts ORDER BY seq"
            ).fetchall()
            _require_original_read_carriers()
            rows = tuple(ReadReceipt(*item) for item in saved)
            if len(rows) != actual.count:
                raise ReadJournalRejected("READ recovery row count changed")
            running_tip = _GENESIS
            for index, row in enumerate(rows, 1):
                _check_receipt(row)
                running_tip = _chain(running_tip, index, row)
            if running_tip != actual.tip_sha256:
                raise ReadJournalRejected("READ recovery receipt chain changed")
            stable()
            next_scan = self._scan()
            if (
                type(next_scan) is not _WITNESS_TYPE
                or next_scan.count != actual.count
                or next_scan.tip_sha256 != actual.tip_sha256
            ):
                raise ReadJournalRejected("READ recovery snapshot changed")
            stable()
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise

        # Read-only COMMIT, result construction and denial properties may
        # invoke synthetic callbacks. Never silently rebase saved row epochs.
        stable()
        _require_original_snapshot_class()
        result = ReadJournalSnapshot(actual, rows)
        _require_original_snapshot_class()
        descriptors = _ORIGINAL_SNAPSHOT_DENIALS
        row_fields = tuple(
            (row.request_id, row.step_id, row.operation,
             row.input_digest, row.result_digest)
            for row in rows
        )

        def stable_result() -> None:
            _require_original_read_carriers()
            if (
                type(result) is not _SNAPSHOT_TYPE
                or result.witness is not actual
                or result.receipts is not rows
                or type(result.receipts) is not tuple
                or len(result.receipts) != len(rows)
                or any(
                    current is not original or type(current) is not _RECEIPT_TYPE
                    or any(now is not earlier for now, earlier in zip(
                        (current.request_id, current.step_id, current.operation,
                         current.input_digest, current.result_digest),
                        fields, strict=True,
                    ))
                    for current, original, fields in zip(
                        result.receipts, rows, row_fields, strict=True,
                    )
                )
                or any(
                    getattr(_SNAPSHOT_TYPE, name) is not descriptor
                    for name, descriptor in zip(
                        _SNAPSHOT_DENIALS, descriptors, strict=True,
                    )
                )
                or actual.count != retained_fields[0]
                or actual.tip_sha256 != retained_fields[1]
            ):
                raise ReadJournalRejected("READ recovery result changed")
            stable()

        stable_result()
        for flag in _SNAPSHOT_DENIALS:
            if getattr(result, flag) is not False:
                raise ReadJournalRejected("READ recovery gained authority")
            stable_result()
        return result

    def append(self, row: ReadReceipt, retained: ReadJournalWitness) -> ReadJournalWitness:
        """Append one synthetic READ digest with transaction-scoped CAS.

        Post-COMMIT validation is diagnostic only: a failed result must never
        imply that the SQLite append was rolled back or is safe to retry.
        """
        _check_receipt(row)
        _check_witness(retained)
        fields = (row.request_id, row.step_id, row.operation,
                  row.input_digest, row.result_digest)
        witness_epoch = (retained.count, retained.tip_sha256)

        def stable() -> None:
            _check_witness(retained)
            if (
                type(row) is not _RECEIPT_TYPE
                or type(retained) is not _WITNESS_TYPE
                or retained.count is not witness_epoch[0]
                or retained.tip_sha256 is not witness_epoch[1]
                or any(current is not earlier for current, earlier in zip(
                    (row.request_id, row.step_id, row.operation,
                     row.input_digest, row.result_digest), fields, strict=True,
                ))
            ):
                raise ReadJournalRejected("READ append carriers changed")

        stable()
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            actual = self._scan()
            stable()
            if (
                type(actual) is not _WITNESS_TYPE
                or actual.count != witness_epoch[0]
                or actual.tip_sha256 != witness_epoch[1]
                or actual.count >= _MAX_ROWS
            ):
                raise ReadJournalRejected("stale or exhausted journal witness")
            next_index = actual.count + 1
            next_tip = _chain(actual.tip_sha256, next_index, row)
            stable()
            self._connection.execute(
                "INSERT INTO receipts VALUES (?,?,?,?,?,?,?,?)",
                (next_index, *fields, actual.tip_sha256, next_tip),
            )
            stable()
            self._connection.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise ReadJournalRejected("duplicate synthetic receipt") from exc
        except BaseException:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise
        # COMMIT is durable. An invalid result or mutated caller receipt must
        # fail closed, without claiming rollback or performing an automatic retry.
        stable()
        result = ReadJournalWitness(next_index, next_tip)
        stable()
        try:
            _check_witness(result)
        except ReadJournalRejected as exc:
            raise ReadJournalRejected("post-commit READ witness changed") from exc
        if (
            type(result) is not _WITNESS_TYPE
            or type(result.count) is not int or result.count != next_index
            or type(result.tip_sha256) is not str or result.tip_sha256 != next_tip
        ):
            raise ReadJournalRejected("post-commit READ witness changed")
        stable()
        return result
