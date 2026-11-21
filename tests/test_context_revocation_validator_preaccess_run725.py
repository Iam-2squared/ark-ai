"""Revocation continuity never passes private SQLite to a replaced validator.

This synthetic denial is not independently authenticated revocation custody,
cross-store privacy atomicity, user consent or an erasure decision.
"""

from __future__ import annotations

import pytest

from ark import personal_context_revocation_continuity_review as continuity
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _ledger(tmp_path):
    return SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")


@pytest.mark.parametrize("retained", (False, True))
def test_preinstalled_hostile_validator_never_receives_private_connection(
    tmp_path, monkeypatch, retained,
):
    ledger = _ledger(tmp_path)
    previous = continuity.review_revocation_continuity(ledger) if retained else None
    calls = []

    def hostile(conn):
        calls.append(conn)
        raise AssertionError("private SQLite connection passed to hostile validator")

    with monkeypatch.context() as patch:
        patch.setattr(continuity, "_validate", hostile)
        with pytest.raises(
            SyntheticContextRevocationRejected,
            match="revocation digest implementation changed",
        ):
            continuity.review_revocation_continuity(ledger, retained=previous)
    assert calls == []
    observed = continuity.review_revocation_continuity(ledger, retained=previous)
    assert observed.rows == ()
    assert observed.witness_id.startswith("rvk_")


def test_reentrant_validator_rebinding_is_denied_before_sqlite_validation(
    tmp_path, monkeypatch,
):
    ledger = _ledger(tmp_path)
    original_source_check = ledger._assert_source_path
    calls = []
    private_connections = []

    def hostile(conn):
        private_connections.append(conn)
        raise AssertionError("hostile schema validator ran")

    with monkeypatch.context() as patch:
        def rebind_during_source_check(expected):
            result = original_source_check(expected)
            calls.append(True)
            if len(calls) == 1:
                patch.setattr(continuity, "_validate", hostile)
            return result

        patch.setattr(ledger, "_assert_source_path", rebind_during_source_check)
        with pytest.raises(
            SyntheticContextRevocationRejected,
            match="revocation digest implementation changed",
        ):
            continuity.review_revocation_continuity(ledger)
    assert calls
    assert private_connections == []
    assert continuity.review_revocation_continuity(ledger).rows == ()
