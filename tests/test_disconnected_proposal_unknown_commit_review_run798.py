"""Manual-only unknown-COMMIT triage is not approval, dispatch or retry."""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_proposal_store as store
from ark.agency import disconnected_proposal_unknown_commit_review as triage

_A = "proposal_" + "a" * 64
_B = "proposal_" + "b" * 64


def _new(tmp_path):
    path = tmp_path / "proposal.sqlite3"
    genesis = store.create_disconnected_proposal_store(path)
    return path, genesis


def _read(path, proposal=_A):
    return store.inspect_disconnected_proposal_store(path, proposal_id=proposal)


def _append(path, proposal, prior, state="PROPOSED"):
    return store.append_disconnected_proposal_transition(
        path, proposal_id=proposal, new_state=state,
        expected_revision=0 if prior.proposal_tip is None else prior.proposal_tip.revision,
        expected_tip=prior.proposal_tip, retained=prior.witness,
    )


def _triage(path, prior, proposal=_A, state="PROPOSED"):
    return triage.review_disconnected_proposal_unknown_commit(
        path, proposal_id=proposal, new_state=state,
        expected_revision=0 if prior.proposal_tip is None else prior.proposal_tip.revision,
        expected_tip=prior.proposal_tip, retained_before=prior.witness,
    )


def _no_authority(report):
    assert report.automatic_retry_authorized is False
    assert report.code_change_authorized is False
    assert report.human_review_authenticated is False
    assert report.training_authorized is False
    assert report.candidate_promotion_authorized is False
    assert report.observed_witness.externally_authenticated is False


def test_no_append_observed_cannot_grant_retry(tmp_path):
    path, genesis = _new(tmp_path)
    before = _read(path)
    report = _triage(path, before)
    assert report.disposition == triage.OBSERVED_UNCHANGED
    assert report.observed_witness == genesis
    assert report.observed_tip is None
    assert len(report.expected_next_global_digest) == 64
    _no_authority(report)
    # Read-only triage must never record a proposal by itself.
    assert _read(path) == before


def test_lost_append_receipt_matches_exact_single_event(tmp_path):
    path, _ = _new(tmp_path)
    before = _read(path)
    appended = _append(path, _A, before)  # Pretend this receipt was lost.
    report = _triage(path, before)
    assert report.disposition == triage.OBSERVED_EXACT_APPEND
    assert report.observed_witness == appended.witness
    assert report.observed_tip == appended.proposal_tip
    assert report.expected_next_global_digest == appended.witness.chain_digest
    _no_authority(report)
    assert _read(path) == appended


def test_existing_proposal_second_transition_match(tmp_path):
    path, _ = _new(tmp_path)
    first = _append(path, _A, _read(path))
    second = _append(path, _A, first, "REVIEW_REQUIRED")
    report = _triage(path, first, state="REVIEW_REQUIRED")
    assert report.disposition == triage.OBSERVED_EXACT_APPEND
    assert report.observed_tip == second.proposal_tip
    _no_authority(report)


def test_other_owner_intervened_in_global_prefix(tmp_path):
    path, _ = _new(tmp_path)
    before = _read(path)
    _append(path, _B, _read(path, _B))
    report = _triage(path, before)
    assert report.disposition == triage.MANUAL_REVIEW_REQUIRED
    assert report.observed_tip is None
    _no_authority(report)


def test_even_a_matching_tip_requires_exact_global_prefix(tmp_path):
    path, _ = _new(tmp_path)
    before = _read(path)
    first = _append(path, _A, before)
    _append(path, _B, _read(path, _B))
    report = _triage(path, before)
    assert report.disposition == triage.MANUAL_REVIEW_REQUIRED
    assert report.observed_tip == first.proposal_tip
    _no_authority(report)


def test_expected_event_on_nonzero_unrelated_prefix(tmp_path):
    path, _ = _new(tmp_path)
    _append(path, _B, _read(path, _B))
    before = _read(path, _A)
    next_a = _append(path, _A, before)
    report = _triage(path, before)
    assert report.disposition == triage.OBSERVED_EXACT_APPEND
    assert report.observed_witness == next_a.witness
    _no_authority(report)


