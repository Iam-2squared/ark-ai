"""Run1309: Memory store APIs reject string-subclass scope identities before I/O."""

from __future__ import annotations

import pytest

from ark.memory import MemoryQuery, MemoryScope, MemoryWrite, SQLiteMemoryStore


class _StrSubclass(str):
    pass


@pytest.mark.parametrize("field", ("owner_id", "namespace"))
@pytest.mark.parametrize("api", ("get", "search", "delete", "purge", "events"))
def test_scope_identifier_subclasses_are_rejected_before_store_io(
    tmp_path, monkeypatch: pytest.MonkeyPatch, field: str, api: str,
) -> None:
    clock_calls: list[bool] = []
    store = SQLiteMemoryStore(
        tmp_path / "memory.sqlite3",
        clock_ms=lambda: clock_calls.append(True) or 100,
    )
    valid = MemoryScope("fixture-owner", "private")
    saved = store.put(MemoryWrite(valid, "source", "synthetic-private"))
    clock_calls.clear()

    owner = _StrSubclass(valid.owner_id) if field == "owner_id" else valid.owner_id
    namespace = (
        _StrSubclass(valid.namespace) if field == "namespace" else valid.namespace
    )
    scope = MemoryScope(owner, namespace)
    assert type(scope) is MemoryScope

    calls: list[str] = []

    def forbidden_io(*_args: object, **_kwargs: object) -> None:
        calls.append("sqlite")
        raise AssertionError("inexact scope fields must be rejected before SQLite")

    def forbidden_clock() -> int:
        calls.append("clock")
        raise AssertionError("inexact scope fields must be rejected before clock")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect", forbidden_io)
        patch.setattr(store, "_connect_readonly", forbidden_io)
        patch.setattr(store, "_now", forbidden_clock)

        with pytest.raises(TypeError, match="scope identifiers must be exact strings"):
            if api == "get":
                store.get(saved.memory_id, scope, include_expired=True)
            elif api == "search":
                store.search(MemoryQuery(scope))
            elif api == "delete":
                store.delete(saved.memory_id, scope, expected_revision=1)
            elif api == "purge":
                store.purge_expired(scope=scope)
            else:
                store.events(scope)

    assert calls == []
    assert clock_calls == []
    assert store.get(saved.memory_id, valid, include_expired=True) == saved
    assert [event.operation for event in store.events(valid)] == ["create"]
