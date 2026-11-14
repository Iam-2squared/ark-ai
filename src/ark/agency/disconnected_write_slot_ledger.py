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
import os
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
_CLAIM_TYPE = DetachedWriteSlotClaim
# Frozen, slotted data carriers remain patchable at class level. Pin their
# field descriptors and lookup hooks before reading a caller-owned witness
# or claim, before any SQLite access, and at every callback boundary.
_WITNESS_FIELDS = ("count", "chain_sha256")
_CLAIM_FIELDS = ("slot_id", "plan_id", "step_id", "request_sha256")
_CARRIER_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_WITNESS_FIELDS = tuple(
    vars(_WITNESS_TYPE)[name] for name in _WITNESS_FIELDS
)
_ORIGINAL_CLAIM_FIELDS = tuple(
    vars(_CLAIM_TYPE)[name] for name in _CLAIM_FIELDS
)
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(name) for name in _CARRIER_HOOKS
)
_ORIGINAL_CLAIM_HOOKS = tuple(
    vars(_CLAIM_TYPE).get(name) for name in _CARRIER_HOOKS
)
_ORIGINAL_CLAIM_INIT = vars(_CLAIM_TYPE)["__init__"]
_ORIGINAL_WITNESS_DENIAL = vars(_WITNESS_TYPE)["independently_authenticated"]
_RECEIPT_DENIALS = (
    "dispatch_authorized", "automatic_replay_authorized",
    "exact_once_external_effect_proven", "trusted_clock_verified",
    "owner_or_consent_verified",
)
# Pin declarations from import time, not a potentially replaced set of
# False-only getters collected only after a reservation was committed.
_ORIGINAL_RECEIPT_DENIALS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_DENIALS
)
_ORIGINAL_WITNESS_INIT = vars(_WITNESS_TYPE)["__init__"]
_ORIGINAL_RECEIPT_INIT = vars(_RECEIPT_TYPE)["__init__"]
_RECEIPT_FIELDS = ("added_count", "witness")
_RECEIPT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RECEIPT_FIELDS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_FIELDS
)
_ORIGINAL_RECEIPT_HOOKS = tuple(
    vars(_RECEIPT_TYPE).get(name) for name in _RECEIPT_HOOKS
)


# Pin the local reservation hashing and schema protocol before any private
# claim/witness bytes reach serializers, digests or SQLite. A local pin is not
# a signed approval or trusted evidence against a compromised interpreter.
_ORIGINAL_SQLITE3 = sqlite3
_ORIGINAL_CONNECT = sqlite3.connect
_ORIGINAL_OS = os
_ORIGINAL_FSENCODE = os.fsencode
_MAX_DB_PATH_BYTES = 4096
_ORIGINAL_MAX_DB_PATH_BYTES = _MAX_DB_PATH_BYTES
_ORIGINAL_MAX_ROWS = _MAX_ROWS
_ORIGINAL_MAX_BATCH = _MAX_BATCH
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_DDL = _DDL
_ORIGINAL_ID_PATTERNS = (_PLAN, _STEP, _SLOT, _SHA)


def _require_original_constructors() -> None:
    # Constructor custody is independent from the established denial-getter
    # check timings. Keep those existing checks and error paths intact: a
    # synthetic post-COMMIT getter fixture must still test its own boundary.
    if (
        sqlite3 is not _ORIGINAL_SQLITE3
        or sqlite3.connect is not _ORIGINAL_CONNECT
        or os is not _ORIGINAL_OS
        or os.fsencode is not _ORIGINAL_FSENCODE
        or type(_MAX_DB_PATH_BYTES) is not int
        or _MAX_DB_PATH_BYTES != _ORIGINAL_MAX_DB_PATH_BYTES
        or type(_MAX_ROWS) is not int or _MAX_ROWS != _ORIGINAL_MAX_ROWS
        or type(_MAX_BATCH) is not int or _MAX_BATCH != _ORIGINAL_MAX_BATCH
        or hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _DDL is not _ORIGINAL_DDL
        or any(
            candidate is not expected
            for candidate, expected in zip(
                (_PLAN, _STEP, _SLOT, _SHA), _ORIGINAL_ID_PATTERNS, strict=True,
            )
        )
        or WriteSlotLedgerWitness is not _WITNESS_TYPE
        or WriteSlotReservationReceipt is not _RECEIPT_TYPE
        or DetachedWriteSlotClaim is not _CLAIM_TYPE
        or vars(_WITNESS_TYPE).get("__init__") is not _ORIGINAL_WITNESS_INIT
        or vars(_RECEIPT_TYPE).get("__init__") is not _ORIGINAL_RECEIPT_INIT
        or vars(_CLAIM_TYPE).get("__init__") is not _ORIGINAL_CLAIM_INIT
        or any(
            vars(cls).get(name) is not original
            for cls, fields, originals in (
                (_WITNESS_TYPE, _WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS),
                (_CLAIM_TYPE, _CLAIM_FIELDS, _ORIGINAL_CLAIM_FIELDS),
                (_WITNESS_TYPE, _CARRIER_HOOKS, _ORIGINAL_WITNESS_HOOKS),
                (_CLAIM_TYPE, _CARRIER_HOOKS, _ORIGINAL_CLAIM_HOOKS),
                (_RECEIPT_TYPE, _RECEIPT_FIELDS, _ORIGINAL_RECEIPT_FIELDS),
                (_RECEIPT_TYPE, _RECEIPT_HOOKS, _ORIGINAL_RECEIPT_HOOKS),
            )
            for name, original in zip(fields, originals, strict=True)
        )
    ):
        raise WriteSlotLedgerRejected("reservation constructor or authority changed")


