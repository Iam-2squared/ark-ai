"""Disallow symlink-grandparent and dot-dot paths for due-slot fixture ledgers."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationRejected,
    genesis_due_witness,
)


def _fixture_tree(tmp_path: Path) -> tuple[Path, Path]:
    real = tmp_path / "real"
    (real / "deep").mkdir(parents=True)
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"directory symlink unavailable: {exc}")
    return real, alias


def test_nested_real_source_can_reserve_without_dispatch(tmp_path: Path) -> None:
    (tmp_path / "real" / "deep").mkdir(parents=True)
    store = DisconnectedDueReservations(tmp_path / "real" / "deep" / "due.db")
    witness = store.witness()
    assert witness == genesis_due_witness()
    receipt = store.reserve_due(
        policy_sha256="a" * 64,
        due_at_ms=1_000,
        observed_now_ms=1_001,
        retained=witness,
    )
    assert not receipt.execution_authorized
    assert not receipt.notification_authorized


def test_nested_symbolic_ancestor_refused_before_creation(tmp_path: Path) -> None:
    real, alias = _fixture_tree(tmp_path)
    redirected = alias / "deep" / "due.db"
    with pytest.raises(DueReservationRejected):
        DisconnectedDueReservations(redirected)
    assert not (real / "deep" / "due.db").exists()


def test_nested_symbolic_ancestor_refused_on_reopen(tmp_path: Path) -> None:
    real, alias = _fixture_tree(tmp_path)
    store = DisconnectedDueReservations(real / "deep" / "due.db")
    object.__setattr__(store, "_path", alias / "deep" / "due.db")
    with pytest.raises(DueReservationRejected):
        store.witness()


def test_lexical_parent_escape_refused(tmp_path: Path) -> None:
    (tmp_path / "real").mkdir()
    redirect = tmp_path / "real" / ".." / "due.db"
    with pytest.raises(DueReservationRejected):
        DisconnectedDueReservations(redirect)
    assert not (tmp_path / "due.db").exists()
