"""Direct privacy veto operations must retain exact scope field objects."""

from pathlib import Path

import pytest

import ark.personal_context_revocation_review as privacy
from ark.memory.contracts import MemoryScope


def _clone(value: str) -> str:
    replacement = (" " + value)[1:]
    assert replacement == value and replacement is not value
    return replacement


def _invoke(ledger, scope, operation):
    if operation == "revoke":
        return ledger.revoke(scope, at_ms=100)
    return ledger.assert_not_revoked((scope,))


@pytest.mark.parametrize("operation", ("revoke", "check"))
@pytest.mark.parametrize("field", ("owner_id", "namespace"))
def test_initial_scope_digest_callback_cannot_swap_equal_field_carrier(
    tmp_path: Path, monkeypatch, operation, field,
):
    ledger = privacy.SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    scope = MemoryScope("offline-owner", "private")
    original = privacy._scope_digest

    def digest_and_swap(value):
        digest = original(value)
        if value is scope:
            object.__setattr__(scope, field, _clone(getattr(scope, field)))
        return digest

    with monkeypatch.context() as patch:
        patch.setattr(privacy, "_scope_digest", digest_and_swap)
        with pytest.raises(
            privacy.SyntheticContextRevocationRejected, match="scope changed",
        ):
            _invoke(ledger, scope, operation)

    # No veto row was committed, no private content was projected.
    ledger.assert_not_revoked((MemoryScope("offline-owner", "private"),))


@pytest.mark.parametrize("operation", ("revoke", "check"))
@pytest.mark.parametrize("field", ("owner_id", "namespace"))
def test_schema_validation_callback_cannot_swap_equal_field_carrier(
    tmp_path: Path, monkeypatch, operation, field,
):
    ledger = privacy.SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    scope = MemoryScope("offline-owner", "private")
    original = privacy._validate

    def validate_and_swap(connection):
        original(connection)
        object.__setattr__(scope, field, _clone(getattr(scope, field)))

    with monkeypatch.context() as patch:
        patch.setattr(privacy, "_validate", validate_and_swap)
        with pytest.raises(
            privacy.SyntheticContextRevocationRejected, match="scope changed",
        ):
            _invoke(ledger, scope, operation)

    ledger.assert_not_revoked((MemoryScope("offline-owner", "private"),))
