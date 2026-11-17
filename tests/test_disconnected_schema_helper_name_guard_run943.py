"""Run943: schema helper-name vector is an import-time preaccess contract.

The only database is a disposable in-memory synthetic schema. A forged alias
must never execute a substituted schema reader or be accepted as a receipt.
"""

import sqlite3

import pytest

from ark import disconnected_sqlite_schema_probe as schema


def _query_only_connection():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE synthetic_fixture(id INTEGER PRIMARY KEY)")
    connection.execute("PRAGMA query_only=ON")
    return connection


@pytest.mark.parametrize("form", ("reordered", "equal_replacement", "alias"))
def test_replaced_helper_names_are_rejected_before_schema_reader(monkeypatch, form):
    connection = _query_only_connection()
    calls = []

    def poisoned(_connection):
        calls.append("unsafe schema reader called")
        raise AssertionError("replaced reader was invoked")

    try:
        old_names = schema._SCHEMA_HELPER_NAMES
        if form == "reordered":
            names = ("_seal_fields", "_state", "_assert_inert_seal")
        elif form == "equal_replacement":
            names = tuple(list(old_names))
            assert names == old_names and names is not old_names
        else:
            monkeypatch.setattr(schema, "_synthetic_alias", schema._state, raising=False)
            monkeypatch.setattr(schema, "_state", poisoned)
            names = ("_synthetic_alias", "_seal_fields", "_assert_inert_seal")
        monkeypatch.setattr(schema, "_SCHEMA_HELPER_NAMES", names)
        with pytest.raises(schema.SQLiteSchemaProbeRejected, match="contract changed"):
            schema.capture_disconnected_sqlite_schema(connection)
        assert not calls
        assert connection.in_transaction is False
    finally:
        connection.close()


def test_original_helper_vector_still_captures_non_authorizing_seal():
    connection = _query_only_connection()
    try:
        seal = schema.capture_disconnected_sqlite_schema(connection)
        assert seal.object_count == 1
        assert seal.schema_version >= 1
        assert len(seal.schema_sha256) == 64
        assert seal.source_authenticated is False
        assert seal.wal_snapshot_verified is False
        assert seal.application_data_disclosure_authorized is False
    finally:
        connection.close()
