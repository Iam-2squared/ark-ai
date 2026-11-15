"""Restart triage of synthetic expired schedule slots never grants replay.

No scheduler, timer, notification, external execution or trusted clock.
"""

from dataclasses import replace

import pytest

from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)
from ark.offline_schedule_unknown_quarantine_review import (
    ScheduleUnknownQuarantineRejected,
    review_schedule_unknown_quarantine,
)


def _policy() -> QuarantinePolicy:
    return QuarantinePolicy("a" * 64, 100, 1000, 3, 5)


def _ledger(tmp_path):
    policy = _policy()
    path = tmp_path / "quarantine.sqlite"
    initial = DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    return policy, initial, path


def _review(ledger, policy, before, index, observed):
    return review_schedule_unknown_quarantine(
        ledger, policy, before, index=index,
        occurrence_id=derive_quarantined_occurrence(policy, index),
        observed_ms=observed,
    )


def _deny_authority(result):
    assert result.notification_authorized is False
    assert result.execution_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.trusted_clock_verified is False
    assert result.consent_verified is False
    assert result.manual_review_required is True


def test_restart_recognizes_possible_committed_quarantine_without_replay(tmp_path):
    policy, ledger, path = _ledger(tmp_path)
    prior = genesis_quarantine_witness(policy)
    receipt = ledger.quarantine_expired(
        index=0, occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=110, retained=prior,
    )
    restarted = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    result = _review(restarted, policy, prior, 0, 110)
    assert result.local_state == "LOCALLY_QUARANTINED"
    assert result.before_count == 0 and result.observed_count == 1
    assert result.locally_present is True
    _deny_authority(result)
    assert restarted.inspect(retained=receipt.witness) == receipt.witness


def test_retained_postcommit_prefix_yields_preexisting_not_new_permission(tmp_path):
    policy, ledger, path = _ledger(tmp_path)
    genesis = genesis_quarantine_witness(policy)
    receipt = ledger.quarantine_expired(
        index=0, occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=110, retained=genesis,
    )
    reopened = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    result = _review(reopened, policy, receipt.witness, 0, 110)
    assert result.local_state == "PREEXISTING"
    assert result.before_count == result.observed_count == 1
    assert result.locally_present is True
    _deny_authority(result)


def test_uncommitted_and_unrelated_advance_are_distinct_unknown_states(tmp_path):
    policy, ledger, path = _ledger(tmp_path)
    genesis = genesis_quarantine_witness(policy)
    clean = _review(ledger, policy, genesis, 0, 110)
    assert clean.local_state == "UNCHANGED"
    assert clean.locally_present is False
    _deny_authority(clean)
    ledger.quarantine_expired(
        index=0, occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=110, retained=genesis,
    )
    reopened = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    another = _review(reopened, policy, genesis, 1, 1110)
    assert another.local_state == "ADVANCED_OTHER"
    assert another.locally_present is False
    assert another.observed_count == 1
    _deny_authority(another)


def test_forged_genesis_and_wrong_observation_cannot_reconcile(tmp_path):
    policy, ledger, path = _ledger(tmp_path)
    genesis = genesis_quarantine_witness(policy)
    wrong = replace(genesis, chain_sha256="f" * 64)
    with pytest.raises(ScheduleUnknownQuarantineRejected, match="genesis mismatch"):
        _review(ledger, policy, wrong, 0, 110)
    receipt = ledger.quarantine_expired(
        index=0, occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=110, retained=genesis,
    )
    restarted = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    with pytest.raises(ScheduleUnknownQuarantineRejected, match="evidence differs"):
        _review(restarted, policy, genesis, 0, 111)
    assert restarted.inspect(retained=receipt.witness) == receipt.witness
