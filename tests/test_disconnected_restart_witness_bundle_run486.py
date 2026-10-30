"""Restart fixture: three independently committed SQLite tips, no authority."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

import ark.disconnected_restart_witness_bundle as bundle
from ark.agency.disconnected_due_reservation import DisconnectedDueReservations
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview
from ark.memory.disconnected_witness_ledger import DisconnectedMemoryWitnessLedger
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayWitness,
)


def _setup(tmp_path):
    memory_path = tmp_path / "memory_witness.sqlite"
    context_path = tmp_path / "context_replay.sqlite"
    due_path = tmp_path / "due_reservations.sqlite"
    memory = DisconnectedMemoryWitnessLedger(memory_path, create=True)
    context = DisconnectedContextReplayLedger(context_path, create=True)
    due = DisconnectedDueReservations(due_path)
    # The actual genesis tips are read from each new local store. They are
    # retained by this test caller, never treated as authenticated custody.
    from ark.memory.disconnected_witness_ledger import genesis_memory_ledger_witness

    retained = (
        genesis_memory_ledger_witness(), context.witness(), due.witness(),
    )
    return (memory, context, due), retained


def _review(stores, witnesses):
    memory, context, due = stores
    wm, wc, wd = witnesses
    return bundle.review_disconnected_restart_witnesses(
        memory, wm, context, wc, due, wd,
    )


def test_clean_genesis_restart_is_consistent_but_not_authorized(tmp_path):
    stores, witnesses = _setup(tmp_path)
    result = _review(stores, witnesses)
    assert (result.memory_epochs, result.context_requests, result.due_occurrences) == (
        0, 0, 0,
    )
    assert len(result.fingerprint) == 64
    assert result.cross_store_atomicity_proven is False
    assert result.independent_custody_proven is False
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.personal_context_use_authorized is False
    assert result.trusted_clock_verified is False


def test_repeat_read_does_not_append_or_change_fingerprint(tmp_path):
    stores, witnesses = _setup(tmp_path)
    first = _review(stores, witnesses)
    assert first == _review(stores, witnesses)
    assert stores[0].inspect(retained=witnesses[0]) == witnesses[0]
    assert stores[1].witness() == witnesses[1]
    assert stores[2].witness() == witnesses[2]


def test_verified_restart_against_same_persisted_files(tmp_path):
    stores, witnesses = _setup(tmp_path)
    restarted = (
        DisconnectedMemoryWitnessLedger(tmp_path / "memory_witness.sqlite"),
        DisconnectedContextReplayLedger(tmp_path / "context_replay.sqlite"),
        DisconnectedDueReservations(tmp_path / "due_reservations.sqlite"),
    )
    assert _review(stores, witnesses) == _review(restarted, witnesses)


def test_appended_memory_observation_requires_new_retained_witness(tmp_path):
    stores, witnesses = _setup(tmp_path)
    epoch = AtomicMemoryEpochReview(
        ("a" * 64,), (1,), (1,), (1,), "b" * 64, "c" * 64,
    )
    changed = stores[0].append(epoch, retained=witnesses[0])
    with pytest.raises(Exception):
        _review(stores, witnesses)
    assert _review(stores, (changed, witnesses[1], witnesses[2])).memory_epochs == 1


def test_due_reservation_advancement_blocks_stale_restart(tmp_path):
    stores, witnesses = _setup(tmp_path)
    changed = stores[2].reserve_due(
        policy_sha256="a" * 64, due_at_ms=100,
        observed_now_ms=101, retained=witnesses[2],
    ).witness
    with pytest.raises(bundle.OfflineRestartWitnessRejected, match="tip differs"):
        _review(stores, witnesses)
    assert _review(stores, (witnesses[0], witnesses[1], changed)).due_occurrences == 1


@pytest.mark.parametrize("index", [0, 1, 2])
def test_invalid_retained_digest_rejected(tmp_path, index):
    stores, retained = _setup(tmp_path)
    current = list(retained)
    field = ("chain_sha256", "chain_sha256", "fingerprint")[index]
    current[index] = replace(current[index], **{field: "x" * 64})
    with pytest.raises(bundle.OfflineRestartWitnessRejected):
        _review(stores, tuple(current))


@pytest.mark.parametrize("index", [0, 1, 2])
def test_boolean_retained_count_rejected(tmp_path, index):
    stores, retained = _setup(tmp_path)
    current = list(retained)
    field = "epochs" if index == 0 else "count"
    current[index] = replace(current[index], **{field: True})
    with pytest.raises(bundle.OfflineRestartWitnessRejected):
        _review(stores, tuple(current))


def test_wrong_exact_retained_type_rejected(tmp_path):
    stores, retained = _setup(tmp_path)
    wrong = OfflineContextReplayWitness(0, retained[0].chain_sha256)
    with pytest.raises(bundle.OfflineRestartWitnessRejected, match="type"):
        _review(stores, (wrong, retained[1], retained[2]))


def test_reentrant_context_read_cannot_retarget_due_retained_tip(tmp_path, monkeypatch):
    stores, retained = _setup(tmp_path)
    original = stores[1].witness

    def tamper():
        current = original()
        object.__setattr__(retained[2], "fingerprint", "f" * 64)
        return current

    monkeypatch.setattr(stores[1], "witness", tamper)
    with pytest.raises(bundle.OfflineRestartWitnessRejected):
        _review(stores, retained)


def test_store_path_replacement_during_read_is_detected(tmp_path, monkeypatch):
    stores, retained = _setup(tmp_path)
    original = stores[1].witness

    def tamper():
        result = original()
        stores[2]._path = Path(str(stores[2]._path))
        return result

    monkeypatch.setattr(stores[1], "witness", tamper)
    with pytest.raises(bundle.OfflineRestartWitnessRejected, match="identity changed"):
        _review(stores, retained)


def test_injected_startup_report_cannot_grant_dispatch(tmp_path, monkeypatch):
    stores, retained = _setup(tmp_path)
    monkeypatch.setattr(bundle, "OfflineRestartWitnessReport", lambda *a: object())
    with pytest.raises(bundle.OfflineRestartWitnessRejected, match="report authority"):
        _review(stores, retained)


def test_same_count_due_witness_rewrite_denied(tmp_path):
    stores, retained = _setup(tmp_path)
    forged = replace(retained[2], fingerprint="f" * 64)
    with pytest.raises(bundle.OfflineRestartWitnessRejected, match="tip differs"):
        _review(stores, (retained[0], retained[1], forged))


def test_same_count_context_witness_rewrite_denied(tmp_path):
    stores, retained = _setup(tmp_path)
    forged = replace(retained[1], chain_sha256="f" * 64)
    with pytest.raises(bundle.OfflineRestartWitnessRejected, match="tip differs"):
        _review(stores, (retained[0], forged, retained[2]))
