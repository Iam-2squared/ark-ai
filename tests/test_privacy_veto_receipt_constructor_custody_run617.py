"""The local privacy-veto receipt constructor cannot execute injected code.

The denial marker remains committed when evidence after COMMIT becomes
uncertain. A local veto never proves consent, identity, deletion or a grant.
"""

import pytest

from ark import disconnected_privacy_veto as mod

OWNER = "a" * 64
SCOPE = "b" * 64


def _fixture(tmp_path):
    path = tmp_path / "constructor-veto.sqlite3"
    ledger = mod.DisconnectedPrivacyVetoLedger(path)
    return ledger, path


def _veto(ledger, retained):
    return ledger.veto(
        owner_sha256=OWNER, scope_sha256=SCOPE,
        observed_now_ms=17, retained=retained,
    )


def test_preinstalled_receipt_constructor_refused_before_write(
    tmp_path, monkeypatch,
):
    ledger, _path = _fixture(tmp_path)
    before = ledger.witness()
    calls = []

    def injected(self, *args):
        calls.append(args)
        raise AssertionError("forged receipt constructor executed")

    monkeypatch.setattr(mod.OfflinePrivacyVetoReceipt, "__init__", injected)
    with pytest.raises(
        mod.OfflinePrivacyVetoRejected, match="receipt authority changed",
    ):
        _veto(ledger, before)
    assert calls == []
    assert ledger.witness().count == 0


def test_postcommit_receipt_constructor_rebound_is_manual_only(
    tmp_path, monkeypatch,
):
    ledger, path = _fixture(tmp_path)
    before = ledger.witness()
    calls = []

    def injected(self, *args):
        calls.append(args)
        raise AssertionError("forged post-COMMIT receipt constructor executed")

    original_open = ledger._open

    class CommitProxy:
        def __init__(self, conn):
            self._conn = conn

        def commit(self):
            self._conn.commit()
            monkeypatch.setattr(
                mod.OfflinePrivacyVetoReceipt, "__init__", injected,
            )

        def __getattr__(self, name):
            return getattr(self._conn, name)

    def open_with_callback(*, read_only):
        conn = original_open(read_only=read_only)
        return conn if read_only else CommitProxy(conn)

    monkeypatch.setattr(ledger, "_open", open_with_callback)
    with pytest.raises(mod.OfflinePrivacyVetoRejected, match="post-COMMIT"):
        _veto(ledger, before)
    assert calls == []
    reopened = mod.DisconnectedPrivacyVetoLedger(path)
    assert reopened.witness().count == 1


def test_clean_privacy_veto_receipt_is_still_denial_only(tmp_path):
    ledger, _path = _fixture(tmp_path)
    receipt = _veto(ledger, ledger.witness())
    assert receipt.witness.count == 1
    assert receipt.consent_verified is False
    assert receipt.deletion_proven is False
    assert receipt.context_release_authorized is False
