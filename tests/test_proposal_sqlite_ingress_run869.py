"""SQLite proposal path/row admission before hydrating untrusted persisted metadata.

All fixtures are synthetic and disconnected: no approval, model changes, or tool dispatch.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_proposal_store as store

_PROPOSAL = "proposal_" + "a" * 64


def _seed(tmp_path):
    path = tmp_path / "proposals.sqlite3"
    genesis = store.create_disconnected_proposal_store(path)
    first = store.append_disconnected_proposal_transition(
        path, proposal_id=_PROPOSAL, new_state="PROPOSED",
        expected_revision=0, expected_tip=None, retained=genesis,
    )
    return path, first


@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("proposal_id", "proposal_" + "é" * 64),
        ("proposal_id", sqlite3.Binary(b"proposal_" + b"a" * 64)),
        ("revision", "not-an-integer"),
        ("prior_state", "é" * 32),
        ("new_state", sqlite3.Binary(b"PROPOSED")),
        ("previous_digest", "é" * 64),
        ("event_digest", sqlite3.Binary(b"a" * 64)),
        ("global_digest", "é" * 64),
    ),
)
def test_invalid_row_rejected_before_python_hydration(tmp_path, column, replacement):
    path, prior = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            f"UPDATE synthetic_proposal_events SET {column}=? WHERE seq=1",
            (replacement,),
        ).rowcount == 1

    with pytest.raises(
        store.DisconnectedProposalStoreRejected, match="hydration admission"
    ):
        store.inspect_disconnected_proposal_store(path, proposal_id=_PROPOSAL)
    with pytest.raises(store.DisconnectedProposalStoreRejected):
        store.append_disconnected_proposal_transition(
            path, proposal_id=_PROPOSAL, new_state="REVIEW_REQUIRED",
            expected_revision=1, expected_tip=prior.proposal_tip, retained=prior.witness,
        )
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_proposal_events").fetchone() == (1,)


def test_oversized_proposal_history_denied_before_replay(tmp_path):
    path, _ = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.executemany(
            "INSERT INTO synthetic_proposal_events VALUES (?,?,?,?,?,?,?,?)",
            (
                (i, "proposal_" + format(i, "064x"), 1, "NONE",
                 "PROPOSED", "0" * 64, "0" * 64, "0" * 64)
                for i in range(2, 514)
            ),
        )
    with pytest.raises(
        store.DisconnectedProposalStoreRejected, match="row budget"
    ):
        store.inspect_disconnected_proposal_store(path, proposal_id=_PROPOSAL)


@pytest.mark.parametrize("bad_name", ("nul\x00path.sqlite3", "é" * 2100))
def test_invalid_native_sqlite_path_rejected_before_file_access(tmp_path, bad_name):
    path = tmp_path / bad_name
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="path"):
        store.create_disconnected_proposal_store(path)
    # Avoid stat() on an intentionally ENAMETOOLONG or NUL-containing name.
    assert list(tmp_path.iterdir()) == []


def test_clean_proposal_history_retains_restart_cas_and_denial_only(tmp_path):
    path, previous = _seed(tmp_path)
    restored = store.inspect_disconnected_proposal_store(
        path, proposal_id=_PROPOSAL, retained=previous.witness,
    )
    assert restored == previous
    next_state = store.append_disconnected_proposal_transition(
        path, proposal_id=_PROPOSAL, new_state="REVIEW_REQUIRED",
        expected_revision=previous.proposal_tip.revision,
        expected_tip=previous.proposal_tip, retained=restored.witness,
    )
    assert next_state.witness.event_count == 2
    assert next_state.execution_authorized is False
    assert next_state.human_review_authenticated is False
    assert next_state.candidate_promotion_authorized is False
