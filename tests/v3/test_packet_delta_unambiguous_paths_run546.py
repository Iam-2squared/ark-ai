"""Run546: passive packet deltas must not hide structural changes."""

from __future__ import annotations

import pytest

from ark.learning import authorization_packet_delta_review as mod
from ark.learning.execution import canonical_json


def test_literal_dot_key_never_aliases_nested_path():
    output = mod._leaf_bytes({"a.b": 1, "a": {"b": 2}})
    assert output == {"a~2b": canonical_json(1), "a.b": canonical_json(2)}


def test_literal_tilde_and_array_delimiters_are_unambiguous():
    output = mod._leaf_bytes({
        "a~2b": 1,
        "a.b": 2,
        "array": [3],
        "array[0]": 4,
        "a": {"[0]": 5},
    })
    assert output["a~02b"] == canonical_json(1)
    assert output["a~2b"] == canonical_json(2)
    assert output["array[0]"] == canonical_json(3)
    assert output["array~30~4"] == canonical_json(4)
    assert output["a.~30~4"] == canonical_json(5)
    assert len(output) == 5


@pytest.mark.parametrize("old,new", (
    ({}, []),
    ([], {}),
    ({}, 0),
    ([], 0),
    ({"nested": {}}, {"nested": []}),
))
def test_empty_container_replacements_alter_canonical_leaves(old, new):
    before = mod._leaf_bytes({"field": old})
    after = mod._leaf_bytes({"field": new})
    assert before != after


def test_empty_mapping_and_list_are_retained_as_field_name_only():
    output = mod._leaf_bytes({"config": {}, "values": []})
    assert output == {
        "config": canonical_json({}),
        "values": canonical_json([]),
    }


def test_ordinary_packet_paths_keep_existing_dotted_notation():
    output = mod._leaf_bytes({"budget": {"max_cost_jpy": 50}})
    assert output == {"budget.max_cost_jpy": canonical_json(50)}


def test_scalar_types_remain_distinct_and_unapproved():
    assert mod._leaf_bytes({"flag": True}) != mod._leaf_bytes({"flag": 1})


@pytest.mark.parametrize("payload", (
    {"a" * 513: "x"},
    {str(index): 0 for index in range(513)},
))
def test_review_field_budgets_fail_closed(payload):
    with pytest.raises(mod.ReviewPacketDeltaRejected):
        mod._leaf_bytes(payload)
