"""Unapproved packet-delta paths cannot display control/bidi spoofing."""

from __future__ import annotations

import pytest

from ark.learning.authorization_packet_delta_review import _leaf_bytes
from ark.learning.execution import canonical_json


@pytest.mark.parametrize(("key", "expected"), (
    ("line\nbreak", "line~u{A}break"),
    ("a\\b", "a~6b"),
    ("right\u202eleft", "right~u{202E}left"),
    ("\u200d", "~u{200D}"),
    ("\u2028", "~u{2028}"),
    ("\ud800", "~u{D800}"),
    ("\x00", "~u{0}"),
))
def test_control_and_directional_key_paths_are_printable(key, expected):
    paths = _leaf_bytes({key: 1})
    assert paths == {expected: canonical_json(1)}
    assert all(char.isprintable() for char in next(iter(paths)))


def test_literal_marker_is_distinct_from_control_escape():
    control = _leaf_bytes({"\n": 1})
    literal = _leaf_bytes({"~u{A}": 1})
    assert control == {"~u{A}": canonical_json(1)}
    assert literal == {"~0u{A}": canonical_json(1)}
    assert control != literal


def test_natural_dotted_and_array_paths_unchanged():
    assert _leaf_bytes({"arr": [{"nested": 1}]}) == {
        "arr[0].nested": canonical_json(1),
    }


def test_printable_delimiters_are_injective():
    assert _leaf_bytes({"a\\b": 1, "a~6b": 2}) == {
        "a~6b": canonical_json(1),
        "a~06b": canonical_json(2),
    }
