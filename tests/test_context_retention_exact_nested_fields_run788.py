"""Deny value-equal nested retention witness substitutions before SQLite.

Disposable Memory/veto stores only. These receipts cannot authorize context
reuse, erasure, external disclosure or a real tool dispatch.
"""

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_recheck_review import (
    SyntheticRetentionRecheckRejected,
    review_synthetic_retention_recheck,
)
from ark.personal_context_retention_review import (
    RetentionState,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


class EqualString(str):
    """A value-equal but nonexact identity carrier."""


def _fixture(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "private")
    memory.put(MemoryWrite(
        scope, "source", "fixture private bytes", expires_at_ms=150,
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    cached = review_synthetic_retention_inventory(memory, scope, veto, now_ms=100)
    assert cached.items[0].state is RetentionState.NOT_EXPIRED
    return memory, scope, veto, cached


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("revision", True),
        ("revision", 1.0),
        ("state", "not_expired"),
        ("memory_id", "equal-subclass"),
    ),
)
def test_equal_value_nonexact_cached_item_is_denied_before_store_open(
    tmp_path, monkeypatch, field, replacement,
):
    memory, scope, veto, cached = _fixture(tmp_path)
    item = cached.items[0]
    if field == "memory_id":
        replacement = EqualString(item.memory_id)
    assert replacement == getattr(item, field)
    object.__setattr__(item, field, replacement)
    calls = []

    def forbidden_open(_self):
        calls.append("opened")
        raise AssertionError("private Memory opened for malformed cached witness")

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_connect_readonly", forbidden_open)
        with pytest.raises(
            SyntheticRetentionRecheckRejected,
            match="exact cached retention item types required",
        ):
            review_synthetic_retention_recheck(
                memory, scope, veto, cached, now_ms=101, max_age_ms=10,
            )
    assert calls == []


def test_unchanged_retention_inventory_remains_denial_only(tmp_path):
    memory, scope, veto, cached = _fixture(tmp_path)
    receipt = review_synthetic_retention_recheck(
        memory, scope, veto, cached, now_ms=101, max_age_ms=10,
    )
    assert receipt.deletion_authorized is False
    assert receipt.erasure_completed is False
    assert receipt.context_use_authorized is False
    assert receipt.external_disclosure_authorized is False
