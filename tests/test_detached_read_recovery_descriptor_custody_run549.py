"""Deny-only descriptor custody across detached READ recovery callbacks."""

import pytest

import ark.agency.disconnected_read_recovery_journal_bridge as bridge
from ark.agency.disconnected_read_journal import (
    ReadJournalSnapshot,
    ReadJournalWitness,
    ReadReceipt,
    _chain,
    genesis_witness,
)
from ark.agency.disconnected_read_recovery_journal_bridge import (
    ReadRecoveryJournalRejected,
    ReadRecoveryJournalReview,
)
from ark.agency.disconnected_read_recovery_schedule import ReadRecoveryStep

_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "1" * 16
_DIGEST = "b" * 64
_INPUT = "c" * 64


def _evidence():
    row = ReadReceipt(_REQUEST, _STEP, "math.sum", _INPUT, _DIGEST)
    start = genesis_witness()
    retained = ReadJournalWitness(1, _chain(start.tip_sha256, 1, row))
    snapshot = ReadJournalSnapshot(retained, (row,))
    history = (ReadRecoveryStep(_STEP, "math.sum", (), "SUCCEEDED", _DIGEST),)
    return history, snapshot, retained


@pytest.mark.parametrize(
    ("carrier", "flag"),
    [
        (ReadJournalSnapshot, "dispatch_authorized"),
        (ReadJournalSnapshot, "effect_proven"),
        (ReadJournalSnapshot, "automatic_replay_authorized"),
        (ReadJournalSnapshot, "independent_custody_proven"),
        (ReadJournalWitness, "dispatch_authorized"),
        (ReadJournalWitness, "effect_proven"),
        (ReadJournalWitness, "replay_authorized"),
        (ReadJournalWitness, "independent_custody_proven"),
        (ReadRecoveryJournalReview, "backend_dispatched"),
        (ReadRecoveryJournalReview, "external_result_proven"),
        (ReadRecoveryJournalReview, "automatic_replay_authorized"),
        (ReadRecoveryJournalReview, "independent_custody_proven"),
    ],
)
def test_false_only_descriptor_replacement_during_schedule_is_denied(
    monkeypatch, carrier, flag,
):
    history, snapshot, retained = _evidence()
    schedule = bridge.schedule_detached_read_recovery

    def swapped(request_id, steps):
        # An unchanged False return is NOT evidence the original descriptor
        # is still installed. The second scheduler invocation must not mask it.
        monkeypatch.setattr(carrier, flag, property(lambda _: False))
        return schedule(request_id, steps)

    monkeypatch.setattr(bridge, "schedule_detached_read_recovery", swapped)
    with pytest.raises(ReadRecoveryJournalRejected):
        bridge.review_detached_read_journal_recovery(
            _REQUEST, history, snapshot, retained,
        )


def test_original_denial_descriptors_preserve_valid_inert_recovery():
    history, snapshot, retained = _evidence()
    report = bridge.review_detached_read_journal_recovery(
        _REQUEST, history, snapshot, retained,
    )
    assert report.successful_step_ids == (_STEP,)
    assert report.backend_dispatched is False
    assert report.external_result_proven is False
    assert report.automatic_replay_authorized is False
    assert report.independent_custody_proven is False
