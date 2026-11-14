"""Run748: Personal Context restart diagnostics must not execute substituted codecs.

Temporary replay ledgers contain only synthetic digest identities. No live
context disclosure, consent, deletion, notification or tool dispatch occurs.
"""

from __future__ import annotations

import pytest

import ark.personal_context_replay_recovery as recovery
from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger


def _fixture(tmp_path):
    ledger = DisconnectedContextReplayLedger(
        tmp_path / "private-context-replay.sqlite3", create=True,
    )
    return ledger, ledger.witness()


@pytest.mark.parametrize("attack", (
    "sha256", "dumps", "hashlib_module", "json_module",
    "domain_changed", "domain_equal_clone",
))
def test_preinstalled_codec_replacement_denied_before_private_read(
    tmp_path, monkeypatch, attack,
):
    ledger, retained = _fixture(tmp_path)
    calls = []

    def execute(*_args, **_kwargs):
        calls.append("substituted codec")
        raise AssertionError("untrusted recovery codec executed")

    def private_read():
        calls.append("private ledger read")
        raise AssertionError("private witness read before codec verification")

    monkeypatch.setattr(ledger, "witness", private_read)
    if attack == "sha256":
        monkeypatch.setattr(recovery.hashlib, "sha256", execute)
    elif attack == "dumps":
        monkeypatch.setattr(recovery.json, "dumps", execute)
    elif attack == "hashlib_module":
        monkeypatch.setattr(recovery, "hashlib", object())
    elif attack == "json_module":
        monkeypatch.setattr(recovery, "json", object())
    elif attack == "domain_changed":
        monkeypatch.setattr(recovery, "_DOMAIN", b"forged-recovery-domain")
    else:
        cloned = bytes(bytearray(recovery._DOMAIN))
        assert cloned == recovery._DOMAIN
        assert cloned is not recovery._DOMAIN
        monkeypatch.setattr(recovery, "_DOMAIN", cloned)
    with pytest.raises(
        recovery.OfflineContextRecoveryRejected,
        match="digest implementation changed",
    ):
        recovery.review_restarted_context_replay(ledger, retained)
    assert calls == []


def test_ledger_callback_cannot_rebind_domain_before_recovery_digest(
    tmp_path, monkeypatch,
):
    ledger, retained = _fixture(tmp_path)
    original = ledger.witness
    reads = []

    def retarget_during_read():
        reads.append("witness")
        value = original()
        monkeypatch.setattr(recovery, "_DOMAIN", b"forged-recovery-domain")
        return value

    monkeypatch.setattr(ledger, "witness", retarget_during_read)
    with pytest.raises(
        recovery.OfflineContextRecoveryRejected,
        match="digest implementation changed",
    ):
        recovery.review_restarted_context_replay(ledger, retained)
    assert reads == ["witness"]


def test_unchanged_local_history_remains_inert(tmp_path):
    ledger, retained = _fixture(tmp_path)
    report = recovery.review_restarted_context_replay(ledger, retained)
    assert report.status == "UNCHANGED_LOCAL_HISTORY"
    assert report.observed_count == 0
    assert len(report.comparison_sha256) == 64
    assert report.historical_prefix_proven is False
    assert report.independent_custody_proven is False
    assert report.consent_verified is False
    assert report.context_disclosure_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.automatic_replay_authorized is False
