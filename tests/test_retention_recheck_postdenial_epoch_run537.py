"""A final False privacy authority getter cannot retarget a retention review.

Only locally seeded SQLite fixtures; no deletion, disclosure or real consent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.personal_context_retention_recheck_review as recheck
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _fixture(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "private")
    memory.put(MemoryWrite(
        scope, "fixture", "PRIVATE TEXT NEVER EXPORTED", expires_at_ms=101,
    ))
    revocations = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    cached = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=100,
    )
    return memory, scope, revocations, cached


@pytest.mark.parametrize("target", (
    "result_ids", "result_flag", "cached_digest", "cached_item",
    "current_item", "scope", "memory_path", "veto_path",
    "earlier_denial_descriptor",
))
def test_last_false_denial_cannot_mutate_checked_privacy_epoch(
    tmp_path, monkeypatch, target,
):
    state = _fixture(tmp_path)
    memory, scope, veto, cached = state
    original = recheck.review_synthetic_retention_inventory
    observed = []

    def collect(*args, **kwargs):
        value = original(*args, **kwargs)
        observed.append(value)
        return value

    monkeypatch.setattr(recheck, "review_synthetic_retention_inventory", collect)

    def mutate(self):
        if target == "result_ids":
            object.__setattr__(self, "expired_memory_ids", ("forged",))
        elif target == "result_flag":
            object.__setattr__(self, "scope_revoked", True)
        elif target == "cached_digest":
            object.__setattr__(cached, "inventory_digest", "retention_" + "f" * 64)
        elif target == "cached_item":
            object.__setattr__(cached.items[0], "revision", 99)
        elif target == "current_item":
            assert len(observed) == 4
            object.__setattr__(observed[1].items[0], "revision", 99)
        elif target == "scope":
            object.__setattr__(scope, "owner_id", "unexpected-owner")
        elif target == "memory_path":
            memory.path = Path(str(tmp_path / "other-memory.sqlite"))
        elif target == "veto_path":
            veto.path = Path(str(tmp_path / "other-veto.sqlite"))
        else:
            assert target == "earlier_denial_descriptor"
            monkeypatch.setattr(
                recheck.SyntheticRetentionRecheck,
                "deletion_authorized",
                property(lambda _result: True),
            )
        return False

    monkeypatch.setattr(
        recheck.SyntheticRetentionRecheck,
        "external_disclosure_authorized",
        property(mutate),
    )
    with pytest.raises(recheck.SyntheticRetentionRecheckRejected, match="changed"):
        recheck.review_synthetic_retention_recheck(
            *state, now_ms=101, max_age_ms=10,
        )
    assert len(observed) == 4


def test_stable_privacy_recheck_remains_content_free_and_non_authorizing(tmp_path):
    result = recheck.review_synthetic_retention_recheck(
        *_fixture(tmp_path), now_ms=101, max_age_ms=10,
    )
    assert len(result.expired_memory_ids) == 1
    assert result.scope_revoked is False
    assert result.external_disclosure_authorized is False
    assert result.deletion_authorized is False
    assert "PRIVATE TEXT NEVER EXPORTED" not in repr(result)
