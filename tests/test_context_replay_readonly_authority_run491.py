"""Synthetic context ledger must never mint authority through read-only review."""

from __future__ import annotations

import pytest

from ark import personal_context_replay_ledger as replay


class SpoofedWitness(replay.OfflineContextReplayWitness):
    @property
    def independent_custody_proven(self) -> bool:
        return True


def _spoofed() -> SpoofedWitness:
    genesis = replay.genesis_offline_context_replay_witness()
    return SpoofedWitness(genesis.count, genesis.chain_sha256)


def test_restart_rejects_witness_class_substitution(tmp_path, monkeypatch):
    path = tmp_path / "context.sqlite"
    replay.DisconnectedContextReplayLedger(path, create=True)
    monkeypatch.setattr(replay, "_inspect", lambda _conn: _spoofed())
    with pytest.raises(replay.OfflineContextReplayRejected, match="invalid exact retained"):
        replay.DisconnectedContextReplayLedger(path)


def test_readonly_snapshot_rejects_authority_bearing_result(tmp_path, monkeypatch):
    path = tmp_path / "context.sqlite"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    monkeypatch.setattr(replay, "_inspect", lambda _conn: _spoofed())
    with pytest.raises(replay.OfflineContextReplayRejected, match="invalid exact retained"):
        ledger.witness()


def test_readonly_snapshot_rejects_reflective_authority_property(tmp_path, monkeypatch):
    path = tmp_path / "context.sqlite"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    original = replay._inspect
    old_property = replay.OfflineContextReplayWitness.independent_custody_proven

    def forged(conn):
        witness = original(conn)
        monkeypatch.setattr(
            replay.OfflineContextReplayWitness,
            "independent_custody_proven",
            property(lambda self: True),
        )
        return witness

    monkeypatch.setattr(replay, "_inspect", forged)
    with pytest.raises(replay.OfflineContextReplayRejected, match="invalid exact retained"):
        ledger.witness()
    monkeypatch.setattr(replay, "_inspect", original)
    monkeypatch.setattr(
        replay.OfflineContextReplayWitness, "independent_custody_proven", old_property,
    )
    assert ledger.witness() == replay.genesis_offline_context_replay_witness()
