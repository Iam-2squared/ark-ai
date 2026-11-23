"""Run1211: V3 dataset JSON rejects non-standard numeric constants."""

from __future__ import annotations

import pytest

from ark.learning.dataset import loads_unique_json


@pytest.mark.parametrize(
    "payload",
    (
        '{"value": NaN}',
        '{"outer": {"value": Infinity}}',
        '[-Infinity]',
    ),
)
def test_nonstandard_json_constants_are_rejected_at_every_depth(
    payload: str,
) -> None:
    with pytest.raises(ValueError, match="non-standard JSON constant"):
        loads_unique_json(payload)


def test_finite_json_numbers_remain_supported() -> None:
    assert loads_unique_json('{"positive": 1.25, "negative": -2, "zero": 0}') == {
        "positive": 1.25,
        "negative": -2,
        "zero": 0,
    }