def _hash(value: tuple[object, ...]) -> str:
    _require_original_constructors()
    encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    _require_original_constructors()
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    _require_original_constructors()
    return digest


def genesis_write_slot_witness() -> WriteSlotLedgerWitness:
    _require_original_constructors()
    chain = _hash(("genesis",))
    _require_original_constructors()
    return _WITNESS_TYPE(0, chain)


def _valid(value: object, pattern: re.Pattern[str]) -> bool:
    # Bound hostile strings before invoking the pattern matcher. A caller
    # cannot supply an alternate grammar as a synthetic WRITE identity.
    if pattern is _STEP:
        width = 21
    elif pattern is _PLAN or pattern is _SLOT:
        width = 69
    elif pattern is _SHA:
        width = 64
    else:
        return False
    return type(value) is str and len(value) == width and pattern.fullmatch(value) is not None


def derive_disconnected_write_slot_id(
    plan_id: str, step_id: str, request_sha256: str,
) -> str:
    """Compute a claim ID; computing it does not authorize or reserve a WRITE."""
    _require_original_constructors()
    if not (_valid(plan_id, _PLAN) and _valid(step_id, _STEP)
            and _valid(request_sha256, _SHA)):
        raise WriteSlotLedgerRejected("invalid exact WRITE identity")
    return "slot_" + _hash(("slot", plan_id, step_id, request_sha256))


def _check_witness(value: object) -> None:
    # A property returning False can still be executable attacker code.
    # Pin the import-time class and denial descriptor before every getter.
    def original_denial() -> None:
        _require_original_constructors()
        if (
            WriteSlotLedgerWitness is not _WITNESS_TYPE
            or vars(_WITNESS_TYPE).get("independently_authenticated")
            is not _ORIGINAL_WITNESS_DENIAL
        ):
            raise WriteSlotLedgerRejected("invalid retained witness")

    original_denial()
    if (
        type(value) is not _WITNESS_TYPE
        or type(value.count) is not int
        or not 0 <= value.count <= _MAX_ROWS
        or not _valid(value.chain_sha256, _SHA)
    ):
        raise WriteSlotLedgerRejected("invalid retained witness")
    original_denial()
    if value.independently_authenticated is not False:
        raise WriteSlotLedgerRejected("invalid retained witness")
    original_denial()


