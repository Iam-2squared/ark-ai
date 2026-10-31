"""Offline retention recheck cannot forge the final human-review candidate queue.

Local content-free SQLite fixtures only. This never deletes data, confirms
erasure, establishes consent, or authorizes any external disclosure.
"""

import pytest

import ark.personal_context_retention_recheck_review as recheck
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _fixture(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "private")
    memory.put(MemoryWrite(
        scope, "synthetic-001", "PRIVATE LOCAL FIXTURE", expires_at_ms=101,
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    cached = review_synthetic_retention_inventory(memory, scope, veto, now_ms=100)
    return memory, scope, veto, cached


def _clone(value):
    other = ("!" + value)[1:]
    assert other == value and other is not value
    return other


@pytest.mark.parametrize("target", (
    "scope_digest", "captured_inventory_digest", "current_inventory_digest",
    "checked_at_ms", "expired_memory_ids", "unbounded_memory_ids", "scope_revoked",
    "cached_owner", "cached_digest", "cached_item_id",
    "current_digest", "current_items",
))
def test_final_constructor_cannot_retarget_privacy_diagnostic(
    tmp_path, monkeypatch, target,
):
    state = _fixture(tmp_path)
    native_init = recheck.SyntheticRetentionRecheck.__init__
    original_inventory = recheck.review_synthetic_retention_inventory
    current = []
    reviews = []

    def collect(*args, **kwargs):
        value = original_inventory(*args, **kwargs)
        reviews.append(value)
        if len(reviews) == 2:
            current.append(value)
        return value

    def tamper(self, *args, **kwargs):
        native_init(self, *args, **kwargs)
        if target in {
            "scope_digest", "captured_inventory_digest", "current_inventory_digest",
        }:
            object.__setattr__(self, target, _clone(getattr(self, target)))
        elif target == "checked_at_ms":
            object.__setattr__(self, target, self.checked_at_ms + 1)
        elif target == "expired_memory_ids":
            replacement = tuple(list(self.expired_memory_ids))
            assert replacement == self.expired_memory_ids
            assert replacement is not self.expired_memory_ids
            object.__setattr__(self, target, replacement)
        elif target == "unbounded_memory_ids":
            object.__setattr__(self, target, ("forged",))
        elif target == "scope_revoked":
            object.__setattr__(self, target, not self.scope_revoked)
        elif target == "cached_owner":
            scope = state[1]
            object.__setattr__(scope, "owner_id", _clone(scope.owner_id))
        elif target == "cached_digest":
            cached = state[3]
            object.__setattr__(
                cached, "inventory_digest", _clone(cached.inventory_digest),
            )
        elif target == "cached_item_id":
            item = state[3].items[0]
            object.__setattr__(item, "memory_id", _clone(item.memory_id))
        elif target == "current_digest":
            assert current
            value = current[0]
            object.__setattr__(
                value, "inventory_digest", _clone(value.inventory_digest),
            )
        else:
            assert target == "current_items"
            value = current[0]
            object.__setattr__(value, "items", tuple(list(value.items)))

    monkeypatch.setattr(recheck, "review_synthetic_retention_inventory", collect)
    monkeypatch.setattr(recheck.SyntheticRetentionRecheck, "__init__", tamper)
    expect = (
        "source or evidence changed" if target.startswith("cached_")
        else "current retention evidence changed"
        if target in {"current_digest", "current_items"}
        else "returned result changed"
    )
    with pytest.raises(recheck.SyntheticRetentionRecheckRejected, match=expect):
        recheck.review_synthetic_retention_recheck(
            *state, now_ms=101, max_age_ms=10,
        )
    assert len(reviews) == 4


def test_unchanged_recheck_is_a_non_authorizing_review_queue(tmp_path):
    result = recheck.review_synthetic_retention_recheck(
        *_fixture(tmp_path), now_ms=101, max_age_ms=10,
    )
    assert len(result.expired_memory_ids) == 1
    assert result.unbounded_memory_ids == ()
    assert not result.deletion_authorized
    assert not result.erasure_completed
    assert not result.context_use_authorized
    assert not result.external_disclosure_authorized
    assert "PRIVATE LOCAL FIXTURE" not in repr(result)
