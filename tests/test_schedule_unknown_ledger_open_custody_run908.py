"""Schedule UNKNOWN review never uses a substituted instance method.

Disconnected overdue schedule facts remain caller-controlled, non-authorizing
and subject to manual review, including after a local SQLite commit.
"""

import pytest

from ark import disconnected_schedule_quarantine_ledger as ledger_module
from ark import offline_schedule_unknown_quarantine_review as review_module


def _fixture(tmp_path):
    policy = ledger_module.QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    path = tmp_path / "quarantine.sqlite"
    ledger = ledger_module.DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    before = ledger_module.genesis_quarantine_witness(policy)
    occurrence = ledger_module.derive_quarantined_occurrence(policy, 0)
    return ledger, policy, before, occurrence, path


def _review(ledger, policy, before, occurrence):
    return review_module.review_schedule_unknown_quarantine(
        ledger, policy, before, index=0,
        occurrence_id=occurrence, observed_ms=10_501,
    )


@pytest.mark.parametrize("shadow", ("_open", "_check_witness", "unexpected"))
def test_instance_open_or_protocol_shadow_refused_before_callback(
    tmp_path, shadow,
):
    ledger, policy, before, occurrence, path = _fixture(tmp_path)
    calls = []

    def injected(*args, **kwargs):
        calls.append("executed")
        raise AssertionError("forged ledger callback executed")

    setattr(ledger, shadow, injected)
    with pytest.raises(
        review_module.ScheduleUnknownQuarantineRejected,
        match="ledger instance changed",
    ):
        _review(ledger, policy, before, occurrence)
    assert calls == []
    assert path.exists()


def test_untouched_ledger_unknown_is_inert(tmp_path):
    ledger, policy, before, occurrence, _ = _fixture(tmp_path)
    result = _review(ledger, policy, before, occurrence)
    assert result.local_state == "UNCHANGED"
    assert result.locally_present is False
    assert result.manual_review_required is True
    assert result.automatic_replay_authorized is False
    assert result.execution_authorized is False
    assert result.notification_authorized is False


def test_locally_recorded_expiry_remains_manual_review_only(tmp_path):
    ledger, policy, before, occurrence, _ = _fixture(tmp_path)
    ledger.quarantine_expired(
        index=0, occurrence_id=occurrence,
        observed_ms=10_501, retained=before,
    )
    result = _review(ledger, policy, before, occurrence)
    assert result.local_state == "LOCALLY_QUARANTINED"
    assert result.locally_present is True
    assert result.automatic_replay_authorized is False
    assert result.trusted_clock_verified is False


def test_restart_prior_quarantine_does_not_gain_authority(tmp_path):
    ledger, policy, before, occurrence, path = _fixture(tmp_path)
    committed = ledger.quarantine_expired(
        index=0, occurrence_id=occurrence,
        observed_ms=10_501, retained=before,
    )
    reopened = ledger_module.DisconnectedScheduleQuarantineLedger(
        path, policy=policy,
    )
    result = _review(reopened, policy, committed.witness, occurrence)
    assert result.local_state == "PREEXISTING"
    assert result.before_count == result.observed_count == 1
    assert result.manual_review_required is True
    assert result.consent_verified is False
