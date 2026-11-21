"""Synthetic privacy-veto COMMIT is durable even when its receipt is refused.

A local veto only denies reuse; no consent, deletion or external export grant.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark import disconnected_privacy_veto as mod

OWNER = "a" * 64
SCOPE = "b" * 64


def make_ledger(tmp_path):
    path = tmp_path / "synthetic-veto.sqlite3"
    return mod.DisconnectedPrivacyVetoLedger(path), path


def veto(ledger, before):
    return ledger.veto(
        owner_sha256=OWNER, scope_sha256=SCOPE,
        observed_now_ms=17, retained=before,
    )


@pytest.mark.parametrize("flag", (
    "consent_verified", "deletion_proven", "context_release_authorized",
))
def test_original_receipt_denial_required_before_sqlite_write(
    tmp_path, monkeypatch, flag,
):
    ledger, _ = make_ledger(tmp_path)
    before = ledger.witness()
    invoked = []

    def substituted(_receipt):
        invoked.append(True)
        return False

    monkeypatch.setattr(mod.OfflinePrivacyVetoReceipt, flag, property(substituted))
    with pytest.raises(mod.OfflinePrivacyVetoRejected, match="receipt authority"):
        veto(ledger, before)
    assert invoked == []
    assert ledger.witness().count == 0


@pytest.mark.parametrize("forged", ("owner", "witness"))
def test_preinstalled_forged_receipt_constructor_refused_before_commit(
    tmp_path, monkeypatch, forged,
):
    ledger, path = make_ledger(tmp_path)
    before = ledger.witness()
    original = mod.OfflinePrivacyVetoReceipt.__init__
    invoked = []

    def tamper_receipt(self, *args):
        invoked.append(True)
        original(self, *args)
        if forged == "owner":
            object.__setattr__(self, "owner_sha256", "c" * 64)
        else:
            object.__setattr__(self.witness, "fingerprint", "f" * 64)

    # Original constructor preflight refuses a preinstalled counterfeit
    # BEFORE the local veto is written. The separate Run617 regression
    # exercises a constructor rebound from an actual post-COMMIT callback.
    with monkeypatch.context() as patch:
        patch.setattr(mod.OfflinePrivacyVetoReceipt, "__init__", tamper_receipt)
        with pytest.raises(
            mod.OfflinePrivacyVetoRejected, match="receipt authority changed",
        ):
            veto(ledger, before)

    assert invoked == []
    reopened = mod.DisconnectedPrivacyVetoLedger(path)
    retained = reopened.witness()
    assert retained.count == 0
    assert reopened.review(
        owner_sha256=OWNER, scope_sha256=SCOPE, retained=retained,
    ).local_veto_seen is False


def test_postcommit_path_retarget_requires_manual_reconciliation(
    tmp_path, monkeypatch,
):
    ledger, path = make_ledger(tmp_path)
    before = ledger.witness()
    open_original = ledger._open

    class ConnectionProxy:
        def __init__(self, conn):
            self.conn = conn

        def commit(self):
            self.conn.commit()
            ledger._path = Path(str(path))

        def __getattr__(self, name):
            return getattr(self.conn, name)

    monkeypatch.setattr(
        ledger, "_open",
        lambda *, read_only: ConnectionProxy(open_original(read_only=read_only)),
    )
    with pytest.raises(mod.OfflinePrivacyVetoRejected, match="post-COMMIT"):
        veto(ledger, before)

    reopened = mod.DisconnectedPrivacyVetoLedger(path)
    assert reopened.witness().count == 1


def test_regular_receipt_still_deny_only(tmp_path):
    ledger, _ = make_ledger(tmp_path)
    receipt = veto(ledger, ledger.witness())
    assert receipt.witness.count == 1
    assert receipt.consent_verified is False
    assert receipt.deletion_proven is False
    assert receipt.context_release_authorized is False
