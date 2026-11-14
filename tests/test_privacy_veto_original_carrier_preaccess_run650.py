"""Pre-access custody of the local, denial-only privacy veto carriers.

No user data, external notification or consent is involved; a synthetic witness
never authorizes disclosure. Replaced Python-level descriptors must not execute
before a review, veto transaction, or post-COMMIT receipt construction.
"""

from __future__ import annotations

import pytest

import ark.disconnected_privacy_veto as veto

OWNER = "a" * 64
SCOPE = "b" * 64


def _fixture(tmp_path):
    ledger = veto.DisconnectedPrivacyVetoLedger(tmp_path / "privacy-custody.sqlite3")
    return ledger, ledger.witness()


def _request(ledger, retained, *, operation):
    if operation == "review":
        return ledger.review(
            owner_sha256=OWNER, scope_sha256=SCOPE, retained=retained,
        )
    return ledger.veto(
        owner_sha256=OWNER, scope_sha256=SCOPE,
        observed_now_ms=12, retained=retained,
    )


_MISSING = object()


def _poison(carrier_type, name, calls):
    original = vars(carrier_type).get(name, _MISSING)
    if name in ("__getattribute__", "__getattr__"):
        def poisoned(self, field):
            calls.append((name, field))
            raise AssertionError("poisoned carrier hook executed")

        setattr(carrier_type, name, poisoned)
    elif name == "__init__":
        def poisoned(self, *args, **kwargs):
            calls.append((name, len(args)))
            raise AssertionError("poisoned carrier constructor executed")

        setattr(carrier_type, name, poisoned)
    else:
        def poisoned(self):
            calls.append((name, "read"))
            raise AssertionError("poisoned carrier slot executed")

        setattr(carrier_type, name, property(poisoned))

    def restore():
        # __getattribute__ is inherited, not an original class dictionary
        # member. A normal monkeypatch undo would install an own descriptor
        # and poison every later test in the suite.
        if original is _MISSING:
            delattr(carrier_type, name)
        else:
            setattr(carrier_type, name, original)

    return restore


@pytest.mark.parametrize("operation", ("review", "veto"))
@pytest.mark.parametrize(
    "slot", ("count", "fingerprint", "__init__", "__getattribute__", "__getattr__"),
)
def test_retained_witness_poison_rejected_before_any_private_sqlite_read(
    tmp_path, monkeypatch, operation, slot,
):
    ledger, retained = _fixture(tmp_path)
    calls = []
    opened = []

    def forbidden_open(*, read_only):
        opened.append(read_only)
        raise AssertionError("poisoned witness must be rejected before SQLite")

    monkeypatch.setattr(ledger, "_open", forbidden_open)
    restore = _poison(veto.OfflinePrivacyVetoWitness, slot, calls)
    try:
        with pytest.raises(veto.OfflinePrivacyVetoRejected, match="witness carrier changed"):
            _request(ledger, retained, operation=operation)
        assert calls == []
    finally:
        restore()
    assert opened == []


@pytest.mark.parametrize(
    "slot", ("local_veto_seen", "witness", "__init__", "__getattribute__", "__getattr__"),
)
def test_review_result_poison_rejected_before_private_sqlite_read(
    tmp_path, monkeypatch, slot,
):
    ledger, retained = _fixture(tmp_path)
    calls = []
    opened = []

    def forbidden_open(*, read_only):
        opened.append(read_only)
        raise AssertionError("poisoned review must be rejected before SQLite")

    monkeypatch.setattr(ledger, "_open", forbidden_open)
    restore = _poison(veto.OfflinePrivacyVetoReview, slot, calls)
    try:
        with pytest.raises(veto.OfflinePrivacyVetoRejected, match="review acquired authority"):
            _request(ledger, retained, operation="review")
        assert calls == []
    finally:
        restore()
    assert opened == []


@pytest.mark.parametrize(
    "slot",
    (
        "owner_sha256", "scope_sha256", "recorded_at_ms", "witness",
        "__init__", "__getattribute__", "__getattr__",
    ),
)
def test_receipt_poison_rejected_before_any_local_veto_mutation(
    tmp_path, monkeypatch, slot,
):
    ledger, retained = _fixture(tmp_path)
    calls = []
    opened = []

    def forbidden_open(*, read_only):
        opened.append(read_only)
        raise AssertionError("poisoned receipt must be rejected before SQLite")

    monkeypatch.setattr(ledger, "_open", forbidden_open)
    restore = _poison(veto.OfflinePrivacyVetoReceipt, slot, calls)
    try:
        with pytest.raises(veto.OfflinePrivacyVetoRejected, match="receipt authority changed"):
            _request(ledger, retained, operation="veto")
        assert calls == []
    finally:
        restore()
    assert opened == []


def test_original_carriers_still_support_denial_only_restart(tmp_path):
    ledger, retained = _fixture(tmp_path)
    assert not _request(ledger, retained, operation="review").local_veto_seen
    receipt = _request(ledger, retained, operation="veto")
    assert receipt.witness.count == 1
    reopened = veto.DisconnectedPrivacyVetoLedger(
        tmp_path / "privacy-custody.sqlite3",
    )
    report = _request(reopened, receipt.witness, operation="review")
    assert report.local_veto_seen is True
    assert report.consent_verified is False
    assert report.context_release_authorized is False
    assert receipt.deletion_proven is False
