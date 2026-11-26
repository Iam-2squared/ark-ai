"""Offline Context replay witness getters are never trusted as authority.

All SQLite state is disposable; no personal text, consent or tool execution.
"""

import pytest

import ark.personal_context_replay_ledger as replay
from ark.personal_context_replay_prefix_review import (
    OfflineContextPrefixRejected,
    review_retained_context_replay_prefix,
)


@pytest.mark.parametrize("lane", ("direct", "witness", "retained_prefix"))
def test_preinstalled_false_getter_is_rejected_without_execution(
    tmp_path, monkeypatch, lane,
):
    ledger = replay.DisconnectedContextReplayLedger(
        tmp_path / "context.sqlite", create=True,
    )
    retained = replay.genesis_offline_context_replay_witness()
    invoked = []

    def counterfeit(_self):
        invoked.append("getter-called")
        return False

    monkeypatch.setattr(
        replay.OfflineContextReplayWitness,
        "independent_custody_proven", property(counterfeit),
    )
    if lane == "direct":
        with pytest.raises(
            replay.OfflineContextReplayRejected, match="witness",
        ):
            replay._check_witness(retained)
    elif lane == "witness":
        with pytest.raises(
            replay.OfflineContextReplayRejected, match="witness",
        ):
            ledger.witness()
    else:
        with pytest.raises(
            OfflineContextPrefixRejected, match="witness",
        ):
            review_retained_context_replay_prefix(ledger, retained)
    assert invoked == []


def test_copied_descriptor_foreign_witness_class_is_not_accepted(monkeypatch):
    retained = replay.genesis_offline_context_replay_witness()
    original = replay.OfflineContextReplayWitness

    class Counterfeit(original):
        pass

    monkeypatch.setattr(replay, "OfflineContextReplayWitness", Counterfeit)
    with pytest.raises(
        replay.OfflineContextReplayRejected, match="witness",
    ):
        replay._check_witness(retained)


def test_normal_genesis_replay_prefix_stays_read_only(tmp_path):
    ledger = replay.DisconnectedContextReplayLedger(
        tmp_path / "context.sqlite", create=True,
    )
    retained = replay.genesis_offline_context_replay_witness()
    assert replay._check_witness(retained)[0] == 0
    assert ledger.witness() == retained
    report = review_retained_context_replay_prefix(ledger, retained)
    assert report.status == "UNCHANGED_LOCAL_HISTORY"
    assert report.consent_verified is False
    assert report.tool_dispatch_authorized is False
    assert report.automatic_replay_authorized is False
