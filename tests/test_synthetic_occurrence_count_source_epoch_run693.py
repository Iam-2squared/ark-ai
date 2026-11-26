"""Read-only occurrence counts pin their original source across open callbacks.

The SQLite fixture contains only synthetic reservation metadata. A source
replacement is a new identity epoch even when the resolved path is equal;
no such callback may cause unrelated private schema or rows to be read.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency import durable_occurrence_review as occurrence


@pytest.mark.parametrize("equal", (True, False))
def test_count_rejects_path_resolve_rebase_before_sqlite_open(
    tmp_path, monkeypatch, equal,
):
    path = tmp_path / "synthetic.sqlite"
    ledger = occurrence.SyntheticOccurrenceStore(path)
    real_resolve = Path.resolve
    opened = []

    def hostile_resolve(self, *args, **kwargs):
        if self is path:
            ledger._path = (
                Path(str(path)) if equal else tmp_path / "unrelated.sqlite"
            )
            assert ledger._path is not path
        return real_resolve(self, *args, **kwargs)

    def forbidden_connection(*args, **kwargs):
        opened.append(True)
        pytest.fail("no private SQLite open after path identity changed")

    monkeypatch.setattr(Path, "resolve", hostile_resolve)
    monkeypatch.setattr(occurrence.sqlite3, "connect", forbidden_connection)
    with pytest.raises(
        occurrence.SyntheticReplayRejected,
        match="source changed during count",
    ):
        ledger.count_synthetic()
    assert opened == []


@pytest.mark.parametrize("equal", (True, False))
def test_count_rejects_connection_callback_rebase_before_schema_read(
    tmp_path, monkeypatch, equal,
):
    path = tmp_path / "synthetic.sqlite"
    ledger = occurrence.SyntheticOccurrenceStore(path)
    real_connect = occurrence.sqlite3.connect
    validations = []
    opened = []

    def reentrant_connect(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        opened.append(True)
        ledger._path = (
            Path(str(path)) if equal else tmp_path / "unrelated.sqlite"
        )
        assert ledger._path is not path
        return connection

    def forbidden_validation(_conn):
        validations.append(True)
        pytest.fail("no private ledger validation after source replacement")

    monkeypatch.setattr(occurrence.sqlite3, "connect", reentrant_connect)
    monkeypatch.setattr(occurrence, "_validate", forbidden_validation)
    with pytest.raises(
        occurrence.SyntheticReplayRejected,
        match="source changed during count",
    ):
        ledger.count_synthetic()
    assert opened == [True]
    assert validations == []


def test_normal_disconnected_count_is_read_only_and_non_authorizing(tmp_path):
    path = tmp_path / "synthetic.sqlite"
    ledger = occurrence.SyntheticOccurrenceStore(path)
    assert ledger.count_synthetic() == 0
    assert occurrence.SyntheticOccurrenceStore(path).count_synthetic() == 0
