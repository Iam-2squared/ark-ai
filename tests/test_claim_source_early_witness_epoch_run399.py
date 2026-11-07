"""Exact retained claim-source history is pinned before validation callbacks.

Disconnected diagnostic fixture only; neither a claim link nor a reservation
witness authenticates human consent or the outcome of an external WRITE.
"""

import hashlib

import pytest

import ark.agency.synthetic_claim_occurrence_recheck_review as recheck
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_review import SyntheticCancellationLedger
from ark.agency.synthetic_approval_claim_review import make_synthetic_approval_claim
from ark.agency.synthetic_claim_occurrence_link_review import SyntheticClaimOccurrenceLinkStore
from ark.agency.synthetic_occurrence_continuity_review import (
    SyntheticLedgerWitness,
    read_synthetic_ledger_witness,
)


class NeverBackend:
    def execute(self, call):
        raise AssertionError("source correlation must never dispatch")


def _digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _sources(tmp_path):
    registry = ToolRegistry((
        ToolRegistration("offline", "write", Effect.WRITE, "fixture", NeverBackend()),
    ))
    call = ToolCall("offline", "write", "local")
    source_path = tmp_path / "reservation.sqlite"
    reservations = SyntheticOccurrenceStore(source_path)
    cancellation = SyntheticCancellationLedger(tmp_path / "cancellation.sqlite")
    links = SyntheticClaimOccurrenceLinkStore(tmp_path / "links.sqlite")
    claim = make_synthetic_approval_claim(
        registry, call,
        issuer_digest=_digest("issuer"), subject_digest=_digest("subject"),
        purpose_digest=_digest("purpose"), recipient_digest=_digest("recipient"),
        nonce_digest=_digest("nonce"), issued_at_ms=10, expires_at_ms=100,
    )
    receipt = reservations.reserve_synthetic(
        registry, call, OneShotAuthorization("test-token", call.request_id, 500),
        occurrence_id="occ_" + _digest("occurrence"), now_ms=11,
    )
    links.link_synthetic(
        claim, cancellation, registry, call, reservations, receipt, now_ms=20,
    )
    return links, source_path, links.read_witness(), read_synthetic_ledger_witness(source_path)


@pytest.mark.parametrize(
    "phase",
    ("link_shape", "reservation_integrity", "continuity", "link_read"),
)
def test_claim_source_retained_history_mutated_by_callback_fails_closed(
    tmp_path, monkeypatch, phase,
):
    links, source_path, prior_links, prior_source = _sources(tmp_path)
    calls = 0
    original_rows = prior_source.row_hashes
    assert original_rows

    if phase == "link_shape":
        original = recheck._retained_shape

        def mutate_link_shape(retained):
            nonlocal calls
            original(retained)
            calls += 1
            if retained is prior_links:
                object.__setattr__(prior_links, "event_count", 0)

        monkeypatch.setattr(recheck, "_retained_shape", mutate_link_shape)
    elif phase == "reservation_integrity":
        original = SyntheticLedgerWitness.assert_integrity

        def mutate_integrity(self):
            nonlocal calls
            original(self)
            if self is prior_source:
                calls += 1
                if calls == 1:
                    new_rows = tuple(list(original_rows))
                    assert new_rows == original_rows and new_rows is not original_rows
                    object.__setattr__(prior_source, "row_hashes", new_rows)

        monkeypatch.setattr(SyntheticLedgerWitness, "assert_integrity", mutate_integrity)
    elif phase == "continuity":
        original = recheck.assert_synthetic_history_continues

        def mutate_continuity(earlier, current):
            nonlocal calls
            original(earlier, current)
            calls += 1
            object.__setattr__(prior_source, "row_hashes", tuple(list(original_rows)))

        monkeypatch.setattr(
            recheck, "assert_synthetic_history_continues", mutate_continuity,
        )
    else:
        original = links.read_witness

        def mutate_read(*args, **kwargs):
            nonlocal calls
            result = original(*args, **kwargs)
            calls += 1
            object.__setattr__(prior_links, "event_count", 0)
            return result

        monkeypatch.setattr(links, "read_witness", mutate_read)

    with pytest.raises(recheck.SyntheticClaimSourceRejected, match="retained witness"):
        recheck.review_synthetic_claim_occurrence_sources(
            links, source_path, retained_links=prior_links,
            retained_reservations=prior_source,
        )
    assert calls >= 1

    monkeypatch.undo()
    # Restoring the unchanged historical witness lets the read-only diagnostic
    # run again; nothing was dispatched or written by the rejected operation.
    object.__setattr__(prior_links, "event_count", 1)
    object.__setattr__(prior_source, "row_hashes", original_rows)
    result = recheck.review_synthetic_claim_occurrence_sources(
        links, source_path, retained_links=prior_links,
        retained_reservations=prior_source,
    )
    assert result.link_event_count == 1
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
