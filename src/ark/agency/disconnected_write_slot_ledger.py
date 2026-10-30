"""Persistent, disconnected WRITE occurrence *reservation* fixture.

A SQLite UNIQUE constraint and BEGIN IMMEDIATE serialize local reservations,
not external effects. Claims and independently retained witnesses are caller
controlled: neither proves user identity, consent, trusted time, tool permission,
file/WAL custody, or an exactly-once side effect. A crash after commit but
before witness retention deliberately blocks further writes pending review.
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

_PLAN = re.compile(r"plan_[0-9a-f]{64}\Z")
_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_SLOT = re.compile(r"slot_[0-9a-f]{64}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_ROWS = 512
_MAX_BATCH = 16
_DOMAIN = b"ARK-disconnected-durable-write-slot-v1\0"
_DDL = (
    "CREATE TABLE synthetic_write_slots ("
    "seq INTEGER PRIMARY KEY, slot_id TEXT NOT NULL UNIQUE, "
    "plan_id TEXT NOT NULL, step_id TEXT NOT NULL, "
    "request_sha256 TEXT NOT NULL, chain_sha256 TEXT NOT NULL, "
    "UNIQUE(plan_id, step_id))"
)


class WriteSlotLedgerRejected(ValueError):
    """The synthetic reservation or retained ledger epoch is not acceptable."""


@dataclass(frozen=True, slots=True)
class DetachedWriteSlotClaim:
    slot_id: str = field(repr=False)
    plan_id: str = field(repr=False)
    step_id: str = field(repr=False)
    request_sha256: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class WriteSlotLedgerWitness:
    count: int
    chain_sha256: str

    @property
    def independently_authenticated(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class WriteSlotReservationReceipt:
    added_count: int
    witness: WriteSlotLedgerWitness

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def exact_once_external_effect_proven(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def owner_or_consent_verified(self) -> bool:
        return False


_RECEIPT_TYPE = WriteSlotReservationReceipt
_WITNESS_TYPE = WriteSlotLedgerWitness


def _hash(value: tuple[object, ...]) -> str:
    encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(_DOMAIN + encoded).hexdigest()


def genesis_write_slot_witness() -> WriteSlotLedgerWitness:
    return WriteSlotLedgerWitness(0, _hash(("genesis",)))


def _valid(value: object, pattern: re.Pattern[str]) -> bool:
    return type(value) is str and pattern.fullmatch(value) is not None


def derive_disconnected_write_slot_id(
    plan_id: str, step_id: str, request_sha256: str,
) -> str:
    """Compute a claim ID; computing it does not authorize or reserve a WRITE."""
    if not (_valid(plan_id, _PLAN) and _valid(step_id, _STEP)
            and _valid(request_sha256, _SHA)):
        raise WriteSlotLedgerRejected("invalid exact WRITE identity")
    return "slot_" + _hash(("slot", plan_id, step_id, request_sha256))


def _check_witness(value: object) -> None:
    if (type(value) is not _WITNESS_TYPE
            or type(value.count) is not int or not 0 <= value.count <= _MAX_ROWS
            or not _valid(value.chain_sha256, _SHA)
            or value.independently_authenticated is not False):
        raise WriteSlotLedgerRejected("invalid retained witness")


def _check_path(value: object, *, create: bool) -> Path:
    if (type(value) is not type(Path(".")) or not value.is_absolute()
            or ".." in value.parts or len(str(value)) > 4096
            or value.name in ("", ".", "..")):
        raise WriteSlotLedgerRejected("exact absolute fixture path required")
    try:
        for ancestor in value.parents:
            info = ancestor.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise WriteSlotLedgerRejected("unsafe SQLite ancestor")
        try:
            info = value.lstat()
        except FileNotFoundError:
            if not create:
                raise WriteSlotLedgerRejected("missing durable reservation ledger") from None
        else:
            if create or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise WriteSlotLedgerRejected("existing or aliased SQLite path")
    except OSError as exc:
        raise WriteSlotLedgerRejected("SQLite fixture path unavailable") from exc
    return value


def _schema(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone() != (1,):
        raise WriteSlotLedgerRejected("unknown SQLite ledger version")
    with closing(sqlite3.connect(":memory:")) as expected:
        expected.execute(_DDL)
        query = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(conn.execute(query)) != tuple(expected.execute(query)):
            raise WriteSlotLedgerRejected("reservation schema drift")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise WriteSlotLedgerRejected("reservation SQLite integrity failure")


def _inspect(conn: sqlite3.Connection) -> WriteSlotLedgerWitness:
    _schema(conn)
    witness = genesis_write_slot_witness()
    seen: set[tuple[str, str]] = set()
    for seq, slot, plan, step, request, chain in conn.execute(
        "SELECT seq,slot_id,plan_id,step_id,request_sha256,chain_sha256 "
        "FROM synthetic_write_slots ORDER BY seq"
    ):
        if (witness.count >= _MAX_ROWS or type(seq) is not int
                or seq != witness.count + 1 or not _valid(slot, _SLOT)
                or not _valid(plan, _PLAN) or not _valid(step, _STEP)
                or not _valid(request, _SHA) or not _valid(chain, _SHA)
                or (plan, step) in seen
                or slot != derive_disconnected_write_slot_id(plan, step, request)):
            raise WriteSlotLedgerRejected("invalid persisted reservation row")
        wanted = _hash(("row", witness.chain_sha256, seq, slot, plan, step, request))
        if chain != wanted:
            raise WriteSlotLedgerRejected("reservation history changed")
        seen.add((plan, step))
        witness = WriteSlotLedgerWitness(seq, chain)
    return witness


class DisconnectedWriteSlotLedger:
    """A synthetic local uniqueness ledger, never a WRITE execution gate."""

    def __init__(self, path: Path, *, create: bool = False) -> None:
        if type(create) is not bool:
            raise WriteSlotLedgerRejected("explicit exact create flag required")
        self._path = _check_path(path, create=create)
        # Reopening a persisted WRITE slot ledger only inspects its history.
        # The explicit create branch alone may take a write/bootstrap lock.
        mode = "rwc" if create else "ro"
        with closing(sqlite3.connect(
            self._path.as_uri() + "?mode=" + mode,
            uri=True, timeout=10, isolation_level=None,
        )) as conn:
            conn.execute("BEGIN IMMEDIATE" if create else "BEGIN")
            try:
                if create:
                    if (conn.execute("PRAGMA user_version").fetchone() != (0,)
                            or tuple(conn.execute("SELECT name FROM sqlite_master"))):
                        raise WriteSlotLedgerRejected("nonempty new ledger")
                    conn.execute(_DDL)
                    conn.execute("PRAGMA user_version=1")
                _inspect(conn)
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _open(self, *, read_only: bool) -> sqlite3.Connection:
        path = _check_path(self._path, create=False)
        mode = "ro" if read_only else "rw"
        return sqlite3.connect(path.as_uri() + "?mode=" + mode, uri=True,
                               timeout=10, isolation_level=None)

    def inspect(self, *, retained: WriteSlotLedgerWitness) -> WriteSlotLedgerWitness:
        """Compare an independently retained caller witness; never recreate missing DB."""
        _check_witness(retained)
        original = (retained.count, retained.chain_sha256)
        with closing(self._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                actual = _inspect(conn)
                if actual != retained or original != (retained.count, retained.chain_sha256):
                    raise WriteSlotLedgerRejected("stale or changed retained history")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        return actual

    def reserve_many(
        self, claims: tuple[DetachedWriteSlotClaim, ...], *, retained: WriteSlotLedgerWitness,
    ) -> WriteSlotReservationReceipt:
        """Atomically record 1-16 synthetic identities, without executing any action."""
        if (type(claims) is not tuple or not 1 <= len(claims) <= _MAX_BATCH
                or any(type(claim) is not DetachedWriteSlotClaim for claim in claims)):
            raise WriteSlotLedgerRejected("exact bounded synthetic claim tuple required")
        _check_witness(retained)
        saved = tuple((c.slot_id, c.plan_id, c.step_id, c.request_sha256) for c in claims)
        old_witness = (retained.count, retained.chain_sha256)
        if len(set(saved)) != len(saved):
            raise WriteSlotLedgerRejected("duplicate identities in batch")
        for slot, plan, step, request in saved:
            if (not _valid(slot, _SLOT) or not _valid(plan, _PLAN)
                    or not _valid(step, _STEP) or not _valid(request, _SHA)
                    or slot != derive_disconnected_write_slot_id(plan, step, request)):
                raise WriteSlotLedgerRejected("invalid synthetic reservation claim")

        def stable() -> None:
            if (
                old_witness != (retained.count, retained.chain_sha256)
                or retained.count is not old_witness[0]
                or retained.chain_sha256 is not old_witness[1]
                or any(
                    c is not old
                    or (c.slot_id, c.plan_id, c.step_id, c.request_sha256) != values
                    or any(
                        current is not pinned
                        for current, pinned in zip(
                            (c.slot_id, c.plan_id, c.step_id, c.request_sha256),
                            values, strict=True,
                        )
                    )
                    for c, old, values in zip(claims, originals, saved, strict=True)
                )
            ):
                raise WriteSlotLedgerRejected("reservation carriers changed")

        originals = tuple(claims)
        stable()
        with closing(self._open(read_only=False)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                current = _inspect(conn)
                stable()
                if current != retained:
                    raise WriteSlotLedgerRejected("stale or rolled-back reservation witness")
                if current.count + len(saved) > _MAX_ROWS:
                    raise WriteSlotLedgerRejected("reservation history capacity exceeded")
                for slot, plan, step, request in saved:
                    seq = current.count + 1
                    chain = _hash(("row", current.chain_sha256, seq, slot, plan, step, request))
                    conn.execute("INSERT INTO synthetic_write_slots VALUES(?,?,?,?,?,?)",
                                 (seq, slot, plan, step, request, chain))
                    current = WriteSlotLedgerWitness(seq, chain)
                stable()
                if _inspect(conn) != current:
                    raise WriteSlotLedgerRejected("reservation append lost integrity")
                stable()
                committed_witness = (current.count, current.chain_sha256)
                conn.commit()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise WriteSlotLedgerRejected("duplicate durable reservation") from exc
            except BaseException:
                conn.rollback()
                raise
        # A commit has already reserved these identities. If a callback or
        # reflective mutation changes a claim, retained witness or receipt,
        # fail closed without pretending that rolling back is still possible.
        stable()
        receipt = WriteSlotReservationReceipt(len(saved), current)
        stable()
        if (
            type(receipt) is not _RECEIPT_TYPE
            or type(receipt.added_count) is not int
            or receipt.added_count != len(saved)
            or receipt.witness is not current
            or type(current) is not _WITNESS_TYPE
            or current.independently_authenticated is not False
            or receipt.dispatch_authorized is not False
            or receipt.automatic_replay_authorized is not False
            or receipt.exact_once_external_effect_proven is not False
            or receipt.trusted_clock_verified is not False
            or receipt.owner_or_consent_verified is not False
            or (current.count, current.chain_sha256) != committed_witness
            or current.count is not committed_witness[0]
            or current.chain_sha256 is not committed_witness[1]
        ):
            raise WriteSlotLedgerRejected("post-commit reservation receipt changed")
        stable()
        if (
            type(receipt) is not _RECEIPT_TYPE
            or receipt.dispatch_authorized is not False
            or receipt.automatic_replay_authorized is not False
            or receipt.exact_once_external_effect_proven is not False
            or receipt.trusted_clock_verified is not False
            or receipt.owner_or_consent_verified is not False
        ):
            raise WriteSlotLedgerRejected("post-commit reservation authority changed")
        return receipt
