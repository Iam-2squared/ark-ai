"""Run970: Planner/WRITE slot join refuses replaced class and result vectors.

No real tool, hardware, authentication, or automatic WRITE recovery is used.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_planner_slot_restart_bridge as bridge


@pytest.mark.parametrize(
    "vector",
    ("_FIELDS", "_INPUT_TYPES", "_INPUT_FIELD_NAMES", "_INPUT_HOOKS"),
)
@pytest.mark.parametrize("mutation", ("shortened", "reversed", "rebuilt"))
def test_restart_bridge_guard_vector_replacement_is_preaccess_failure(
    monkeypatch: pytest.MonkeyPatch, vector: str, mutation: str,
) -> None:
    original = getattr(bridge, vector)
    changed = {
        "shortened": original[:1],
        "reversed": tuple(reversed(original)),
        "rebuilt": tuple(list(original)),
    }[mutation]
    assert changed is not original
    with monkeypatch.context() as patch:
        patch.setattr(bridge, vector, changed)
        with pytest.raises(
            bridge.DisconnectedPlannerSlotBridgeRejected,
            match="restart bridge protocol changed",
        ):
            bridge.review_disconnected_planner_slot_restart(
                ledger=object(),
                retained_slot_witness=object(),
                recovered=object(),
                retained_tail=object(),
                claims=(),
                independently_expected_write_ids=(),
                observations=(),
                dependency=object(),
                offline_steps=(),
            )
