"""A free-only lane selector emits decisions, never write/spend authority."""

import pytest

from ark import agency_synthetic_lane_selector_review as mod


def _lane():
    return mod.SyntheticWorkLane(
        "memory", 10, ("src/ark/memory",),
        cost_class="free_local", requires_approval=False, reversible=True,
    )


def _select(lane):
    return mod.review_disconnected_work_lanes((lane,))


def test_stable_selector_remains_a_non_authority():
    result = _select(_lane())
    assert result.selected == ("memory",)
    assert result.execution_authorized is False
    assert result.github_write_authorized is False
    assert result.spending_authorized is False


@pytest.mark.parametrize("flag", [
    "execution_authorized", "github_write_authorized", "spending_authorized",
])
def test_injected_grant_cannot_authorize_synthetic_work(monkeypatch, flag):
    monkeypatch.setattr(
        mod.SyntheticLaneSelection, flag, property(lambda _self: True),
    )
    with pytest.raises(mod.SyntheticLaneSelectionRejected, match="forged authority"):
        _select(_lane())


def test_last_grant_getter_cannot_modify_previously_checked_result(monkeypatch):
    def change_result(self):
        object.__setattr__(self, "selected", ("paid_gpu",))
        return False

    monkeypatch.setattr(
        mod.SyntheticLaneSelection, "spending_authorized", property(change_result),
    )
    with pytest.raises(mod.SyntheticLaneSelectionRejected, match="decision changed"):
        _select(_lane())


def test_last_grant_getter_cannot_mutate_untrusted_work_lane(monkeypatch):
    lane = _lane()

    def change_lane(_self):
        object.__setattr__(lane, "cost_class", "potentially_billable")
        return False

    monkeypatch.setattr(
        mod.SyntheticLaneSelection, "spending_authorized", property(change_lane),
    )
    with pytest.raises(mod.SyntheticLaneSelectionRejected, match="lanes changed"):
        _select(lane)


def test_result_subclass_injection_rejected(monkeypatch):
    class DerivedResult(mod.SyntheticLaneSelection):
        pass

    monkeypatch.setattr(mod, "SyntheticLaneSelection", DerivedResult)
    with pytest.raises(mod.SyntheticLaneSelectionRejected, match="decision changed"):
        _select(_lane())
