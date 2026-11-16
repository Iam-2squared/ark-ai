"""Quarantine ledger source/policy carriers survive separate fixture calls.

All schedule slots, timestamps and SQLite files are synthetic. A classification
receipt never authorizes an external action or automatic replay.
"""

from pathlib import Path

import pytest

from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)


def _fixture(tmp_path):
    policy = QuarantinePolicy("a" * 64, 1000, 1000, 2, 100)
    store = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.sqlite", policy=policy, create=True,
    )
    return store, policy, genesis_quarantine_witness(policy)


@pytest.mark.parametrize("retarget", ("different-path", "equal-path", "equal-policy"))
@pytest.mark.parametrize("operation", ("inspect", "quarantine"))
def test_quarantine_rejects_between_call_retargeting(
    tmp_path, retarget, operation,
):
    store, policy, witness = _fixture(tmp_path)
    if retarget == "different-path":
        store._path = Path(str(tmp_path / "other.sqlite"))
    elif retarget == "equal-path":
        store._path = Path(str(store._path))
        assert store._path == store._source_path_epoch
    else:
        store._epoch = tuple([*store._epoch])
        assert store._epoch == store._source_policy_epoch
    with pytest.raises(
        ScheduleQuarantineRejected, match="source or policy identity changed",
    ):
        if operation == "inspect":
            store.inspect(retained=witness)
        else:
            store.quarantine_expired(
                index=0, occurrence_id=derive_quarantined_occurrence(policy, 0),
                observed_ms=1200, retained=witness,
            )
    # The intended original file was not mutated or redirected.
    assert (tmp_path / "quarantine.sqlite").is_file()


def test_original_carriers_preserve_nonexecuting_quarantine_flow(tmp_path):
    store, policy, retained = _fixture(tmp_path)
    assert store.inspect(retained=retained) == retained
    receipt = store.quarantine_expired(
        index=0, occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=1200, retained=retained,
    )
    assert receipt.witness.count == 1
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    restarted = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.sqlite", policy=policy, create=False,
    )
    assert restarted.inspect(retained=receipt.witness) == receipt.witness
