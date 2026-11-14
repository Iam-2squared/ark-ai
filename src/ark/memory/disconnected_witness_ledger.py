"""Separate local SQLite witness history for disconnected Memory epoch observations.

This opt-in fixture stores only metadata digests/counts, never Memory content.
Its external caller-retained CAS witness detects local rollback/rewrite, but the
caller and SQLite writer are NOT independently authenticated. Appended event
prefixes are NOT proven authentic. No Memory v1 schema change or tool dispatch.
"""

from __future__ import annotations

import hashlib
import json
import os
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
_MAX_SQLITE_PATH_BYTES = 4096
_MAX_SCHEMA_DDL_BYTES = 4096
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
    expected = _digest(("genesis",))
    witness = MemoryLedgerWitness(0, expected)
    # A synthetic constructor or modified descriptor must not elevate the
    # standalone genesis receipt into custody, disclosure or Tool authority.
    _check_witness(witness)
    if witness.epochs != 0 or witness.chain_sha256 != expected:
        raise MemoryWitnessLedgerRejected("Memory genesis witness changed")
    return witness


def _path(path: object, *, create: bool) -> Path:
    # Fail closed before lstat or SQLite connects: journal siblings are longer
    # than the main name, and POSIX/Windows enforce native byte budgets.
    if (
        type(path) is not type(Path("."))
        or not path.is_absolute()
        or ".." in path.parts
        or "\x00" in str(path)
        or path.name in ("", ".", "..")
    ):
        raise MemoryWitnessLedgerRejected("exact absolute ledger path required")
    try:
        encoded_length = len(os.fsencode(path))
    except (UnicodeError, ValueError, OSError) as exc:
        raise MemoryWitnessLedgerRejected("witness ledger path encoding invalid") from exc
    if encoded_length + len(b"-journal") > _MAX_SQLITE_PATH_BYTES:
        raise MemoryWitnessLedgerRejected("witness ledger path byte budget exceeded")
    try:
        for parent in path.parents:
            info = parent.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise MemoryWitnessLedgerRejected("unsafe ledger ancestor")
        main_missing = False
        try:
            info = path.lstat()
        except FileNotFoundError:
            main_missing = True
            if not create:
                raise MemoryWitnessLedgerRejected("missing retained ledger") from None
        else:
            if create or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise MemoryWitnessLedgerRejected("existing or aliased ledger")
        # Refuse orphan, symlink, multi-linked or non-file SQLite sidecars.
        # This is only an lstat preflight, NOT race-free pathname custody.
        for suffix in ("-wal", "-shm", "-journal"):
            companion = path.with_name(path.name + suffix)
            try:
                sidecar = companion.lstat()
            except FileNotFoundError:
                continue
            if (
                main_missing or create or not stat.S_ISREG(sidecar.st_mode)
                or sidecar.st_nlink != 1
            ):
                raise MemoryWitnessLedgerRejected("unsafe witness SQLite sidecar")
    except OSError as exc:
        raise MemoryWitnessLedgerRejected("ledger path cannot be inspected") from exc
    return path


def _schema(conn: sqlite3.Connection) -> None:
    try:
        if conn.execute("PRAGMA user_version").fetchone() != (1,):
            raise MemoryWitnessLedgerRejected("unknown witness schema version")
        # SQL-side admission bounds catalog hydration within the SAME SQLite
        # read/write transaction. Exactly one table is the original DDL.
        objects, ddl_bytes = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(length(CAST(sql AS BLOB))), 0) "
            "FROM sqlite_master"
        ).fetchone()
        if (
            type(objects) is not int or objects != 1
            or type(ddl_bytes) is not int
            or not 0 <= ddl_bytes <= _MAX_SCHEMA_DDL_BYTES
        ):
            raise MemoryWitnessLedgerRejected("witness schema drift")
        with closing(sqlite3.connect(":memory:")) as expected:
            expected.execute(_DDL)
            query = (
                "SELECT type,name,tbl_name,sql FROM sqlite_master "
                "ORDER BY type,name"
            )
            if tuple(conn.execute(query)) != tuple(expected.execute(query)):
                raise MemoryWitnessLedgerRejected("witness schema drift")
        if conn.execute("PRAGMA quick_check").fetchmany(2) != [("ok",)]:
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
    # Reject oversized or mistyped persisted rows while they are still inside
    # SQLite. The existing 257-row SELECT must never hydrate attacker-sized
    # TEXT/BLOB values or trust a row count truncated by its LIMIT.
    admission = conn.execute(
        "SELECT COUNT(*), "
        "COALESCE(SUM(length(CAST(payload_json AS BLOB))),0), "
        "COALESCE(MAX(length(CAST(payload_json AS BLOB))),0), "
        "COALESCE(MAX(length(CAST(status AS BLOB))),0), "
        "COALESCE(MAX(length(CAST(chain_sha256 AS BLOB))),0), "
        "COALESCE(SUM(CASE WHEN typeof(payload_json)!='text' "
        "OR typeof(status)!='text' OR typeof(chain_sha256)!='text' "
        "THEN 1 ELSE 0 END),0) "
        "FROM retained_memory_epochs"
    ).fetchone()
    if (
        type(admission) is not tuple or len(admission) != 6
        or any(type(value) is not int for value in admission)
        or not 0 <= admission[0] <= _MAX_EPOCHS
        or not 0 <= admission[1] <= _MAX_EPOCHS * 4096
        or not 0 <= admission[2] <= 4096
        or not 0 <= admission[3] <= 128
        or not 0 <= admission[4] <= 64
        or admission[5] != 0
    ):
        raise MemoryWitnessLedgerRejected("witness history admission failed")
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
            _check_witness(witness)
            if witness.epochs != seq or witness.chain_sha256 != wanted:
                raise MemoryWitnessLedgerRejected("Memory history witness changed")
    except sqlite3.Error as exc:
        raise MemoryWitnessLedgerRejected("cannot read retained witness history") from exc
    _check_witness(witness)
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
                    # Probe existence inside the bootstrap transaction without
                    # allocating a Python tuple of foreign SQLite catalog rows.
                    if (
                        conn.execute("PRAGMA user_version").fetchone() != (0,)
                        or (
                            conn.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone()
                            is not None
                        )
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
                # Dataclass equality is replaceable; pin the read-only tip scalars.
                if (
                    observed.epochs != original[0]
                    or observed.chain_sha256 != original[1]
                ):
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
                # The SQLite CAS tip is independent of patched witness __eq__.
                if (
                    observed.epochs != old_tip[0]
                    or observed.chain_sha256 != old_tip[1]
                ):
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
                # Verify the in-transaction appended chain by exact scalars.
                if inspected.epochs != seq or inspected.chain_sha256 != new_sha:
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
