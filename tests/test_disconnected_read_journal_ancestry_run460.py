"""READ evidence journal path ancestry must remain local and non-symbolic."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    genesis_witness,
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


def test_regular_nested_read_journal_still_works(tmp_path: Path) -> None:
    path = tmp_path / "real" / "deep" / "read.db"
    path.parent.mkdir(parents=True)
    with DisconnectedReadJournal.create(path) as journal:
        assert journal.verify(genesis_witness()) == genesis_witness()
    with DisconnectedReadJournal.open(path) as reopened:
        assert reopened.verify(genesis_witness()) == genesis_witness()


def test_nested_symbolic_ancestor_refused_before_journal_creation(tmp_path: Path) -> None:
    real, alias = _fixture_tree(tmp_path)
    redirected = alias / "deep" / "read.db"
    with pytest.raises(ReadJournalRejected):
        DisconnectedReadJournal.create(redirected)
    assert not (real / "deep" / "read.db").exists()


def test_nested_symbolic_ancestor_refused_for_existing_read_journal(tmp_path: Path) -> None:
    real, alias = _fixture_tree(tmp_path)
    with DisconnectedReadJournal.create(real / "deep" / "read.db"):
        pass
    with pytest.raises(ReadJournalRejected):
        DisconnectedReadJournal.open(alias / "deep" / "read.db")


def test_lexical_parent_escape_refused_before_creation(tmp_path: Path) -> None:
    (tmp_path / "real").mkdir()
    redirect = tmp_path / "real" / ".." / "read.db"
    with pytest.raises(ReadJournalRejected):
        DisconnectedReadJournal.create(redirect)
    assert not (tmp_path / "read.db").exists()
