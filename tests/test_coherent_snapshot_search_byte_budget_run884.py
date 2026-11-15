"""No private Memory connection for unbounded detached snapshot search text.

The request is validated independently of a MemoryStore or SQLite read.
"""

import pytest

from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest


@pytest.mark.parametrize(
    ("search", "accepted"),
    (
        ("a" * 4096, True),
        ("é" * 2048, True),
        ("🪐" * 1024, True),
        ("é" * 2049, False),
        ("🪐" * 1025, False),
        ("a" * 4095 + "é", False),
        ("a" * 4097, False),
    ),
)
def test_exact_utf8_search_budget_before_database(
    search: str, accepted: bool,
) -> None:
    args = {
        "owner_id": "synthetic-owner",
        "namespaces": ("synthetic-private",),
        "text": search,
    }
    if accepted:
        request = CoherentSnapshotRequest(**args)
        assert request.text == search
        assert len(request.text.encode("utf-8")) <= 4096
    else:
        with pytest.raises(ValueError, match="4096"):
            CoherentSnapshotRequest(**args)


def test_search_surrogate_remains_refused_before_database() -> None:
    with pytest.raises(ValueError, match="UTF-8 encodable"):
        CoherentSnapshotRequest(
            owner_id="synthetic-owner", namespaces=("synthetic-private",),
            text="unpaired\ud800",
        )


def test_valid_request_does_not_grant_expired_memory_access() -> None:
    request = CoherentSnapshotRequest(
        owner_id="synthetic-owner", namespaces=("private",),
        text="🪐" * 1024,
    )
    assert request.include_expired is False
    assert request.per_namespace_limit == 10
