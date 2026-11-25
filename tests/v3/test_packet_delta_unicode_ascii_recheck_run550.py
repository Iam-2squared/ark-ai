"""Unapproved packet path producer and detached validator use ASCII-safe keys."""

from __future__ import annotations

import pytest

from ark.learning.authorization_packet_delta_recheck import (
    DetachedPacketDeltaRejected,
    _fields,
)
from ark.learning.authorization_packet_delta_review import (
    ReviewPacketDelta,
    _leaf_bytes,
)
from ark.learning.execution import canonical_json


@pytest.mark.parametrize(
    ("key", "expected"),
    (
        ("é", "~u{E9}"),
        ("漢", "~u{6F22}"),
        ("α", "~u{3B1}"),
        ("雪", "~u{96EA}"),
        ("😀", "~u{1F600}"),
        ("e\u0301", "e~u{301}"),
    ),
)
def test_printable_unicode_keys_pass_detached_ascii_path_contract(key, expected):
    paths = _leaf_bytes({key: 1})
    assert paths == {expected: canonical_json(1)}
    receipt = ReviewPacketDelta("a" * 64, "b" * 64, (expected,), "c" * 64)
    assert _fields(receipt)[2] == (expected,)
    assert all(32 <= ord(char) <= 126 for char in expected)


def test_unicode_literal_escape_and_plain_ascii_have_noncolliding_paths():
    paths = _leaf_bytes({
        "café": 1,
        "caf~u{E9}": 2,
        "cafe": 3,
        "plain key": 4,
    })
    assert paths == {
        "caf~u{E9}": canonical_json(1),
        "caf~0u{E9}": canonical_json(2),
        "cafe": canonical_json(3),
        "plain key": canonical_json(4),
    }
    changed = tuple(sorted(paths))
    receipt = ReviewPacketDelta("a" * 64, "b" * 64, changed, "c" * 64)
    assert _fields(receipt)[2] == changed


@pytest.mark.parametrize("key", ("é", "漢", "😀"))
def test_detached_review_still_rejects_unescaped_non_ascii(key):
    receipt = ReviewPacketDelta(
        "a" * 64, "b" * 64, (key,), "c" * 64,
    )
    with pytest.raises(DetachedPacketDeltaRejected, match="noncanonical"):
        _fields(receipt)


def test_nested_unicode_field_and_array_index_keep_distinct_paths():
    paths = _leaf_bytes({"領域": [{"項目": 1}], "領域[0]": 2})
    assert paths == {
        "~u{9818}~u{57DF}[0].~u{9805}~u{76EE}": canonical_json(1),
        "~u{9818}~u{57DF}~30~4": canonical_json(2),
    }
    changed = tuple(sorted(paths))
    receipt = ReviewPacketDelta("a" * 64, "b" * 64, changed, "c" * 64)
    assert _fields(receipt)[2] == changed
