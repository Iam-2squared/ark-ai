"""Coherent local Memory requests reject invalid UTF-8 before any SQLite scan.

No Memory v1 schema change, personal connector, purge or authorization grant.
"""

from __future__ import annotations

import pytest

from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest


@pytest.mark.parametrize("field", ("owner", "namespace", "query"))
def test_lone_surrogate_is_rejected_at_request_validation(field):
    data = {
        "owner_id": "fixture-owner",
        "namespaces": ("private",),
        "text": "ordinary query",
    }
    if field == "owner":
        data["owner_id"] = "fixture-\ud800"
    elif field == "namespace":
        data["namespaces"] = ("private-\ud800",)
    else:
        data["text"] = "query-\ud800"
    with pytest.raises(ValueError, match="UTF-8 encodable"):
        CoherentSnapshotRequest(**data)


def test_valid_multilingual_query_remains_a_coherent_snapshot_request():
    request = CoherentSnapshotRequest(
        "所有者", ("個人", "研究"), text="こんにちは / مرحبا",
        per_namespace_limit=20, include_expired=False,
    )
    assert request.owner_id == "所有者"
    assert request.namespaces == ("個人", "研究")
    assert request.text == "こんにちは / مرحبا"
    assert request.include_expired is False
