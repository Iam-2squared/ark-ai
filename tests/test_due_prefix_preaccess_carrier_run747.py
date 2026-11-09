"""Run747: synthetic due-prefix review must not execute substituted carriers.

These are disconnected fixture checks; no trusted time, notification or tool
authorization is conferred by a retained SQLite witness or digest.
"""

import pytest

from ark.agency import disconnected_due_prefix_review as prefix


@pytest.mark.parametrize(
    ("carrier", "member"),
    [
        ("result", "previous_count"),
        ("result", "current_fingerprint"),
        ("result", "status"),
        ("result", "__init__"),
        ("result", "__getattribute__"),
        ("witness", "count"),
        ("witness", "fingerprint"),
        ("witness", "__getattribute__"),
    ],
)
def test_due_prefix_refuses_replaced_carrier_before_any_private_read(
    monkeypatch, carrier, member,
):
    cls = prefix._RESULT if carrier == "result" else prefix._WITNESS
    callbacks = []

    def hostile(*_args, **_kwargs):
        callbacks.append(member)
        raise AssertionError("substituted carrier was executed")

    replacement = (
        property(hostile) if member in prefix._RESULT_FIELDS + prefix._WITNESS_FIELDS
        else hostile
    )
    monkeypatch.setattr(cls, member, replacement)
    # Only a type-correct shell is needed: the class fence must fire before
    # the ledger path, stored rows, or retained witness values are accessed.
    ledger = object.__new__(prefix._LEDGER)
    witness = object.__new__(prefix._WITNESS)
    with pytest.raises(
        prefix.DisconnectedDuePrefixRejected,
        match="authority definition changed",
    ):
        prefix.review_retained_due_prefix(ledger, witness)
    assert callbacks == []


@pytest.mark.parametrize("binding", ["DueReservationWitness", "DisconnectedDueReservations"])
def test_due_prefix_refuses_substituted_dependency_class_preaccess(
    monkeypatch, binding,
):
    monkeypatch.setattr(prefix.due, binding, object)
    ledger = object.__new__(prefix._LEDGER)
    witness = object.__new__(prefix._WITNESS)
    with pytest.raises(
        prefix.DisconnectedDuePrefixRejected,
        match="authority definition changed",
    ):
        prefix.review_retained_due_prefix(ledger, witness)
