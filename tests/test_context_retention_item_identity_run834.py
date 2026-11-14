"""Retained private Memory items must not execute substituted comparisons.

The tests use in-memory DTOs only: no deletion, SQLite write or user data.
"""

from __future__ import annotations

import pytest

import ark.personal_context_retention_review as retention


def _item() -> retention.SyntheticRetentionItem:
    return retention.SyntheticRetentionItem(
        "private-memory-id", 257, retention.RetentionState.EXPIRED,
    )


def test_unchanged_retained_item_matches_its_original_carriers() -> None:
    item = _item()
    assert retention._item_carriers_original(
        item, item.memory_id, item.revision, item.state,
    )


@pytest.mark.parametrize("field", ("memory_id", "revision", "state"))
def test_reflected_item_poison_never_executes_equality(field: str) -> None:
    item = _item()
    epoch = (item.memory_id, item.revision, item.state)
    invoked: list[str] = []

    class Poisoned:
        def __eq__(self, other: object) -> bool:
            invoked.append("eq")
            raise AssertionError("private retention item equality executed")

        def __ne__(self, other: object) -> bool:
            invoked.append("ne")
            raise AssertionError("private retention item inequality executed")

    object.__setattr__(item, field, Poisoned())
    assert not retention._item_carriers_original(item, *epoch)
    assert invoked == []


def test_equal_value_retained_memory_id_clone_is_not_same_epoch() -> None:
    item = _item()
    epoch = (item.memory_id, item.revision, item.state)
    clone = item.memory_id[:8] + item.memory_id[8:]
    assert clone == item.memory_id and clone is not item.memory_id
    object.__setattr__(item, "memory_id", clone)
    assert not retention._item_carriers_original(item, *epoch)


def test_foreign_item_type_refused_without_attribute_callbacks() -> None:
    class Hostile:
        def __getattribute__(self, name: str) -> object:
            raise AssertionError("foreign retained item getter executed")

    assert not retention._item_carriers_original(
        Hostile(), "private-memory-id", 257, retention.RetentionState.EXPIRED,
    )
