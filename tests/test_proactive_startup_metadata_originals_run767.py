"""Synthetic proactive startup denies substituted metadata/epoch readers.

A replaced metadata extractor is executable and could see private trigger,
policy and readiness attributes before deny-only output checks.
"""

from __future__ import annotations

import pytest

import ark.proactive_startup_fence_review as startup
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerReceipt,
)
from ark.startup_readiness_review import StartupSnapshot


@pytest.mark.parametrize(
    "callback", ("fields", "_epoch", "_snapshot_epoch"),
)
def test_changed_startup_metadata_reader_denied_before_private_inputs(
    callback: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked: list[bool] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        invoked.append(True)
        raise AssertionError("private startup metadata was inspected")

    monkeypatch.setattr(startup, callback, forbidden)
    # These exact-typed inputs have no initialized private fields. An early
    # reader call would raise AttributeError or execute the forbidden hook.
    ledger = object.__new__(SyntheticProactiveLedger)
    receipt = object.__new__(SyntheticTriggerReceipt)
    policy = object.__new__(SyntheticTriggerPolicy)
    snapshot = object.__new__(StartupSnapshot)
    with pytest.raises(
        startup.SyntheticProactiveStartupRejected,
        match="authority descriptor epoch changed",
    ):
        startup.review_synthetic_proactive_startup(
            ledger, receipt, policy, snapshot, (),
            source_digest="a" * 64,
            observation_digest="b" * 64,
            captured_at_ms=10,
            now_ms=10,
            max_startup_age_ms=100,
            max_observation_age_ms=100,
        )
    assert not invoked
