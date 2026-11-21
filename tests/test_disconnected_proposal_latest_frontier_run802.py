"""Read-only proposal batch can require the retained exact global frontier.

A matched frontier remains unauthenticated local evidence, never a permission
to execute, train, edit source, replay writes, or open a protected evaluation.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_proposal_snapshot_bundle as batch
from ark.agency import disconnected_proposal_store as store

_A = "proposal_" + "a" * 64
_B = "proposal_" + "b" * 64


def _new(tmp_path):
    path = tmp_path / "proposals.sqlite3"
    return path, store.create_disconnected_proposal_store(path)


def _append(path, proposal_id, retained):
    return store.append_disconnected_proposal_transition(
        path,
        proposal_id=proposal_id,
        new_state="PROPOSED",
        expected_revision=0,
        expected_tip=None,
        retained=retained,
    )


def test_genesis_is_exact_frontier_only_when_empty(tmp_path):
    path, genesis = _new(tmp_path)
    observed = batch.inspect_disconnected_proposal_batch(
        path, proposal_ids=(_A,), retained=genesis, require_latest=True,
    )
    assert observed.witness == genesis
    assert observed.tips == (None,)
    assert observed.automatic_retry_authorized is False
    assert observed.code_change_authorized is False


def test_latest_frontier_rejects_older_valid_prefix(tmp_path):
    path, genesis = _new(tmp_path)
    first = _append(path, _A, genesis)
    prefix_only = batch.inspect_disconnected_proposal_batch(
        path, proposal_ids=(_A,), retained=genesis,
    )
    assert prefix_only.witness == first.witness
    with pytest.raises(
        batch.DisconnectedProposalBatchRejected, match="coherent proposal batch",
    ) as caught:
        batch.inspect_disconnected_proposal_batch(
            path, proposal_ids=(_A,), retained=genesis, require_latest=True,
        )
    assert type(caught.value.__cause__) is store.DisconnectedProposalStoreRejected
    assert "stale" in str(caught.value.__cause__)
    verified = batch.inspect_disconnected_proposal_batch(
        path, proposal_ids=(_A,), retained=first.witness, require_latest=True,
    )
    assert verified.witness == first.witness
    assert verified.tips == (first.proposal_tip,)
    assert verified.human_review_authenticated is False
    assert verified.training_authorized is False


def test_unrequested_proposal_append_invalidates_prior_frontier(tmp_path):
    path, genesis = _new(tmp_path)
    first = _append(path, _A, genesis)
    second = _append(path, _B, first.witness)
    with pytest.raises(
        batch.DisconnectedProposalBatchRejected, match="coherent proposal batch",
    ) as caught:
        batch.inspect_disconnected_proposal_batch(
            path, proposal_ids=(_A,), retained=first.witness,
            require_latest=True,
        )
    assert type(caught.value.__cause__) is store.DisconnectedProposalStoreRejected
    assert "stale" in str(caught.value.__cause__)
    observed = batch.inspect_disconnected_proposal_batch(
        path, proposal_ids=(_B, _A), retained=second.witness,
        require_latest=True,
    )
    assert observed.tips == (second.proposal_tip, first.proposal_tip)
    assert observed.witness.event_count == 2
    assert observed.automatic_retry_authorized is False


@pytest.mark.parametrize("invalid", (None, 0, 1, "true", (), []))
def test_nonexact_latest_flag_rejected_before_db_access(tmp_path, invalid):
    missing = tmp_path / "missing.sqlite3"
    with pytest.raises(
        batch.DisconnectedProposalBatchRejected, match="latest-frontier",
    ):
        batch.inspect_disconnected_proposal_batch(
            missing,
            proposal_ids=(_A,),
            retained=store.genesis_disconnected_proposal_witness(),
            require_latest=invalid,
        )
