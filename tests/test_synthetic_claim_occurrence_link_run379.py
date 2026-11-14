"""Offline approval claim ↔ occurrence sidecar: identity and failure matrix."""

import hashlib
import sqlite3

import pytest

from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_review import SyntheticCancellationLedger
from ark.agency.synthetic_approval_claim_review import (
    SyntheticApprovalRejected,
    make_synthetic_approval_claim,
)
from ark.agency.synthetic_claim_occurrence_link_review import (
    SyntheticClaimLinkRejected,
    SyntheticClaimOccurrenceLinkStore,
)


class NeverBackend:
    def execute(self, call):
        raise AssertionError("claim link reviews cannot run a backend")


def _hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _fixture(tmp_path):
    registry = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.WRITE, "offline", NeverBackend()),
    ))
    call = ToolCall("fixture", "write", "private-scope", {"data": "not-for-output"})
    ledger = SyntheticOccurrenceStore(tmp_path / "occurrence #1 %.sqlite")
    cancellation = SyntheticCancellationLedger(tmp_path / "cancel.sqlite")
    links = SyntheticClaimOccurrenceLinkStore(tmp_path / "claims.sqlite")
    return registry, call, ledger, cancellation, links


def _claim(registry, call, *, nonce="nonce", purpose="purpose"):
    return make_synthetic_approval_claim(
        registry, call,
        issuer_digest=_hash("issuer"),
        subject_digest=_hash("subject"),
        purpose_digest=_hash(purpose),
        recipient_digest=_hash("recipient"),
        nonce_digest=_hash(nonce),
        issued_at_ms=10,
        expires_at_ms=100,
    )


def _reserve(registry, call, ledger, *, tag="one", when=11):
    return ledger.reserve_synthetic(
        registry, call,
        OneShotAuthorization("token-" + tag, call.request_id, 500),
        occurrence_id="occ_" + _hash(tag),
        now_ms=when,
    )


def _link(state, claim, reservation, **changes):
    registry, call, ledger, cancellation, links = state
    return links.link_synthetic(
        claim, cancellation, registry, call, ledger, reservation,
        now_ms=20, **changes,
    )


def test_link_one_claim_to_one_committed_reservation_is_inert(tmp_path):
    state = _fixture(tmp_path)
    claim = _claim(state[0], state[1])
    reserved = _reserve(*state[:3])
    result = _link(state, claim, reserved)
    assert result.approval_id == claim.approval_id
    assert result.occurrence_id == reserved.occurrence_id
    assert result.link_hash.startswith("clink_")
    assert result.human_consent_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert "not-for-output" not in repr(result)
    witness = state[4].read_witness()
    assert witness.event_count == 1
    assert witness.tail_hash == result.link_hash
    assert (
        SyntheticClaimOccurrenceLinkStore(state[4].path).read_witness()
        == witness
    )


def test_same_claim_cannot_be_reassociated_to_different_occurrence(tmp_path):
    state = _fixture(tmp_path)
    claim = _claim(state[0], state[1])
    first = _reserve(*state[:3], tag="first")
    second = _reserve(*state[:3], tag="second", when=12)
    _link(state, claim, first)
    with pytest.raises(SyntheticClaimLinkRejected, match="already linked"):
        _link(state, claim, second)
    assert state[4].read_witness().event_count == 1


def test_different_claim_nonce_cannot_reassociate_same_occurrence(tmp_path):
    state = _fixture(tmp_path)
    first_claim = _claim(state[0], state[1], nonce="one")
    second_claim = _claim(state[0], state[1], nonce="two")
    assert first_claim.approval_id != second_claim.approval_id
    reserved = _reserve(*state[:3])
    _link(state, first_claim, reserved)
    with pytest.raises(SyntheticClaimLinkRejected, match="already linked"):
        _link(state, second_claim, reserved)


@pytest.mark.parametrize("change", ["nonce", "purpose"])
def test_claim_identity_changes_when_provenance_claim_changes(tmp_path, change):
    state = _fixture(tmp_path)
    base = _claim(state[0], state[1])
    changed = _claim(
        state[0], state[1], **{change: "different"},
    )
    assert base.approval_id != changed.approval_id


def test_expired_or_cancelled_claim_is_not_linked(tmp_path):
    state = _fixture(tmp_path)
    claim = _claim(state[0], state[1])
    reserved = _reserve(*state[:3])
    state[3].cancel_synthetic(claim.approval_id, at_ms=12)
    with pytest.raises(RuntimeError, match="cancelled"):
        _link(state, claim, reserved)
    assert state[4].read_witness().event_count == 0


def test_link_at_exact_expiry_is_refused(tmp_path):
    state = _fixture(tmp_path)
    claim = _claim(state[0], state[1])
    reserved = _reserve(*state[:3])
    with pytest.raises(SyntheticApprovalRejected, match="current"):
        state[4].link_synthetic(
            claim, state[3], state[0], state[1], state[2], reserved, now_ms=100,
        )
    assert state[4].read_witness().event_count == 0


def test_retained_witness_detects_deleted_persisted_history(tmp_path):
    state = _fixture(tmp_path)
    claim = _claim(state[0], state[1])
    receipt = _reserve(*state[:3])
    _link(state, claim, receipt)
    witness = state[4].read_witness()
    with sqlite3.connect(state[4].path) as conn:
        conn.execute("DELETE FROM synthetic_claim_occurrence_links")
    with pytest.raises(SyntheticClaimLinkRejected, match="retained"):
        state[4].read_witness(retained=witness)


@pytest.mark.parametrize(
    "alter",
    [
        "PRAGMA user_version=2",
        "CREATE TABLE unexpected(value TEXT)",
        "ALTER TABLE synthetic_claim_occurrence_links ADD COLUMN note TEXT",
    ],
)
def test_link_schema_tamper_fails_closed(tmp_path, alter):
    state = _fixture(tmp_path)
    with sqlite3.connect(state[4].path) as conn:
        conn.execute(alter)
    with pytest.raises(SyntheticClaimLinkRejected, match="schema"):
        state[4].read_witness()


def test_missing_sidecar_read_refuses_recreation(tmp_path):
    state = _fixture(tmp_path)
    original = state[4].path
    original.rename(tmp_path / "moved.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        state[4].read_witness()
    assert not original.exists()


def test_missing_reservation_source_refuses_recreation(tmp_path):
    state = _fixture(tmp_path)
    claim = _claim(state[0], state[1])
    receipt = _reserve(*state[:3])
    original = state[2]._path
    original.rename(tmp_path / "missing-source.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        _link(state, claim, receipt)
    assert not original.exists()
    assert state[4].read_witness().event_count == 0


@pytest.mark.parametrize("when", [-1, True, 2**63, 9])
def test_bad_link_clock_cannot_append(tmp_path, when):
    state = _fixture(tmp_path)
    claim = _claim(state[0], state[1])
    receipt = _reserve(*state[:3])
    with pytest.raises((SyntheticClaimLinkRejected, RuntimeError)):
        state[4].link_synthetic(
            claim, state[3], state[0], state[1], state[2], receipt,
            now_ms=when,
        )
    assert state[4].read_witness().event_count == 0
