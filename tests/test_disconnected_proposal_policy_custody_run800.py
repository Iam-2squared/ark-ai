"""Synthetic proposal transition grammar cannot be expanded at runtime.

The local rule table is a disconnected state machine, not human authorization.
"""

from __future__ import annotations

import re

import pytest

from ark.agency import disconnected_proposal_lifecycle as lifecycle
from ark.agency import disconnected_proposal_store as store

_ID = "proposal_" + "a" * 64


@pytest.mark.parametrize(("state", "replacement"), (
    ("REJECTED", frozenset(("PROPOSED",))),
    ("PROPOSED", frozenset(("ACCEPTED_FOR_IMPLEMENTATION",))),
    ("NEW_STATE", frozenset(("PROPOSED",))),
))
def test_policy_cannot_be_modified_in_place(state, replacement):
    with pytest.raises(TypeError):
        lifecycle._ALLOWED[state] = replacement
    assert lifecycle._ALLOWED["REJECTED"] == frozenset()
    assert "NEW_STATE" not in lifecycle._ALLOWED


@pytest.mark.parametrize(("name", "forged"), (
    ("_MAX_EVENTS", 257),
    ("_MAX_EVENTS", 256.0),
    ("_GENESIS", "f" * 64),
    ("_PROPOSAL_ID", re.compile(r".*")),
    ("_DIGEST", re.compile(r".*")),
))
def test_rebound_core_lifecycle_contract_refused_before_event(
    monkeypatch, name, forged,
):
    with monkeypatch.context() as patch:
        patch.setattr(lifecycle, name, forged)
        with pytest.raises(
            lifecycle.DisconnectedProposalLifecycleRejected,
            match="protocol changed",
        ):
            lifecycle.prepare_disconnected_proposal_transition(
                _ID, None, "PROPOSED",
            )


def test_rebound_policy_cannot_synthesize_terminal_reopen(
    tmp_path, monkeypatch,
):
    path = tmp_path / "synthetic-proposals.sqlite3"
    genesis = store.create_disconnected_proposal_store(path)
    first = store.append_disconnected_proposal_transition(
        path, proposal_id=_ID, new_state="PROPOSED",
        expected_revision=0, expected_tip=None, retained=genesis,
    )
    rejected = store.append_disconnected_proposal_transition(
        path, proposal_id=_ID, new_state="REJECTED",
        expected_revision=1, expected_tip=first.proposal_tip,
        retained=first.witness,
    )
    with monkeypatch.context() as patch:
        patch.setattr(lifecycle, "_ALLOWED", {
            "NONE": frozenset(("PROPOSED",)),
            "PROPOSED": frozenset(("REJECTED",)),
            "REJECTED": frozenset(("PROPOSED",)),
        })
        with pytest.raises(
            lifecycle.DisconnectedProposalLifecycleRejected,
            match="protocol changed",
        ):
            lifecycle.prepare_disconnected_proposal_transition(
                _ID, rejected.proposal_tip, "PROPOSED",
            )
    observed = store.inspect_disconnected_proposal_store(
        path, proposal_id=_ID, retained=rejected.witness,
    )
    assert observed == rejected
    assert observed.proposal_tip.state == "REJECTED"
    assert observed.proposal_tip.human_review_authenticated is False
    assert observed.execution_authorized is False


def test_immutable_policy_retains_normal_inert_lifecycle():
    first = lifecycle.prepare_disconnected_proposal_transition(
        _ID, None, "PROPOSED",
    )
    tip = lifecycle.replay_disconnected_proposal_lifecycle(_ID, (first,))
    second = lifecycle.prepare_disconnected_proposal_transition(
        _ID, tip, "REVIEW_REQUIRED",
    )
    final = lifecycle.replay_disconnected_proposal_lifecycle(
        _ID, (first, second),
    )
    assert final.revision == 2
    assert final.state == "REVIEW_REQUIRED"
    assert final.human_review_authenticated is False
    assert final.code_change_authorized is False
    assert final.training_authorized is False
    assert final.candidate_promotion_authorized is False