def _check_path(value: object, *, create: bool) -> Path:
    if (type(value) is not type(Path(".")) or not value.is_absolute()
            or ".." in value.parts or len(str(value)) > _MAX_DB_PATH_BYTES
            or "\x00" in str(value)
            or value.name in ("", ".", "..")):
        raise WriteSlotLedgerRejected("exact absolute fixture path required")
    # SQLite may access the longest rollback-journal sidecar, even if the main
    # pathname fits a Unicode character count. Bound native filesystem bytes
    # before lstat, SQLite connect or any attempted reservation.
    try:
        path_bytes = len(os.fsencode(value))
    except (UnicodeError, ValueError, OSError) as exc:
        raise WriteSlotLedgerRejected("invalid native reservation path") from exc
    if path_bytes + len(b"-journal") > _MAX_DB_PATH_BYTES:
        raise WriteSlotLedgerRejected("reservation SQLite path byte budget exceeded")
    try:
        for ancestor in value.parents:
            info = ancestor.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise WriteSlotLedgerRejected("unsafe SQLite ancestor")
        main_exists = False
        try:
            info = value.lstat()
        except FileNotFoundError:
            if not create:
                raise WriteSlotLedgerRejected("missing durable reservation ledger") from None
        else:
            main_exists = True
            if create or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise WriteSlotLedgerRejected("existing or aliased SQLite path")
        # A regular main DB does not authenticate the WAL, SHM or rollback
        # journal. Refuse orphaned and aliased sidecar names before SQLite
        # can follow them. This lexical preflight is NOT an atomic file
        # custody or external-write authorization guarantee.
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = value.with_name(value.name + suffix)
            try:
                sidecar_info = sidecar.lstat()
            except FileNotFoundError:
                continue
            if (
                create or not main_exists
                or not stat.S_ISREG(sidecar_info.st_mode)
                or sidecar_info.st_nlink != 1
            ):
                raise WriteSlotLedgerRejected("unsafe or orphaned SQLite sidecar")
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
    _require_original_constructors()
    _schema(conn)
    _require_original_constructors()
    # The full chain is checked below. First reject count/width/type without
    # fetching potentially oversized persisted identity BLOB/TEXT into Python.
    count = conn.execute("SELECT COUNT(*) FROM synthetic_write_slots").fetchone()[0]
    if type(count) is not int or not 0 <= count <= _MAX_ROWS:
        raise WriteSlotLedgerRejected("invalid persisted reservation row")
    malformed = conn.execute(
        "SELECT 1 FROM synthetic_write_slots WHERE "
        "typeof(slot_id)!='text' OR length(slot_id)!=69 OR "
        "typeof(plan_id)!='text' OR length(plan_id)!=69 OR "
        "typeof(step_id)!='text' OR length(step_id)!=21 OR "
        "typeof(request_sha256)!='text' OR length(request_sha256)!=64 OR "
        "typeof(chain_sha256)!='text' OR length(chain_sha256)!=64 LIMIT 1"
    ).fetchone()
    if malformed is not None:
        raise WriteSlotLedgerRejected("invalid persisted reservation row")
    _require_original_constructors()
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
        _require_original_constructors()
        witness = _WITNESS_TYPE(seq, chain)
        _require_original_constructors()
    return witness


