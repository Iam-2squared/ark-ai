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


def _assert_inert_seal(seal: object) -> None:
    """A local schema hash must not impersonate trusted custody or disclosure."""
    if (
        type(seal) is not _SEAL_TYPE
        or seal.source_authenticated is not False
        or seal.independent_custody_proven is not False
        or seal.wal_snapshot_verified is not False
        or seal.cross_store_atomicity_proven is not False
        or seal.application_data_disclosure_authorized is not False
    ):
        raise SQLiteSchemaProbeRejected("schema seal acquired authority")


def _state(connection: sqlite3.Connection) -> tuple[str, int, int, int]:
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
        payload = json.dumps(record, ensure_ascii=True, separators=(",", ":"))
        size += len(payload.encode("ascii"))
        if size > _MAX_DDL_BYTES:
            raise SQLiteSchemaProbeRejected("schema text exceeds byte budget")
        records.append(record)
    # Return only a digest, never the SQL text (which may contain private literals).
    packed = json.dumps(
        (user[0], schema[0], records), ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + packed).hexdigest(), len(records), user[0], schema[0]


def capture_disconnected_sqlite_schema(
    connection: sqlite3.Connection,
) -> DisconnectedSQLiteSchemaSeal:
    """Capture one transaction-scoped synthetic schema; leave no open BEGIN."""
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
        (retained.schema_sha256, retained.object_count,
         retained.user_version, retained.schema_version) != original
        or retained.schema_sha256 is not original[0]
        or current != retained
    ):
        raise SQLiteSchemaProbeRejected("retained and current schema differ")
    _assert_inert_seal(retained)
    _assert_inert_seal(current)
    return current
