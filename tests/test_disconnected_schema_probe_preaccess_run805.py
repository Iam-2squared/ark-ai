"""SQLite schema seals must fail before swapped Python getters or codecs.

These are offline metadata probes, never trusted storage custody, disclosure
approval, filesystem erasure, or authorization to execute a real tool.
"""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from types import SimpleNamespace

import pytest

from ark import disconnected_sqlite_schema_probe as probe


def _db() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE item (id INTEGER PRIMARY KEY, value TEXT)")
    connection.execute("PRAGMA query_only=ON")
    return connection


_FIELDS = (
    "schema_sha256", "object_count", "user_version", "schema_version",
)
# Do not patch inherited __new__: CPython can retain a changed tp_new slot.
_HOOKS = ("__init__", "__getattribute__", "__getattr__")
_DENIALS = (
    "source_authenticated", "independent_custody_proven",
    "wal_snapshot_verified", "cross_store_atomicity_proven",
    "application_data_disclosure_authorized",
)


@pytest.mark.parametrize("field", _FIELDS + _HOOKS + _DENIALS)
@pytest.mark.parametrize("operation", ("capture", "review"))
def test_poisoned_schema_seal_descriptor_never_invoked(
    field: str, operation: str,
) -> None:
    touched: list[str] = []
    with closing(_db()) as connection:
        retained = probe.capture_disconnected_sqlite_schema(connection)

        def poison(*_args: object, **_kwargs: object) -> object:
            touched.append(field)
            raise AssertionError("hostile schema descriptor executed")

        replacement = property(poison) if field in _FIELDS + _DENIALS else poison
        carrier = probe.DisconnectedSQLiteSchemaSeal
        had_own = field in vars(carrier)
        original = vars(carrier).get(field)
        try:
            # Restoration must delete originally inherited lookup hooks;
            # MonkeyPatch.setattr would leave an own class descriptor.
            setattr(carrier, field, replacement)
            with pytest.raises(probe.SQLiteSchemaProbeRejected, match="contract"):
                if operation == "capture":
                    probe.capture_disconnected_sqlite_schema(connection)
                else:
                    probe.review_disconnected_sqlite_schema(connection, retained)
        finally:
            if had_own:
                setattr(carrier, field, original)
            elif field in vars(carrier):
                delattr(carrier, field)
        assert touched == []
        assert not connection.in_transaction


@pytest.mark.parametrize(
    ("field", "substitute"),
    (
        ("_SHA", re.compile(r".*")),
        ("_DOMAIN", b"untrusted-domain"),
        ("_QUERY", "SELECT sql FROM sqlite_master"),
        ("_MAX_ITEMS", 2048),
        ("_MAX_DDL_BYTES", 2**20),
        ("_MAX_VERSION", 2**32),
        ("_MAX_ITEMS", True),
    ),
)
def test_changed_probe_admission_rejected_before_sqlite(
    monkeypatch: pytest.MonkeyPatch, field: str, substitute: object,
) -> None:
    with closing(_db()) as connection:
        monkeypatch.setattr(probe, field, substitute)
        with pytest.raises(probe.SQLiteSchemaProbeRejected, match="contract"):
            probe.capture_disconnected_sqlite_schema(connection)
        assert not connection.in_transaction


@pytest.mark.parametrize("dependency", ("json", "hashlib"))
def test_swapped_codec_or_hash_never_receives_schema_text(
    monkeypatch: pytest.MonkeyPatch, dependency: str,
) -> None:
    touched: list[str] = []

    def poison(*_args: object, **_kwargs: object) -> object:
        touched.append(dependency)
        raise AssertionError("hostile serializer invoked")

    replacement = (
        SimpleNamespace(dumps=poison)
        if dependency == "json"
        else SimpleNamespace(sha256=poison)
    )
    with closing(_db()) as connection:
        monkeypatch.setattr(probe, dependency, replacement)
        with pytest.raises(probe.SQLiteSchemaProbeRejected, match="contract"):
            probe.capture_disconnected_sqlite_schema(connection)
        assert touched == []
        assert not connection.in_transaction


def test_untouched_schema_seal_remains_stable_and_deny_only() -> None:
    with closing(_db()) as connection:
        baseline = probe.capture_disconnected_sqlite_schema(connection)
        assert probe.review_disconnected_sqlite_schema(connection, baseline) == baseline
        assert baseline.object_count == 1
        assert baseline.source_authenticated is False
        assert baseline.independent_custody_proven is False
        assert baseline.wal_snapshot_verified is False
        assert baseline.cross_store_atomicity_proven is False
        assert baseline.application_data_disclosure_authorized is False
