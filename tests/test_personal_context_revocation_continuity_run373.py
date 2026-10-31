"""Independently preserved revocation evidence detects later local rewrites."""

import sqlite3
from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_continuity_review import (
    SyntheticRevocationWitness,
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _ledger(tmp_path: Path):
    return SyntheticContextRevocationLedger(tmp_path / "revoked #100 %.sqlite")


def test_empty_history_and_extension_remain_inert(tmp_path: Path):
    store = _ledger(tmp_path)
    genesis = review_revocation_continuity(store)
    assert genesis.rows == ()
    assert genesis.witness_id.startswith("rvk_")
    scope = MemoryScope("owner", "profile")
    store.revoke(scope, at_ms=101)
    one = review_revocation_continuity(store, retained=genesis)
    assert len(one.rows) == 1
    store.revoke(MemoryScope("owner", "notes"), at_ms=102)
    two = review_revocation_continuity(store, retained=one)
    assert len(two.rows) == 2
    assert two != one
    assert review_revocation_continuity(store, retained=genesis) == two


@pytest.mark.parametrize("change", ["delete", "time"])
def test_independently_retained_veto_detects_deletion_or_rewrite(
    tmp_path: Path, change: str,
):
    store = _ledger(tmp_path)
    store.revoke(MemoryScope("owner", "profile"), at_ms=100)
    earlier = review_revocation_continuity(store)
    with sqlite3.connect(store.path) as conn:
        if change == "delete":
            conn.execute("DELETE FROM synthetic_context_revocations")
        else:
            conn.execute(
                "UPDATE synthetic_context_revocations SET revoked_at_ms=101"
            )
    with pytest.raises(SyntheticContextRevocationRejected, match="history changed"):
        review_revocation_continuity(store, retained=earlier)
    # Without independently retained evidence, syntactically valid changed
    # local data is not independently authenticated.
    assert review_revocation_continuity(store) != earlier


def test_mutated_witness_digest_is_rejected(tmp_path: Path):
    store = _ledger(tmp_path)
    witness = review_revocation_continuity(store)
    object.__setattr__(witness, "witness_id", "rvk_" + "f" * 64)
    with pytest.raises(SyntheticContextRevocationRejected, match="digest mismatch"):
        review_revocation_continuity(store, retained=witness)


def test_mutated_witness_rows_rejected_even_with_old_id(tmp_path: Path):
    store = _ledger(tmp_path)
    store.revoke(MemoryScope("owner", "notes"), at_ms=101)
    witness = review_revocation_continuity(store)
    object.__setattr__(witness, "rows", ())
    with pytest.raises(SyntheticContextRevocationRejected, match="digest mismatch"):
        review_revocation_continuity(store, retained=witness)


def test_wrong_type_or_malformed_witness_fails_closed(tmp_path: Path):
    store = _ledger(tmp_path)
    with pytest.raises(SyntheticContextRevocationRejected, match="exact retained"):
        review_revocation_continuity(store, retained=object())
    malformed = SyntheticRevocationWitness(((("X" * 64), 100),), "rvk_" + "a" * 64)
    with pytest.raises(SyntheticContextRevocationRejected, match="order/identity"):
        review_revocation_continuity(store, retained=malformed)


def test_missing_ledger_read_never_creates_empty_replacement(tmp_path: Path):
    store = _ledger(tmp_path)
    store.path.unlink()
    with pytest.raises(sqlite3.OperationalError):
        review_revocation_continuity(store)
    assert not store.path.exists()
