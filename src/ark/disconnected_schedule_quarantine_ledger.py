"""Disconnected, policy-bound quarantine history for *expired* scheduled slots.

This stores only synthetic overdue classifications. Caller time, schedule identity
and retained witnesses are not authenticated. Recording quarantine never grants
execution, notification, consent, automatic replay, or trusted-clock authority.
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

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_SLOT = re.compile(r"slot_[0-9a-f]{64}\Z")
_MAX_MS = 2**63 - 1
_MAX_ROWS = 512
_MAX_OCCURRENCES = 4096
_MAX_INTERVAL_MS = 366 * 24 * 60 * 60 * 1000
_MAX_DB_PATH = 4096
_DOMAIN = b"ARK-disconnected-quarantine-ledger-v1\0"
_DDL = (
    "CREATE TABLE policy (policy_sha256 TEXT PRIMARY KEY, first_ms INTEGER NOT NULL, "
    "interval_ms INTEGER NOT NULL, count INTEGER NOT NULL, grace_ms INTEGER NOT NULL)",
    "CREATE TABLE quarantines (seq INTEGER PRIMARY KEY, occurrence_id TEXT NOT NULL "
    "UNIQUE, due_ms INTEGER NOT NULL, observed_ms INTEGER NOT NULL, "
    "chain_sha256 TEXT NOT NULL)",
)


# These local protocol constants and codecs define the persisted hash chain.
# Refuse post-import mutation before accepting a retained witness or opening a
# SQLite writer. This is instrumentation defense, not external provenance.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_OS = os
_ORIGINAL_FSENCODE = os.fsencode
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_SHA = _SHA
_ORIGINAL_SLOT = _SLOT
_ORIGINAL_DDL = _DDL
_ORIGINAL_BOUNDS = (_MAX_MS, _MAX_ROWS, _MAX_OCCURRENCES, _MAX_INTERVAL_MS, _MAX_DB_PATH)


def _require_original_quarantine_protocol() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or os is not _ORIGINAL_OS
        or os.fsencode is not _ORIGINAL_FSENCODE
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _SHA is not _ORIGINAL_SHA
        or _SLOT is not _ORIGINAL_SLOT
        or _DDL is not _ORIGINAL_DDL
        or any(type(value) is not int for value in (
            _MAX_MS, _MAX_ROWS, _MAX_OCCURRENCES, _MAX_INTERVAL_MS, _MAX_DB_PATH,
        ))
        or (_MAX_MS, _MAX_ROWS, _MAX_OCCURRENCES, _MAX_INTERVAL_MS, _MAX_DB_PATH)
           != _ORIGINAL_BOUNDS
    ):
        raise ScheduleQuarantineRejected("quarantine digest or protocol changed")


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


# Pin result class identity/slots before a prospective SQLite write. A
# preinstalled synthetic constructor or field property could otherwise run
# only AFTER the quarantine had already committed. These are not permission.
_RECEIPT_TYPE = QuarantineReceipt
_RECEIPT_CARRIER_NAMES = (
    "witness", "quarantined_index", "__init__", "__new__",
    "__getattribute__", "__getattr__",
)
_ORIGINAL_RECEIPT_CARRIER = tuple(
    vars(_RECEIPT_TYPE).get(name) for name in _RECEIPT_CARRIER_NAMES
)


def _require_original_quarantine_receipt_carrier() -> None:
    _require_original_quarantine_protocol()
    if (
        QuarantineReceipt is not _RECEIPT_TYPE
        or any(
            vars(_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _RECEIPT_CARRIER_NAMES, _ORIGINAL_RECEIPT_CARRIER, strict=True,
            )
        )
    ):
        raise ScheduleQuarantineRejected(
            "quarantine receipt constructor or field descriptor changed"
        )


# Capture denial-only descriptors before any caller-supplied callback can
# replace them with plausible False-returning getters. An unchanged False
# return value alone is not proof of original authority semantics.
_ORIGINAL_RECEIPT_DENIALS = (
    ("execution_authorized", QuarantineReceipt.execution_authorized),
    ("notification_authorized", QuarantineReceipt.notification_authorized),
    ("automatic_replay_authorized", QuarantineReceipt.automatic_replay_authorized),
    ("trusted_clock_verified", QuarantineReceipt.trusted_clock_verified),
    ("consent_verified", QuarantineReceipt.consent_verified),
)
_ORIGINAL_WITNESS_DENIAL = QuarantineWitness.independently_authenticated

# Quarantine inputs are local fixtures, not capabilities. Frozen dataclass
# fields and lookup hooks can nevertheless be replaced at class level with
# executable descriptors. Inspect the import-time class dictionary before
# the first policy/witness value is accessed, including the error path.
_POLICY_INPUT_TYPE = QuarantinePolicy
_WITNESS_INPUT_TYPE = QuarantineWitness
_POLICY_INPUT_FIELDS = (
    "policy_sha256", "first_ms", "interval_ms", "count", "grace_ms",
)
_WITNESS_INPUT_FIELDS = ("count", "chain_sha256")
_INPUT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_POLICY_INPUT_ORIGINALS = tuple(
    vars(_POLICY_INPUT_TYPE).get(name)
    for name in (*_POLICY_INPUT_FIELDS, *_INPUT_HOOKS)
)
_WITNESS_INPUT_ORIGINALS = tuple(
    vars(_WITNESS_INPUT_TYPE).get(name)
    for name in (*_WITNESS_INPUT_FIELDS, *_INPUT_HOOKS)
)


def _require_original_quarantine_input_carriers() -> None:
    _require_original_quarantine_protocol()
    if (
        QuarantinePolicy is not _POLICY_INPUT_TYPE
        or QuarantineWitness is not _WITNESS_INPUT_TYPE
        or any(
            vars(cls).get(name) is not original
            for cls, fields, originals in (
                (_POLICY_INPUT_TYPE, (*_POLICY_INPUT_FIELDS, *_INPUT_HOOKS),
                 _POLICY_INPUT_ORIGINALS),
                (_WITNESS_INPUT_TYPE, (*_WITNESS_INPUT_FIELDS, *_INPUT_HOOKS),
                 _WITNESS_INPUT_ORIGINALS),
            )
            for name, original in zip(fields, originals, strict=True)
        )
    ):
        raise ScheduleQuarantineRejected(
            "quarantine input carrier descriptor changed"
        )


def _digest(payload: tuple[object, ...]) -> str:
    _require_original_quarantine_protocol()
    data = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    _require_original_quarantine_protocol()
    digest = hashlib.sha256(_DOMAIN + data).hexdigest()
    _require_original_quarantine_protocol()
    return digest


def _policy_epoch(policy: object) -> tuple[str, int, int, int, int]:
    _require_original_quarantine_input_carriers()
    if type(policy) is not QuarantinePolicy:
        raise ScheduleQuarantineRejected("exact synthetic policy required")
    values = (policy.policy_sha256, policy.first_ms, policy.interval_ms,
              policy.count, policy.grace_ms)
    sha, first, interval, count, grace = values
    if (type(sha) is not str or len(sha) != 64 or _SHA.fullmatch(sha) is None
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
    _require_original_quarantine_protocol()
    # Match the independent deterministic preview identifier without importing
    # or trusting a preview result object as authority.
    result = "slot_" + hashlib.sha256(
        b"ARK-disconnected-schedule-preview-v1\0" + b"occurrence\0" + payload
    ).hexdigest()
    _require_original_quarantine_protocol()
    return result


def _path(value: object, *, create: bool) -> Path:
    # SQLite can open the main file and a longer -journal sibling. Reject
    # malformed/oversized native-encoded paths before any lstat or connection.
    _require_original_quarantine_protocol()
    if (type(value) is not type(Path(".")) or not value.is_absolute()
            or ".." in value.parts or "\x00" in str(value)
            or value.name in ("", ".", "..")):
        raise ScheduleQuarantineRejected("absolute exact fixture path required")
    try:
        encoded_length = len(os.fsencode(value))
    except (UnicodeError, ValueError, OSError) as exc:
        raise ScheduleQuarantineRejected("invalid quarantine SQLite path encoding") from exc
    if encoded_length + len(b"-journal") > _MAX_DB_PATH:
        raise ScheduleQuarantineRejected("quarantine SQLite path byte budget exceeded")
    try:
        for parent in value.parents:
            info = parent.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise ScheduleQuarantineRejected("unsafe quarantine ancestor")
        try:
            info = value.lstat()
        except FileNotFoundError:
            main_missing = True
            if not create:
                raise ScheduleQuarantineRejected("missing quarantine ledger") from None
        else:
            main_missing = False
            if create or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ScheduleQuarantineRejected("aliased or existing quarantine ledger")
        # SQLite also opens these known sibling paths. Do not adopt orphaned
        # journals on create, or follow an aliased sidecar on later reads/writes.
        # This is a lexical lstat preflight, not race-free dirfd custody.
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = value.with_name(value.name + suffix)
            try:
                sidecar_info = sidecar.lstat()
            except FileNotFoundError:
                continue
            if (
                main_missing or create
                or not stat.S_ISREG(sidecar_info.st_mode)
                or sidecar_info.st_nlink != 1
            ):
                raise ScheduleQuarantineRejected("unsafe quarantine SQLite sidecar")
    except OSError as exc:
        raise ScheduleQuarantineRejected("quarantine path unavailable") from exc
    return value


def _validate(conn: sqlite3.Connection, epoch: tuple[str, int, int, int, int]) -> QuarantineWitness:
    if conn.execute("PRAGMA user_version").fetchone() != (1,):
        raise ScheduleQuarantineRejected("quarantine schema version changed")
    # Inspect DDL size and object count inside the caller's single SQLite
    # transaction, before hydrating a potentially huge or attacker-altered
    # sqlite_master into Python.
    schema_rows, ddl_bytes = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(length(CAST(sql AS BLOB))), 0) "
        "FROM sqlite_master"
    ).fetchone()
    if (type(schema_rows) is not int or type(ddl_bytes) is not int
            or not 0 <= schema_rows <= 8 or not 0 <= ddl_bytes <= 8192):
        raise ScheduleQuarantineRejected("quarantine schema preflight budget exceeded")
    with closing(sqlite3.connect(":memory:")) as expected:
        for statement in _DDL:
            expected.execute(statement)
        q = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(conn.execute(q)) != tuple(expected.execute(q)):
            raise ScheduleQuarantineRejected("quarantine schema drift")
    if conn.execute("PRAGMA quick_check").fetchmany(2) != [("ok",)]:
        raise ScheduleQuarantineRejected("quarantine SQLite integrity failure")
    # Reject excessive or malformed persisted rows in SQLite before Python
    # receives occurrence identifiers and digest-bearing private metadata.
    persisted_count = conn.execute(
        "SELECT COUNT(*) FROM quarantines"
    ).fetchone()[0]
    if type(persisted_count) is not int or persisted_count > _MAX_ROWS:
        raise ScheduleQuarantineRejected("quarantine persisted row budget exceeded")
    malformed = conn.execute(
        "SELECT 1 FROM quarantines WHERE "
        "typeof(occurrence_id)!='text' OR length(occurrence_id)!=69 OR "
        "typeof(chain_sha256)!='text' OR length(chain_sha256)!=64 OR "
        "typeof(seq)!='integer' OR typeof(due_ms)!='integer' OR "
        "typeof(observed_ms)!='integer' LIMIT 1"
    ).fetchone()
    if malformed is not None:
        raise ScheduleQuarantineRejected("quarantine persisted storage type or width changed")
    # A two-row cursor caps row count, but it does not cap the size of a
    # single private policy value. Reject oversized or noninteger SQLite
    # storage classes before even one policy row reaches Python.
    invalid_policy = conn.execute(
        "SELECT 1 FROM policy WHERE "
        "typeof(policy_sha256)!='text' "
        "OR length(CAST(policy_sha256 AS BLOB))!=64 "
        "OR typeof(first_ms)!='integer' "
        "OR typeof(interval_ms)!='integer' "
        "OR typeof(count)!='integer' "
        "OR typeof(grace_ms)!='integer' LIMIT 1"
    ).fetchone()
    if invalid_policy is not None:
        raise ScheduleQuarantineRejected(
            "quarantine policy hydration admission failed"
        )
    # A malformed store can have many distinct policy rows. Examine at most
    # two: any second row is a failure, never an unbounded tuple materialization.
    if tuple(conn.execute("SELECT * FROM policy").fetchmany(2)) != (epoch,):
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
                or type(chain) is not str or len(chain) != 64
                or _SHA.fullmatch(chain) is None
                or type(occurrence) is not str or len(occurrence) != 69
                or _SLOT.fullmatch(occurrence) is None):
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
        # Existing-ledger startup is inspection-only. Do not reserve a
        # SQLite writer slot or permit mutation merely to validate a restart.
        mode = "rwc" if create else "ro"
        with closing(sqlite3.connect(
            self._path.as_uri() + "?mode=" + mode, uri=True,
            isolation_level=None, timeout=10,
        )) as conn:
            conn.execute("BEGIN IMMEDIATE" if create else "BEGIN")
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
        original_path = self._path
        original_policy = self._epoch
        original = (retained.count, retained.chain_sha256)

        def stable() -> None:
            # Open/BEGIN/validation/COMMIT are independent callback boundaries.
            # A value-equal witness or source carrier swap is still a new epoch.
            if (
                self._path is not original_path
                or self._epoch is not original_policy
                or type(retained) is not QuarantineWitness
                or retained.count is not original[0]
                or retained.chain_sha256 is not original[1]
            ):
                raise ScheduleQuarantineRejected("quarantine inspect carrier changed")

        stable()
        with closing(self._open(read_only=True)) as conn:
            stable()
            conn.execute("BEGIN")
            stable()
            try:
                actual = _validate(conn, original_policy)
                stable()
                if (
                    type(actual) is not QuarantineWitness
                    or actual.count != retained.count
                    or actual.chain_sha256 != retained.chain_sha256
                ):
                    raise ScheduleQuarantineRejected("stale or changed quarantine witness")
                result_epoch = (actual.count, actual.chain_sha256)
                conn.commit()
                stable()
                if (
                    type(actual) is not QuarantineWitness
                    or actual.count is not result_epoch[0]
                    or actual.chain_sha256 is not result_epoch[1]
                ):
                    raise ScheduleQuarantineRejected("quarantine inspect result changed")
            except BaseException:
                conn.rollback()
                raise
        stable()
        if (
            type(actual) is not QuarantineWitness
            or actual.count is not result_epoch[0]
            or actual.chain_sha256 is not result_epoch[1]
        ):
            raise ScheduleQuarantineRejected("quarantine inspect result changed")
        return actual

    @staticmethod
    def _check_witness(value: object) -> None:
        _require_original_quarantine_input_carriers()
        if (type(value) is not QuarantineWitness
                or type(value.count) is not int or not 0 <= value.count <= _MAX_ROWS
                or type(value.chain_sha256) is not str
                or len(value.chain_sha256) != 64
                or _SHA.fullmatch(value.chain_sha256) is None):
            raise ScheduleQuarantineRejected("invalid retained quarantine witness")

    def quarantine_expired(
        self, *, index: int, occurrence_id: str, observed_ms: int,
        retained: QuarantineWitness,
    ) -> QuarantineReceipt:
        """Record one *already expired* synthetic occurrence in order, without dispatch."""
        _require_original_quarantine_receipt_carrier()
        self._check_witness(retained)
        original = (retained.count, retained.chain_sha256)
        original_epoch = self._epoch
        original_path = self._path

        def stable() -> None:
            _require_original_quarantine_receipt_carrier()
            if (
                self._path is not original_path
                or self._epoch is not original_epoch
                or type(retained) is not QuarantineWitness
                or retained.count is not original[0]
                or retained.chain_sha256 is not original[1]
            ):
                raise ScheduleQuarantineRejected("quarantine write carrier changed")

        stable()
        if (type(index) is not int or type(observed_ms) is not int
                or not 0 <= observed_ms <= _MAX_MS
                or type(occurrence_id) is not str
                or len(occurrence_id) != 69
                or _SLOT.fullmatch(occurrence_id) is None):
            raise ScheduleQuarantineRejected("invalid synthetic expiry claim")
        policy = QuarantinePolicy(*self._epoch)
        if index >= self._epoch[3] or index < 0:
            raise ScheduleQuarantineRejected("occurrence index outside policy")
        due = self._epoch[1] + index * self._epoch[2]
        if (occurrence_id != derive_quarantined_occurrence(policy, index)
                or observed_ms <= due + self._epoch[4]):
            raise ScheduleQuarantineRejected("occurrence is not expired or not policy-bound")
        stable()
        with closing(self._open(read_only=False)) as conn:
            stable()
            conn.execute("BEGIN IMMEDIATE")
            stable()
            try:
                current = _validate(conn, original_epoch)
                stable()
                if (
                    type(current) is not QuarantineWitness
                    or current.count != retained.count
                    or current.chain_sha256 != retained.chain_sha256
                ):
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
                # Do not invoke a caller-replaced dataclass __eq__ on
                # the retained or recomputed witnesses.
                checked = _validate(conn, original_epoch)
                if (
                    type(checked) is not QuarantineWitness
                    or checked.count != result.count
                    or checked.chain_sha256 != result.chain_sha256
                ):
                    raise ScheduleQuarantineRejected("quarantine write lost integrity")
                stable()
                result_epoch = (result.count, result.chain_sha256)
                conn.commit()
                stable()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise ScheduleQuarantineRejected("duplicate quarantine occurrence") from exc
            except BaseException:
                conn.rollback()
                raise
        # This reservation is already durable. Never return a forged or
        # reflectively retargeted receipt as an authority to advance a cursor.
        stable()
        receipt = QuarantineReceipt(result, index)
        if (
            type(receipt) is not QuarantineReceipt
            or receipt.witness is not result
            or type(result) is not QuarantineWitness
            or (result.count, result.chain_sha256) != result_epoch
            or result.count is not result_epoch[0]
            or result.chain_sha256 is not result_epoch[1]
            or type(receipt.quarantined_index) is not int
            or receipt.quarantined_index != index
            or original != (retained.count, retained.chain_sha256)
            or retained.count is not original[0]
            or retained.chain_sha256 is not original[1]
            or self._epoch is not original_epoch
            or self._path is not original_path
        ):
            raise ScheduleQuarantineRejected("post-commit quarantine receipt changed")
        stable()
        # Persisted quarantine is only an overdue classification. Even a
        # false-valued reentrant result getter may alter the returned witness,
        # its authority descriptors or the already-committed SQLite history.
        denial_flags = (
            "execution_authorized", "notification_authorized",
            "automatic_replay_authorized", "trusted_clock_verified",
            "consent_verified",
        )
        descriptors = tuple(getattr(QuarantineReceipt, key) for key in denial_flags)
        for key in denial_flags:
            if getattr(receipt, key) is not False:
                raise ScheduleQuarantineRejected("post-commit quarantine gained authority")
            stable()
        if (
            type(receipt) is not QuarantineReceipt
            or receipt.witness is not result
            or type(result) is not QuarantineWitness
            or result.count is not result_epoch[0]
            or result.chain_sha256 is not result_epoch[1]
            or type(receipt.quarantined_index) is not int
            or receipt.quarantined_index != index
            or any(
                getattr(QuarantineReceipt, key) is not before
                for key, before in zip(denial_flags, descriptors, strict=True)
            )
        ):
            raise ScheduleQuarantineRejected("post-commit quarantine result epoch changed")
        # Read the durable journal again AFTER all result callbacks. A failed
        # post-COMMIT review never rolls back, retries, dispatches or advances
        # the synthetic occurrence.
        try:
            with closing(self._open(read_only=True)) as readonly:
                readonly.execute("BEGIN")
                try:
                    persisted = _validate(readonly, original_epoch)
                    if (
                        type(persisted) is not QuarantineWitness
                        or persisted.count != result_epoch[0]
                        or persisted.chain_sha256 != result_epoch[1]
                    ):
                        raise ScheduleQuarantineRejected(
                            "post-commit quarantine history changed after denial"
                        )
                    readonly.rollback()
                except BaseException:
                    readonly.rollback()
                    raise
        except sqlite3.Error as exc:
            raise ScheduleQuarantineRejected(
                "post-commit quarantine history cannot be rechecked"
            ) from exc
        stable()
        if (
            type(receipt) is not QuarantineReceipt
            or receipt.witness is not result
            or result.count is not result_epoch[0]
            or result.chain_sha256 is not result_epoch[1]
            or receipt.quarantined_index != index
            or any(
                getattr(QuarantineReceipt, key) is not before
                for key, before in zip(denial_flags, descriptors, strict=True)
            )
        ):
            raise ScheduleQuarantineRejected("post-commit quarantine changed at return")
        # A preinstalled false-valued property replacement would survive the
        # snapshot of descriptors above; compare with import-time originals.
        # The ledger records quarantine only and must never return an
        # authenticated witness or grant dispatch/notification authority.
        if (
            type(receipt) is not QuarantineReceipt
            or type(receipt.witness) is not QuarantineWitness
            or any(
                getattr(QuarantineReceipt, key) is not original
                for key, original in _ORIGINAL_RECEIPT_DENIALS
            )
            or QuarantineWitness.independently_authenticated
            is not _ORIGINAL_WITNESS_DENIAL
        ):
            raise ScheduleQuarantineRejected(
                "post-commit quarantine original denial descriptor changed"
            )
        if receipt.witness.independently_authenticated is not False:
            raise ScheduleQuarantineRejected(
                "post-commit quarantine witness gained authentication"
            )
        stable()
        return receipt
