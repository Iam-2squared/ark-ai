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
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps


def _require_original_due_digest() -> None:
    """Reject substituted digest callbacks before synthetic private payload access.

    This in-process epoch check is not authenticated provenance or a sandbox.
    """
    if hashlib.sha256 is not _ORIGINAL_SHA256 or json.dumps is not _ORIGINAL_DUMPS:
        raise DueReservationRejected("due digest callback authority changed")


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


# Frozen inert result classes: injected constructors must not create
# authority-looking compatible objects or equal-valued carrier substitutions.
_WITNESS_TYPE = DueReservationWitness
_RECEIPT_TYPE = DueReservationReceipt
# A False-looking replacement property is not the reviewed, inert witness
# contract. Inspect the CLASS dictionary without running an untrusted getter.
_ORIGINAL_WITNESS_DENIAL = vars(_WITNESS_TYPE)["independent_custody_proven"]
_ORIGINAL_WITNESS_INIT = vars(_WITNESS_TYPE)["__init__"]
# Import-time class custody must precede every retained witness scalar read.
_WITNESS_FIELDS = ("count", "fingerprint")
_CARRIER_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_WITNESS_FIELDS = tuple(
    vars(_WITNESS_TYPE)[name] for name in _WITNESS_FIELDS
)
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(name) for name in _CARRIER_HOOKS
)


