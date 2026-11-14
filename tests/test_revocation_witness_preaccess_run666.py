"""Privacy veto history must not call swapped witness slots or constructors.

Only synthetic local revocation markers are involved. No actual erasure,
independent custody, authenticated consent or disclosure is established.
"""

from __future__ import annotations

import pytest

import ark.personal_context_revocation_continuity_review as continuity
from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _case(tmp_path):
    ledger = SyntheticContextRevocationLedger(tmp_path / "privacy-veto.sqlite")
    ledger.revoke(MemoryScope("offline-owner", "notes"), at_ms=101)
    return ledger, continuity.review_revocation_continuity(ledger)


@pytest.mark.parametrize(
    "field",
    continuity._WITNESS_FIELDS
    + tuple(name for name in continuity._WITNESS_HOOKS if name != "__new__"),
)
def test_preinstalled_malicious_witness_field_or_hook_rejected_before_read(
    tmp_path, monkeypatch, field,
):
    ledger, retained = _case(tmp_path)
    executed = []

    def poison(*args, **kwargs):
        executed.append("poison")
        raise AssertionError("untrusted witness code executed")

    def forbidden_read(*args, **kwargs):
        executed.append("database")
        raise AssertionError("read should be refused before SQLite")

    monkeypatch.setattr(ledger, "_connect", forbidden_read)
    if field in continuity._WITNESS_FIELDS:
        monkeypatch.setattr(
            continuity.SyntheticRevocationWitness,
            field, property(poison),
        )
    else:
        monkeypatch.setattr(
            continuity.SyntheticRevocationWitness, field, poison,
            raising=False,
        )
    with pytest.raises(
        SyntheticContextRevocationRejected,
        match="revocation integrity validator changed",
    ):
        continuity.review_revocation_continuity(ledger, retained=retained)
    assert executed == []


def test_hash_callback_cannot_install_late_witness_constructor(
    tmp_path, monkeypatch,
):
    ledger, retained = _case(tmp_path)
    real_hash = continuity._hash
    executed = []

    def forbidden_init(*args, **kwargs):
        executed.append("constructor")
        raise AssertionError("injected witness constructor ran")

    def changed_hash(rows):
        digest = real_hash(rows)
        monkeypatch.setattr(
            continuity.SyntheticRevocationWitness,
            "__init__", forbidden_init,
        )
        return digest

    monkeypatch.setattr(continuity, "_hash", changed_hash)
    # Hash implementation substitutions now fail before reading revocation
    # history or invoking a callback that could replace the constructor.
    with pytest.raises(
        SyntheticContextRevocationRejected,
        match="revocation digest implementation changed",
    ):
        continuity.review_revocation_continuity(ledger, retained=retained)
    assert executed == []


def test_unmodified_revocation_witness_still_preserves_veto(tmp_path):
    ledger, retained = _case(tmp_path)
    scope = MemoryScope("offline-owner", "notes")
    assert continuity.review_revocation_continuity(
        ledger, retained=retained,
    ) == retained
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        ledger.assert_not_revoked((scope,))
