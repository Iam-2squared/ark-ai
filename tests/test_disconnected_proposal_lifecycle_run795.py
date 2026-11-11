"""No synthetic proposal transition may become a real authority or replay gap."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency import disconnected_proposal_lifecycle as lifecycle

_ID = "proposal_" + "a" * 64
_OTHER = "proposal_" + "b" * 64


def _history(*states):
    prior = None
    events = ()
    for state in states:
        event = lifecycle.prepare_disconnected_proposal_transition(
            _ID, prior, state,
        )
        events = (*events, event)
        prior = lifecycle.replay_disconnected_proposal_lifecycle(_ID, events)
    return events, prior


def test_replay_is_deterministic_and_returns_only_inert_synthetic_tip():
    events, prior = _history(
        "PROPOSED", "REVIEW_REQUIRED", "ACCEPTED_FOR_IMPLEMENTATION",
    )
    assert lifecycle.replay_disconnected_proposal_lifecycle(_ID, events) == prior
    assert prior.revision == 3
    assert prior.state == "ACCEPTED_FOR_IMPLEMENTATION"
    assert prior.human_review_authenticated is False
    assert prior.code_change_authorized is False
    assert prior.candidate_promotion_authorized is False
    assert prior.training_authorized is False
    assert prior.protected_evaluation_opened is False


def test_retained_tip_can_anchor_prefix_across_later_events():
    events, final = _history("PROPOSED", "REVIEW_REQUIRED", "REJECTED")
    prefix = lifecycle.replay_disconnected_proposal_lifecycle(_ID, events[:2])
    assert lifecycle.replay_disconnected_proposal_lifecycle(
        _ID, events, retained=prefix,
    ) == final


@pytest.mark.parametrize("tamper", (
    {"proposal_id": _OTHER},
    {"revision": 2},
    {"revision": True},
    {"revision": -1},
    {"prior_state": "REVIEW_REQUIRED"},
    {"new_state": "ACCEPTED_FOR_IMPLEMENTATION"},
    {"new_state": "RUN_TRAINING"},
    {"previous_digest": "0" * 63 + "a"},
    {"event_digest": "b" * 64},
    {"event_digest": "A" * 64},
))
def test_first_event_tamper_rejected(tamper):
    events, _ = _history("PROPOSED")
    with pytest.raises(lifecycle.DisconnectedProposalLifecycleRejected):
        lifecycle.replay_disconnected_proposal_lifecycle(
            _ID, (replace(events[0], **tamper),),
        )


def test_missing_or_reordered_events_are_not_accepted():
    events, _ = _history("PROPOSED", "REVIEW_REQUIRED", "SUPERSEDED")
    for invalid in (events[1:], (events[0], events[2]), events[::-1]):
        with pytest.raises(lifecycle.DisconnectedProposalLifecycleRejected):
            lifecycle.replay_disconnected_proposal_lifecycle(_ID, invalid)


def test_prefix_digest_detects_replacement_with_another_valid_history():
    original, tip = _history("PROPOSED", "REVIEW_REQUIRED", "SUPERSEDED")
    other, _ = _history("PROPOSED", "REJECTED")
    assert original[0] == other[0]
    with pytest.raises(lifecycle.DisconnectedProposalLifecycleRejected):
        lifecycle.replay_disconnected_proposal_lifecycle(
            _ID, other, retained=tip,
        )


def test_retained_identity_and_digest_mismatch_fail_closed():
    events, tip = _history("PROPOSED", "REVIEW_REQUIRED")
    for bad_tip in (
        replace(tip, proposal_id=_OTHER),
        replace(tip, revision=True),
        replace(tip, revision=3),
        replace(tip, state="RUN_TRAINING"),
        replace(tip, event_digest="c" * 64),
    ):
        with pytest.raises(lifecycle.DisconnectedProposalLifecycleRejected):
            lifecycle.replay_disconnected_proposal_lifecycle(
                _ID, events, retained=bad_tip,
            )


def test_terminal_state_cannot_reopen_and_acceptance_cannot_trigger_training():
    for terminal in ("REJECTED", "SUPERSEDED"):
        states = (
            ("PROPOSED", terminal) if terminal == "REJECTED"
            else ("PROPOSED", "REVIEW_REQUIRED", terminal)
        )
        _, tip = _history(*states)
        for next_state in ("PROPOSED", "REVIEW_REQUIRED", "ACCEPTED_FOR_IMPLEMENTATION"):
            with pytest.raises(lifecycle.DisconnectedProposalLifecycleRejected):
                lifecycle.prepare_disconnected_proposal_transition(
                    _ID, tip, next_state,
                )


def test_nonexact_inputs_and_unbounded_history_refused():
    events, _ = _history("PROPOSED")
    for invalid in ([], (), list(events), events * 257, ("not-event",)):
        with pytest.raises(lifecycle.DisconnectedProposalLifecycleRejected):
            lifecycle.replay_disconnected_proposal_lifecycle(_ID, invalid)
    with pytest.raises(lifecycle.DisconnectedProposalLifecycleRejected):
        lifecycle.replay_disconnected_proposal_lifecycle("private owner", events)
    with pytest.raises(lifecycle.DisconnectedProposalLifecycleRejected):
        lifecycle.prepare_disconnected_proposal_transition(
            _ID, None, "ACCEPTED_FOR_IMPLEMENTATION",
        )


def test_forged_synthetic_tip_does_not_skip_revision_conflict():
    events, tip = _history("PROPOSED", "REVIEW_REQUIRED")
    claimed = replace(tip, revision=1)
    with pytest.raises(lifecycle.DisconnectedProposalLifecycleRejected):
        lifecycle.replay_disconnected_proposal_lifecycle(
            _ID, events, retained=claimed,
        )


def test_denial_descriptor_change_rejected_before_running_getter(monkeypatch):
    events, _ = _history("PROPOSED")
    called = []

    def malicious(_self):
        called.append("executed")
        return False

    with monkeypatch.context() as patch:
        patch.setattr(
            lifecycle.DetachedProposalLifecycleTip,
            "code_change_authorized", property(malicious),
        )
        with pytest.raises(
            lifecycle.DisconnectedProposalLifecycleRejected, match="protocol",
        ):
            lifecycle.replay_disconnected_proposal_lifecycle(_ID, events)
    assert not called


def test_prepared_events_have_exact_hash_and_do_not_record_an_approval():
    events, tip = _history("PROPOSED", "REVIEW_REQUIRED")
    next_event = lifecycle.prepare_disconnected_proposal_transition(
        _ID, tip, "ACCEPTED_FOR_IMPLEMENTATION",
    )
    assert next_event.previous_digest == tip.event_digest
    assert next_event.revision == tip.revision + 1
    assert lifecycle.replay_disconnected_proposal_lifecycle(
        _ID, (*events, next_event),
    ).human_review_authenticated is False
