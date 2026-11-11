"""Multi-proposal inspection uses one inert SQLite read transaction."""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_proposal_snapshot_bundle as batch
from ark.agency import disconnected_proposal_store as store


_A = "proposal_" + "a" * 64
_B = "proposal_" + "b" * 64
_C = "proposal_" + "c" * 64


def _new(tmp_path):
    path = tmp_path / "proposals.sqlite3"
    genesis = store.create_disconnected_proposal_store(path)
    return path, genesis


def _append(path, proposal_id, retained):
    old = store.inspect_disconnected_proposal_store(
        path, proposal_id=proposal_id, retained=retained,
    )
    return store.append_disconnected_proposal_transition(
        path, proposal_id=proposal_id, new_state="PROPOSED",
        expected_revision=0,
        expected_tip=None,
        retained=old.witness,
    )


def test_ordered_tips_share_one_latest_global_witness(tmp_path):
    path, genesis = _new(tmp_path)
    first = _append(path, _A, genesis)
    second = _append(path, _B, first.witness)
    result = batch.inspect_disconnected_proposal_batch(
        path, proposal_ids=(_B, _C, _A), retained=genesis,
    )
    assert result.proposal_ids == (_B, _C, _A)
    assert result.witness == second.witness
    assert result.witness.event_count == 2
    assert result.tips[0].proposal_id == _B
    assert result.tips[0].revision == 1
    assert result.tips[1] is None
    assert result.tips[2].proposal_id == _A
    assert result.tips[2].revision == 1
    assert result.human_review_authenticated is False
    assert result.code_change_authorized is False
    assert result.training_authorized is False
    assert result.automatic_retry_authorized is False


def test_retained_latest_and_genesis_both_check_same_epoch(tmp_path):
    path, genesis = _new(tmp_path)
    first = _append(path, _A, genesis)
    for retained in (genesis, first.witness):
        result = batch.inspect_disconnected_proposal_batch(
            path, proposal_ids=(_A,), retained=retained,
        )
        assert result.witness == first.witness
        assert result.tips[0].state == "PROPOSED"


def test_retained_later_prefix_detects_deleted_event(tmp_path):
    path, genesis = _new(tmp_path)
    first = _append(path, _A, genesis)
    second = _append(path, _B, first.witness)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_proposal_events WHERE seq=2")
    with pytest.raises(batch.DisconnectedProposalBatchRejected):
        batch.inspect_disconnected_proposal_batch(
            path, proposal_ids=(_A, _B), retained=second.witness,
        )


@pytest.mark.parametrize("ids", (
    (), (_A, _A), (_A, 1), (_A, True), (_A, _B) * 17,
))
def test_nonexact_or_duplicate_ids_refused_before_path_read(tmp_path, ids):
    missing = tmp_path / "missing.sqlite3"
    with pytest.raises(
        batch.DisconnectedProposalBatchRejected, match="proposal IDs",
    ):
        batch.inspect_disconnected_proposal_batch(
            missing, proposal_ids=ids,
            retained=store.genesis_disconnected_proposal_witness(),
        )


@pytest.mark.parametrize("name", (
    "human_review_authenticated", "code_change_authorized",
    "training_authorized", "automatic_retry_authorized",
))
def test_rebound_report_authority_rejected_before_sqlite(
    tmp_path, monkeypatch, name,
):
    path, genesis = _new(tmp_path)
    invoked = []

    def forged(self):
        invoked.append(name)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(batch.DetachedProposalBatchSnapshot, name, property(forged))
        with pytest.raises(
            batch.DisconnectedProposalBatchRejected, match="protocol changed",
        ):
            batch.inspect_disconnected_proposal_batch(
                path, proposal_ids=(_A,), retained=genesis,
            )
    assert invoked == []
    assert store.inspect_disconnected_proposal_store(
        path, proposal_id=_A,
    ).witness == genesis


def test_substituted_store_scan_rejected_without_execution(
    tmp_path, monkeypatch,
):
    path, genesis = _new(tmp_path)
    invoked = []

    def injected(conn):
        invoked.append(conn)
        raise RuntimeError("must not touch private SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_scan", injected)
        with pytest.raises(
            batch.DisconnectedProposalBatchRejected, match="protocol changed",
        ):
            batch.inspect_disconnected_proposal_batch(
                path, proposal_ids=(_A,), retained=genesis,
            )
    assert invoked == []
