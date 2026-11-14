"""A disconnected registered recovery report must retain its original carrier.

No forged receipt constructor, slot, lookup hook or False-only property may
run during a mock-only journal/registry review. These checks do not dispatch
real tools or grant write/replay authority.
"""

from __future__ import annotations

import pytest
from test_recovered_registered_read_join_run550 import invoke, make_case

import ark.agency.disconnected_recovered_registered_read_join as joined


@pytest.mark.parametrize(
    "field",
    joined._REPORT_FIELDS
    + tuple(name for name in joined._REPORT_HOOKS if name != "__new__")
    + joined._DENIED,
)
def test_preinstalled_report_carrier_poison_rejected_before_plan_review(
    tmp_path, monkeypatch, field,
):
    case = make_case(tmp_path)
    executed = []

    def forbidden(*args, **kwargs):
        executed.append("poison")
        raise AssertionError("malicious receipt code must not execute")

    original_verify = joined.verify_disconnected_batch_plan

    def verify(*args, **kwargs):
        executed.append("plan review")
        return original_verify(*args, **kwargs)

    try:
        monkeypatch.setattr(joined, "verify_disconnected_batch_plan", verify)
        if field in joined._REPORT_FIELDS or field in joined._DENIED:
            monkeypatch.setattr(
                joined.RecoveredRegisteredReadReview,
                field, property(forbidden),
            )
        else:
            monkeypatch.setattr(
                joined.RecoveredRegisteredReadReview, field, forbidden,
                raising=False,
            )
        with pytest.raises(
            joined.RecoveredRegisteredReadRejected,
            match="recovery carrier changed",
        ):
            invoke(case)
        assert executed == []
        assert case["backend"].calls == 0
        assert case["gate"]._consumed_tokens == set()
    finally:
        case["journal"].close()


def test_reentrant_plan_callback_cannot_install_late_result_slot(
    tmp_path, monkeypatch,
):
    case = make_case(tmp_path)
    original = joined.verify_disconnected_batch_plan
    executed = []

    def poison(*args, **kwargs):
        executed.append("slot")
        raise AssertionError("late forged slot must not execute")

    def swap(*args, **kwargs):
        reviewed = original(*args, **kwargs)
        executed.append("plan")
        monkeypatch.setattr(
            joined.RecoveredRegisteredReadReview,
            "join_sha256", property(poison),
        )
        return reviewed

    try:
        monkeypatch.setattr(joined, "verify_disconnected_batch_plan", swap)
        with pytest.raises(
            joined.RecoveredRegisteredReadRejected,
            match="recovery carrier changed",
        ):
            invoke(case)
        assert executed == ["plan"]
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


def test_original_report_still_preserves_all_denials(tmp_path):
    case = make_case(tmp_path, ("SUCCEEDED", "FAILED"))
    try:
        report = invoke(case)
        assert type(report) is joined.RecoveredRegisteredReadReview
        assert tuple(row[0] for row in report.registered_steps) == (
            "step_" + "a" * 16,
        )
        assert len(report.join_sha256) == 64
        assert all(getattr(report, field) is False for field in joined._DENIED)
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()
