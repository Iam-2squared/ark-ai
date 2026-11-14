"""Local privacy veto rejects foreign scope descriptors before evaluating them.

No real personal data or external service is involved; only temporary SQLite.
"""

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize("with_valid_prefix", (False, True))
def test_foreign_scope_getters_are_never_executed(tmp_path, with_valid_prefix):
    touches = []

    class HostileScope:
        @property
        def owner_id(self):
            touches.append("owner_id")
            raise AssertionError("foreign scope getter executed")

        @property
        def namespace(self):
            touches.append("namespace")
            raise AssertionError("foreign scope getter executed")

    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    scopes = (HostileScope(),)
    if with_valid_prefix:
        scopes = (MemoryScope("fixture", "local"), *scopes)
    with pytest.raises(
        SyntheticContextRevocationRejected, match="exact MemoryScope",
    ):
        ledger.assert_not_revoked(scopes)
    assert touches == []


def test_memory_scope_subclass_is_rejected_without_privacy_read(tmp_path):
    class DerivedScope(MemoryScope):
        pass

    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    with pytest.raises(
        SyntheticContextRevocationRejected, match="exact MemoryScope",
    ):
        ledger.assert_not_revoked((DerivedScope("fixture", "local"),))


def test_exact_scope_still_permits_read_only_check_and_veto(tmp_path):
    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    scope = MemoryScope("fixture", "local")
    ledger.assert_not_revoked((scope,))
    ledger.revoke(scope, at_ms=10)
    with pytest.raises(
        SyntheticContextRevocationRejected, match="scope revoked",
    ):
        ledger.assert_not_revoked((scope,))
