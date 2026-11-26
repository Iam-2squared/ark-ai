"""Durable Planner WRITE slot restart is pure observation, not permission."""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_write_slot_ledger as slots


def test_existing_write_slot_restart_preserves_persisted_rows(tmp_path):
    path = tmp_path / "slots.sqlite"
    slots.DisconnectedWriteSlotLedger(path, create=True)
    with sqlite3.connect(path) as connection:
        before = tuple(connection.iterdump())

    restarted = slots.DisconnectedWriteSlotLedger(path)
    genesis = slots.genesis_write_slot_witness()
    assert restarted.inspect(retained=genesis) == genesis
    with sqlite3.connect(path) as connection:
        assert tuple(connection.iterdump()) == before
    assert genesis.independently_authenticated is False


def test_existing_write_slot_restart_can_read_under_reserved_writer(
    tmp_path,
):
    path = tmp_path / "slots.sqlite"
    slots.DisconnectedWriteSlotLedger(path, create=True)
    with sqlite3.connect(path, timeout=0.05, isolation_level=None) as writer:
        writer.execute("BEGIN IMMEDIATE")
        try:
            restarted = slots.DisconnectedWriteSlotLedger(path)
            genesis = slots.genesis_write_slot_witness()
            assert restarted.inspect(retained=genesis) == genesis
        finally:
            writer.rollback()
    assert path.exists()


def test_connector_instrumentation_denied_before_callback(tmp_path, monkeypatch):
    path = tmp_path / "slots.sqlite"
    slots.DisconnectedWriteSlotLedger(path, create=True)
    called = []

    def substituted_connect(*args, **kwargs):
        called.append(True)
        raise AssertionError("untrusted connection must not run")

    with monkeypatch.context() as patch:
        patch.setattr(sqlite3, "connect", substituted_connect)
        with pytest.raises(slots.WriteSlotLedgerRejected, match="constructor or authority changed"):
            slots.DisconnectedWriteSlotLedger(path)
    assert called == []
    assert slots.DisconnectedWriteSlotLedger(path).inspect(
        retained=slots.genesis_write_slot_witness(),
    ) == slots.genesis_write_slot_witness()


def test_write_slot_restart_must_not_create_missing_storage(tmp_path):
    path = tmp_path / "missing.sqlite"
    try:
        slots.DisconnectedWriteSlotLedger(path)
    except slots.WriteSlotLedgerRejected as exc:
        assert "missing durable reservation ledger" in str(exc)
    else:
        raise AssertionError("missing write reservations must not be re-created")
    assert not path.exists()
