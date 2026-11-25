"""Consistency of value-free packet paths across producer and detached recheck."""

import pytest

from ark.learning.authorization_packet_delta_recheck import (
    DetachedPacketDeltaRejected,
    _fields,
)
from ark.learning.authorization_packet_delta_review import (
    ReviewPacketDelta,
    _leaf_bytes,
)


def _receipt(path):
    return ReviewPacketDelta("a" * 64, "b" * 64, (path,), "c" * 64)


@pytest.mark.parametrize(
    "key",
    [
        "a b",
        " a",
        "a ",
        "a  b",
        "a [0]",
        "a~0b",
    ],
)
def test_plain_space_produced_by_delta_is_accepted_by_recheck(key):
    # Space (U+0020) is intentionally printable, unlike controls and
    # nonprinting Unicode whitespace, which must be escaped by the producer.
    paths = _leaf_bytes({key: 1})
    assert len(paths) == 1
    path = next(iter(paths))
    assert _fields(_receipt(path))[2] == (path,)


@pytest.mark.parametrize(
    "path",
    [
        "a\tb",
        "a\nb",
        "a\x00b",
        "a\x1fb",
        "a\x7fb",
        "a\u00a0b",
        "",
    ],
)
def test_raw_controls_and_non_ascii_paths_still_fail_closed(path):
    with pytest.raises(DetachedPacketDeltaRejected):
        _fields(_receipt(path))


def test_nonprinting_space_is_escaped_before_detached_recheck():
    path = next(iter(_leaf_bytes({"a\u00a0b": 1})))
    assert path == "a~u{A0}b"
    assert _fields(_receipt(path))[2] == (path,)
