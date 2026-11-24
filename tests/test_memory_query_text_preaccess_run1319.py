"""Run1319: Memory search rejects inexact query text before SQLite access.

The frozen MemoryQuery v1 constructor accepts str subclasses. The local store
must reject those carriers at its own ingress boundary before opening the
private SQLite database or sampling the expiry clock.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryQuery, MemorySchemaError, MemoryScope, SQLiteMemoryStore


class _ObservedText(str):
    def __new__(cls, value: str):
        instance = super().__new__(cls, value)
        instance.calls = []
        return instance

    def strip(self, *args, **kwargs):
        self.calls.append("strip")
        raise AssertionError("query text callback must not run")

    def __eq__(self, other):
        self.calls.append("eq")
        return super().__eq__(other)


def test_memory_query_text_subclass_is_rejected_before_sqlite_or_clock(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock_calls: list[bool] = []
    store = SQLiteMemoryStore(
        tmp_path / "memory.sqlite3",
        clock_ms=lambda: clock_calls.append(True) or 100,
    )
    query_text = _ObservedText("synthetic query")
    query = MemoryQuery(MemoryScope("fixture-owner", "private"), query_text)

    calls: list[str] = []

    def forbidden_sqlite(*_args: object, **_kwargs: object) -> None:
        calls.append("sqlite")
        raise AssertionError("inexact query text must be rejected before SQLite")

    def forbidden_clock() -> int:
        calls.append("clock")
        raise AssertionError("inexact query text must be rejected before clock")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect_readonly", forbidden_sqlite)
        patch.setattr(store, "_now", forbidden_clock)
        with pytest.raises(
            MemorySchemaError,
            match="memory search query changed during read",
        ):
            store.search(query)

    assert calls == []
    assert clock_calls == []
    assert query_text.calls == []

    # A normal exact-string query still follows the existing read path.
    assert store.search(
        MemoryQuery(MemoryScope("fixture-owner", "private"), "synthetic query")
    ) == []
