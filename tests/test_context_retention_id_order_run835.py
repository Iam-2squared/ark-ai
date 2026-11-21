"""Cached privacy inventory IDs must be canonical, unique and ordered.

Read-only synthetic carriers: these tests cannot attest real erasure,
trusted user consent, notification, or authorization to export context.
"""

from __future__ import annotations

import pytest

import ark.personal_context_retention_recheck_review as review
from ark.personal_context_retention_review import (
    RetentionState,
    SyntheticRetentionInventory,
    SyntheticRetentionItem,
)

_VALID = "mem_" + "a" * 64
_SECOND = "mem_" + "b" * 64


def _inventory(*ids: str) -> SyntheticRetentionInventory:
    return SyntheticRetentionInventory(
        "c" * 64, "retention_" + "d" * 64, 0, False,
        tuple(SyntheticRetentionItem(identity, 1, RetentionState.NOT_EXPIRED)
              for identity in ids),
    )


@pytest.mark.parametrize("identity", (
    "",
    "mem_" + "a" * 63,
    "mem_" + "A" * 64,
    "mem_" + "g" * 64,
    "x" * 10000,
    "mem_" + "\ud800" * 64,
))
def test_noncanonical_cached_memory_ids_denied_before_sqlite(identity: str) -> None:
    with pytest.raises(
        review.SyntheticRetentionRecheckRejected,
        match="exact cached retention item",
    ):
        review._epoch(_inventory(identity))


@pytest.mark.parametrize("items", (
    (_VALID, _VALID),
    (_SECOND, _VALID),
))
def test_duplicate_or_unsorted_cached_identity_denied(
    items: tuple[str, ...],
) -> None:
    with pytest.raises(
        review.SyntheticRetentionRecheckRejected,
        match="identity or order",
    ):
        review._epoch(_inventory(*items))


def test_ordered_canonical_cached_ids_remain_read_only() -> None:
    snapshot = _inventory(_VALID, _SECOND)
    image = review._epoch(snapshot)
    assert image[-1] == (
        (_VALID, 1, RetentionState.NOT_EXPIRED),
        (_SECOND, 1, RetentionState.NOT_EXPIRED),
    )
    assert snapshot.items[0].memory_id == _VALID
    assert snapshot.items[1].memory_id == _SECOND
