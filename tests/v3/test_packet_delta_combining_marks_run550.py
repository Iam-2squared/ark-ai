"""Passive V3 packet delta paths cannot be visually overlaid by marks."""

import unicodedata

import pytest

from ark.learning.authorization_packet_delta_review import _leaf_bytes
from ark.learning.execution import canonical_json


@pytest.mark.parametrize(
    "codepoint",
    (
        0x0301,  # combining acute accent
        0x0338,  # combining solidus overlay
        0x20DD,  # combining enclosing circle
        0x0903,  # spacing combining Devanagari sign
        0xFE0F,  # emoji variation selector
        0x3099,  # combining voiced Kana mark
    ),
)
def test_printable_combining_marks_are_escaped_in_value_free_paths(codepoint):
    char = chr(codepoint)
    assert unicodedata.category(char).startswith("M")
    assert char.isprintable()
    escaped = f"left~u{{{codepoint:X}}}right"
    assert _leaf_bytes({"left" + char + "right": 1}) == {
        escaped: canonical_json(1),
    }
    assert escaped.isprintable()


def test_composed_decomposed_and_literal_markers_have_distinct_paths():
    assert _leaf_bytes({
        "é": 1,
        "e\u0301": 2,
        "e~u{301}": 3,
        "e": 4,
    }) == {
        "~u{E9}": canonical_json(1),
        "e~u{301}": canonical_json(2),
        "e~0u{301}": canonical_json(3),
        "e": canonical_json(4),
    }


def test_nested_combining_overlay_cannot_impersonate_plain_key():
    paths = _leaf_bytes({
        "outer": {
            "a\u0338": 1,
            "a": 2,
            "a~u{338}": 3,
        },
    })
    assert paths == {
        "outer.a~u{338}": canonical_json(1),
        "outer.a": canonical_json(2),
        "outer.a~0u{338}": canonical_json(3),
    }


def test_plain_ascii_space_and_normal_brackets_remain_readable():
    assert _leaf_bytes({"plain space": [1]}) == {
        "plain space[0]": canonical_json(1),
    }
