"""Retention review denies preinstalled False-only authority substitutions.

All inputs are temporary local SQLite fixtures; no erasure, consent,
disclosure, scheduling, or external execution is authorized.
"""

from __future__ import annotations

import pytest

from ark import personal_context_retention_recheck_review as mod
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _inputs(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "private")
    memory.put(MemoryWrite(
        scope, "record", "PRIVATE CONTENT", expires_at_ms=102,
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    cached = review_synthetic_retention_inventory(
        memory, scope, veto, now_ms=100,
    )
    return memory, scope, veto, cached


@pytest.mark.parametrize("name", mod._DENIAL_NAMES)
def test_false_only_property_rebound_before_call_rejects_without_inventory_read(
    tmp_path, monkeypatch, name,
):
    inputs = _inputs(tmp_path)
    monkeypatch.setattr(
        mod.SyntheticRetentionRecheck, name, property(lambda _: False),
    )

    def forbidden(*args, **kwargs):
        pytest.fail("retention inventory must not be read under replaced denial")

    monkeypatch.setattr(mod, "review_synthetic_retention_inventory", forbidden)
    with pytest.raises(
        mod.SyntheticRetentionRecheckRejected,
        match="original denial implementation",
    ):
        mod.review_synthetic_retention_recheck(
            *inputs, now_ms=101, max_age_ms=10,
        )


def test_descriptor_replacement_during_first_read_aborts_before_second_read(
    tmp_path, monkeypatch,
):
    inputs = _inputs(tmp_path)
    original = mod.review_synthetic_retention_inventory
    observed = []

    def mutated(*args, **kwargs):
        observed.append(1)
        assert len(observed) == 1, "must reject before second inventory read"
        value = original(*args, **kwargs)
        monkeypatch.setattr(
            mod.SyntheticRetentionRecheck,
            "erasure_completed",
            property(lambda _: False),
        )
        return value

    monkeypatch.setattr(mod, "review_synthetic_retention_inventory", mutated)
    with pytest.raises(
        mod.SyntheticRetentionRecheckRejected,
        match="original denial implementation",
    ):
        mod.review_synthetic_retention_recheck(
            *inputs, now_ms=101, max_age_ms=10,
        )
    assert len(observed) == 1


def test_unchanged_original_denials_leave_review_passive(tmp_path):
    result = mod.review_synthetic_retention_recheck(
        *_inputs(tmp_path), now_ms=101, max_age_ms=10,
    )
    assert all(getattr(result, name) is False for name in mod._DENIAL_NAMES)
    assert "PRIVATE CONTENT" not in repr(result)
