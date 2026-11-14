"""Offline local synthetic CAS event history: no human authority or effects."""

from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

from ark.agency import disconnected_proposal_store as store

_A = "proposal_" + "a" * 64
_B = "proposal_" + "b" * 64


def _new(tmp_path):
    path = tmp_path / "proposals.sqlite3"
    genesis = store.create_disconnected_proposal_store(path)
    return path, genesis


def _append(path, proposal, state, prior):
    return store.append_disconnected_proposal_transition(
        path, proposal_id=proposal, new_state=state,
        expected_revision=0 if prior.proposal_tip is None else prior.proposal_tip.revision,
        expected_tip=prior.proposal_tip, retained=prior.witness,
    )


def test_restart_and_exact_cas_sequence_is_inert(tmp_path):
    path, genesis = _new(tmp_path)
    empty = store.inspect_disconnected_proposal_store(path, proposal_id=_A, retained=genesis)
    assert empty.witness == genesis and empty.proposal_tip is None
    first = _append(path, _A, "PROPOSED", empty)
    second = _append(path, _A, "REVIEW_REQUIRED", first)
    third = _append(path, _A, "ACCEPTED_FOR_IMPLEMENTATION", second)
    observed = store.inspect_disconnected_proposal_store(
        path, proposal_id=_A, retained=first.witness,
    )
    assert observed == third
    assert third.proposal_tip.revision == 3
    assert third.proposal_tip.human_review_authenticated is False
    assert third.proposal_tip.training_authorized is False
    assert third.proposal_tip.candidate_promotion_authorized is False
    assert third.execution_authorized is False
    assert third.human_review_authenticated is False
    assert third.candidate_promotion_authorized is False
    assert third.witness.externally_authenticated is False


def test_cross_proposal_global_cas_is_required(tmp_path):
    path, genesis = _new(tmp_path)
    initial_a = store.inspect_disconnected_proposal_store(path, proposal_id=_A)
    initial_b = store.inspect_disconnected_proposal_store(path, proposal_id=_B)
    assert initial_a.witness == initial_b.witness == genesis
    next_a = _append(path, _A, "PROPOSED", initial_a)
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="stale"):
        _append(path, _B, "PROPOSED", initial_b)
    next_b = _append(path, _B, "PROPOSED", store.inspect_disconnected_proposal_store(
        path, proposal_id=_B, retained=next_a.witness,
    ))
    assert next_b.witness.event_count == 2
    assert store.inspect_disconnected_proposal_store(
        path, proposal_id=_A,
    ).proposal_tip == next_a.proposal_tip


def test_duplicate_uncertain_postcommit_retry_denied(tmp_path):
    path, _ = _new(tmp_path)
    original = store.inspect_disconnected_proposal_store(path, proposal_id=_A)
    _append(path, _A, "PROPOSED", original)  # Caller loses returned receipt.
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="stale"):
        _append(path, _A, "PROPOSED", original)
    assert store.inspect_disconnected_proposal_store(path, proposal_id=_A).witness.event_count == 1


def test_stale_revision_and_forged_tip_denied(tmp_path):
    path, _ = _new(tmp_path)
    empty = store.inspect_disconnected_proposal_store(path, proposal_id=_A)
    first = _append(path, _A, "PROPOSED", empty)
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="revision conflict"):
        store.append_disconnected_proposal_transition(
            path, proposal_id=_A, new_state="REVIEW_REQUIRED", expected_revision=0,
            expected_tip=None, retained=first.witness,
        )
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="revision conflict"):
        store.append_disconnected_proposal_transition(
            path, proposal_id=_A, new_state="REVIEW_REQUIRED", expected_revision=1,
            expected_tip=replace(first.proposal_tip, event_digest="f" * 64),
            retained=first.witness,
        )


def test_retained_prefix_detects_deleted_latest_event(tmp_path):
    path, genesis = _new(tmp_path)
    empty = store.inspect_disconnected_proposal_store(path, proposal_id=_A)
    first = _append(path, _A, "PROPOSED", empty)
    second = _append(path, _A, "REVIEW_REQUIRED", first)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_proposal_events WHERE seq=2")
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="prefix mismatch"):
        store.inspect_disconnected_proposal_store(
            path, proposal_id=_A, retained=second.witness,
        )
    assert store.inspect_disconnected_proposal_store(
        path, proposal_id=_A, retained=genesis,
    ).witness == first.witness  # Old witness alone cannot prove no rollback.


