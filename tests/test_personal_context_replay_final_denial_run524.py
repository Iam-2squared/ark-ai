"""Restarted Personal Context replay denial must not confer disclosure authority.

SQLite is a local synthetic fixture, not a consent, retention or real replay log.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger
from ark.personal_context_replay_recovery import (
    OfflineContextRecoveryRejected,
    OfflineContextRecoveryReview,
    review_restarted_context_replay,
)


def setup_case(tmp_path):
    source = tmp_path / "context-replay.sqlite"
    ledger = DisconnectedContextReplayLedger(source, create=True)
    retained = ledger.witness()
    return source, ledger, retained


def test_restart_empty_local_ledger_remains_denial_only(tmp_path):
    _, ledger, retained = setup_case(tmp_path)
    report = review_restarted_context_replay(ledger, retained)
    assert type(report) is OfflineContextRecoveryReview
    assert report.retained_count == 0
    assert report.observed_count == 0
    assert report.status == "UNCHANGED_LOCAL_HISTORY"
    assert len(report.comparison_sha256) == 64
    assert report.historical_prefix_proven is False
    assert report.independent_custody_proven is False
    assert report.consent_verified is False
    assert report.revocation_freshness_verified is False
    assert report.context_disclosure_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.automatic_replay_authorized is False


@pytest.mark.parametrize("attribute", ["comparison_sha256", "status", "observed_count"])
def test_false_final_authority_getter_cannot_rewrite_report(
    tmp_path, monkeypatch, attribute,
):
    _, ledger, retained = setup_case(tmp_path)

    def malicious_false(self):
        changed = {
            "comparison_sha256": "f" * 64,
            "status": "ADVANCED_HISTORY_UNVERIFIED",
            "observed_count": 1,
        }
        object.__setattr__(self, attribute, changed[attribute])
        return False

    monkeypatch.setattr(
        OfflineContextRecoveryReview, "automatic_replay_authorized",
        property(malicious_false),
    )
    with pytest.raises(
        OfflineContextRecoveryRejected, match="result changed|gained authority",
    ):
        review_restarted_context_replay(ledger, retained)


@pytest.mark.parametrize("forged", [True, 1, "false"])
def test_false_like_or_truthy_execution_authority_is_denied(
    tmp_path, monkeypatch, forged,
):
    _, ledger, retained = setup_case(tmp_path)
    monkeypatch.setattr(
        OfflineContextRecoveryReview, "context_disclosure_authorized",
        property(lambda self: forged),
    )
    with pytest.raises(OfflineContextRecoveryRejected, match="gained authority"):
        review_restarted_context_replay(ledger, retained)


def test_false_denial_getter_cannot_retarget_original_ledger_path(
    tmp_path, monkeypatch,
):
    source, ledger, retained = setup_case(tmp_path)

    def malicious_false(self):
        ledger._path = Path(str(source))
        return False

    monkeypatch.setattr(
        OfflineContextRecoveryReview, "automatic_replay_authorized",
        property(malicious_false),
    )
    with pytest.raises(OfflineContextRecoveryRejected):
        review_restarted_context_replay(ledger, retained)


def test_false_denial_getter_cannot_mutate_durable_schema(
    tmp_path, monkeypatch,
):
    source, ledger, retained = setup_case(tmp_path)

    def malicious_false(self):
        with sqlite3.connect(source) as connection:
            connection.execute("CREATE TABLE forged_context_authority (id INTEGER)")
        return False

    monkeypatch.setattr(
        OfflineContextRecoveryReview, "automatic_replay_authorized",
        property(malicious_false),
    )
    with pytest.raises(OfflineContextRecoveryRejected):
        review_restarted_context_replay(ledger, retained)
