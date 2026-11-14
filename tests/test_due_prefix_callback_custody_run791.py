"""Run791: retained due-prefix callback custody is checked before SQLite.

All data is local disposable SQLite; this never grants notification or tool
permission, independent witness custody, or historical writer provenance.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_due_prefix_review as prefix
from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    genesis_due_witness,
)


@pytest.mark.parametrize(
    "target",
    ("witness", "digest", "sha256", "dumps", "domain"),
)
def test_due_prefix_refuses_substituted_reader_before_private_access(
    target: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked: list[str] = []

    def poison(*_args: object, **_kwargs: object) -> object:
        invoked.append(target)
        raise AssertionError("unreviewed callback ran before prefix admission")

    with monkeypatch.context() as patch:
        if target == "witness":
            patch.setattr(prefix.due, "_check_witness", poison)
        elif target == "digest":
            patch.setattr(prefix.due, "_digest", poison)
        elif target == "sha256":
            patch.setattr(prefix.hashlib, "sha256", poison)
        elif target == "dumps":
            patch.setattr(prefix.json, "dumps", poison)
        else:
            patch.setattr(prefix, "_DOMAIN", b"substituted-domain\0")
        # Never initialize private fields: an unsafe witness/path read would
        # raise or invoke a poison hook before the original callback fence.
        ledger = object.__new__(prefix._LEDGER)
        witness = object.__new__(prefix._WITNESS)
        with pytest.raises(
            prefix.DisconnectedDuePrefixRejected,
            match="authority definition changed",
        ):
            prefix.review_retained_due_prefix(ledger, witness)
    assert not invoked


def test_unmodified_due_prefix_remains_local_and_denial_only(tmp_path) -> None:
    ledger = DisconnectedDueReservations(tmp_path / "run791-due.sqlite")
    review = prefix.review_retained_due_prefix(ledger, genesis_due_witness())
    assert review.previous_count == review.current_count == 0
    assert review.status == "UNCHANGED_LOCAL_HISTORY"
    assert len(review.review_sha256) == 64
    assert review.notification_authorized is False
    assert review.tool_dispatch_authorized is False
    assert review.automatic_replay_authorized is False
