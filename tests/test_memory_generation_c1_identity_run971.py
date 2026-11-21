"""Run971: optional Memory lifetime diagnostics reject C1 metadata pre-I/O.

The frozen Memory v1 scope contract remains unchanged. A local revision
review never grants WRITE, erasure, trusted time, or consent.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, SQLiteMemoryStore
from ark.memory import cas_generation_review as review

_C1 = ("\u0080", "\u0081", "\u0085", "\u008d", "\u009b", "\u009f")


@pytest.mark.parametrize("control", _C1)
@pytest.mark.parametrize("field", ("owner_id", "namespace", "source_id"))
def test_c1_lifetime_identity_denied_before_path_or_sqlite(
    control: str, field: str,
) -> None:
    # A deliberately uninitialized exact store has no usable path. An
    # accidental hash or connection before admission makes this test fail.
    store = object.__new__(SQLiteMemoryStore)
    scope = MemoryScope("local-owner", "private")
    source = "synthetic-source"
    if field == "source_id":
        source += control + "spoof"
    else:
        object.__setattr__(scope, field, getattr(scope, field) + control + "spoof")
    with pytest.raises(review.MemoryGenerationReviewRejected, match="UTF-8 scope"):
        review.review_memory_revision_reuse(store, scope, source, expected_revision=0)


def test_normal_japanese_memory_labels_pass_optional_admission() -> None:
    assert review._strict_utf8_identity("端末所有者", 256)
    assert review._strict_utf8_identity("日記/安全", 256)
    assert review._strict_utf8_identity("source-東京", 512)
    # The frozen public MemoryScope still accepts opaque C1 labels; only
    # the optional history diagnostic restricts what it will inspect.
    assert MemoryScope("端末所有者\u009b", "個人").owner_id.endswith("\u009b")
