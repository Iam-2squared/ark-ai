"""A disconnected privacy veto must not accept transient scope/source drift."""

from pathlib import Path

import pytest

import ark.personal_context_revocation_review as review
from ark.memory.contracts import MemoryScope


def _setup(tmp_path):
    ledger = review.SyntheticContextRevocationLedger(
        tmp_path / "revocations.sqlite",
    )
    scopes = (
        MemoryScope("offline-owner", "private-a"),
        MemoryScope("offline-owner", "private-b"),
    )
    return ledger, scopes


def test_stable_absence_is_not_a_consent_grant(tmp_path):
    ledger, scopes = _setup(tmp_path)
    assert ledger.assert_not_revoked(scopes) is None
    ledger.revoke(scopes[0], at_ms=100)
    with pytest.raises(
        review.SyntheticContextRevocationRejected, match="scope revoked",
    ):
        ledger.assert_not_revoked(scopes)


def test_scope_drift_between_digest_callbacks_cannot_be_restored_later(
    tmp_path, monkeypatch,
):
    ledger, scopes = _setup(tmp_path)
    original = review._scope_digest
    calls = 0

    def change_during_second_digest(scope):
        nonlocal calls
        calls += 1
        if calls == 3:
            object.__setattr__(scopes[0], "namespace", "private-a")
        value = original(scope)
        if calls == 2:
            object.__setattr__(scopes[0], "namespace", "temporary-namespace")
        return value

    monkeypatch.setattr(review, "_scope_digest", change_during_second_digest)
    with pytest.raises(
        review.SyntheticContextRevocationRejected,
        match="scope changed during revocation check",
    ):
        ledger.assert_not_revoked(scopes)
    assert calls == 2


@pytest.mark.parametrize("change", ("scope", "path"))
def test_veto_lookup_callback_cannot_transiently_retarget_scope_or_source(
    tmp_path, monkeypatch, change,
):
    ledger, scopes = _setup(tmp_path)
    original_connect = ledger._connect
    initial_path = ledger.path
    selects = 0

    class _HookedConnection:
        def __init__(self, delegate):
            self.delegate = delegate

        def execute(self, query, *args):
            nonlocal selects
            result = self.delegate.execute(query, *args)
            if query.startswith("SELECT 1 FROM synthetic_context_revocations"):
                selects += 1
                if selects == 1:
                    if change == "scope":
                        object.__setattr__(
                            scopes[0], "namespace", "temporary-namespace",
                        )
                    else:
                        ledger.path = Path(str(initial_path))
                elif selects == 2:
                    if change == "scope":
                        object.__setattr__(scopes[0], "namespace", "private-a")
                    else:
                        ledger.path = initial_path
            return result

        def __getattr__(self, name):
            return getattr(self.delegate, name)

    def hooked_connect(*, readonly):
        return _HookedConnection(original_connect(readonly=readonly))

    monkeypatch.setattr(ledger, "_connect", hooked_connect)
    with pytest.raises(
        review.SyntheticContextRevocationRejected,
        match="scope changed during revocation check|source path changed",
    ):
        ledger.assert_not_revoked(scopes)
    assert selects == 1
