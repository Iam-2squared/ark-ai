"""A privacy inventory must not return cached rows changed after hashing."""

from pathlib import Path
from sys import _getframe

import pytest

import ark.personal_context_retention_review as module
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import (
    RetentionState,
    SyntheticRetentionItem,
    SyntheticRetentionRejected,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _state(tmp_path: Path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("private-owner", "profile")
    for name in ("first", "second"):
        memory.put(MemoryWrite(
            scope, name, "PRIVATE FIXTURE " + name, expires_at_ms=120,
        ))
    veto = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    return memory, scope, veto


def _review(state):
    return module.review_synthetic_retention_inventory(
        state[0], state[1], state[2], now_ms=100,
    )


@pytest.mark.parametrize("phase", ("row", "veto"))
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("memory_id", "mem_" + "0" * 64),
        ("revision", 999),
        ("state", RetentionState.EXPIRED),
    ],
)
def test_cached_inventory_item_mutation_before_digest_return_is_refused(
    tmp_path, monkeypatch, phase, field, value,
):
    state = _state(tmp_path)
    mutations = 0

    def corrupt_retained_item():
        nonlocal mutations
        # Reentrant row/veto callbacks can inspect their calling frame.
        # Do not replace the pinned dataclass constructor: that is correctly
        # rejected before any row is read by the newer pre-access contract.
        selected = _getframe(2).f_locals["selected"]
        assert len(selected) == (1 if phase == "row" else 2)
        assert type(selected[0]) is SyntheticRetentionItem
        object.__setattr__(selected[0], field, value)
        mutations += 1

    if phase == "row":
        original = module._record
        calls = 0

        def changed_second_record(row):
            nonlocal calls
            calls += 1
            if calls == 2:
                corrupt_retained_item()
            return original(row)

        monkeypatch.setattr(module, "_record", changed_second_record)
    else:
        original = module.review_revocation_continuity
        calls = 0

        def changed_second_veto(*args, **kwargs):
            nonlocal calls
            outcome = original(*args, **kwargs)
            calls += 1
            if calls == 2:
                corrupt_retained_item()
            return outcome

        monkeypatch.setattr(
            module, "review_revocation_continuity", changed_second_veto,
        )

    with pytest.raises(
        SyntheticRetentionRejected, match="retention inventory dependency changed",
    ):
        _review(state)
    # The original row/veto codec is required before any retained item is read.
    assert mutations == 0


def test_stable_inventory_remains_content_free_and_non_authoritative(tmp_path):
    result = _review(_state(tmp_path))
    assert len(result.items) == 2
    assert result.expired_count == 0
    assert result.erasure_completed is False
    assert result.deletion_authorized is False
    assert result.context_use_authorized is False
    assert "PRIVATE FIXTURE" not in repr(result)
