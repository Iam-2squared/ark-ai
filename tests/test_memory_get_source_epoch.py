"""Guard transient SQLite Memory get() source drift before the next callback."""

from pathlib import Path

import pytest

import ark.memory.sqlite_store as sqlite_store
from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("interleave", ["connect", "decode"])
def test_get_rejects_source_drift_before_clock_can_restore_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, interleave: str,
) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "profile")
    record = store.put(MemoryWrite(scope, "key", "synthetic-value"))
    original_source = store.path
    clock_samples = []

    def clock_restores_source() -> int:
        clock_samples.append(1)
        store.path = original_source
        return 1000

    store._clock_ms = clock_restores_source

    if interleave == "connect":
        original_connect = store._connect_readonly

        def retarget_after_open():
            conn = original_connect()
            store.path = tmp_path / "retargeted.sqlite"
            return conn

        monkeypatch.setattr(store, "_connect_readonly", retarget_after_open)
    else:
        original_decode = sqlite_store._record

        def retarget_after_decode(row):
            decoded = original_decode(row)
            store.path = tmp_path / "retargeted.sqlite"
            return decoded

        monkeypatch.setattr(sqlite_store, "_record", retarget_after_decode)

    try:
        with pytest.raises(
            MemorySchemaError, match="memory get source changed during read",
        ):
            store.get(record.memory_id, scope)
        # The later clock callback would have concealed temporary drift.
        assert clock_samples == []
    finally:
        store.path = original_source


def test_get_source_epoch_valid_positive_control(tmp_path: Path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "profile")
    record = store.put(MemoryWrite(scope, "key", "synthetic-value"))
    assert store.get(record.memory_id, scope) == record
