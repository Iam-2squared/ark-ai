"""Composite registered READ/archive evidence has no inherited authority.

All fixtures are disconnected. The retained file and SQLite journal remain
separately observed and cannot establish real execution or atomicity.
"""

from __future__ import annotations

import pytest
from test_registered_cycle_archive_bridge_run535 import _fixture, _review

from ark.agency import disconnected_registered_archive_bridge as bridge


@pytest.mark.parametrize(
    ("carrier", "flag"),
    (
        *(
            ("RegisteredArchiveBridgeReview", flag)
            for flag in (
                "backend_dispatched", "write_authorized",
                "automatic_replay_authorized", "consent_authenticated",
                "independent_custody_proven", "external_outcome_proven",
            )
        ),
        *(
            ("ArchivedDisconnectedBatchCycle", flag)
            for flag in (
                "external_dispatch_authorized", "write_authorized",
                "automatic_replay_authorized", "real_outcome_proven",
            )
        ),
        *(
            ("RegisteredBatchSetReview", flag)
            for flag in (
                "backend_dispatched", "write_authorized",
                "automatic_replay_authorized", "dependencies_completed_proven",
                "independent_custody_proven",
            )
        ),
    ),
)
def test_original_denial_descriptor_required_before_join(
    tmp_path, monkeypatch, carrier, flag,
):
    case = _fixture(tmp_path)
    try:
        monkeypatch.setattr(
            getattr(bridge, carrier), flag, property(lambda _self: False),
        )
        with pytest.raises(
            bridge.RegisteredArchiveBridgeRejected,
            match="authority definition changed",
        ):
            _review(case)
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


@pytest.mark.parametrize("lane", ("archive", "registered"))
def test_nested_callback_cannot_replace_denial_and_rebaseline(
    tmp_path, monkeypatch, lane,
):
    case = _fixture(tmp_path)
    if lane == "archive":
        name = "review_disconnected_batch_fixture_cycle_archive"
        cls = bridge.ArchivedDisconnectedBatchCycle
        flag = "real_outcome_proven"
    else:
        name = "review_registered_batch_receipt_set"
        cls = bridge.RegisteredBatchSetReview
        flag = "independent_custody_proven"
    native = getattr(bridge, name)
    called = []

    def replace_after_nested_review(*args, **kwargs):
        outcome = native(*args, **kwargs)
        called.append(1)
        monkeypatch.setattr(cls, flag, property(lambda _self: False))
        return outcome

    try:
        monkeypatch.setattr(bridge, name, replace_after_nested_review)
        with pytest.raises(
            bridge.RegisteredArchiveBridgeRejected,
            match="authority definition changed",
        ):
            _review(case)
        assert called
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


def test_original_nested_denials_keep_registered_join_passive(tmp_path):
    case = _fixture(tmp_path)
    try:
        result = _review(case)
        assert result.step_count == 2
        assert result.cycle_file_sha256 == case["sha"]
        assert result.backend_dispatched is False
        assert result.write_authorized is False
        assert result.automatic_replay_authorized is False
        assert result.consent_authenticated is False
        assert result.independent_custody_proven is False
        assert result.external_outcome_proven is False
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()
