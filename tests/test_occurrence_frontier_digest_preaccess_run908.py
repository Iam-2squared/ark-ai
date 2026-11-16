"""Retained synthetic occurrence hashes must be bounded before regex or SQLite.

No dispatch, trusted custody, approval or replay authority is obtained here.
"""

from pathlib import Path

import pytest

from ark.agency import disconnected_occurrence_frontier_review as module
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)


@pytest.mark.parametrize(
    "digest",
    (
        "a" * 63,
        "a" * 65,
        "a" * 100_000,
        "あ" * 64,
        "\x00" * 64,
        "g" * 64,
        b"a" * 64,
    ),
)
def test_retained_digest_is_rejected_before_nonexistent_db_open(
    tmp_path: Path, digest: object,
) -> None:
    missing = tmp_path / "missing.db"
    store = object.__new__(SyntheticOccurrenceStore)
    store._path = missing
    forged = module.SyntheticOccurrenceFrontier(1, digest, 0)
    with pytest.raises(SyntheticReplayRejected, match="invalid retained occurrence frontier"):
        module.review_synthetic_occurrence_frontier(store, retained=forged)
    assert not missing.exists()


def test_retained_digest_subclass_refused_before_custom_len(tmp_path: Path) -> None:
    class ReflectedDigest(str):
        def __len__(self) -> int:
            raise AssertionError("caller-owned length hook executed")

    missing = tmp_path / "missing.db"
    store = object.__new__(SyntheticOccurrenceStore)
    store._path = missing
    forged = module.SyntheticOccurrenceFrontier(1, ReflectedDigest("a" * 64), 0)
    with pytest.raises(SyntheticReplayRejected, match="invalid retained occurrence frontier"):
        module.review_synthetic_occurrence_frontier(store, retained=forged)
    assert not missing.exists()


def test_valid_empty_frontier_still_rechecks_without_execution(tmp_path: Path) -> None:
    store = SyntheticOccurrenceStore(tmp_path / "empty.db")
    retained = module.review_synthetic_occurrence_frontier(store)
    assert module.review_synthetic_occurrence_frontier(store, retained=retained) == retained
    assert retained.dispatch_authorized is False
    assert retained.automatic_replay_authorized is False
    assert retained.external_outcome_proven is False
