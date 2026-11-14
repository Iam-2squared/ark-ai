"""Bound local Memory/ActionAudit SQLite paths before side effects (Run855).

These are disposable fixtures only; they do not prove atomic path custody,
trusted time, audit authenticity or permission to dispatch a tool.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError
from ark.memory import MemorySchemaError, SQLiteMemoryStore


@pytest.mark.parametrize("kind", ("memory", "audit"))
@pytest.mark.parametrize("invalid", ("overlong", "sidecar", "nul", "root"))
def test_rejects_invalid_path_before_filesystem_and_clock(
    tmp_path: Path, kind: str, invalid: str,
) -> None:
    if invalid == "overlong":
        path = tmp_path / ("x" * 4100)
    elif invalid == "sidecar":
        # Absolute main path is under 4096 chars, but its -journal is not.
        path = Path("/") / ("a" * 4088)
    elif invalid == "nul":
        path = tmp_path / "private\x00database.sqlite"
    else:
        path = Path("/")

    def forbidden_clock() -> int:
        raise AssertionError("invalid path reached caller clock")

    error = MemorySchemaError if kind == "memory" else ActionAuditSchemaError
    with pytest.raises(error, match="path"):
        if kind == "memory":
            SQLiteMemoryStore(path, clock_ms=forbidden_clock)
        else:
            SQLiteActionAudit(path, clock_ms=forbidden_clock)
    # Invalid input must not create a DB or accidentally probe the long name.
    assert list(tmp_path.iterdir()) == []


def test_valid_small_memory_and_audit_paths_remain_usable(tmp_path: Path) -> None:
    memory_path = tmp_path / "memory.sqlite"
    audit_path = tmp_path / "audit.sqlite"
    memory = SQLiteMemoryStore(memory_path, clock_ms=lambda: 10)
    audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 10)
    assert memory.path == memory_path
    assert audit.path == audit_path
    assert memory_path.is_file()
    assert audit_path.is_file()
