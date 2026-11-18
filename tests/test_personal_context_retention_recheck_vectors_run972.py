"""Run972: privacy recheck refuses rebuilt/shortened safety field vectors.

Synthetic local retention review must fail before accessing Memory or
revocation SQLite; no erasure or context-use permission is inferred.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, SQLiteMemoryStore
from ark.personal_context_retention_recheck_review import (
    SyntheticRetentionRecheckRejected,
)
from ark import personal_context_retention_recheck_review as review


@pytest.mark.parametrize("field", ("_DENIAL_NAMES", "_RESULT_FIELDS", "_RESULT_HOOKS"))
@pytest.mark.parametrize("variation", ("empty", "short", "reverse", "copy"))
def test_rebound_privacy_recheck_vector_denied_pre_store(
    monkeypatch: pytest.MonkeyPatch, field: str, variation: str,
) -> None:
    original = getattr(review, field)
    changed = {
        "empty": (),
        "short": original[:-1],
        "reverse": tuple(reversed(original)),
        "copy": tuple(list(original)),
    }[variation]
    assert changed is not original
    store = object.__new__(SQLiteMemoryStore)
    with monkeypatch.context() as patch:
        patch.setattr(review, field, changed)
        with pytest.raises(
            SyntheticRetentionRecheckRejected,
            match="original denial implementation",
        ):
            review.review_synthetic_retention_recheck(
                store,
                MemoryScope("synthetic-owner", "private"),
                object(),
                None,
                now_ms=100,
                max_age_ms=10,
            )


def test_original_retention_guard_vectors_accepted_without_io() -> None:
    review._assert_original_denials()
    assert all(
        current is original for current, original in zip(
            (review._DENIAL_NAMES, review._RESULT_FIELDS, review._RESULT_HOOKS),
            review._ORIGINAL_RECHECK_VECTORS, strict=True,
        )
    )
