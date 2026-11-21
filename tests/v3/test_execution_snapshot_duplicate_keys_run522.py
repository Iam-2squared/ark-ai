"""Execution-snapshot JSON keys must be unambiguous before any V3 gate.

These synthetic local byte fixtures do not authorize compute, Candidate
weights, protected V2 evaluation, promotion, or external provider spending.
"""

from __future__ import annotations

import pytest

from ark.learning.execution import load_snapshot


@pytest.mark.parametrize(
    "payload",
    (
        b'{"authorization":{},"authorization":{"external_compute_authorized":true}}',
        b'{"authorization":{"external_compute_authorized":false,'
        b'"external_compute_authorized":true}}',
        b'{"base":{"revision":"a","revision":"b"}}',
        b'{"dataset":[{"canonical_sha256":"a","canonical_sha256":"b"}]}',
        b'{"a":1,"\\u0061":2}',
        b'{"nested":{"x":1},"nested":{"x":1}}',
    ),
)
def test_duplicate_keys_at_every_depth_are_rejected(tmp_path, payload):
    path = tmp_path / "ambiguous-snapshot.json"
    path.write_bytes(payload)
    with pytest.raises(ValueError, match="duplicate JSON key"):
        load_snapshot(path)


def test_noncanonical_unique_object_is_still_accepted(tmp_path):
    path = tmp_path / "safe-snapshot.json"
    path.write_bytes(b'{ "z": { "value": 2 }, "a": 1 }')
    assert load_snapshot(path) == {"z": {"value": 2}, "a": 1}


def test_same_member_name_in_separate_objects_is_not_a_duplicate(tmp_path):
    path = tmp_path / "scoped-members.json"
    path.write_bytes(b'{"first":{"id":1},"second":{"id":2}}')
    assert load_snapshot(path)["first"]["id"] == 1
    assert load_snapshot(path)["second"]["id"] == 2
