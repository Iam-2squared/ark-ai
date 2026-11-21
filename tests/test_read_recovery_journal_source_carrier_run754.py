"""READ journal join rejects counterfeit source slots before seeing private digests.

Fixture-only checks; neither a journal receipt nor this review authorizes
execution, replay, consent or independently authenticated custody.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_read_recovery_journal_bridge as bridge
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
RESULT = "b" * 64
INPUT = "c" * 64


def _case():
    row = ReadReceipt(REQUEST, STEP, "math.sum", INPUT, RESULT)
    tip = _chain(genesis_witness().tip_sha256, 1, row)
    witness = ReadJournalWitness(1, tip)
    snapshot = ReadJournalSnapshot(witness, (row,))
    steps = (ReadRecoveryStep(STEP, "math.sum", (), "SUCCEEDED", RESULT),)
    return steps, snapshot, witness


@pytest.mark.parametrize(
    "kind,slot",
    (
        ("snapshot", "witness"),
        ("snapshot", "receipts"),
        ("witness", "count"),
        ("witness", "tip_sha256"),
        ("receipt", "input_digest"),
        ("receipt", "result_digest"),
    ),
)
def test_preinstalled_source_descriptor_is_denied_before_getter(
    monkeypatch, kind, slot,
):
    steps, snapshot, retained = _case()
    carrier = {
        "snapshot": ReadJournalSnapshot,
        "witness": ReadJournalWitness,
        "receipt": ReadReceipt,
    }[kind]
    invoked = []

    def hostile(_instance):
        invoked.append(slot)
        raise AssertionError("private retained witness was read by a fake getter")

    with monkeypatch.context() as patch:
        patch.setattr(carrier, slot, property(hostile))
        with pytest.raises(
            bridge.ReadRecoveryJournalRejected,
            match="READ source descriptor changed",
        ):
            bridge.review_detached_read_journal_recovery(
                REQUEST, steps, snapshot, retained,
            )
    assert invoked == []


def test_source_validator_replacement_never_runs_before_private_read(monkeypatch):
    steps, snapshot, retained = _case()
    invoked = []

    def fake_validator():
        invoked.append("unreviewed")

    with monkeypatch.context() as patch:
        patch.setattr(bridge, "_require_original_read_carriers", fake_validator)
        with pytest.raises(
            bridge.ReadRecoveryJournalRejected,
            match="READ source validator changed",
        ):
            bridge.review_detached_read_journal_recovery(
                REQUEST, steps, snapshot, retained,
            )
    assert invoked == []


def test_schedule_callback_cannot_install_receipt_getter_after_first_epoch(
    monkeypatch,
):
    steps, snapshot, retained = _case()
    original = bridge.schedule_detached_read_recovery
    invoked = []

    def hostile(_instance):
        invoked.append("getter")
        raise AssertionError("receipt getter called after synthetic scheduling")

    def inject(request_id, supplied_steps):
        result = original(request_id, supplied_steps)
        monkeypatch.setattr(ReadReceipt, "input_digest", property(hostile))
        return result

    with monkeypatch.context() as patch:
        patch.setattr(bridge, "schedule_detached_read_recovery", inject)
        with pytest.raises(
            bridge.ReadRecoveryJournalRejected,
            match="READ source descriptor changed",
        ):
            bridge.review_detached_read_journal_recovery(
                REQUEST, steps, snapshot, retained,
            )
    assert invoked == []


def test_clean_join_still_denies_execution_and_replay():
    steps, snapshot, retained = _case()
    result = bridge.review_detached_read_journal_recovery(
        REQUEST, steps, snapshot, retained,
    )
    assert result.successful_step_ids == (STEP,)
    assert result.backend_dispatched is False
    assert result.external_result_proven is False
    assert result.automatic_replay_authorized is False
    assert result.independent_custody_proven is False
