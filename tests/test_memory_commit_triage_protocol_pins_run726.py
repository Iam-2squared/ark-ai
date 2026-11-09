"""Manual COMMIT-UNKNOWN Memory diagnostics retain their format and scan bound.

All fixtures use private, disposable SQLite. Local report contents cannot
prove a writer, grant replay, or attest an external effect.
"""

from __future__ import annotations

import pytest
from test_memory_postcommit_triage_run552 import make_case

import ark.memory.postcommit_uncertainty_review as triage


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("_DOMAIN", b"unreviewed-triage-domain"),
        ("_EVENT_DOMAIN", b"unreviewed-event-domain"),
        ("_MAX_EVENTS", 40001),
    ),
)
def test_rebound_triage_format_refused_before_private_sqlite(
    tmp_path, monkeypatch, name, replacement,
):
    store, scope, saved, retained, proposal = make_case(tmp_path)
    calls = []

    def forbidden_read():
        calls.append("unreviewed sqlite read")
        raise AssertionError("protocol changed before SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect_readonly", forbidden_read)
        patch.setattr(triage, name, replacement)
        with pytest.raises(
            triage.MemoryCommitTriageRejected,
            match="Memory triage input or denial changed",
        ):
            triage.review_uncertain_memory_commit(
                store, proposal, retained_before=retained,
            )
        assert calls == []
    # The deliberate no-SQLite hook is no longer active for this independent
    # proof that the original persisted row was untouched.
    assert store.get(saved.memory_id, scope).content == "original"


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("_DOMAIN", b"unreviewed-triage-domain"),
        ("_EVENT_DOMAIN", b"unreviewed-event-domain"),
        ("_MAX_EVENTS", 40001),
    ),
)
def test_rebinding_during_memory_snapshot_refused_without_commit_claim(
    tmp_path, monkeypatch, name, replacement,
):
    store, scope, saved, retained, proposal = make_case(tmp_path)
    original = triage._snapshot
    seen = []

    def rebound_after_snapshot(*args, **kwargs):
        outcome = original(*args, **kwargs)
        seen.append("snapshot read")
        monkeypatch.setattr(triage, name, replacement)
        return outcome

    monkeypatch.setattr(triage, "_snapshot", rebound_after_snapshot)
    with pytest.raises(triage.MemoryCommitTriageRejected):
        triage.review_uncertain_memory_commit(
            store, proposal, retained_before=retained,
        )
    assert seen == ["snapshot read"]
    assert store.get(saved.memory_id, scope).revision == 1
    assert [event.operation for event in store.events(scope)] == ["create"]


def test_unmodified_triage_still_denies_replay_and_attribution(tmp_path):
    store, _, _, retained, proposal = make_case(tmp_path)
    report = triage.review_uncertain_memory_commit(
        store, proposal, retained_before=retained,
    )
    assert report.disposition == "LOCAL_UNCHANGED"
    assert report.automatic_retry_authorized is False
    assert report.caller_attribution_proven is False
    assert report.write_authorized is False
    assert report.trusted_clock_proven is False
