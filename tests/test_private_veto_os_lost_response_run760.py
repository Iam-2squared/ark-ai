"""Privacy veto survives an OS exit after an unacknowledged SQLite COMMIT.

The independent revocation ledger stores only a scope digest. A lost receipt
cannot turn a persisted veto into consent, disclosure or deletion authority.
"""

from __future__ import annotations

import os
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _revoke_then_exit(path: str) -> None:
    scope = MemoryScope("synthetic-secret-owner", "private")
    ledger = SyntheticContextRevocationLedger(Path(path))
    ledger.revoke(scope, at_ms=120)
    os._exit(0)  # No result is delivered after COMMIT.


@pytest.mark.parametrize(
    "unrelated", (
        MemoryScope("other-owner", "private"),
        MemoryScope("synthetic-secret-owner", "tasks"),
    ),
)
def test_cold_privacy_veto_survives_lost_commit_response(
    tmp_path: Path, unrelated,
):
    path = tmp_path / "synthetic-context-veto.sqlite3"
    SyntheticContextRevocationLedger(path)
    child = get_context("spawn").Process(
        target=_revoke_then_exit, args=(str(path),),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0

    scope = MemoryScope("synthetic-secret-owner", "private")
    cold = SyntheticContextRevocationLedger(path)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        cold.assert_not_revoked((scope,))
    # Repeating an unacknowledged revocation is not idempotent consent.
    with pytest.raises(SyntheticContextRevocationRejected, match="already revoked"):
        cold.revoke(scope, at_ms=121)
    cold.assert_not_revoked((unrelated,))
    assert b"synthetic-secret-owner" not in path.read_bytes()
    assert b"other-owner" not in path.read_bytes()
