"""Regression: fixture veto SQLite paths may not traverse symbolic ancestors."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
    genesis_privacy_veto_witness,
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


def test_regular_nested_fixture_still_opens(tmp_path: Path) -> None:
    (tmp_path / "real" / "deep").mkdir(parents=True)
    store = DisconnectedPrivacyVetoLedger(tmp_path / "real" / "deep" / "veto.db")
    assert store.witness() == genesis_privacy_veto_witness()


def test_nested_symbolic_ancestor_refused_before_creation(tmp_path: Path) -> None:
    real, alias = _fixture_tree(tmp_path)
    redirected = alias / "deep" / "veto.db"
    assert not (real / "deep" / "veto.db").exists()
    with pytest.raises(OfflinePrivacyVetoRejected):
        DisconnectedPrivacyVetoLedger(redirected)
    assert not (real / "deep" / "veto.db").exists()


def test_nested_symbolic_ancestor_refused_on_reopen(tmp_path: Path) -> None:
    real, alias = _fixture_tree(tmp_path)
    store = DisconnectedPrivacyVetoLedger(real / "deep" / "veto.db")
    object.__setattr__(store, "_path", alias / "deep" / "veto.db")
    with pytest.raises(OfflinePrivacyVetoRejected):
        store.witness()


def test_lexical_parent_escape_refused(tmp_path: Path) -> None:
    (tmp_path / "real").mkdir()
    redirect = tmp_path / "real" / ".." / "veto.db"
    with pytest.raises(OfflinePrivacyVetoRejected):
        DisconnectedPrivacyVetoLedger(redirect)
    assert not (tmp_path / "veto.db").exists()
