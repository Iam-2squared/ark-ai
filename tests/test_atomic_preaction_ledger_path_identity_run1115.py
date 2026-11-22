"""Atomic pre-action ledger path identity stays fixed across local callbacks."""

from __future__ import annotations

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _ledger(tmp_path):
    path = tmp_path / "atomic-preaction-path.sqlite3"
    return DisconnectedAtomicPreactionLedger.create(path), path


@pytest.mark.parametrize("field", ("_path", "_path_identity"))
def test_path_identity_fields_reject_ordinary_assignment_and_deletion(
    tmp_path, field: str,
) -> None:
    ledger, path = _ledger(tmp_path)
    original = object.__getattribute__(ledger, field)

    with pytest.raises(AttributeError, match="path identity"):
        setattr(ledger, field, tmp_path / "alternate.sqlite3")
    with pytest.raises(AttributeError, match="path identity"):
        delattr(ledger, field)

    assert object.__getattribute__(ledger, field) is original
    assert object.__getattribute__(ledger, "_path") == path
    assert field not in vars(ledger)


def test_instance_dictionary_cannot_shadow_ledger_path(tmp_path) -> None:
    ledger, _path = _ledger(tmp_path)
    alternate = tmp_path / "alternate.sqlite3"
    ledger.__dict__["_path"] = alternate

    with pytest.raises(AtomicPreactionRejected, match="path identity"):
        ledger.inspect(genesis_atomic_preaction_witness())

    assert not alternate.exists()


def test_reflective_path_retarget_is_rejected_before_sqlite_open(tmp_path) -> None:
    ledger, _path = _ledger(tmp_path)
    alternate = tmp_path / "alternate.sqlite3"
    object.__setattr__(ledger, "_path", alternate)

    with pytest.raises(AtomicPreactionRejected, match="path identity"):
        ledger.inspect(genesis_atomic_preaction_witness())

    assert not alternate.exists()


def test_reentrant_open_cannot_retarget_path_before_read(tmp_path, monkeypatch) -> None:
    ledger, _path = _ledger(tmp_path)
    alternate = tmp_path / "alternate.sqlite3"
    original_open = ledger._open

    def reentrant_open(*, read_only: bool):
        object.__setattr__(ledger, "_path", alternate)
        return original_open(read_only=read_only)

    monkeypatch.setattr(ledger, "_open", reentrant_open)
    with pytest.raises(AtomicPreactionRejected, match="path identity"):
        ledger.inspect(genesis_atomic_preaction_witness())

    assert not alternate.exists()


def test_subclass_cannot_create_ledger_file(tmp_path) -> None:
    class DerivedLedger(DisconnectedAtomicPreactionLedger):
        pass

    path = tmp_path / "subclass.sqlite3"
    with pytest.raises(AtomicPreactionRejected, match="exact atomic pre-action ledger"):
        DerivedLedger.create(path)

    assert not path.exists()
