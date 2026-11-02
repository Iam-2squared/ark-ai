"""Empty JSON object keys must never alias packet delta paths.

All inputs are synthetic, unapproved JSON trees. No model, GPU, approval,
payment, Candidate or protected evaluation is performed.
"""

from __future__ import annotations

import pytest

from ark.learning.authorization_packet_delta_review import _leaf_bytes
from ark.learning.execution import canonical_json


def test_empty_root_key_does_not_alias_nonempty_root_key():
    a = _leaf_bytes({"": {"a": 1}})
    b = _leaf_bytes({"a": 1})
    assert a == {"~5.a": canonical_json(1)}
    assert b == {"a": canonical_json(1)}
    assert a != b


def test_empty_key_and_normal_key_can_coexist_without_collision():
    leaves = _leaf_bytes({"": {"a": 1}, "a": 2})
    assert leaves == {
        "~5.a": canonical_json(1),
        "a": canonical_json(2),
    }


@pytest.mark.parametrize(("payload", "path"), (
    ({"": 1}, "~5"),
    ({"": {"": 1}}, "~5.~5"),
    ({"a": {"": 1}}, "a.~5"),
    ({"": [1]}, "~5[0]"),
    ({"~5": 1}, "~05"),
))
def test_empty_key_component_is_distinct_from_literal_marker(payload, path):
    assert _leaf_bytes(payload) == {path: canonical_json(1)}


def test_empty_container_under_empty_key_keeps_root_path():
    assert _leaf_bytes({"": {}}) == {"~5": canonical_json({})}
    assert _leaf_bytes({"": []}) == {"~5": canonical_json([])}
    assert _leaf_bytes({"": {}}) != _leaf_bytes({})


def test_depth_and_budget_rejections_remain_fail_closed():
    nested = 1
    for _ in range(18):
        nested = {"": nested}
    from ark.learning.authorization_packet_delta_review import (
        ReviewPacketDeltaRejected,
    )

    with pytest.raises(ReviewPacketDeltaRejected, match="budget exceeded"):
        _leaf_bytes(nested)
