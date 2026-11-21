"""Proposal-store carrier hooks must not execute before exact witness checks.

These synthetic histories neither authenticate an owner nor authorize replay,
training, protected evaluation, code edits or external tool dispatch.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from ark.agency import disconnected_proposal_store as store


@contextmanager
def _poison_lookup(
    cls: type, name: str, events: list[str],
) -> Iterator[None]:
    # Only patch inherited lookup hooks. Do not patch __new__, because
    # CPython may retain a changed tp_new slot after monkeypatch teardown.
    had_own = name in vars(cls)
    original = vars(cls).get(name)

    def hostile(*_args: object, **_kwargs: object) -> object:
        events.append(name)
        raise AssertionError("injected carrier lookup executed")

    setattr(cls, name, hostile)
    try:
        yield
    finally:
        if had_own:
            setattr(cls, name, original)
        elif name in vars(cls):
            delattr(cls, name)


@pytest.mark.parametrize(
    ("carrier", "hook"),
    (
        ("witness", "__getattribute__"),
        ("witness", "__getattr__"),
        ("snapshot", "__getattribute__"),
        ("snapshot", "__getattr__"),
    ),
)
def test_lookup_rebinding_refused_before_stored_identity_access(
    tmp_path, carrier: str, hook: str,
) -> None:
    path = tmp_path / "proposal.sqlite3"
    genesis = store.create_disconnected_proposal_store(path)
    snapshot = store.inspect_disconnected_proposal_store(
        path, proposal_id="proposal_" + "a" * 64,
    )
    cls = (
        store.DetachedProposalStoreWitness
        if carrier == "witness"
        else store.DetachedProposalStoreSnapshot
    )
    called: list[str] = []
    with _poison_lookup(cls, hook, called):
        with pytest.raises(
            store.DisconnectedProposalStoreRejected,
            match="proposal store protocol changed",
        ):
            if carrier == "witness":
                store._witness(genesis)
            else:
                store.inspect_disconnected_proposal_store(
                    path, proposal_id="proposal_" + "a" * 64,
                )
    assert called == []
    assert store.inspect_disconnected_proposal_store(
        path, proposal_id="proposal_" + "a" * 64,
    ) == snapshot


def test_valid_witness_and_snapshot_still_deny_authority(tmp_path) -> None:
    path = tmp_path / "proposal.sqlite3"
    original = store.create_disconnected_proposal_store(path)
    snapshot = store.inspect_disconnected_proposal_store(
        path, proposal_id="proposal_" + "a" * 64, retained=original,
    )
    assert snapshot.witness == original
    assert snapshot.proposal_tip is None
    assert snapshot.witness.externally_authenticated is False
    assert snapshot.human_review_authenticated is False
    assert snapshot.execution_authorized is False
    assert snapshot.candidate_promotion_authorized is False
