"""Run968: privacy revocation continuation rejects shortened witness vectors.

Only a new disposable synthetic SQLite ledger is read. This is a privacy veto
fixture, never authentication, consent, erasure proof or a disclosure grant.
"""

from __future__ import annotations

import sqlite3

import pytest

import ark.personal_context_revocation_continuity_review as review
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _fixture(tmp_path):
    path = tmp_path / "synthetic-revocation-vectors.sqlite"
    ledger = SyntheticContextRevocationLedger(path)
    witness = review.review_revocation_continuity(ledger)
    assert witness.rows == ()
    return path, ledger, witness


@pytest.mark.parametrize("vector", (
    "_WITNESS_FIELDS", "_WITNESS_HOOKS",
    "_ORIGINAL_WITNESS_FIELDS", "_ORIGINAL_WITNESS_HOOKS",
))
@pytest.mark.parametrize("retained", (False, True))
def test_shortened_retained_witness_vector_fails_before_private_db_read(
    tmp_path, monkeypatch, vector, retained,
):
    path, ledger, witness = _fixture(tmp_path)
    calls = []

    def poison(*_args, **_kwargs):
        calls.append(True)
        raise AssertionError("unreviewed witness field accessed")

    with monkeypatch.context() as patch:
        patch.setattr(review, vector, ())
        patch.setattr(review.SyntheticRevocationWitness, "witness_id", property(poison))
        with pytest.raises(
            SyntheticContextRevocationRejected,
            match="revocation integrity validator changed",
        ):
            review.review_revocation_continuity(
                ledger, retained=witness if retained else None,
            )

    assert calls == []
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_context_revocations"
        ).fetchone() == (0,)


def test_revocation_history_remains_denial_only_after_valid_restart(tmp_path):
    path, ledger, first = _fixture(tmp_path)
    second = review.review_revocation_continuity(ledger, retained=first)
    assert second.rows == ()
    assert second.witness_id == first.witness_id
    restarted = SyntheticContextRevocationLedger(path, require_existing=True)
    third = review.review_revocation_continuity(restarted, retained=second)
    assert third.rows == ()
    assert third.witness_id == second.witness_id
