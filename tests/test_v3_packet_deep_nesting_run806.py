"""Adversarial depth never escapes V3's offline fail-closed JSON boundary."""

from __future__ import annotations

import pytest

from ark.v3_detached_packet_review import (
    DetachedV3PacketRejected,
    review_detached_v3_packet,
)


@pytest.mark.parametrize("depth", [900, 1000, 1200, 1800])
def test_nested_array_packet_is_explicitly_rejected(depth: int) -> None:
    # 3601 bytes at the largest depth: under the reviewed 4096-byte cap.
    packet = b"[" * depth + b"0" + b"]" * depth
    assert len(packet) <= 4096
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(packet)


@pytest.mark.parametrize("depth", [950, 1100, 1500])
def test_nested_value_in_expected_top_level_is_explicitly_rejected(
    depth: int,
) -> None:
    # A parser may accept the outer object yet fail on an arbitrarily deep
    # leaf; either path must yield the domain denial, not RecursionError.
    packet = (
        b'{"evidence":{},"snapshot":'
        + b"[" * depth + b"0" + b"]" * depth + b"}"
    )
    assert len(packet) <= 4096
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(packet)


def test_depth_denial_keeps_byte_budget_and_strict_type() -> None:
    with pytest.raises(DetachedV3PacketRejected, match="bounded"):
        review_detached_v3_packet(b"[" * 2050 + b"]" * 2050)
    with pytest.raises(DetachedV3PacketRejected, match="bounded"):
        review_detached_v3_packet("[]")  # type: ignore[arg-type]
