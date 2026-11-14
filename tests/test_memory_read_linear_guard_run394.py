"""Broad private Memory queries retain linear decoded-row verification.

Do not drop the post-callback drift checks to make the search faster.
Only synthetic local rows are used; no external context disclosure.
"""

from pathlib import Path

import pytest

import ark.memory.sqlite_store as module
from ark.memory import MemoryQuery, MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("text", ("", "apple"))
def test_large_offline_scope_decoded_read_guard_scales_linearly(
    tmp_path: Path, monkeypatch, text,
):
    store = SQLiteMemoryStore(tmp_path / "fixture.sqlite", clock_ms=lambda: 123)
    scope = MemoryScope("offline", "private")
    for index in range(32):
        store.put(MemoryWrite(scope, f"row-{index}", f"private apple {index}"))

    original = module._hydrated_record_epoch
    checks = 0

    def counted(record):
        nonlocal checks
        checks += 1
        return original(record)

    monkeypatch.setattr(module, "_hydrated_record_epoch", counted)
    results = store.search(MemoryQuery(scope, text, limit=100))
    assert len(results) == 32
    assert all(record.scope == scope for record in results)
    assert 32 <= checks <= 32 * 12
