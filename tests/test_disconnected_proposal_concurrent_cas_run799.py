"""Synthetic proposal CAS must serialize competing local SQLite writers.

No proposal outcome authenticates human review or grants execution rights.
This exercises separate SQLite connections, not external services or models.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ark.agency import disconnected_proposal_store as store

_A = "proposal_" + "a" * 64
_B = "proposal_" + "b" * 64


@pytest.mark.parametrize("writers", (2, 3, 4))
@pytest.mark.parametrize("same_proposal", (True, False))
def test_competing_writers_have_one_global_cas_winner(
    tmp_path, writers, same_proposal,
):
    path = tmp_path / "concurrent-proposals.sqlite3"
    retained = store.create_disconnected_proposal_store(path)
    start = Barrier(writers)

    def try_append(index):
        proposal_id = _A if same_proposal or index % 2 == 0 else _B
        start.wait(timeout=20)
        try:
            return store.append_disconnected_proposal_transition(
                path,
                proposal_id=proposal_id,
                new_state="PROPOSED",
                expected_revision=0,
                expected_tip=None,
                retained=retained,
            )
        except store.DisconnectedProposalStoreRejected as exc:
            return exc

    with ThreadPoolExecutor(max_workers=writers) as pool:
        results = tuple(pool.map(try_append, range(writers)))
    winners = tuple(
        result for result in results
        if type(result) is store.DetachedProposalStoreSnapshot
    )
    losers = tuple(
        result for result in results
        if type(result) is store.DisconnectedProposalStoreRejected
    )
    assert len(winners) == 1
    assert len(losers) == writers - 1
    assert winners[0].witness.event_count == 1
    assert winners[0].human_review_authenticated is False
    assert winners[0].execution_authorized is False
    assert winners[0].candidate_promotion_authorized is False

    # Every disconnected reader must observe the same sole committed event,
    # regardless of which proposal ID the competing writer attempted.
    observed_a = store.inspect_disconnected_proposal_store(
        path, proposal_id=_A, retained=retained,
    )
    observed_b = store.inspect_disconnected_proposal_store(
        path, proposal_id=_B, retained=retained,
    )
    assert observed_a.witness == observed_b.witness == winners[0].witness
    assert sum(
        snapshot.proposal_tip is not None
        for snapshot in (observed_a, observed_b)
    ) == 1
    assert observed_a.execution_authorized is False
    assert observed_b.execution_authorized is False
