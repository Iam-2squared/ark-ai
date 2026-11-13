"""Detached, bounded SQLite schema snapshot for synthetic local stores.

Requires a caller-opened, query-only SQLite Connection. It never opens a path,
reads application rows, changes a schema, attaches a database or grants access.
The digest cannot authenticate its source, prove WAL custody, cross-store
atomicity, or establish an independently retained reference.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass

_DOMAIN = b"ARK-disconnected-sqlite-schema-probe-v1\0"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_ITEMS = 128
_MAX_DDL_BYTES = 65_536
_MAX_VERSION = 2**31 - 1
_QUERY = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
# SQL-side count and byte budget before any private DDL is hydrated by Python.
_PREFLIGHT_QUERY = (
    "SELECT COUNT(*), COALESCE(SUM(length(CAST(sql AS BLOB))), 0) "
    "FROM sqlite_master"
)

# The caller may supply private schema SQL through a local SQLite connection.
# Reject altered codec, digest and admission rules before reading that SQL.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_QUERY = _QUERY
_ORIGINAL_PREFLIGHT_QUERY = _PREFLIGHT_QUERY
_ORIGINAL_LIMITS = (_MAX_ITEMS, _MAX_DDL_BYTES, _MAX_VERSION)


class SQLiteSchemaProbeRejected(ValueError):
    """A supplied read-only schema snapshot is malformed or inconsistent."""


@dataclass(frozen=True, slots=True)
class DisconnectedSQLiteSchemaSeal:
    schema_sha256: str
    object_count: int
    user_version: int
    schema_version: int

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False

    @property
    def wal_snapshot_verified(self) -> bool:
        return False

    @property
    def cross_store_atomicity_proven(self) -> bool:
        return False

    @property
    def application_data_disclosure_authorized(self) -> bool:
        return False


_SEAL_TYPE = DisconnectedSQLiteSchemaSeal
_DENIALS = (
    "source_authenticated", "independent_custody_proven",
    "wal_snapshot_verified", "cross_store_atomicity_proven",
    "application_data_disclosure_authorized",
)
# A getter replaced with a different False-only callback is not an original
# denial. Pin descriptors at module import, before untrusted reviews.
_ORIGINAL_DENIALS = tuple(vars(_SEAL_TYPE)[key] for key in _DENIALS)
_SEAL_FIELDS = ("schema_sha256", "object_count", "user_version", "schema_version")
_SEAL_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_SEAL_DESCRIPTORS = tuple(
    vars(_SEAL_TYPE).get(key) for key in _SEAL_FIELDS + _SEAL_HOOKS
)


def _require_original_schema_probe() -> None:
    """Fail before accessing a private seal, SQLite metadata or caller callbacks.

    The fence checks in-process descriptor identity, not authenticated source
    custody. A mutable Python runtime is not a security sandbox.
    """
    if (
        DisconnectedSQLiteSchemaSeal is not _SEAL_TYPE
        or any(
            vars(_SEAL_TYPE).get(key) is not original
            for key, original in zip(
                _SEAL_FIELDS + _SEAL_HOOKS,
                _ORIGINAL_SEAL_DESCRIPTORS, strict=True,
            )
        )
        or any(
            vars(_SEAL_TYPE).get(key) is not original
            for key, original in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
        )
        or hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _SHA is not _ORIGINAL_SHA_PATTERN
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _QUERY is not _ORIGINAL_QUERY
        or _PREFLIGHT_QUERY is not _ORIGINAL_PREFLIGHT_QUERY
        or any(
            type(value) is not int for value in
            (_MAX_ITEMS, _MAX_DDL_BYTES, _MAX_VERSION)
        )
        or (_MAX_ITEMS, _MAX_DDL_BYTES, _MAX_VERSION) != _ORIGINAL_LIMITS
        # A substituted read/receipt helper can forge schema evidence while
        # appearing to use the original digest and deny-only carrier type.
        or any(
            globals().get(name) is not original
            for name, original in zip(
                _SCHEMA_HELPER_NAMES, _ORIGINAL_SCHEMA_HELPERS, strict=True,
            )
        )
    ):
        raise SQLiteSchemaProbeRejected("schema probe contract changed or acquired authority")


def _seal_fields(seal: DisconnectedSQLiteSchemaSeal) -> tuple[str, int, int, int]:
    _require_original_schema_probe()
    return (
        seal.schema_sha256, seal.object_count, seal.user_version,
        seal.schema_version,
    )


def _assert_inert_seal(seal: object) -> None:
    """Check deny-only descriptors and the entire carrier after each callback."""
    _require_original_schema_probe()
    if type(seal) is not _SEAL_TYPE:
        raise SQLiteSchemaProbeRejected("schema seal acquired authority")
    fields = _seal_fields(seal)
    for key, original in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True):
        if (
            getattr(_SEAL_TYPE, key) is not original
            or getattr(seal, key) is not False
            or _seal_fields(seal) != fields
        ):
            raise SQLiteSchemaProbeRejected("schema seal acquired authority")
    if any(
        getattr(_SEAL_TYPE, key) is not original
        for key, original in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
    ) or _seal_fields(seal) != fields:
        raise SQLiteSchemaProbeRejected("schema seal acquired authority")


def _state(connection: sqlite3.Connection) -> tuple[str, int, int, int]:
    _require_original_schema_probe()
    databases = tuple(connection.execute("PRAGMA database_list"))
    if (
        len(databases) != 1 or databases[0][1] != "main"
        or type(databases[0][0]) is not int
    ):
        raise SQLiteSchemaProbeRejected("only a single main database is supported")
    query_only = connection.execute("PRAGMA query_only").fetchone()
    if query_only != (1,):
        raise SQLiteSchemaProbeRejected("query-only connection required")
    user = connection.execute("PRAGMA user_version").fetchone()
    schema = connection.execute("PRAGMA schema_version").fetchone()
    if (
        user is None or schema is None
        or type(user[0]) is not int or type(schema[0]) is not int
        or not 0 <= user[0] <= _MAX_VERSION
        or not 0 <= schema[0] <= _MAX_VERSION
    ):
        raise SQLiteSchemaProbeRejected("invalid schema/version metadata")
    _require_original_schema_probe()
    preflight = connection.execute(_PREFLIGHT_QUERY).fetchone()
    _require_original_schema_probe()
    if (
        preflight is None or len(preflight) != 2
        or type(preflight[0]) is not int or not 0 <= preflight[0] <= _MAX_ITEMS
        or type(preflight[1]) is not int or not 0 <= preflight[1] <= _MAX_DDL_BYTES
    ):
        raise SQLiteSchemaProbeRejected("schema SQL preflight exceeds byte or row budget")
    records = []
    size = 0
    for record in connection.execute(_QUERY):
        if len(records) >= _MAX_ITEMS or type(record) is not tuple or len(record) != 4:
            raise SQLiteSchemaProbeRejected("schema object count exceeds budget")
        typ, name, table, sql = record
        if (
            type(typ) is not str or typ not in ("index", "table", "view", "trigger")
            or type(name) is not str or not name
            or type(table) is not str or not table
            or sql is not None and type(sql) is not str
        ):
            raise SQLiteSchemaProbeRejected("noncanonical schema object")
        # A SQLite autoindex has no SQL text but still belongs in the seal.
        _require_original_schema_probe()
        payload = json.dumps(record, ensure_ascii=True, separators=(",", ":"))
        _require_original_schema_probe()
        size += len(payload.encode("ascii"))
        if size > _MAX_DDL_BYTES:
            raise SQLiteSchemaProbeRejected("schema text exceeds byte budget")
        records.append(record)
    # Return only a digest, never the SQL text (which may contain private literals).
    packed = json.dumps(
        (user[0], schema[0], records), ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    _require_original_schema_probe()
    digest = hashlib.sha256(_DOMAIN + packed).hexdigest()
    _require_original_schema_probe()
    return digest, len(records), user[0], schema[0]


# Keep the helper admission boundary separate from the public capture code.
# These callbacks are not plugins and cannot be replaced to grant schema
# authentication, data disclosure or an authenticated WAL snapshot.
_SCHEMA_HELPER_NAMES = ("_state", "_seal_fields", "_assert_inert_seal")
_ORIGINAL_SCHEMA_HELPERS = tuple(globals()[name] for name in _SCHEMA_HELPER_NAMES)


def capture_disconnected_sqlite_schema(
    connection: sqlite3.Connection,
) -> DisconnectedSQLiteSchemaSeal:
    """Capture one transaction-scoped synthetic schema; leave no open BEGIN."""
    _require_original_schema_probe()
    if type(connection) is not sqlite3.Connection or connection.in_transaction:
        raise SQLiteSchemaProbeRejected("exact idle SQLite connection required")
    try:
        connection.execute("BEGIN")
        first = _state(connection)
        if _state(connection) != first:
            raise SQLiteSchemaProbeRejected("schema changed within read transaction")
        connection.execute("COMMIT")
        seal = DisconnectedSQLiteSchemaSeal(*first)
        _assert_inert_seal(seal)
        if _seal_fields(seal) != first:
            raise SQLiteSchemaProbeRejected("schema seal changed during capture")
        return seal
    except sqlite3.Error as exc:
        raise SQLiteSchemaProbeRejected("cannot read stable SQLite schema") from exc
    finally:
        if connection.in_transaction:
            connection.execute("ROLLBACK")


def review_disconnected_sqlite_schema(
    connection: sqlite3.Connection, retained: DisconnectedSQLiteSchemaSeal,
) -> DisconnectedSQLiteSchemaSeal:
    """Compare with caller-supplied prior seal; no trust or consent is inferred."""
    _require_original_schema_probe()
    if (
        type(retained) is not DisconnectedSQLiteSchemaSeal
        or type(retained.schema_sha256) is not str
        or _SHA.fullmatch(retained.schema_sha256) is None
        or any(type(x) is not int for x in (
            retained.object_count, retained.user_version, retained.schema_version,
        ))
        or not 0 <= retained.object_count <= _MAX_ITEMS
        or not 0 <= retained.user_version <= _MAX_VERSION
        or not 0 <= retained.schema_version <= _MAX_VERSION
    ):
        raise SQLiteSchemaProbeRejected("invalid retained schema seal")
    original = (
        retained.schema_sha256, retained.object_count,
        retained.user_version, retained.schema_version,
    )
    _assert_inert_seal(retained)
    current = capture_disconnected_sqlite_schema(connection)
    if (
        _seal_fields(retained) != original
        or retained.schema_sha256 is not original[0]
        or _seal_fields(current) != original
    ):
        raise SQLiteSchemaProbeRejected("retained and current schema differ")
    _assert_inert_seal(retained)
    _assert_inert_seal(current)
    if _seal_fields(retained) != original or _seal_fields(current) != original:
        raise SQLiteSchemaProbeRejected("schema seal changed during review")
    return current
