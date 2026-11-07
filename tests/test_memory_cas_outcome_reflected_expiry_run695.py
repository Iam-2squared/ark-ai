"""Manual-only CAS outcome review validates reflected payload before private SQLite.

A content match after COMMIT-UNKNOWN never authenticates the committing writer.
The optional review must not inspect a private row for a malformed proposal.
Frozen Memory v1 APIs and storage are not changed.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_cas_outcome_review import (
    MemoryCASOutcomeRejected,
    review_memory_generation_cas_outcome,
)
from ark.memory.generation_fenced_cas import observe_memory_generation_for_cas


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        ("content", "", "content"),
        ("content", "   ", "content"),
        ("expires_at_ms", True, "expiry"),
        ("expires_at_ms", False, "expiry"),
        ("expires_at_ms", -1, "expiry"),
        ("expires_at_ms", 2**63, "expiry"),
        ("expires_at_ms", "500", "expiry"),
        ("metadata", [("label", "value")], "metadata"),
        ("metadata", (("label", "value"),), "metadata"),
        ("metadata", frozenset({("label", "value")}), "metadata"),
    ),
)
def test_reflected_invalid_review_payload_is_rejected_before_private_read(
    tmp_path, monkeypatch, field, replacement, message,
):
    scope = MemoryScope("fixture-owner", "private")
    path = tmp_path / "memory.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    original = store.put(
        MemoryWrite(scope, "source", "before", expires_at_ms=500),
    )
    retained = observe_memory_generation_for_cas(store, scope, "source")
    proposed = MemoryWrite(scope, "source", "after", expires_at_ms=500)
    object.__setattr__(proposed, field, replacement)
    opens = []

    def forbidden_read():
        opens.append("private")
        pytest.fail("invalid review proposal opened private SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect_readonly", forbidden_read)
        with pytest.raises(MemoryCASOutcomeRejected, match=message):
            review_memory_generation_cas_outcome(
                store, proposed, retained=retained,
            )

    assert not opens
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    assert cold.get(original.memory_id, scope).content == "before"
    assert len(cold.events(scope)) == 1
    assert observe_memory_generation_for_cas(cold, scope, "source") == retained


def test_valid_finite_expiry_and_mapping_proxy_remain_manual_only(tmp_path):
    scope = MemoryScope("fixture-owner", "private")
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(scope, "source", "before", expires_at_ms=500))
    retained = observe_memory_generation_for_cas(store, scope, "source")
    proposed = MemoryWrite(
        scope, "source", "after", {"label": "safe"}, expires_at_ms=500,
    )
    review = review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert review.observation == "UNCHANGED_OBSERVED"
    assert review.commit_attributed_to_caller is False
    assert review.automatic_retry_authorized is False
    assert review.external_action_authorized is False
    assert review.consent_authenticated is False
    assert review.trusted_clock_verified is False
