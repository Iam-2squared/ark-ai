"""Inert preaction IO/path admission, without real execution authority."""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as atomic


def _claim() -> atomic.AtomicIntentClaim:
    return atomic.AtomicIntentClaim(
        "occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64,
    )


@pytest.mark.parametrize("mutation", (
    "module", "connect", "max_path", "bool_path",
))
@pytest.mark.parametrize("operation", ("create", "reopen"))
def test_preaction_refuses_changed_storage_contract_before_sqlite(
    tmp_path, monkeypatch: pytest.MonkeyPatch, mutation: str, operation: str,
) -> None:
    path = tmp_path / "inert-preaction.db"
    if operation == "reopen":
        atomic.DisconnectedAtomicPreactionLedger.create(path)

    calls: list[str] = []

    def forbidden_connect(*args, **kwargs):
        calls.append("called")
        raise AssertionError("hostile SQLite callback ran")

    with monkeypatch.context() as patch:
        if mutation == "module":
            patch.setattr(atomic, "sqlite3", object())
        elif mutation == "connect":
            patch.setattr(sqlite3, "connect", forbidden_connect)
        elif mutation == "max_path":
            patch.setattr(atomic, "_MAX_PATH", 99999)
        else:
            patch.setattr(atomic, "_MAX_PATH", True)

        with pytest.raises(
            atomic.AtomicPreactionRejected, match="codec or schema changed",
        ):
            if operation == "create":
                atomic.DisconnectedAtomicPreactionLedger.create(path)
            else:
                atomic.DisconnectedAtomicPreactionLedger(path)

    assert calls == []
    if operation == "create":
        assert not path.exists()
    else:
        ledger = atomic.DisconnectedAtomicPreactionLedger(path)
        assert ledger.inspect(atomic.genesis_atomic_preaction_witness()).witness.count == 0


@pytest.mark.parametrize("relative", (True, False))
def test_overlong_preaction_path_refused_before_any_stat(tmp_path, relative):
    path = (tmp_path / ("z" * 4100)) if not relative else (
        type(tmp_path)("z" * 4100)
    )
    with pytest.raises(atomic.AtomicPreactionRejected, match="unsafe intent ledger path"):
        atomic.DisconnectedAtomicPreactionLedger.create(path)
    # A negative existence check on an overlong component can itself raise
    # ENAMETOOLONG on POSIX. Check the actual fixture directory instead.
    assert list(tmp_path.iterdir()) == []


def test_valid_preaction_witness_remains_non_authorizing(tmp_path):
    path = tmp_path / "inert-preaction.db"
    ledger = atomic.DisconnectedAtomicPreactionLedger.create(path)
    retained = atomic.genesis_atomic_preaction_witness()
    committed = ledger.reserve(_claim(), retained=retained)
    restarted = atomic.DisconnectedAtomicPreactionLedger(path)
    result = restarted.inspect(committed)
    assert result.occurrence_ids == (_claim().occurrence_id,)
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.trusted_approval_verified is False
