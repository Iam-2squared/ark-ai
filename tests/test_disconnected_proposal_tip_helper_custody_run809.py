"""Unknown-COMMIT triage must not accept substituted tip projection callbacks."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_proposal_store as store
from ark.agency import disconnected_proposal_unknown_commit_review as triage

_PROPOSAL = "proposal_" + "a" * 64


@pytest.mark.parametrize("replacement", (None, object(), str, lambda value: value))
def test_substituted_tip_image_helper_denied_before_sqlite(
    monkeypatch: pytest.MonkeyPatch, tmp_path, replacement: object,
) -> None:
    # A non-existent path makes any accidental read visible without creating
    # a proposal database, while protocol rejection must happen first.
    path = tmp_path / "must-remain-absent.sqlite3"
    with monkeypatch.context() as patch:
        patch.setattr(triage, "_tip_fields", replacement)
        with pytest.raises(
            triage.OfflineProposalUnknownCommitRejected, match="protocol changed",
        ):
            triage.review_disconnected_proposal_unknown_commit(
                path,
                proposal_id=_PROPOSAL,
                new_state="PROPOSED",
                expected_revision=0,
                expected_tip=None,
                retained_before=store.genesis_disconnected_proposal_witness(),
            )
    assert not path.exists()


def test_normal_unwritten_proposal_still_requires_manual_review(tmp_path) -> None:
    path = tmp_path / "proposal.sqlite3"
    store.create_disconnected_proposal_store(path)
    before = store.inspect_disconnected_proposal_store(path, proposal_id=_PROPOSAL)
    reviewed = triage.review_disconnected_proposal_unknown_commit(
        path,
        proposal_id=_PROPOSAL,
        new_state="PROPOSED",
        expected_revision=0,
        expected_tip=None,
        retained_before=before.witness,
    )
    assert reviewed.disposition == triage.OBSERVED_UNCHANGED
    assert reviewed.automatic_retry_authorized is False
    assert reviewed.code_change_authorized is False
    assert reviewed.training_authorized is False
