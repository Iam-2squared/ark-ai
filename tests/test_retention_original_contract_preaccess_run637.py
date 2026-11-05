"""Privacy inventory must reject altered DTO hooks before private row reads."""

from __future__ import annotations

import pytest

import ark.personal_context_retention_review as retention
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _case(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "private.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("private-fixture", "only-local")
    memory.put(MemoryWrite(scope, "source", "DO-NOT-EXPOSE-CONTENT"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    return memory, scope, ledger


@pytest.mark.parametrize(
    ("kind", "name"),
    (
        ("denial", "erasure_completed"),
        ("denial", "deletion_authorized"),
        ("denial", "context_use_authorized"),
        ("inventory_slot", "scope_digest"),
        ("inventory_slot", "items"),
        ("inventory_init", "__init__"),
        ("item_init", "__init__"),
        ("item_slot", "revision"),
    ),
)
def test_preinstalled_executable_retention_hook_never_runs_or_reads_memory(
    tmp_path, monkeypatch, kind, name,
):
    memory, scope, ledger = _case(tmp_path)
    triggered = []

    def rogue(*_args, **_kwargs):
        triggered.append(name)
        return False

    def memory_read():
        triggered.append("sqlite-open")
        raise AssertionError("private Memory should not be read")

    if kind in ("denial", "inventory_slot"):
        monkeypatch.setattr(
            retention.SyntheticRetentionInventory, name, property(rogue),
        )
    elif kind == "inventory_init":
        monkeypatch.setattr(retention.SyntheticRetentionInventory, name, rogue)
    elif kind == "item_init":
        monkeypatch.setattr(retention.SyntheticRetentionItem, name, rogue)
    else:
        monkeypatch.setattr(retention.SyntheticRetentionItem, name, property(rogue))
    monkeypatch.setattr(memory, "_connect_readonly", memory_read)

    with pytest.raises(
        retention.SyntheticRetentionRejected,
        match="authority denial descriptor changed",
    ):
        retention.review_synthetic_retention_inventory(
            memory, scope, ledger, now_ms=100,
        )
    assert triggered == []


def test_original_private_retention_inventory_remains_denied(tmp_path):
    memory, scope, ledger = _case(tmp_path)
    result = retention.review_synthetic_retention_inventory(
        memory, scope, ledger, now_ms=100,
    )
    assert len(result.items) == 1
    assert result.erasure_completed is False
    assert result.deletion_authorized is False
    assert result.context_use_authorized is False
    assert "DO-NOT-EXPOSE-CONTENT" not in repr(result)