class DisconnectedWriteSlotLedger:
    """A synthetic local uniqueness ledger, never a WRITE execution gate."""

    def __init__(self, path: Path, *, create: bool = False) -> None:
        _require_original_constructors()
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
                if self._path is not path:
                    raise WriteSlotLedgerRejected("ledger path changed during startup")
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
        source = self._path

        def stable() -> None:
            _check_witness(retained)
            if (
                self._path is not source
                or type(retained) is not _WITNESS_TYPE
                or retained.count is not original[0]
                or retained.chain_sha256 is not original[1]
                or retained.independently_authenticated is not False
            ):
                raise WriteSlotLedgerRejected("read-only ledger custody changed")

        stable()
        with closing(self._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                actual = _inspect(conn)
                _check_witness(actual)
                stable()
                # Compare independent scalar custody, never patchable dataclass __eq__.
                if (
                    actual.count != original[0]
                    or actual.chain_sha256 != original[1]
                    or original != (retained.count, retained.chain_sha256)
                ):
                    raise WriteSlotLedgerRejected("stale or changed retained history")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        stable()
        _check_witness(actual)
        return actual

    def reserve_many(
        self, claims: tuple[DetachedWriteSlotClaim, ...], *, retained: WriteSlotLedgerWitness,
    ) -> WriteSlotReservationReceipt:
        """Atomically record 1-16 synthetic identities, without executing any action."""
        _require_original_constructors()
        if (type(claims) is not tuple or not 1 <= len(claims) <= _MAX_BATCH
                or any(type(claim) is not DetachedWriteSlotClaim for claim in claims)):
            raise WriteSlotLedgerRejected("exact bounded synthetic claim tuple required")
        _check_witness(retained)
        saved = tuple((c.slot_id, c.plan_id, c.step_id, c.request_sha256) for c in claims)
        old_witness = (retained.count, retained.chain_sha256)
        source = self._path
        if len(set(saved)) != len(saved):
            raise WriteSlotLedgerRejected("duplicate identities in batch")
        for slot, plan, step, request in saved:
            if (not _valid(slot, _SLOT) or not _valid(plan, _PLAN)
                    or not _valid(step, _STEP) or not _valid(request, _SHA)
                    or slot != derive_disconnected_write_slot_id(plan, step, request)):
                raise WriteSlotLedgerRejected("invalid synthetic reservation claim")

        def stable() -> None:
            # A retained witness is never authority. Re-check its denied
            # capability flag at every re-entrant SQLite boundary.
            _check_witness(retained)
            if (
                self._path is not source
                or type(retained) is not _WITNESS_TYPE
                or old_witness != (retained.count, retained.chain_sha256)
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
                _check_witness(current)
                stable()
                # A synthetic retained witness must match persisted history.
                # Patched witness equality is not an integrity check.
                if (
                    current.count != old_witness[0]
                    or current.chain_sha256 != old_witness[1]
                ):
                    raise WriteSlotLedgerRejected("stale or rolled-back reservation witness")
                if current.count + len(saved) > _MAX_ROWS:
                    raise WriteSlotLedgerRejected("reservation history capacity exceeded")
                for slot, plan, step, request in saved:
                    seq = current.count + 1
                    chain = _hash(("row", current.chain_sha256, seq, slot, plan, step, request))
                    conn.execute("INSERT INTO synthetic_write_slots VALUES(?,?,?,?,?,?)",
                                 (seq, slot, plan, step, request, chain))
                    _require_original_constructors()
                    current = _WITNESS_TYPE(seq, chain)
                    _require_original_constructors()
                stable()
                inspected = _inspect(conn)
                _check_witness(inspected)
                # Recompute the appended tip: object equality is replaceable.
                if (
                    inspected.count != current.count
                    or inspected.chain_sha256 != current.chain_sha256
                ):
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
        _check_witness(current)
        _require_original_constructors()
        receipt = _RECEIPT_TYPE(len(saved), current)
        _require_original_constructors()
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
        # Freeze class-level denial descriptors too: a false-valued getter
        # may replace another descriptor while processing the final callback.
        # The witness and SQLite write are already committed, so a failed
        # final review must NEVER be represented as a rolled-back reservation.
        denial_names = _RECEIPT_DENIALS
        denial_descriptors = tuple(
            getattr(_RECEIPT_TYPE, name) for name in denial_names
        )
        stable()
        if (
            type(receipt) is not _RECEIPT_TYPE
            or any(getattr(receipt, name) is not False for name in denial_names)
        ):
            raise WriteSlotLedgerRejected("post-commit reservation authority changed")
        # Check *after* the final reentrant getter, not merely before it.
        stable()
        _check_witness(current)
        if (
            type(receipt) is not _RECEIPT_TYPE
            or type(receipt.added_count) is not int
            or receipt.added_count != len(saved)
            or receipt.witness is not current
            or current.count is not committed_witness[0]
            or current.chain_sha256 is not committed_witness[1]
            or any(
                getattr(_RECEIPT_TYPE, name) is not descriptor
                for name, descriptor in zip(
                    denial_names, denial_descriptors, strict=True,
                )
            )
            or any(
                vars(_RECEIPT_TYPE).get(name) is not original
                for name, original in zip(
                    _RECEIPT_DENIALS, _ORIGINAL_RECEIPT_DENIALS, strict=True,
                )
            )
        ):
            raise WriteSlotLedgerRejected("post-commit reservation receipt epoch changed")
        # Reopen a *read-only* transaction after all receipt callbacks; a
        # synthetic callback may alter persisted history after COMMIT.
        # This is local continuity detection, not proof of an external effect.
        try:
            with closing(self._open(read_only=True)) as readonly:
                readonly.execute("BEGIN")
                try:
                    persisted = _inspect(readonly)
                    _check_witness(persisted)
                    if (
                        type(persisted) is not _WITNESS_TYPE
                        or persisted.count != current.count
                        or persisted.chain_sha256 != current.chain_sha256
                    ):
                        raise WriteSlotLedgerRejected(
                            "post-commit reservation persisted history changed"
                        )
                    readonly.rollback()
                except BaseException:
                    readonly.rollback()
                    raise
        except sqlite3.Error as exc:
            raise WriteSlotLedgerRejected(
                "post-commit reservation history cannot be rechecked"
            ) from exc
        stable()
        _check_witness(current)
        if (
            type(receipt) is not _RECEIPT_TYPE
            or receipt.witness is not current
            or type(receipt.added_count) is not int
            or receipt.added_count != len(saved)
            or current.count is not committed_witness[0]
            or current.chain_sha256 is not committed_witness[1]
            or any(
                getattr(_RECEIPT_TYPE, name) is not descriptor
                for name, descriptor in zip(
                    denial_names, denial_descriptors, strict=True,
                )
            )
            or any(
                vars(_RECEIPT_TYPE).get(name) is not original
                for name, original in zip(
                    _RECEIPT_DENIALS, _ORIGINAL_RECEIPT_DENIALS, strict=True,
                )
            )
        ):
            raise WriteSlotLedgerRejected("post-commit reservation receipt changed at return")
        return receipt
