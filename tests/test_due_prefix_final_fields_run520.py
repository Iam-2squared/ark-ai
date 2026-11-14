"""A denied scheduler receipt flag must not conceal a forged final status."""

from dataclasses import replace

import pytest

import ark.agency.disconnected_due_prefix_review as prefix
from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    genesis_due_witness,
)


def fixture(tmp_path):
    ledger = DisconnectedDueReservations(tmp_path / "due-prefix.db")
    first = ledger.reserve_due(
        policy_sha256="a" * 64, due_at_ms=1000, observed_now_ms=1005,
        retained=genesis_due_witness(),
    )
    return ledger, first.witness


@pytest.mark.parametrize(
    "field,value",
    (
        ("status", "EXECUTION_AUTHORIZED"),
        ("current_count", 999),
        ("previous_count", 0),
        ("current_fingerprint", "f" * 64),
        ("review_sha256", "f" * 64),
        ("current_count", True),
    ),
)
def test_false_automatic_replay_getter_cannot_rewrite_other_report_fields(
    tmp_path, monkeypatch, field, value,
):
    ledger, retained = fixture(tmp_path)

    def mutate_and_deny(self):
        object.__setattr__(self, field, value)
        return False

    # The original validation reads fields BEFORE this last authority
    # getter. Its false return must not cover a changed status or count.
    monkeypatch.setattr(
        prefix.DisconnectedDuePrefixReview,
        "automatic_replay_authorized",
        property(mutate_and_deny),
    )
    with pytest.raises(prefix.DisconnectedDuePrefixRejected, match="changed"):
        prefix.review_retained_due_prefix(ledger, retained)


def test_late_denial_can_mutate_original_retained_witness_but_not_pass(
    tmp_path, monkeypatch,
):
    ledger, retained = fixture(tmp_path)

    def mutate_retention(self):
        object.__setattr__(retained, "fingerprint", "f" * 64)
        return False

    monkeypatch.setattr(
        prefix.DisconnectedDuePrefixReview,
        "automatic_replay_authorized", property(mutate_retention),
    )
    with pytest.raises(prefix.DisconnectedDuePrefixRejected, match="source/witness"):
        prefix.review_retained_due_prefix(ledger, retained)


def test_valid_restarted_read_only_preview_remains_non_authorizing(tmp_path):
    ledger, retained = fixture(tmp_path)
    reopened = DisconnectedDueReservations(ledger._path, require_existing=True)
    one = prefix.review_retained_due_prefix(reopened, retained)
    two = prefix.review_retained_due_prefix(reopened, retained)
    assert one == two
    assert one.status == "UNCHANGED_LOCAL_HISTORY"
    assert one.previous_count == one.current_count == 1
    assert one.automatic_replay_authorized is False
    assert one.notification_authorized is False


def test_replaced_retained_witness_does_not_validate_a_different_prefix(tmp_path):
    ledger, retained = fixture(tmp_path)
    forged = replace(retained, fingerprint="f" * 64)
    with pytest.raises(prefix.DisconnectedDuePrefixRejected, match="prefix"):
        prefix.review_retained_due_prefix(ledger, forged)