def _require_original_witness_denial() -> None:
    if (
        DueReservationWitness is not _WITNESS_TYPE
        or vars(_WITNESS_TYPE).get("__init__") is not _ORIGINAL_WITNESS_INIT
        or vars(_WITNESS_TYPE).get("independent_custody_proven")
        is not _ORIGINAL_WITNESS_DENIAL
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for names, originals in (
                (_WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS),
                (_CARRIER_HOOKS, _ORIGINAL_WITNESS_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise DueReservationRejected("due witness authority descriptor changed")


# Keep the original fail-closed receipt descriptors, not merely their Boolean
# values: a False-returning replacement is still an unreviewed authority epoch.
_RECEIPT_DENIALS = (
    "execution_authorized", "notification_authorized",
    "automatic_replay_authorized", "trusted_clock_verified",
)
_ORIGINAL_RECEIPT_DENIALS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_DENIALS
)
_ORIGINAL_RECEIPT_INIT = vars(_RECEIPT_TYPE)["__init__"]
_ORIGINAL_RECEIPT_POST_INIT = vars(_RECEIPT_TYPE).get("__post_init__")
_RECEIPT_FIELDS = ("occurrence_id", "due_at_ms", "reserved_at_ms", "witness")
_ORIGINAL_RECEIPT_FIELDS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_FIELDS
)
_ORIGINAL_RECEIPT_HOOKS = tuple(
    vars(_RECEIPT_TYPE).get(name) for name in _CARRIER_HOOKS
)


def _require_original_receipt_constructor() -> None:
    # A forged dataclass initializer can execute arbitrary code BEFORE the
    # later inert-receipt checks. Inspect the class dictionary statically.
    if (
        DueReservationReceipt is not _RECEIPT_TYPE
        or vars(_RECEIPT_TYPE).get("__init__") is not _ORIGINAL_RECEIPT_INIT
        or vars(_RECEIPT_TYPE).get("__post_init__") is not _ORIGINAL_RECEIPT_POST_INIT
        or any(
            vars(_RECEIPT_TYPE).get(name) is not original
            for names, originals in (
                (_RECEIPT_DENIALS, _ORIGINAL_RECEIPT_DENIALS),
                (_RECEIPT_FIELDS, _ORIGINAL_RECEIPT_FIELDS),
                (_CARRIER_HOOKS, _ORIGINAL_RECEIPT_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise DueReservationRejected("due receipt constructor authority changed")


def _checked_witness(count: int, fingerprint: str) -> DueReservationWitness:
    # Reject constructor replacement before calling an unreviewed callable.
    if DueReservationWitness is not _WITNESS_TYPE:
        raise DueReservationRejected("constructed due witness changed")
    _require_original_witness_denial()
    witness = DueReservationWitness(count, fingerprint)
    _require_original_witness_denial()
    if (
        type(witness) is not _WITNESS_TYPE
        or witness.count is not count
        or witness.fingerprint is not fingerprint
        or witness.independent_custody_proven is not False
    ):
        raise DueReservationRejected("constructed due witness changed")
    # A synthetic getter may rewrite its own class while returning False.
    _require_original_witness_denial()
    return witness


def _digest(rows: tuple[tuple[object, ...], ...]) -> str:
    _require_original_due_digest()
    payload = json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    _require_original_due_digest()
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    _require_original_due_digest()
    return digest


def genesis_due_witness() -> DueReservationWitness:
    return _checked_witness(0, _digest(()))


def _check_witness(witness: object) -> None:
    _require_original_witness_denial()
    if (
        type(witness) is not _WITNESS_TYPE
        or type(witness.count) is not int
        or not 0 <= witness.count <= _MAX_ROWS
        or type(witness.fingerprint) is not str
        or _SHA.fullmatch(witness.fingerprint) is None
        or witness.independent_custody_proven is not False
    ):
        raise DueReservationRejected("invalid independently retained due witness")
    _require_original_witness_denial()


def _check_path(path: object, *, exists: bool) -> Path:
    _require_original_due_digest()
    if (
        type(path) is not type(Path("."))
        or len(str(path)) > 4096
        or not path.is_absolute()
        or ".." in path.parts
    ):
        raise DueReservationRejected("absolute local fixture Path required")
    # Checking only path.parent.is_symlink() accepts a redirected grandparent.
    # Validate every ancestor before SQLite opens or creates a fixture file.
    # No filesystem path check alone can eliminate concurrent path swaps.
    try:
        for parent in path.parents:
            info = parent.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise DueReservationRejected("due ancestor is not a real directory")
    except OSError as exc:
        raise DueReservationRejected("due ancestor unavailable") from exc
    try:
        main = path.lstat()
    except FileNotFoundError:
        main_exists = False
        if exists:
            raise DueReservationRejected("missing or symbolic due ledger") from None
    except OSError as exc:
        raise DueReservationRejected("due ledger metadata unavailable") from exc
    else:
        main_exists = True
        if not stat.S_ISREG(main.st_mode) or main.st_nlink != 1:
            raise DueReservationRejected("due ledger requires one regular-file link")
    # Refuse orphaned or aliased WAL/SHM/journal paths BEFORE SQLite opens,
    # including during a new ledger bootstrap. This is only best-effort
    # lexical custody; it does not eliminate concurrent path swaps.
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = path.with_name(path.name + suffix)
        try:
            info = sidecar.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise DueReservationRejected("due sidecar metadata unavailable") from exc
        if (
            not main_exists or not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
        ):
            raise DueReservationRejected("unsafe or orphaned due SQLite sidecar")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise DueReservationRejected("due ledger parent must be a real directory")
    return path


def _schema(conn: sqlite3.Connection) -> None:
    _require_original_due_digest()
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
    _require_original_due_digest()
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
    return _checked_witness(len(rows), _digest(rows)), last_reserved


class DisconnectedDueReservations:
    """Fixture SQLite reservations, never an actual autonomous scheduler."""

    def __init__(self, path: Path, *, require_existing: bool = False) -> None:
        # Only explicit fixture creation may take write intent. Existing-only
        # restart opens SQLite in read-only mode with a read transaction:
        # neither bootstrap/migration nor a RESERVED writer lock is allowed.
        if type(require_existing) is not bool:
            raise DueReservationRejected("exact existing-only flag required")
        self._path = _check_path(path, exists=require_existing)
        mode = "ro" if require_existing else "rwc"
        with closing(sqlite3.connect(
            self._path.as_uri() + "?mode=" + mode,
            uri=True, timeout=10, isolation_level=None,
        )) as conn:
            conn.execute("BEGIN" if require_existing else "BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if require_existing:
                        raise DueReservationRejected("uninitialized due ledger on restart")
                    if tuple(conn.execute("SELECT name FROM sqlite_master")):
                        raise DueReservationRejected("unversioned nonempty due ledger")
                    conn.execute(_DDL)
                    conn.execute("PRAGMA user_version=1")
                inspected, _ = _inspect(conn)
                _check_witness(inspected)
                if self._path is not path:
                    raise DueReservationRejected("due ledger path changed")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    @classmethod
    def reopen_with_witness(
        cls, path: Path, *, retained: DueReservationWitness,
    ) -> DisconnectedDueReservations:
        """Read-only restart reconciliation before any new due reservation.

        A separately retained caller witness is necessary but does not prove
        independent custody, trusted time, consent, or execution authority.
        """
        if cls is not DisconnectedDueReservations:
            raise DueReservationRejected("exact due ledger restart class required")
        _check_witness(retained)
        epoch = (retained.count, retained.fingerprint)
        store = cls(path, require_existing=True)
        with closing(store._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                actual, _ = _inspect(conn)
                _check_witness(actual)
                # The caller-held witness can be reflectively changed while
                # the independent SQLite snapshot is inspected. A retained
                # tip is never permission, even if its digest still matches.
                _check_witness(retained)
                if (
                    type(retained) is not _WITNESS_TYPE
                    or retained.count is not epoch[0]
                    or retained.fingerprint is not epoch[1]
                    or actual.count != epoch[0]
                    or actual.fingerprint != epoch[1]
                    or store._path is not path
                ):
                    raise DueReservationRejected("retained due witness differs on restart")
                conn.commit()
                _check_witness(retained)
            except BaseException:
                conn.rollback()
                raise
        _check_witness(retained)
        if store._path is not path:
            raise DueReservationRejected("due ledger source changed after restart")
        return store

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
                _check_witness(result)
                if self._path is not source:
                    raise DueReservationRejected("due ledger source changed during read")
                conn.commit()
                _check_witness(result)
                if self._path is not source:
                    raise DueReservationRejected("due ledger source changed after read")
                return result
            except BaseException:
                conn.rollback()
                raise

    def reserve_due(
        self, *, policy_sha256: str, due_at_ms: int,
        observed_now_ms: int, retained: DueReservationWitness,
    ) -> DueReservationReceipt:
        """Persist one synthetic reservation, then return a non-executing receipt."""
        _require_original_due_digest()
        if (
            type(policy_sha256) is not str or _SHA.fullmatch(policy_sha256) is None
            or type(due_at_ms) is not int or type(observed_now_ms) is not int
            or not 0 <= due_at_ms <= observed_now_ms <= _MAX_MS
            or observed_now_ms - due_at_ms > _MAX_LATENESS_MS
        ):
            raise DueReservationRejected("invalid or stale caller-asserted due claim")
        _require_original_receipt_constructor()
        _check_witness(retained)
        prior_epoch = (retained.count, retained.fingerprint)
        path_epoch = self._path

        def assert_retained_epoch() -> None:
            _require_original_receipt_constructor()
            # The retained witness must remain non-authorizing throughout
            # every callback/transaction boundary, not just at entry.
            # Report a changed custody *carrier* before checking semantic
            # validity. Both must fail closed; this distinction also makes a
            # float/count substitution unambiguously a custody-epoch drift.
            if (
                type(retained) is not _WITNESS_TYPE
                or retained.count is not prior_epoch[0]
                or retained.fingerprint is not prior_epoch[1]
                or self._path is not path_epoch
            ):
                raise DueReservationRejected("retained due custody changed")
            _check_witness(retained)

        assert_retained_epoch()
        _require_original_due_digest()
        identity = "slot_" + hashlib.sha256(
            _DOMAIN + (policy_sha256 + ":" + str(due_at_ms)).encode("ascii")
        ).hexdigest()
        _require_original_due_digest()
        assert_retained_epoch()
        with closing(self._open(read_only=False)) as conn:
            assert_retained_epoch()
            conn.execute("BEGIN IMMEDIATE")
            assert_retained_epoch()
            try:
                current, last = _inspect(conn)
                _check_witness(current)
                assert_retained_epoch()
                if (
                    current.count != prior_epoch[0]
                    or current.fingerprint != prior_epoch[1]
                ):
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
                _check_witness(result)
                assert_retained_epoch()
                if (
                    type(result) is not _WITNESS_TYPE
                    or result.count != current.count + 1
                    or result.independent_custody_proven is not False
                ):
                    raise DueReservationRejected("unverified due reservation insert")
                result_epoch = (result.count, result.fingerprint)
                conn.commit()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise DueReservationRejected("duplicate synthetic due occurrence") from exc
            except BaseException:
                conn.rollback()
                raise
        def assert_committed_witness() -> None:
            _require_original_witness_denial()
            if (
                type(result) is not _WITNESS_TYPE
                or result.count is not result_epoch[0]
                or result.fingerprint is not result_epoch[1]
                or result.independent_custody_proven is not False
            ):
                raise DueReservationRejected("post-commit due witness changed")
            _require_original_witness_denial()

        assert_retained_epoch()
        assert_committed_witness()
        # This is post-COMMIT: a forged result is rejected, never silently
        # described as a rolled-back reservation or retried as a new WRITE.
        _require_original_receipt_constructor()
        receipt = _RECEIPT_TYPE(identity, due_at_ms, observed_now_ms, result)
        assert_retained_epoch()
        assert_committed_witness()
        def assert_receipt() -> None:
            _require_original_receipt_constructor()
            if (
                type(receipt) is not _RECEIPT_TYPE
                or receipt.occurrence_id is not identity
                or receipt.due_at_ms is not due_at_ms
                or receipt.reserved_at_ms is not observed_now_ms
                or receipt.witness is not result
                or any(
                    vars(_RECEIPT_TYPE).get(name) is not original
                    for name, original in zip(
                        _RECEIPT_DENIALS, _ORIGINAL_RECEIPT_DENIALS, strict=True,
                    )
                )
            ):
                raise DueReservationRejected("constructed due reservation receipt changed")

        assert_receipt()
        for name in _RECEIPT_DENIALS:
            if getattr(receipt, name) is not False:
                raise DueReservationRejected("constructed due reservation receipt changed")
            # A malicious property can swap a previously checked descriptor or
            # replace a frozen receipt scalar while returning a plausible False.
            assert_receipt()
            assert_committed_witness()
            assert_retained_epoch()
        assert_receipt()
        return receipt
