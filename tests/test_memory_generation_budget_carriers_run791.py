"""Run791: generation-recheck limits require exact import-time integer carriers.

All negative cases fail before reading any Memory identity or opening SQLite.
There is no automatic CAS retry, consent, erasure, or dispatch authorization.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import retained_generation_fence as fence
from ark.memory.cas_generation_review import review_memory_revision_reuse


class PoisonComparison:
    def __eq__(self, _other: object) -> bool:
        raise AssertionError("untrusted equality executed")

    def __ne__(self, _other: object) -> bool:
        raise AssertionError("untrusted inequality executed")


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("_MAX_EVENTS", 40_000.0),
        ("_MAX_EVENTS", PoisonComparison()),
        ("SQLITE_INT_MAX", float(2**63 - 1)),
        ("_ORIGINAL_EVENT_BUDGET", 40_000.0),
        ("_ORIGINAL_SQLITE_LIMIT", float(2**63 - 1)),
    ),
)
def test_generation_limits_refuse_equal_or_poisoned_carriers_preaccess(
    name: str, value: object, monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(fence, name, value)
        # All other objects intentionally lack fields; no private lookup is
        # allowed before the exact limit epoch is rejected.
        with pytest.raises(
            fence.RetainedMemoryGenerationRejected,
            match="parser or review helper changed",
        ):
            fence.verify_retained_memory_generation(
                object(), object(), object(), "synthetic",
                expected_revision=1,
            )


def test_original_memory_generation_budget_keeps_readonly_restart_path(tmp_path) -> None:
    path = tmp_path / "run791-memory.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    scope = MemoryScope("test-owner", "private")
    item = store.put(MemoryWrite(scope, "local-source", "fixture-data"))
    retained = review_memory_revision_reuse(
        store, scope, "local-source", expected_revision=1,
    )
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 300)
    assert fence.verify_retained_memory_generation(
        retained, reopened, scope, "local-source", expected_revision=1,
    ) is None
    assert reopened.get(item.memory_id, scope).revision == 1
    assert retained.write_authorized is False
    assert retained.erase_authorized is False
    assert retained.generation_authenticated is False
