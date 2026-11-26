"""Bounded canonical ToolCall JSON ingress; entirely disconnected fixtures."""

from collections.abc import Mapping
from itertools import count

import pytest

from ark.agency.contracts import ToolCall


def _call(arguments):
    return ToolCall("fixture.write", "fixture.write", "offline:test", arguments)


class InfiniteItems(Mapping):
    def __init__(self):
        self.yielded = 0

    def __len__(self):
        return 1

    def __iter__(self):
        return iter(())

    def __getitem__(self, key):
        raise KeyError(key)

    def items(self):
        for index in count():
            self.yielded += 1
            yield str(index), index


class DuplicateItems(Mapping):
    def __len__(self):
        return 2

    def __iter__(self):
        return iter(("a",))

    def __getitem__(self, key):
        return 2

    def items(self):
        yield "a", 1
        yield "a", 2


def test_infinite_mapping_items_rejected_before_exhaustion():
    hostile = InfiniteItems()
    with pytest.raises(ValueError, match="canonical JSON-compatible"):
        _call(hostile)
    assert hostile.yielded <= 4096


def test_duplicate_items_cannot_ambiguously_change_canonical_request():
    with pytest.raises(ValueError, match="canonical JSON-compatible"):
        _call(DuplicateItems())


def test_exact_node_boundary_preserves_hash_for_valid_arguments():
    valid = {"values": list(range(4094))}
    a = _call(valid)
    b = _call({"values": tuple(range(4094))})
    assert a.request_id == b.request_id
    with pytest.raises(ValueError, match="canonical JSON-compatible"):
        _call({"values": list(range(4095))})


def test_depth_boundary_and_cycle_fail_closed_without_recursion_error():
    accepted = 1
    for _ in range(31):
        accepted = [accepted]
    assert _call({"x": accepted}).request_id.startswith("act_")
    rejected = [accepted]
    with pytest.raises(ValueError, match="canonical JSON-compatible"):
        _call({"x": rejected})
    cycle = []
    cycle.append(cycle)
    with pytest.raises(ValueError, match="canonical JSON-compatible"):
        _call({"x": cycle})


def test_single_text_length_budget_rejects_huge_string():
    assert _call({"x": "a" * 65536}).request_id.startswith("act_")
    with pytest.raises(ValueError, match="canonical JSON-compatible"):
        _call({"x": "a" * 65537})


def test_cumulative_unicode_budget_rejects_large_parallel_fields():
    valid = {"first": "😀" * 32000, "second": "😀" * 32000}
    assert _call(valid).request_id.startswith("act_")
    with pytest.raises(ValueError, match="canonical JSON-compatible"):
        _call({"first": "😀" * 32768, "second": "😀" * 32768})


def test_invalid_unicode_surrogate_rejected_before_hashing():
    with pytest.raises(ValueError, match="canonical JSON-compatible"):
        _call({"name": "\ud800"})


def test_canonical_valid_nested_arguments_preserve_order_independence():
    left = _call({"b": [1, {"y": 2, "x": 3}], "a": "ok"})
    right = _call({"a": "ok", "b": (1, {"x": 3, "y": 2})})
    assert left.arguments_sha256 == right.arguments_sha256
    assert left.request_id == right.request_id
