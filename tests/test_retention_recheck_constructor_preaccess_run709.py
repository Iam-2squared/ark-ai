"""Retention recheck constructor custody precedes private-memory projection.

Synthetic in-process fault injection only. These tests never erase memories,
make a consent decision, or authorize export, notification, or execution.
"""

from __future__ import annotations

import pytest

import ark.personal_context_retention_recheck_review as retention
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _state(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "private")
    memory.put(MemoryWrite(
        scope, "offline", "PRIVATE-FIXTURE-BYTES", expires_at_ms=101,
    ))
    revocations = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    cached = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=100,
    )
    return memory, scope, revocations, cached


@pytest.mark.parametrize("injection", ("before_read", "after_first_projection"))
def test_constructor_replacement_denied_before_next_private_projection(
    tmp_path, monkeypatch, injection,
):
    state = _state(tmp_path)
    reviewed: list[str] = []
    hostile_calls: list[str] = []

    def hostile_constructor(*_args, **_kwargs):
        hostile_calls.append("forged constructor")
        raise AssertionError("private data reached substituted constructor")

    original = retention.review_synthetic_retention_inventory

    def witness_projection(*args, **kwargs):
        reviewed.append("private read")
        if len(reviewed) > 1:
            raise AssertionError("second private inventory projection was reached")
        observed = original(*args, **kwargs)
        monkeypatch.setattr(
            retention.SyntheticRetentionRecheck, "__init__", hostile_constructor,
        )
        return observed

    with monkeypatch.context() as patch:
        if injection == "before_read":
            patch.setattr(
                retention.SyntheticRetentionRecheck,
                "__init__", hostile_constructor,
            )
            patch.setattr(
                retention, "review_synthetic_retention_inventory",
                lambda *_args, **_kwargs: pytest.fail(
                    "preinstalled constructor reached private SQLite"
                ),
            )
        else:
            patch.setattr(
                retention, "review_synthetic_retention_inventory",
                witness_projection,
            )
        with pytest.raises(
            retention.SyntheticRetentionRecheckRejected,
            match="original denial implementation",
        ):
            retention.review_synthetic_retention_recheck(
                *state, now_ms=101, max_age_ms=10,
            )
    assert hostile_calls == []
    assert len(reviewed) == (0 if injection == "before_read" else 1)


def test_original_retention_constructor_remains_non_authorizing(tmp_path):
    result = retention.review_synthetic_retention_recheck(
        *_state(tmp_path), now_ms=101, max_age_ms=10,
    )
    assert result.expired_memory_ids
    assert result.deletion_authorized is False
    assert result.erasure_completed is False
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert "PRIVATE-FIXTURE-BYTES" not in repr(result)
