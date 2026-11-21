"""Restart reports must remain inert across their final SQLite recheck.

The late callback can mutate a frozen report or replace an authority
descriptor after the first result validation. No Personal Context is read.
"""

from __future__ import annotations

import inspect

import pytest

import ark.personal_context_replay_recovery as recovery
from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger


def _fixture(tmp_path):
    ledger = DisconnectedContextReplayLedger(tmp_path / "replay.sqlite", create=True)
    return ledger, ledger.witness()


def test_unchanged_context_replay_result_remains_non_authorizing(tmp_path):
    ledger, witness = _fixture(tmp_path)
    result = recovery.review_restarted_context_replay(ledger, witness)
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert result.context_disclosure_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False


@pytest.mark.parametrize("attack", [
    "status",
    "comparison_sha256",
    "observed_count",
    "automatic_replay_authorized",
    "context_disclosure_authorized",
])
def test_final_sqlite_callback_cannot_retire_result_validation(
    tmp_path, monkeypatch, attack,
):
    ledger, witness = _fixture(tmp_path)
    original_result_type = recovery._RESULT_TYPE
    original_inspect = recovery._inspect
    calls = 0

    def in_flight_review():
        # Observe the original result carrier without replacing the now
        # protected result constructor. A passive frame inspection is limited
        # to this synthetic fault-injection test, never production code.
        frame = inspect.currentframe()
        try:
            while frame is not None:
                if frame.f_code.co_name == "review_restarted_context_replay":
                    return frame.f_locals["result"]
                frame = frame.f_back
        finally:
            del frame
        raise AssertionError("result not yet constructed")

    def mutate_during_final_read(conn):
        nonlocal calls
        calls += 1
        observed = original_inspect(conn)
        if calls == 2:
            report = in_flight_review()
            if attack == "status":
                object.__setattr__(report, "status", "ADVANCED_HISTORY_UNVERIFIED")
            elif attack == "comparison_sha256":
                object.__setattr__(report, "comparison_sha256", "0" * 64)
            elif attack == "observed_count":
                object.__setattr__(report, "observed_count", 1)
            else:
                monkeypatch.setattr(
                    original_result_type, attack, property(lambda _self: True),
                )
        return observed

    monkeypatch.setattr(recovery, "_inspect", mutate_during_final_read)
    with pytest.raises(
        recovery.OfflineContextRecoveryRejected, match="review result (changed|gained authority)",
    ):
        recovery.review_restarted_context_replay(ledger, witness)
    # All mutations are now rejected after the second durable read,
    # before a substituted permission getter can be invoked again.
    assert calls == 2
    assert ledger.witness() == witness
