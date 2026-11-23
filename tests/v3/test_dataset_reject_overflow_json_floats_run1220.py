"""Run1220: V3 dataset JSON rejects exponent-overflow floating-point values."""

from __future__ import annotations

import pytest

from ark.learning.dataset import loads_unique_json


@pytest.mark.parametrize(
    "payload",
    (
        "1e999",
        "-1e999",
        '{"outer": [1e999]}',
        b'{"value": -1e999}',
    ),
)
def test_exponent_overflow_is_rejected_at_every_depth(payload: str | bytes) -> None:
    with pytest.raises(ValueError, match="non-finite JSON number"):
        loads_unique_json(payload)


def test_large_but_finite_json_floats_remain_supported() -> None:
    assert loads_unique_json(
        '{"positive": 1e308, "negative": -1e308, "tiny": 1e-308}'
    ) == {
        "positive": 1e308,
        "negative": -1e308,
        "tiny": 1e-308,
    }
