"""Disconnected sidecar↔reservation re-attestation and drift matrix."""

import hashlib
import sqlite3

import pytest

from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_review import SyntheticCancellationLedger
from ark.agency.synthetic_approval_claim_review import make_synthetic_approval_claim
from ark.agency.synthetic_claim_occurrence_link_review import (
    SyntheticClaimOccurrenceLinkStore,
)
from ark.agency.synthetic_claim_occurrence_recheck_review import (
    SyntheticClaimSourceRejected,
    review_synthetic_claim_occurrence_sources,
)
from ark.agency.synthetic_occurrence_continuity_review import (
    read_synthetic_ledger_witness,
)


class NeverBackend:
    def execute(self, call):
        raise AssertionError("a source review must never execute a backend")


def digest(item):
    return hashlib.sha256(item.encode("utf-8")).hexdigest()


def fixture(tmp_path):
    registry = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.WRITE, "offline", NeverBackend()),
    ))
    call = ToolCall("fixture", "write", "local-private", {"private": "never-log"})
    path = tmp_path / "source # percent %.sqlite"
    source = SyntheticOccurrenceStore(path)
    veto = SyntheticCancellationLedger(tmp_path / "veto.sqlite")
    sidecar = SyntheticClaimOccurrenceLinkStore(tmp_path / "links.sqlite")
    return registry, call, path, source, veto, sidecar


def write_pair(state, *, tag="first", linked_at=20):
    registry, call, _, source, veto, sidecar = state
    claim = make_synthetic_approval_claim(
        registry, call, issuer_digest=digest("issuer"),
        subject_digest=digest("subject"), purpose_digest=digest("purpose"),
        recipient_digest=digest("recipient"), nonce_digest=digest(tag),
        issued_at_ms=10, expires_at_ms=100,
    )
    receipt = source.reserve_synthetic(
        registry, call, OneShotAuthorization(
            "synthetic-" + tag, call.request_id, 500,
        ),
        occurrence_id="occ_" + digest(tag), now_ms=11,
    )
    sidecar.link_synthetic(
        claim, veto, registry, call, source, receipt, now_ms=linked_at,
    )
    return claim, receipt


def review(state, **options):
    return review_synthetic_claim_occurrence_sources(
        state[5], state[2], **options,
    )


def test_committed_pair_can_be_rechecked_without_any_execution(tmp_path):
    state = fixture(tmp_path)
    claim, receipt = write_pair(state)
    result = review(
        state, expected_pair=(claim.approval_id, receipt.occurrence_id),
    )
    assert result.expected_pair_found is True
    assert result.link_event_count == 1
    assert result.reservation_row_count == 1
    assert result.link_tail_hash.startswith("clink_")
    assert result.reservation_digest.startswith("synthetic_ledger_")
    assert result.human_consent_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert "never-log" not in repr(result)


def test_empty_sidecar_recheck_is_not_an_approval(tmp_path):
    state = fixture(tmp_path)
    result = review(state)
    assert result.link_event_count == 0
    assert result.expected_pair_found is False
    assert result.dispatch_authorized is False


def test_missing_claim_pair_fails_even_with_matching_request(tmp_path):
    state = fixture(tmp_path)
    claim, receipt = write_pair(state)
    with pytest.raises(SyntheticClaimSourceRejected, match="missing"):
        review(state, expected_pair=(
            "approval_" + digest("other"), receipt.occurrence_id,
        ))
    with pytest.raises(SyntheticClaimSourceRejected, match="missing"):
        review(state, expected_pair=(
            claim.approval_id, "occ_" + digest("other"),
        ))


@pytest.mark.parametrize("operation", [
    "DELETE FROM synthetic_occurrence_reservations",
    "UPDATE synthetic_occurrence_reservations SET occurrence_id='occ_" +
    digest("replacement") + "'",
    "UPDATE synthetic_occurrence_reservations SET reserved_at_ms=21",
])
def test_replayable_source_row_changes_are_rejected(tmp_path, operation):
    state = fixture(tmp_path)
    write_pair(state)
    with sqlite3.connect(state[2]) as db:
        db.execute(operation)
    with pytest.raises(SyntheticClaimSourceRejected, match="missing or changed"):
        review(state)


def test_independently_retained_reservation_witness_detects_row_change(tmp_path):
    state = fixture(tmp_path)
    write_pair(state)
    prior = read_synthetic_ledger_witness(state[2])
    with sqlite3.connect(state[2]) as db:
        db.execute(
            "UPDATE synthetic_occurrence_reservations SET expires_at_ms=501"
        )
    with pytest.raises(RuntimeError, match="retained"):
        review(state, retained_reservations=prior)


def test_independently_retained_link_witness_detects_rollback(tmp_path):
    state = fixture(tmp_path)
    write_pair(state)
    prior = state[5].read_witness()
    with sqlite3.connect(state[5].path) as db:
        db.execute("DELETE FROM synthetic_claim_occurrence_links")
    with pytest.raises(RuntimeError, match="retained"):
        review(state, retained_links=prior)


@pytest.mark.parametrize("which", ["source", "sidecar"])
def test_missing_initialized_database_is_not_recreated(tmp_path, which):
    state = fixture(tmp_path)
    write_pair(state)
    path = state[2] if which == "source" else state[5].path
    path.rename(tmp_path / ("moved-" + which + ".sqlite"))
    with pytest.raises(sqlite3.OperationalError):
        review(state)
    assert not path.exists()


@pytest.mark.parametrize("which", ["source", "sidecar"])
def test_changed_sqlite_schema_fails_closed(tmp_path, which):
    state = fixture(tmp_path)
    write_pair(state)
    path = state[2] if which == "source" else state[5].path
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE unexpected(data TEXT)")
    with pytest.raises(RuntimeError, match="schema"):
        review(state)


@pytest.mark.parametrize("bad", [
    ("bad", "occ_" + digest("first")),
    ("approval_" + digest("first"), "bad"),
    ("approval_" + digest("first"),),
    ["approval_" + digest("first"), "occ_" + digest("first")],
    (True, "occ_" + digest("first")),
])
def test_noncanonical_expected_pair_is_rejected(tmp_path, bad):
    state = fixture(tmp_path)
    write_pair(state)
    with pytest.raises(SyntheticClaimSourceRejected, match="exact"):
        review(state, expected_pair=bad)


def test_recheck_does_not_depend_on_new_or_unchanged_other_reservations(tmp_path):
    state = fixture(tmp_path)
    claim, receipt = write_pair(state)
    state[3].reserve_synthetic(
        state[0], state[1],
        OneShotAuthorization("other-token", state[1].request_id, 500),
        occurrence_id="occ_" + digest("unlinked"), now_ms=12,
    )
    result = review(
        state, expected_pair=(claim.approval_id, receipt.occurrence_id),
    )
    assert result.link_event_count == 1
    assert result.reservation_row_count == 2
    assert result.external_outcome_known is False