def test_later_transition_does_not_masquerade_as_exact_one(tmp_path):
    path, _ = _new(tmp_path)
    before = _read(path)
    first = _append(path, _A, before)
    _append(path, _A, first, "REVIEW_REQUIRED")
    report = _triage(path, before)
    assert report.disposition == triage.MANUAL_REVIEW_REQUIRED
    _no_authority(report)


@pytest.mark.parametrize("bad", (True, 1.0, -1, 1, "0", 256))
def test_bad_expected_revision_fails_before_db_open(tmp_path, bad):
    with pytest.raises(triage.OfflineProposalUnknownCommitRejected):
        triage.review_disconnected_proposal_unknown_commit(
            tmp_path / "missing.db", proposal_id=_A, new_state="PROPOSED",
            expected_revision=bad, expected_tip=None,
            retained_before=store.genesis_disconnected_proposal_witness(),
        )


@pytest.mark.parametrize("bad", ("PROPOSED", "ACCEPTED_FOR_IMPLEMENTATION", "", 5))
def test_illegal_synthetic_transition_fails_before_db_open(tmp_path, bad):
    path, _ = _new(tmp_path)
    proposed = _append(path, _A, _read(path))
    with pytest.raises(triage.OfflineProposalUnknownCommitRejected):
        triage.review_disconnected_proposal_unknown_commit(
            tmp_path / "missing.db", proposal_id=_A, new_state=bad,
            expected_revision=proposed.proposal_tip.revision,
            expected_tip=proposed.proposal_tip, retained_before=proposed.witness,
        )


def test_roll_back_detected_against_retained_witness(tmp_path):
    path, _ = _new(tmp_path)
    before = _read(path)
    appended = _append(path, _A, before)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_proposal_events")
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="prefix mismatch"):
        _triage(path, appended, state="REVIEW_REQUIRED")


def test_invalid_schema_is_not_classified_as_unchanged(tmp_path):
    path, _ = _new(tmp_path)
    before = _read(path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE unexpected (n INTEGER)")
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="schema changed"):
        _triage(path, before)

@pytest.mark.parametrize(("target", "name"), (
    # Rebinding inherited __new__ permanently changes CPython tp_new on
    # slotted dataclasses, even if the class attribute is later removed.
    # Test the checked own constructor instead, with no global slot poison.
    ("report", "__init__"),
    ("report", "__getattribute__"),
    ("report", "__getattr__"),
    ("triage", "_protocol"),
    ("store", "_protocol"),
    ("lifecycle", "_protocol"),
    ("triage", "OBSERVED_UNCHANGED"),
    ("triage", "OBSERVED_EXACT_APPEND"),
    ("triage", "MANUAL_REVIEW_REQUIRED"),
))
def test_unknown_commit_protocol_substitution_refused_before_store_read(
    tmp_path, monkeypatch, target, name,
):
    path, _ = _new(tmp_path)
    before = _read(path)
    invoked = []

    def injected(*args, **kwargs):
        invoked.append((args, kwargs))
        raise RuntimeError("injected unknown-commit callback must not run")

    owner = {
        "report": triage.OfflineProposalUnknownCommitReport,
        "triage": triage,
        "store": store,
        "lifecycle": triage.lifecycle,
    }[target]
    replacement = "FORGED_STATE" if name.isupper() else injected
    # Restoring inherited class hooks by assignment leaves a new own
    # __new__/__getattribute__ descriptor and can corrupt later tests.
    had_own_attribute = name in vars(owner)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(owner, name, replacement, raising=False)
            with pytest.raises(
                triage.OfflineProposalUnknownCommitRejected,
                match="proposal reconciliation protocol changed",
            ):
                _triage(path, before)
    finally:
        if not had_own_attribute and name in vars(owner):
            delattr(owner, name)
    assert invoked == []
    assert _read(path) == before
