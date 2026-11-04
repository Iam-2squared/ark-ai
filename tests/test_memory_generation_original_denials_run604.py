"""Original Memory generation deny-only getters must never execute a replacement.

All cases use throwaway local SQLite; no mutation of the retained production DB.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import retained_generation_fence as fence


class Counterfeit:
    def __init__(self, original, calls):
        self.original = original
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("invoked")
        return self.original if instance is None else False


def _case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "retained-static-denial.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("synthetic-owner", "private")
    source = "retained-source"
    store.put(MemoryWrite(scope, source, "local secret"), expected_revision=0)
    retained = fence.review_memory_revision_reuse(
        store, scope, source, expected_revision=1,
    )
    return store, scope, source, retained


@pytest.mark.parametrize("flag", fence._DENIALS)
@pytest.mark.parametrize("moment", ("entry", "after_snapshot"))
def test_counterfeit_denial_descriptor_never_runs(
    tmp_path, monkeypatch, flag, moment,
):
    store, scope, source, retained = _case(tmp_path)
    calls = []
    original = vars(fence.MemoryGenerationReview)[flag]

    def counterfeit():
        monkeypatch.setattr(
            fence.MemoryGenerationReview, flag, Counterfeit(original, calls),
        )

    if moment == "entry":
        counterfeit()
    else:
        original_review = fence.review_memory_revision_reuse

        def after_snapshot(*args, **kwargs):
            observed = original_review(*args, **kwargs)
            counterfeit()
            return observed

        monkeypatch.setattr(
            fence, "review_memory_revision_reuse", after_snapshot,
        )

    with pytest.raises(
        fence.RetainedMemoryGenerationRejected, match="descriptor changed",
    ):
        fence.verify_retained_memory_generation(
            retained, store, scope, source, expected_revision=1,
        )
    assert calls == []


def test_original_generation_report_can_still_reconcile(tmp_path):
    store, scope, source, retained = _case(tmp_path)
    assert fence.verify_retained_memory_generation(
        retained, store, scope, source, expected_revision=1,
    ) is None