def test_column_edit_and_sequence_hole_fail_closed(tmp_path):
    path, _ = _new(tmp_path)
    initial = store.inspect_disconnected_proposal_store(path, proposal_id=_A)
    first = _append(path, _A, "PROPOSED", initial)
    _append(path, _B, "PROPOSED", store.inspect_disconnected_proposal_store(
        path, proposal_id=_B, retained=first.witness,
    ))
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE synthetic_proposal_events SET event_digest=? WHERE seq=1", (
            "f" * 64,
        ))
    with pytest.raises(store.DisconnectedProposalStoreRejected):
        store.inspect_disconnected_proposal_store(path, proposal_id=_A)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_proposal_events WHERE seq=1")
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="sequence"):
        store.inspect_disconnected_proposal_store(path, proposal_id=_B)


def test_illegal_terminal_reopen_cannot_write(tmp_path):
    path, _ = _new(tmp_path)
    empty = store.inspect_disconnected_proposal_store(path, proposal_id=_A)
    proposed = _append(path, _A, "PROPOSED", empty)
    rejected = _append(path, _A, "REJECTED", proposed)
    with pytest.raises(ValueError):
        _append(path, _A, "PROPOSED", rejected)
    assert store.inspect_disconnected_proposal_store(path, proposal_id=_A) == rejected


@pytest.mark.parametrize("bad", (True, 1.0, "1", -1, 257))
def test_nonexact_expected_revision_rejected_before_io(tmp_path, bad):
    missing = tmp_path / "missing.sqlite3"
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="revision"):
        store.append_disconnected_proposal_transition(
            missing, proposal_id=_A, new_state="PROPOSED", expected_revision=bad,
            expected_tip=None, retained=store.genesis_disconnected_proposal_witness(),
        )


def test_changed_global_witness_rejected(tmp_path):
    path, genesis = _new(tmp_path)
    for forged in (
        replace(genesis, event_count=True),
        replace(genesis, event_count=-1),
        replace(genesis, chain_digest="F" * 64),
        replace(genesis, chain_digest="f" * 64),
    ):
        with pytest.raises(store.DisconnectedProposalStoreRejected):
            store.append_disconnected_proposal_transition(
                path, proposal_id=_A, new_state="PROPOSED", expected_revision=0,
                expected_tip=None, retained=forged,
            )


def test_new_store_never_overwrites_existing(tmp_path):
    path, _ = _new(tmp_path)
    with pytest.raises(store.DisconnectedProposalStoreRejected):
        store.create_disconnected_proposal_store(path)


def test_symlink_and_hardlink_refused(tmp_path):
    path, _ = _new(tmp_path)
    hardlink = tmp_path / "hardlink.sqlite3"
    hardlink.hardlink_to(path)
    with pytest.raises(store.DisconnectedProposalStoreRejected):
        store.inspect_disconnected_proposal_store(path, proposal_id=_A)
    hardlink.unlink()
    link = tmp_path / "symlink.sqlite3"
    link.symlink_to(path)
    with pytest.raises(store.DisconnectedProposalStoreRejected):
        store.inspect_disconnected_proposal_store(link, proposal_id=_A)


def test_schema_mismatch_fail_closed(tmp_path):
    path, _ = _new(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE attacker (x TEXT)")
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="schema changed"):
        store.inspect_disconnected_proposal_store(path, proposal_id=_A)


def test_only_content_free_metadata_is_persisted(tmp_path):
    path, _ = _new(tmp_path)
    initial = store.inspect_disconnected_proposal_store(path, proposal_id=_A)
    _append(path, _A, "PROPOSED", initial)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT * FROM synthetic_proposal_events").fetchall()
    assert len(rows) == 1 and len(rows[0]) == 8
    assert rows[0][1] == _A
    assert rows[0][4] == "PROPOSED"
    assert all(type(value) in (str, int) for value in rows[0])
