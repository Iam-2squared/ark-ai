"""A registry revision change must not reset durable mock replay guards.

This validates the SQLite fixture's global occurrence/token uniqueness across
different immutable registry fingerprints. The mocked backend is never called.
A synthetic token is NOT proof of permission, approval, or trusted time.
"""

from __future__ import annotations

import hashlib

import pytest
from test_registry_policy_durable_occurrence_restart_run643 import _fixture

from ark.agency.contracts import Effect, OneShotAuthorization
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


@pytest.mark.parametrize(
    "replay", ("token_across_revisions", "occurrence_across_revisions"),
)
def test_changed_registry_revision_cannot_reset_persisted_reservation(
    tmp_path, replay,
):
    original, call, grant, token, ledger, occurrence, path, backend = _fixture(tmp_path)
    bound_before = PermissionGate().authorize_registered(
        original, call, (grant,), now_ms=100, one_shot=token,
    )
    first = ledger.reserve_synthetic(
        original, call, token, occurrence_id=occurrence, now_ms=100,
    )
    assert first.bound_action_id == bound_before.bound_action_id
    assert first.dispatch_authorized is False

    changed = ToolRegistry((
        ToolRegistration(
            "fixture.write", "offline.write", Effect.WRITE, "mock-v2", backend,
        ),
    ))
    assert changed.revision != original.revision
    assert changed.bind(call).bound_action_id != bound_before.bound_action_id
    if replay == "token_across_revisions":
        second_token = token
        second_occurrence = "occ_" + hashlib.sha256(b"new-id").hexdigest()
    else:
        second_token = OneShotAuthorization("new-revision-token", call.request_id, 200)
        second_occurrence = occurrence

    # A new process-local gate may approve the mock value, but it cannot
    # override the reservation already durably recorded for another revision.
    second_bound = PermissionGate().authorize_registered(
        changed, call, (grant,), now_ms=110, one_shot=second_token,
    )
    assert second_bound.registry_revision == changed.revision
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        SyntheticOccurrenceStore(path).reserve_synthetic(
            changed, call, second_token,
            occurrence_id=second_occurrence, now_ms=110,
        )
    assert SyntheticOccurrenceStore(path).count_synthetic() == 1
    assert backend.calls == 0


def test_changed_registry_with_new_token_and_new_occurrence_is_not_an_approval(
    tmp_path,
):
    original, call, grant, token, ledger, occurrence, path, backend = _fixture(tmp_path)
    ledger.reserve_synthetic(
        original, call, token, occurrence_id=occurrence, now_ms=100,
    )
    changed = ToolRegistry((
        ToolRegistration(
            "fixture.write", "offline.write", Effect.WRITE, "mock-v2", backend,
        ),
    ))
    new_token = OneShotAuthorization("different-revision-token", call.request_id, 200)
    new_occurrence = "occ_" + hashlib.sha256(b"fresh-local-occurrence").hexdigest()
    result = SyntheticOccurrenceStore(path).reserve_synthetic(
        changed, call, new_token,
        occurrence_id=new_occurrence, now_ms=110,
    )
    assert SyntheticOccurrenceStore(path).count_synthetic() == 2
    assert result.dispatch_authorized is False
    assert result.outcome_known is False
    assert result.automatic_replay_authorized is False
    assert backend.calls == 0
