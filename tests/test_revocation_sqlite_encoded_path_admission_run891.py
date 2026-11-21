"""Synthetic revocation SQLite path admission precedes all filesystem access.

No real private data, consent, unrevocation or external account is involved.
"""

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize(
    "filename",
    [
        "private\x00veto.sqlite",
        "x" * 4200 + ".sqlite",
        "あ" * 1500 + ".sqlite",
    ],
)
def test_invalid_path_never_creates_a_database_or_sidecar(tmp_path, filename):
    # Explicitly exercise both character-length and encoded-byte budgets.
    # The first Python string literal evaluates to an actual NUL byte in the pathname.
    candidate = tmp_path / filename
    with pytest.raises(SyntheticContextRevocationRejected, match="path exceeds"):
        SyntheticContextRevocationLedger(candidate)
    assert list(tmp_path.iterdir()) == []


def test_normal_local_veto_lifecycle_remains_available(tmp_path):
    path = tmp_path / "revocations.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    ledger = SyntheticContextRevocationLedger(path)
    digest = ledger.revoke(scope, at_ms=100)
    assert len(digest) == 64
    reopened = SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        reopened.assert_not_revoked((scope,))
    with pytest.raises(SyntheticContextRevocationRejected, match="already revoked"):
        reopened.revoke(scope, at_ms=101)
