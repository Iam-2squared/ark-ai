"""Separate local SQLite witness history for disconnected Memory epoch observations.

This opt-in fixture stores only metadata digests/counts, never Memory content.
Its external caller-retained CAS witness detects local rollback/rewrite, but the
caller and SQLite writer are NOT independently authenticated. Appended event
prefixes are NOT proven authentic. No Memory v1 schema change or tool dispatch.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import stat
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .atomic_epoch_review import AtomicMemoryEpochReview
from .contracts import MemorySchemaError
from .retained_epoch_review import _validate, review_retained_memory_epoch

_DOMAIN = b"ARK-disconnected-memory-witness-ledger-v1\\0"
_MAX_EPOCHS = 256
_DDL = (
    "CREATE TABLE retained_memory_epochs ("
    "seq INTEGER PRIMARY KEY, payload_json TEXT NOT NULL, "
    "status TEXT NOT NULL, chain_sha256 TEXT NOT NULL)"
)


class MemoryWitnessLedgerRejected(MemorySchemaError):
    """The synthetic local witness history failed closed."""


@dataclass(frozen=True, slots=True)
class MemoryLedgerWitness:
    epochs: int
    chain_sha256: str

    @property
    def custody_authenticated(self) -> bool:
        return False

    @property
    def independent_writer_proven(self) -> bool:
        return False

    @property
    def historical_prefix_proven(self) -> bool:
        return False

    @property
    def memory_disclosure_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False


_WITNESS_TYPE = MemoryLedgerWitness
_REVIEW_TYPE = AtomicMemoryEpochReview


def _digest(data: object) -> str:
    payload = json.dumps(
        data, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + payload).hexdigest()


def genesis_memory_ledger_witness() -> MemoryLedgerWitness:
    return MemoryLedgerWitness(0, _digest(("genesis",)))


def _path(path: object, *, create: bool) -> Path:
    if (
        type(path) is not type(Path("."))
        or not path.is_absolute()
        or ".." in path.parts
        or len(str(path)) > 4096
        or path.name in ("", ".", "..")
    ):
        raise MemoryWitnessLedgerRejected("exact absolute ledger path required")
    try:
        for parent in path.parents:
            info = parent.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise MemoryWitnessLedgerRejected("unsafe ledger ancestor")
        try:
            info = path.lstat()
        except FileNotFoundError:
            if not create:
                raise MemoryWitnessLedgerRejected("missing retained ledger") from None
        else:
            if create or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise MemoryWitnessLedgerRejected("existing or aliased ledger")
    except OSError as exc:
        raise MemoryWitnessLedgerRejected("ledger path cannot be inspected") from exc
    return path


def _schema(conn: sqlite3.Connection) -> None:
    try:
        if conn.execute("PRAGMA user_version").fetchone() != (1,):
            raise MemoryWitnessLedgerRejected("unknown witness schema version")
        with closing(sqlite3.connect(":memory:")) as expected:
            expected.execute(_DDL)
            query = (
                "SELECT type,name,tbl_name,sql FROM sqlite_master "
                "ORDER BY type,name"
            )
            if tuple(conn.execute(query)) != tuple(expected.execute(query)):
                raise MemoryWitnessLedgerRejected("witness schema drift")
        if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise MemoryWitnessLedgerRejected("witness database integrity failed")
    except sqlite3.Error as exc:
        raise MemoryWitnessLedgerRejected("invalid local witness database") from exc


def _payload(review: AtomicMemoryEpochReview) -> str:
    parts = _validate(review)
    return json.dumps(
        parts, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    )


def _decoded(raw: object) -> AtomicMemoryEpochReview:
    if type(raw) is not str or len(raw) > 4096:
        raise MemoryWitnessLedgerRejected("invalid witness epoch payload")
    # The 4KiB byte budget alone does not bound JSON container depth.
    # Reject pathological nesting deterministically on every Python/OS,
    # before decoder recursion limits are reached. Quoted brackets do not
    # contribute to the container depth.
    depth = 0
    quoted = False
    escaped = False
    for char in raw:
        if quoted:
            if escaped:
                escaped = False
            elif char == chr(92):
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > 64:
                raise MemoryWitnessLedgerRejected("witness JSON nesting budget exceeded")
        elif char in "]}":
            depth -= 1
    try:
        parsed = json.loads(raw)
        if (
            type(parsed) is not list
            or len(parsed) != 6
            or any(type(part) is not list for part in parsed[:4])
        ):
            raise MemoryWitnessLedgerRejected("invalid witness epoch structure")
        review = AtomicMemoryEpochReview(
            *(tuple(part) for part in parsed[:4]), parsed[4], parsed[5],
        )
        if _payload(review) != raw:
            raise MemoryWitnessLedgerRejected("witness epoch is not canonical")
        return review
    except (TypeError, ValueError, MemorySchemaError, RecursionError) as exc:
        raise MemoryWitnessLedgerRejected("invalid persisted witness epoch") from exc


def _inspect(
    conn: sqlite3.Connection,
) -> tuple[MemoryLedgerWitness, AtomicMemoryEpochReview | None]:
    _schema(conn)
    witness = genesis_memory_ledger_witness()
    previous = None
    try:
        rows = conn.execute(
            "SELECT seq,payload_json,status,chain_sha256 "
            "FROM retained_memory_epochs ORDER BY seq LIMIT ?",
            (_MAX_EPOCHS + 1,),
        )
        for seq, payload, status, chain in rows:
            if (
                witness.epochs >= _MAX_EPOCHS
                or type(seq) is not int
                or seq != witness.epochs + 1
                or type(status) is not str
                or type(chain) is not str
            ):
                raise MemoryWitnessLedgerRejected("invalid witness sequence")
            review = _decoded(payload)
            if previous is None:
                expected_status = "BASELINE_UNAUTHENTICATED"
            else:
                expected_status = review_retained_memory_epoch(previous, review).status
            wanted = _digest(("epoch", witness.chain_sha256, seq, payload, expected_status))
            if status != expected_status or chain != wanted:
                raise MemoryWitnessLedgerRejected("retained witness history rewritten")
            previous = review
            witness = MemoryLedgerWitness(seq, wanted)
    except sqlite3.Error as exc:
        raise MemoryWitnessLedgerRejected("cannot read retained witness history") from exc
    return witness, previous


def _check_witness(value: object) -> None:
    if (
        type(value) is not _WITNESS_TYPE
        or type(value.epochs) is not int
        or not 0 <= value.epochs <= _MAX_EPOCHS
        or type(value.chain_sha256) is not str
        or len(value.chain_sha256) != 64
        or any(ch not in "0123456789abcdef" for ch in value.chain_sha256)
        or value.custody_authenticated is not False
        or value.independent_writer_proven is not False
        or value.historical_prefix_proven is not False
        or value.memory_disclosure_authorized is not False
        or value.dispatch_authorized is not False
    ):
        raise MemoryWitnessLedgerRejected("invalid retained witness or authority")


class DisconnectedMemoryWitnessLedger:
    """An opt-in non-authorizing local CAS witness store; not an audit trust root."""

    def __init__(self, path: Path, *, create: bool = False) -> None:
        if type(create) is not bool:
            raise MemoryWitnessLedgerRejected("explicit create flag required")
        self._path = _path(path, create=create)
        source = self._path
        if create:
            try:
                with path.open("xb"):
                    pass
            except OSError as exc:
                raise MemoryWitnessLedgerRejected("ledger already exists or unsafe") from exc
        # Existing witness histories are inspected, never migrated. Do not
        # acquire a RESERVED SQLite writer lock merely to reopen a ledger.
        # Explicit create=True retains its separate write/bootstrap path.
        with closing(self._open(read_only=not create)) as conn:
            conn.execute("BEGIN IMMEDIATE" if create else "BEGIN")
            try:
                if create:
                    if (
                        conn.execute("PRAGMA user_version").fetchone() != (0,)
                        or tuple(conn.execute("SELECT name FROM sqlite_master"))
                    ):
                        raise MemoryWitnessLedgerRejected("new witness ledger not empty")
                    conn.execute(_DDL)
                    conn.execute("PRAGMA user_version=1")
                inspected, _ = _inspect(conn)
                _check_witness(inspected)
                if self._path is not source:
                    raise MemoryWitnessLedgerRejected("witness startup path changed")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _open(self, *, read_only: bool) -> sqlite3.Connection:
        safe = _path(self._path, create=False)
        mode = "ro" if read_only else "rw"
        try:
            return sqlite3.connect(
                safe.as_uri() + "?mode=" + mode,
                uri=True, timeout=10, isolation_level=None,
            )
        except sqlite3.Error as exc:
            raise MemoryWitnessLedgerRejected("cannot open witness ledger") from exc

    def inspect(self, *, retained: MemoryLedgerWitness) -> MemoryLedgerWitness:
        """Require the exact previously retained chain tip; never auto-repair."""
        _check_witness(retained)
        original_path = self._path
        original = (retained.epochs, retained.chain_sha256)

        def stable() -> None:
            # SQLite callbacks and an OS open can re-enter fixture code. An
            # equal-valued Path or witness substitution is not the same epoch.
            if (
                self._path is not original_path
                or type(retained) is not _WITNESS_TYPE
                or retained.epochs is not original[0]
                or retained.chain_sha256 is not original[1]
            ):
                raise MemoryWitnessLedgerRejected("retained Memory witness carrier changed")

        stable()
        with closing(self._open(read_only=True)) as conn:
            stable()
            conn.execute("BEGIN")
            stable()
            try:
                observed, _ = _inspect(conn)
                stable()
                _check_witness(observed)
                if observed != retained:
                    raise MemoryWitnessLedgerRejected("retained witness mismatch")
                conn.commit()
                stable()
            except BaseException:
                conn.rollback()
                raise
        stable()
        _check_witness(observed)
        return observed

    def append(
        self, review: AtomicMemoryEpochReview, *,
        retained: MemoryLedgerWitness,
    ) -> MemoryLedgerWitness:
        """Serialize one metadata observation via SQLite CAS; no Memory writes."""
        _check_witness(retained)
        if type(review) is not _REVIEW_TYPE:
            raise MemoryWitnessLedgerRejected("exact local Memory epoch required")
        old_fields = _validate(review)
        old_tip = (retained.epochs, retained.chain_sha256)
        original_path = self._path

        def stable() -> None:
            try:
                # Recheck denied authority on every callback boundary, not
                # only at entry or after a locally committed append.
                _check_witness(retained)
                unchanged = (
                    type(review) is _REVIEW_TYPE
                    and all(
                        a is b
                        for a, b in zip(_validate(review), old_fields, strict=True)
                    )
                    and self._path is original_path
                    and (retained.epochs, retained.chain_sha256) == old_tip
                    and retained.epochs is old_tip[0]
                    and retained.chain_sha256 is old_tip[1]
                )
            except (MemorySchemaError, AttributeError, TypeError) as exc:
                raise MemoryWitnessLedgerRejected("Memory witness inputs changed") from exc
            if not unchanged:
                raise MemoryWitnessLedgerRejected("Memory witness inputs changed")

        stable()
        payload = _payload(review)
        stable()
        with closing(self._open(read_only=False)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                observed, last = _inspect(conn)
                # A callback may change the caller's retained authority while
                # the SQLite row is being inspected. Check caller custody first,
                # then independently validate the observed witness before CAS.
                stable()
                _check_witness(observed)
                stable()
                if observed != retained:
                    raise MemoryWitnessLedgerRejected("stale witness CAS tip")
                if observed.epochs >= _MAX_EPOCHS:
                    raise MemoryWitnessLedgerRejected("witness history budget exceeded")
                status = (
                    "BASELINE_UNAUTHENTICATED" if last is None
                    else review_retained_memory_epoch(last, review).status
                )
                stable()
                seq = observed.epochs + 1
                new_sha = _digest(("epoch", observed.chain_sha256, seq, payload, status))
                conn.execute(
                    "INSERT INTO retained_memory_epochs VALUES (?,?,?,?)",
                    (seq, payload, status, new_sha),
                )
                stable()
                inspected, _ = _inspect(conn)
                _check_witness(inspected)
                if inspected != MemoryLedgerWitness(seq, new_sha):
                    raise MemoryWitnessLedgerRejected("witness insert changed")
                stable()
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        # If a post-commit callback mutates inputs, report uncertainty and
        # never pretend the completed SQLite commit was rolled back.
        stable()
        result = MemoryLedgerWitness(seq, new_sha)
        _check_witness(result)
        stable()
        return result
