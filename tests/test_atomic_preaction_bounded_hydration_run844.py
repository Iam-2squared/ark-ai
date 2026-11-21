"""Bound retained atomic-preaction identities before hydrating private rows."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ark.agency.disconnected_atomic_preaction_ledger as atomic
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim() -> AtomicIntentClaim:
    return AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64)


@pytest.mark.parametrize(
    ("column", "table"),
    [
        ("occurrence_id", "intents"),
        ("bound_action_id", "intents"),
        ("request_sha256", "intents"),
        ("chain_sha256", "intents"),
        ("occurrence_id", "preaction_audit"),
        ("audit_sha256", "preaction_audit"),
    ],
)
@pytest.mark.parametrize("bad_kind", ["oversized-text", "blob"])
def test_persisted_malformed_identity_refused_before_receipt(
    tmp_path: Path, column: str, table: str, bad_kind: str,
) -> None:
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    prior = genesis_atomic_preaction_witness()
    current = store.reserve(_claim(), retained=prior)
    bad = "f" * 65536 if bad_kind == "oversized-text" else sqlite3.Binary(b"x" * 32)
    with sqlite3.connect(path) as conn:
        conn.execute(f"UPDATE {table} SET {column}=?", (bad,))
    with pytest.raises(AtomicPreactionRejected):
        store.inspect(current)
    with sqlite3.connect(path) as conn:
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone() == (1,)
    assert not hasattr(store, "execute")


@pytest.mark.parametrize(
    "bad_claim",
    [
        AtomicIntentClaim("occ_" + "a" * 65536, "bound_" + "b" * 64, "c" * 64),
        AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 65536, "c" * 64),
        AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 65536),
    ],
)
def test_overlong_request_rejected_without_ledger_mutation(
    tmp_path: Path, bad_claim: AtomicIntentClaim,
) -> None:
    path = tmp_path / "atomic.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    prior = genesis_atomic_preaction_witness()
    with pytest.raises(AtomicPreactionRejected):
        ledger.reserve(bad_claim, retained=prior)
    assert ledger.inspect(prior).occurrence_ids == ()


def test_replaced_digest_pattern_rejected_before_match_or_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ExecutablePattern:
        def fullmatch(self, value: object) -> None:
            raise AssertionError("an untrusted pattern executed")

    path = tmp_path / "atomic.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    prior = genesis_atomic_preaction_witness()
    with monkeypatch.context() as guarded:
        guarded.setattr(atomic, "_SHA", ExecutablePattern())
        with pytest.raises(AtomicPreactionRejected):
            ledger.reserve(_claim(), retained=prior)
    assert ledger.inspect(prior).occurrence_ids == ()
