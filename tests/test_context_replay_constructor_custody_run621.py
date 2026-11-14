"""Synthetic Personal Context restart may never execute a forged result initializer.

Read-only SQLite witnesses are not authenticated consent, disclosure permission,
revocation freshness, tool dispatch, or safe replay after a crashed WRITE.
"""

import pytest
from test_personal_context_replay_recovery_run482 import _ledger

import ark.personal_context_replay_recovery as review


@pytest.mark.parametrize("attack", ("class", "initializer"))
def test_preinstalled_result_code_refused_without_reopening_sqlite(
    tmp_path, monkeypatch, attack,
):
    ledger = _ledger(tmp_path)
    retained = ledger.witness()
    executed = []

    def forbidden(*_args, **_kwargs):
        executed.append("executed")
        raise AssertionError("forged review constructor may not execute")

    def no_sqlite(*_args, **_kwargs):
        raise AssertionError("preinstalled forgery must be rejected before SQLite")

    with monkeypatch.context() as patch:
        if attack == "class":
            patch.setattr(review, "OfflineContextRecoveryReview", forbidden)
        else:
            patch.setattr(review.OfflineContextRecoveryReview, "__init__", forbidden)
        patch.setattr(type(ledger), "_open", no_sqlite)
        with pytest.raises(
            review.OfflineContextRecoveryRejected,
            match="review result gained authority",
        ):
            review.review_restarted_context_replay(ledger, retained)

    assert executed == []


@pytest.mark.parametrize("phase", ("witness", "durable_read"))
def test_reentrant_read_cannot_install_late_result_constructor(
    tmp_path, monkeypatch, phase,
):
    ledger = _ledger(tmp_path)
    retained = ledger.witness()
    executed = []

    def forbidden(*_args, **_kwargs):
        executed.append("executed")
        raise AssertionError("forged review constructor may not execute")

    with monkeypatch.context() as patch:
        if phase == "witness":
            original = ledger.witness

            def witness_hook():
                observed = original()
                patch.setattr(review.OfflineContextRecoveryReview, "__init__", forbidden)
                return observed

            patch.setattr(ledger, "witness", witness_hook)
        else:
            original = review._inspect

            def read_hook(conn):
                observed = original(conn)
                patch.setattr(review.OfflineContextRecoveryReview, "__init__", forbidden)
                return observed

            patch.setattr(review, "_inspect", read_hook)

        with pytest.raises(
            review.OfflineContextRecoveryRejected,
            match="review result gained authority",
        ):
            review.review_restarted_context_replay(ledger, retained)

    assert executed == []


def test_original_restart_review_remains_denial_only(tmp_path):
    ledger = _ledger(tmp_path)
    retained = ledger.witness()
    report = review.review_restarted_context_replay(ledger, retained)
    assert report.status == "UNCHANGED_LOCAL_HISTORY"
    assert report.historical_prefix_proven is False
    assert report.consent_verified is False
    assert report.context_disclosure_authorized is False
    assert report.automatic_replay_authorized is False
