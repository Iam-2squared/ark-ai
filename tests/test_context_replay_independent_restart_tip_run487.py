"""Context restart reports cannot trust an overridable witness callback."""

from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

import ark.personal_context_replay_ledger as ledger_module
import ark.personal_context_replay_recovery as recovery
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayWitness,
    genesis_offline_context_replay_witness,
)


def _setup(tmp_path):
    path = tmp_path / "context.sqlite"
    ledger = DisconnectedContextReplayLedger(path, create=True)
    return ledger, genesis_offline_context_replay_witness(), path


def _append_valid_row(path):
    previous = genesis_offline_context_replay_witness()
    fields = (
        "ctxreq_" + "a" * 64,
        "b" * 64,
        "c" * 64,
        "d" * 64,
    )
    chain = ledger_module._hash(
        ("row", previous.chain_sha256, 1, *fields),
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO context_requests VALUES(?,?,?,?,?,?)",
            (1, *fields, chain),
        )
    return OfflineContextReplayWitness(1, chain)


def _review(ledger, retained):
    return recovery.review_restarted_context_replay(ledger, retained)


def test_unchanged_durable_history_is_inert(tmp_path):
    ledger, retained, _ = _setup(tmp_path)
    report = _review(ledger, retained)
    assert report.status == "UNCHANGED_LOCAL_HISTORY"
    assert report.observed_count == 0
    assert report.independent_custody_proven is False
    assert report.consent_verified is False
    assert report.context_disclosure_authorized is False
    assert report.automatic_replay_authorized is False


def test_valid_advanced_history_remains_unverified(tmp_path):
    ledger, retained, path = _setup(tmp_path)
    latest = _append_valid_row(path)
    report = _review(ledger, retained)
    assert report.status == "ADVANCED_HISTORY_UNVERIFIED"
    assert report.observed_count == 1
    assert ledger.witness() == latest
    assert report.tool_dispatch_authorized is False


@pytest.mark.parametrize("count", [0, 1, 512])
def test_spoofed_exact_type_witness_cannot_replace_durable_tip(
    tmp_path, monkeypatch, count,
):
    ledger, retained, _ = _setup(tmp_path)
    forged = replace(retained, count=count, chain_sha256="f" * 64)
    monkeypatch.setattr(ledger, "witness", lambda: forged)
    with pytest.raises(recovery.OfflineContextRecoveryRejected, match="durable tip"):
        _review(ledger, retained)


def test_stale_callback_result_after_sqlite_append_is_rejected(
    tmp_path, monkeypatch,
):
    ledger, retained, path = _setup(tmp_path)

    def write_then_return_stale():
        _append_valid_row(path)
        return retained

    monkeypatch.setattr(ledger, "witness", write_then_return_stale)
    with pytest.raises(recovery.OfflineContextRecoveryRejected, match="durable tip"):
        _review(ledger, retained)
    assert ledger.witness is write_then_return_stale
    assert DisconnectedContextReplayLedger(path).witness().count == 1


def test_report_constructor_cannot_hide_intervening_append(tmp_path, monkeypatch):
    ledger, retained, path = _setup(tmp_path)
    original = recovery.OfflineContextRecoveryReview

    def append_during_report(*args):
        result = original(*args)
        _append_valid_row(path)
        return result

    monkeypatch.setattr(recovery, "OfflineContextRecoveryReview", append_during_report)
    with pytest.raises(recovery.OfflineContextRecoveryRejected, match="durable tip"):
        _review(ledger, retained)


def test_callback_with_legitimate_new_durable_tip_still_unverified(
    tmp_path, monkeypatch,
):
    ledger, retained, path = _setup(tmp_path)
    new_tip = _append_valid_row(path)
    monkeypatch.setattr(ledger, "witness", lambda: new_tip)
    report = _review(ledger, retained)
    assert report.status == "ADVANCED_HISTORY_UNVERIFIED"
    assert report.independent_custody_proven is False
    assert report.context_disclosure_authorized is False
