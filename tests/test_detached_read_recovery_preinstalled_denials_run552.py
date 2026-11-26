"""READ recovery must reject a preinstalled passive-authority callback."""

import pytest

import ark.agency.disconnected_read_recovery_journal_bridge as bridge
from ark.agency.disconnected_read_journal import (
    ReadJournalSnapshot,
    ReadJournalWitness,
    ReadReceipt,
    _chain,
    genesis_witness,
)
from ark.agency.disconnected_read_recovery_schedule import ReadRecoveryStep

REQUEST = "req_" + "a" * 32
STEP = "step_" + "1" * 16
DIGEST = "b" * 64


def evidence():
    row = ReadReceipt(REQUEST, STEP, "math.sum", "c" * 64, DIGEST)
    genesis = genesis_witness()
    retained = ReadJournalWitness(1, _chain(genesis.tip_sha256, 1, row))
    snapshot = ReadJournalSnapshot(retained, (row,))
    steps = (ReadRecoveryStep(STEP, "math.sum", (), "SUCCEEDED", DIGEST),)
    return steps, snapshot, retained


@pytest.mark.parametrize(
    ("carrier", "flag"),
    (
        (ReadJournalSnapshot, "dispatch_authorized"),
        (ReadJournalSnapshot, "effect_proven"),
        (ReadJournalSnapshot, "automatic_replay_authorized"),
        (ReadJournalSnapshot, "independent_custody_proven"),
        (ReadJournalWitness, "dispatch_authorized"),
        (ReadJournalWitness, "effect_proven"),
        (ReadJournalWitness, "replay_authorized"),
        (ReadJournalWitness, "independent_custody_proven"),
        (bridge.ReadRecoveryJournalReview, "backend_dispatched"),
        (bridge.ReadRecoveryJournalReview, "external_result_proven"),
        (bridge.ReadRecoveryJournalReview, "automatic_replay_authorized"),
        (bridge.ReadRecoveryJournalReview, "independent_custody_proven"),
    ),
)
def test_preinstalled_false_only_denial_does_not_become_custody(
    monkeypatch, carrier, flag,
):
    steps, snapshot, retained = evidence()
    invoked = []

    def forbidden(*args, **kwargs):
        invoked.append(True)
        raise AssertionError("do not schedule a precompromised recovery")

    monkeypatch.setattr(
        carrier, flag, property(lambda self: False),
    )
    monkeypatch.setattr(bridge, "schedule_detached_read_recovery", forbidden)
    with pytest.raises(
        bridge.ReadRecoveryJournalRejected,
        match="READ source descriptor changed|carrier changed",
    ):
        bridge.review_detached_read_journal_recovery(
            REQUEST, steps, snapshot, retained,
        )
    assert not invoked


def test_unchanged_recovery_still_reconciles_without_execution():
    steps, snapshot, retained = evidence()
    report = bridge.review_detached_read_journal_recovery(
        REQUEST, steps, snapshot, retained,
    )
    assert report.successful_step_ids == (STEP,)
    assert report.journal_tip_sha256 == retained.tip_sha256
    assert report.backend_dispatched is False
    assert report.automatic_replay_authorized is False
