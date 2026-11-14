"""Revocation continuity rejects an unreviewed hash or schema-parser epoch.

A local SQLite prefix is diagnostic privacy evidence, not authenticated
consent, a deletion command, or proof of erasure from other stores.
"""

from __future__ import annotations

import re

import pytest

from ark import personal_context_revocation_continuity_review as continuity
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger

_MUTATIONS = (
    ("_DOMAIN", b"unreviewed-revocation-digest\\0"),
    ("_SHA", re.compile(r".*\\Z")),
    ("_DIGEST", re.compile(r".*\\Z")),
    ("_MAX", 2**63),
)


@pytest.mark.parametrize(("name", "replacement"), _MUTATIONS)
@pytest.mark.parametrize("with_retained", (False, True))
def test_unreviewed_revocation_protocol_refuses_before_private_sqlite(
    tmp_path, monkeypatch, name, replacement, with_retained,
):
    ledger = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    previous = continuity.review_revocation_continuity(ledger) if with_retained else None
    observed_connections = []

    def forbidden_connection(*args, **kwargs):
        observed_connections.append(True)
        raise AssertionError("private SQLite connection opened under drift")

    monkeypatch.setattr(ledger, "_connect", forbidden_connection)
    monkeypatch.setattr(continuity, name, replacement)
    with pytest.raises(
        continuity.SyntheticContextRevocationRejected,
        match="revocation digest implementation changed",
    ):
        continuity.review_revocation_continuity(ledger, retained=previous)
    assert observed_connections == []


def test_equal_value_domain_replacement_is_not_trusted(tmp_path, monkeypatch):
    ledger = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    copied = bytes(bytearray(continuity._DOMAIN))
    assert copied == continuity._DOMAIN and copied is not continuity._DOMAIN
    monkeypatch.setattr(continuity, "_DOMAIN", copied)
    with pytest.raises(
        continuity.SyntheticContextRevocationRejected,
        match="revocation digest implementation changed",
    ):
        continuity.review_revocation_continuity(ledger)


def test_original_revocation_prefix_is_denial_only(tmp_path):
    ledger = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    witness = continuity.review_revocation_continuity(ledger)
    assert witness.rows == ()
    assert witness.witness_id.startswith("rvk_")
    assert continuity.review_revocation_continuity(ledger, retained=witness) == witness
