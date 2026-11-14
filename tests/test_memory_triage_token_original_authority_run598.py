"""Uncertain Memory writes cannot gain authority from retained token getters.

All operations use fixture SQLite. A surviving row or matching update never
authorizes retry, asserts caller identity, or proves user consent.
"""

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import postcommit_uncertainty_review as triage
from ark.memory.generation_fenced_cas import MemoryGenerationCASToken


@pytest.mark.parametrize(
    "name", ("external_action_authorized", "consent_authenticated"),
)
@pytest.mark.parametrize("value", (False, True))
def test_preinstalled_token_authority_getter_is_not_invoked(
    tmp_path, monkeypatch, name, value,
):
    store, scope, saved, retained, proposed = make_case(tmp_path)
    hits = []

    def forged(_self):
        hits.append(name)
        return value

    monkeypatch.setattr(MemoryGenerationCASToken, name, property(forged))
    with pytest.raises(
        triage.MemoryCommitTriageRejected,
        match="invalid retained Memory triage inputs",
    ):
        triage.review_uncertain_memory_commit(
            store, proposed, retained_before=retained,
        )
    assert hits == []
    assert store.get(saved.memory_id, scope).revision == 1


@pytest.mark.parametrize(
    "name", ("external_action_authorized", "consent_authenticated"),
)
def test_post_snapshot_token_authority_substitution_is_not_invoked(
    tmp_path, monkeypatch, name,
):
    store, scope, saved, retained, proposed = make_case(tmp_path)
    original = triage._snapshot
    hits = []

    def forged(_self):
        hits.append(name)
        return False

    def changed_snapshot(conn, memory_id, scope, source_id):
        observed = original(conn, memory_id, scope, source_id)
        monkeypatch.setattr(MemoryGenerationCASToken, name, property(forged))
        return observed

    monkeypatch.setattr(triage, "_snapshot", changed_snapshot)
    with pytest.raises(
        triage.MemoryCommitTriageRejected, match="manual review required",
    ):
        triage.review_uncertain_memory_commit(
            store, proposed, retained_before=retained,
        )
    assert hits == []
    assert store.get(saved.memory_id, scope).revision == 1


def test_unmodified_manual_triage_never_licenses_retry(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    result = triage.review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert result.disposition == "LOCAL_UNCHANGED"
    assert result.automatic_retry_authorized is False
    assert result.write_authorized is False
