"""Disconnected atomic intent and pre-action audit, without tool dispatch.

Intent and its digest-only pre-action audit commit in one SQLite transaction.
This opt-in fixture does NOT bridge ARK's other SQLite stores, authenticate an
issuer, prove external effects, or authorize replay of an ambiguous WRITE.
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

_DOMAIN = b"ARK-disconnected-atomic-preaction-v1\0"
_AUDIT_DOMAIN = b"ARK-disconnected-preaction-audit-v1\0"
_GENESIS = hashlib.sha256(_DOMAIN + b"genesis").hexdigest()
_ID = re.compile(r"occ_[0-9a-f]{64}\Z")
_BOUND = re.compile(r"bound_[0-9a-f]{64}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX = 128
_MAX_PATH = 4096  # Local fixture pathname budget, before filesystem access.
# Pin the three identity grammars and reject overlong labels before regex.
_ORIGINAL_PATTERNS = (_ID, _BOUND, _SHA)
_INTENTS = (
    "CREATE TABLE intents ("
    "seq INTEGER PRIMARY KEY, occurrence_id TEXT NOT NULL UNIQUE, "
    "bound_action_id TEXT NOT NULL, request_sha256 TEXT NOT NULL, "
    "chain_sha256 TEXT NOT NULL)"
)
_AUDITS = (
    "CREATE TABLE preaction_audit ("
    "seq INTEGER PRIMARY KEY, occurrence_id TEXT NOT NULL UNIQUE, "
    "audit_sha256 TEXT NOT NULL)"
)


# Explicit process-local custody of the digest codec, ledger DDL and admission
# bound. Refuse replacements before constructing/reviewing private intent rows
# or opening a SQLite fixture. These checks cannot authenticate provenance.
_ORIGINAL_SQLITE3 = sqlite3
_ORIGINAL_CONNECT = sqlite3.connect
_ORIGINAL_OS = os
_ORIGINAL_FSENCODE = os.fsencode
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_AUDIT_DOMAIN = _AUDIT_DOMAIN
_ORIGINAL_GENESIS = _GENESIS
_ORIGINAL_SQL = (_INTENTS, _AUDITS)
_ORIGINAL_MAX = _MAX
_ORIGINAL_MAX_PATH = _MAX_PATH


class AtomicPreactionRejected(ValueError):
    """An inert reservation or its audit cannot be safely reconciled."""


@dataclass(frozen=True, slots=True)
class AtomicIntentClaim:
    occurrence_id: str
    bound_action_id: str
    request_sha256: str


@dataclass(frozen=True, slots=True)
class AtomicPreactionWitness:
    count: int
    tip_sha256: str


@dataclass(frozen=True, slots=True)
class AtomicPreactionSnapshot:
    witness: AtomicPreactionWitness
    occurrence_ids: tuple[str, ...]

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_effect_proven(self) -> bool:
        return False

    @property
    def trusted_approval_verified(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False


# Exact in-process custody of the inert intent/audit carriers. A frozen,
# slotted dataclass is still patchable at class level: a replacement slot or
# __getattribute__ executes before ordinary value/type validation. Check the
# originals without invoking the substituted descriptors.
_CLAIM_TYPE = AtomicIntentClaim
_WITNESS_TYPE = AtomicPreactionWitness
_SNAPSHOT_TYPE = AtomicPreactionSnapshot
_CLAIM_FIELDS = ("occurrence_id", "bound_action_id", "request_sha256")
_WITNESS_FIELDS = ("count", "tip_sha256")
_SNAPSHOT_FIELDS = ("witness", "occurrence_ids")
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_SNAPSHOT_DENIALS = (
    "tool_dispatch_authorized", "automatic_replay_authorized",
    "external_effect_proven", "trusted_approval_verified",
    "independent_custody_proven",
)
_ORIGINAL_CARRIER_SLOTS = tuple(
    (cls, names, tuple(vars(cls).get(name) for name in names))
    for cls, names in (
        (_CLAIM_TYPE, _CLAIM_FIELDS + _CARRIER_HOOKS),
        (_WITNESS_TYPE, _WITNESS_FIELDS + _CARRIER_HOOKS),
        (_SNAPSHOT_TYPE, _SNAPSHOT_FIELDS + _CARRIER_HOOKS + _SNAPSHOT_DENIALS),
    )
)


def _require_original_atomic_carriers(*, snapshot: bool = True) -> None:
    if (
        sqlite3 is not _ORIGINAL_SQLITE3
        or sqlite3.connect is not _ORIGINAL_CONNECT
        or os is not _ORIGINAL_OS
        or os.fsencode is not _ORIGINAL_FSENCODE
        or hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _AUDIT_DOMAIN is not _ORIGINAL_AUDIT_DOMAIN
        or _GENESIS is not _ORIGINAL_GENESIS
        or _INTENTS is not _ORIGINAL_SQL[0]
        or _AUDITS is not _ORIGINAL_SQL[1]
        or type(_MAX) is not int or _MAX != _ORIGINAL_MAX
        or type(_MAX_PATH) is not int or _MAX_PATH != _ORIGINAL_MAX_PATH
    ):
        raise AtomicPreactionRejected("atomic preaction codec or schema changed")
    # Genesis and raw witness/claim validation must remain independently
    # usable while a downstream recovery reviewer tests a forbidden snapshot
    # getter. The private _scan boundary checks the snapshot definition.
    if (
        AtomicIntentClaim is not _CLAIM_TYPE
        or AtomicPreactionWitness is not _WITNESS_TYPE
        or (snapshot and AtomicPreactionSnapshot is not _SNAPSHOT_TYPE)
        or any(
            vars(cls).get(name) is not original
            for cls, names, originals in _ORIGINAL_CARRIER_SLOTS
            if snapshot or cls is not _SNAPSHOT_TYPE
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise AtomicPreactionRejected("atomic intent or audit carrier definition changed")


def genesis_atomic_preaction_witness() -> AtomicPreactionWitness:
    _require_original_atomic_carriers(snapshot=False)
    return AtomicPreactionWitness(0, _GENESIS)


def _hex_id(value: object, pattern: re.Pattern[str]) -> bool:
    if any(
        current is not original
        for current, original in zip((_ID, _BOUND, _SHA), _ORIGINAL_PATTERNS, strict=True)
    ):
        raise AtomicPreactionRejected("atomic identifier protocol changed")
    if type(value) is not str:
        return False
    if pattern is _ID:
        expected = 68
    elif pattern is _BOUND:
        expected = 70
    elif pattern is _SHA:
        expected = 64
    else:
        return False
    return len(value) == expected and pattern.fullmatch(value) is not None


def _check_witness(value: object) -> None:
    _require_original_atomic_carriers(snapshot=False)
    if (
        type(value) is not AtomicPreactionWitness
        or type(value.count) is not int or not 0 <= value.count <= _MAX
        or not _hex_id(value.tip_sha256, _SHA)
    ):
        raise AtomicPreactionRejected("invalid retained pre-action witness")


def _witness_image(value: object) -> tuple[int, str]:
    """Exact scalar CAS, never user-replaceable dataclass equality."""
    _check_witness(value)
    return value.count, value.tip_sha256


def _check_claim(value: object) -> None:
    _require_original_atomic_carriers(snapshot=False)
    if (
        type(value) is not AtomicIntentClaim
        or not _hex_id(value.occurrence_id, _ID)
        or not _hex_id(value.bound_action_id, _BOUND)
        or not _hex_id(value.request_sha256, _SHA)
    ):
        raise AtomicPreactionRejected("invalid exact synthetic intent")


def _path(value: object, *, create: bool) -> Path:
    _require_original_atomic_carriers(snapshot=False)
    if (
        type(value) is not type(Path())
        or len(str(value)) > _MAX_PATH
        or "\x00" in str(value)
        or not value.name
        or ".." in value.parts
    ):
        raise AtomicPreactionRejected("unsafe intent ledger path")
    path = value.absolute()
    if len(str(path)) > _MAX_PATH:
        raise AtomicPreactionRejected("unsafe intent ledger path")
    # Both the caller-provided name and the normalized absolute DB plus the
    # longest rollback-journal name must fit the native filesystem byte limit
    # before lstat, SQLite connection, or any synthetic intent reservation.
    try:
        raw_bytes = len(os.fsencode(value))
        absolute_bytes = len(os.fsencode(path))
    except (UnicodeError, ValueError, OSError) as exc:
        raise AtomicPreactionRejected("unsafe intent ledger path encoding") from exc
    if raw_bytes > _MAX_PATH or absolute_bytes + len(b"-journal") > _MAX_PATH:
        raise AtomicPreactionRejected("unsafe intent ledger path")
    try:
        for parent in path.parents:
            meta = parent.lstat()
            if not stat.S_ISDIR(meta.st_mode) or stat.S_ISLNK(meta.st_mode):
                raise AtomicPreactionRejected("unsafe intent ledger ancestor")
        try:
            meta = path.lstat()
        except FileNotFoundError:
            if not create:
                raise AtomicPreactionRejected("intent ledger missing") from None
        else:
            if create or not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1:
                raise AtomicPreactionRejected("intent ledger already exists or unsafe")
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = path.with_name(path.name + suffix)
            try:
                meta = sidecar.lstat()
            except FileNotFoundError:
                continue
            # Never adopt a sidecar on first creation, nor retry a special
            # inode. SQLite's last-close cleanup can unlink an otherwise
            # ordinary regular inode between lstat lookup and its snapshot.
            # Re-observe only that already-unlinked regular case ONCE; the
            # second observation must be absent or a new single-link regular.
            if create or not stat.S_ISREG(meta.st_mode):
                raise AtomicPreactionRejected("unsafe intent ledger sidecar")
            if meta.st_nlink == 0:
                try:
                    meta = sidecar.lstat()
                except FileNotFoundError:
                    continue
            if not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1:
                raise AtomicPreactionRejected("unsafe intent ledger sidecar")
    except OSError as exc:
        raise AtomicPreactionRejected("intent ledger path cannot be inspected") from exc
    return path


def _schema(conn: sqlite3.Connection) -> None:
    _require_original_atomic_carriers()
    if conn.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise AtomicPreactionRejected("pre-action schema version mismatch")
    # A corrupted database may return many diagnostics. Two rows suffice to
    # reject any response other than one exact "ok" without unbounded hydration.
    quick = conn.execute("PRAGMA quick_check").fetchmany(2)
    if len(quick) != 1 or tuple(quick[0]) != ("ok",):
        raise AtomicPreactionRejected("pre-action SQLite integrity failure")
    # Check SQLite's catalog inside the caller's transaction BEFORE bringing
    # any persisted DDL into Python. Two UNIQUE indexes are auto-generated,
    # so the frozen v1 fixture has exactly four catalog entries.
    object_count, ddl_bytes = conn.execute(
        "SELECT COUNT(*),COALESCE(SUM(length(CAST(sql AS BLOB))),0) "
        "FROM sqlite_master"
    ).fetchone()
    if (
        type(object_count) is not int or object_count != 4
        or type(ddl_bytes) is not int or not 0 <= ddl_bytes <= 4_096
    ):
        raise AtomicPreactionRejected("pre-action schema catalog preflight failed")
    query = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
    # A SQLite connection context manager does not close the DDL oracle.
    # Release the throwaway handle even if schema comparison raises.
    with closing(sqlite3.connect(":memory:")) as expected:
        expected.execute(_INTENTS)
        expected.execute(_AUDITS)
        if conn.execute(query).fetchall() != expected.execute(query).fetchall():
            raise AtomicPreactionRejected("pre-action schema changed")


def _digest(domain: bytes, row: tuple[object, ...]) -> str:
    _require_original_atomic_carriers(snapshot=False)
    raw = json.dumps(row, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(domain + raw).hexdigest()


def _chain(previous: str, seq: int, claim: AtomicIntentClaim) -> str:
    return _digest(_DOMAIN, (
        previous, seq, claim.occurrence_id, claim.bound_action_id,
        claim.request_sha256,
    ))


def _audit(seq: int, claim: AtomicIntentClaim, chain: str) -> str:
    return _digest(_AUDIT_DOMAIN, (
        seq, claim.occurrence_id, claim.bound_action_id,
        claim.request_sha256, chain,
    ))


def _scan(conn: sqlite3.Connection) -> AtomicPreactionSnapshot:
    _require_original_atomic_carriers()
    _schema(conn)
    # Bound the relational set and exact text widths in SQLite before Python
    # materializes any malformed persisted row contents. This also fails
    # closed on BLOBs or NULLs rather than coercing identity fields.
    count = conn.execute("SELECT COUNT(*) FROM intents").fetchone()[0]
    if type(count) is not int or not 0 <= count <= _MAX:
        raise AtomicPreactionRejected("oversized or malformed pre-action intent set")
    bad_intent = conn.execute(
        "SELECT 1 FROM intents WHERE "
        "typeof(occurrence_id)!='text' OR length(CAST(occurrence_id AS BLOB))!=68 OR "
        "typeof(bound_action_id)!='text' OR length(CAST(bound_action_id AS BLOB))!=70 OR "
        "typeof(request_sha256)!='text' OR length(CAST(request_sha256 AS BLOB))!=64 OR "
        "typeof(chain_sha256)!='text' OR length(CAST(chain_sha256 AS BLOB))!=64 LIMIT 1"
    ).fetchone()
    bad_audit = conn.execute(
        "SELECT 1 FROM preaction_audit WHERE "
        "typeof(occurrence_id)!='text' OR length(CAST(occurrence_id AS BLOB))!=68 OR "
        "typeof(audit_sha256)!='text' OR length(CAST(audit_sha256 AS BLOB))!=64 LIMIT 1"
    ).fetchone()
    if bad_intent is not None or bad_audit is not None:
        raise AtomicPreactionRejected("pre-action persisted identity width or type changed")
    rows = conn.execute(
        "SELECT i.seq,i.occurrence_id,i.bound_action_id,i.request_sha256,"
        "i.chain_sha256,a.occurrence_id,a.audit_sha256 "
        "FROM intents i LEFT JOIN preaction_audit a ON a.seq=i.seq "
        "ORDER BY i.seq LIMIT ?", (_MAX + 1,),
    ).fetchall()
    audit_count = conn.execute("SELECT COUNT(*) FROM preaction_audit").fetchone()[0]
    if len(rows) > _MAX or audit_count != len(rows):
        raise AtomicPreactionRejected("orphan, missing or oversized pre-action audit")
    tip = _GENESIS
    occurrences: list[str] = []
    for seq, row in enumerate(rows, 1):
        index, occurrence, bound, request, chain, audit_occurrence, audit_sha = row
        claim = AtomicIntentClaim(occurrence, bound, request)
        _check_claim(claim)
        if (
            type(index) is not int or index != seq
            or not _hex_id(chain, _SHA) or audit_occurrence != occurrence
            or not _hex_id(audit_sha, _SHA)
            or chain != _chain(tip, seq, claim)
            or audit_sha != _audit(seq, claim, chain)
        ):
            raise AtomicPreactionRejected("pre-action row/audit chain mismatch")
        tip = chain
        occurrences.append(occurrence)
    _require_original_atomic_carriers()
    result = AtomicPreactionSnapshot(
        AtomicPreactionWitness(len(rows), tip), tuple(occurrences),
    )
    _require_original_atomic_carriers()
    return result


class DisconnectedAtomicPreactionLedger:
    """Local digest-only intent storage; intentionally has no execute method."""

    def __init__(self, path: Path) -> None:
        self._path = _path(path, create=False)
        with closing(self._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            _scan(conn)

    @classmethod
    def create(cls, path: Path) -> DisconnectedAtomicPreactionLedger:
        target = _path(path, create=True)
        with closing(sqlite3.connect(target)) as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            if conn.execute("PRAGMA journal_mode=WAL").fetchone()[0] != "wal":
                raise AtomicPreactionRejected("intent WAL setup refused")
            with conn:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(_INTENTS)
                conn.execute(_AUDITS)
                conn.execute("PRAGMA user_version=1")
                _schema(conn)
        return cls(path)

    def _open(self, *, read_only: bool) -> sqlite3.Connection:
        target = _path(self._path, create=False)
        uri = target.as_uri() + ("?mode=ro" if read_only else "?mode=rw")
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def inspect(self, retained: AtomicPreactionWitness) -> AtomicPreactionSnapshot:
        expected = _witness_image(retained)
        with closing(self._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            snapshot = _scan(conn)
        if (
            _witness_image(retained) != expected
            or _witness_image(snapshot.witness) != expected
        ):
            raise AtomicPreactionRejected("retained pre-action witness is stale or mismatched")
        return snapshot

    def reserve(
        self, claim: AtomicIntentClaim, *, retained: AtomicPreactionWitness,
    ) -> AtomicPreactionWitness:
        _check_claim(claim)
        expected = _witness_image(retained)
        frozen = (claim.occurrence_id, claim.bound_action_id, claim.request_sha256)
        with closing(self._open(read_only=False)) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            snapshot = _scan(conn)
            if (
                _witness_image(retained) != expected
                or _witness_image(snapshot.witness) != expected
                or expected[0] == _MAX
            ):
                raise AtomicPreactionRejected("pre-action CAS mismatch or ledger full")
            if frozen != (claim.occurrence_id, claim.bound_action_id, claim.request_sha256):
                raise AtomicPreactionRejected("synthetic intent changed")
            seq = expected[0] + 1
            tip = _chain(expected[1], seq, claim)
            audit = _audit(seq, claim, tip)
            try:
                conn.execute("INSERT INTO intents VALUES (?,?,?,?,?)", (seq, *frozen, tip))
                conn.execute(
                    "INSERT INTO preaction_audit VALUES (?,?,?)", (seq, frozen[0], audit),
                )
            except sqlite3.IntegrityError as exc:
                raise AtomicPreactionRejected("duplicate synthetic occurrence") from exc
            if (
                frozen != (claim.occurrence_id, claim.bound_action_id, claim.request_sha256)
                or _witness_image(retained) != expected
            ):
                raise AtomicPreactionRejected(
                    "synthetic intent or CAS witness changed before commit"
                )
        return AtomicPreactionWitness(seq, tip)
