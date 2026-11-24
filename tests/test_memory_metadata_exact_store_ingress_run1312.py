"""Run1312: Memory metadata ingress rejects inexact carriers before store I/O."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


class _TextSubclass(str):
    pass


def _seed_store(tmp_path: Path) -> tuple[SQLiteMemoryStore, MemoryScope, object]:
    store = SQLiteMemoryStore(tmp_path / "memory-metadata-exact.sqlite3")
    scope = MemoryScope("owner-a", "personal")
    original = store.put(
        MemoryWrite(scope, "source-a", "original content", {"label": "original"}),
    )
    return store, scope, original


@pytest.mark.parametrize(
    "metadata",
    [
        {_TextSubclass("label"): "replacement"},
        {"label": _TextSubclass("replacement")},
    ],
    ids=("subclass-key", "subclass-value"),
)
def test_put_rejects_metadata_string_subclasses_before_sqlite_or_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    metadata: dict[str, str],
) -> None:
    store, scope, original = _seed_store(tmp_path)
    invalid = MemoryWrite(scope, "source-a", "replacement content", metadata)
    calls: list[str] = []

    def unexpected_connect() -> None:
        calls.append("connect")
        raise AssertionError("invalid metadata reached SQLite")

    def unexpected_clock() -> int:
        calls.append("clock")
        raise AssertionError("invalid metadata sampled the clock")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect", unexpected_connect)
        patch.setattr(store, "_now", unexpected_clock)
        with pytest.raises(MemorySchemaError, match="metadata"):
            store.put(invalid, expected_revision=original.revision)

    assert calls == []
    assert store.get(original.memory_id, scope) == original


class _ExplodingMapping(Mapping):
    def __init__(self) -> None:
        self.calls = 0

    def __getitem__(self, key: object) -> object:
        self.calls += 1
        raise AssertionError("replaced metadata mapping was read")

    def __iter__(self):
        self.calls += 1
        raise AssertionError("replaced metadata mapping was iterated")

    def __len__(self) -> int:
        self.calls += 1
        raise AssertionError("replaced metadata mapping was measured")

    def items(self):
        self.calls += 1
        raise AssertionError("replaced metadata mapping items were read")


def test_put_rejects_reflectively_replaced_metadata_carrier_before_callbacks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, scope, original = _seed_store(tmp_path)
    invalid = MemoryWrite(scope, "source-a", "replacement content", {"label": "replacement"})
    hostile = _ExplodingMapping()
    object.__setattr__(invalid, "metadata", hostile)
    calls: list[str] = []

    def unexpected_connect() -> None:
        calls.append("connect")
        raise AssertionError("invalid metadata reached SQLite")

    def unexpected_clock() -> int:
        calls.append("clock")
        raise AssertionError("invalid metadata sampled the clock")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect", unexpected_connect)
        patch.setattr(store, "_now", unexpected_clock)
        with pytest.raises(MemorySchemaError, match="metadata"):
            store.put(invalid, expected_revision=original.revision)

    assert hostile.calls == 0
    assert calls == []
    assert store.get(original.memory_id, scope) == original
