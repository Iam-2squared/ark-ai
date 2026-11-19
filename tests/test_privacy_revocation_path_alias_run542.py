"""Synthetic privacy-veto SQLite files must not follow obvious path aliases.

These are fixture path checks, not authenticated custody, secure erasure or
permission to disclose personal data. Files owned by tests are left intact.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope

from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def test_revocation_open_rejects_symlink_to_ordinary_file(tmp_path):
    original = tmp_path / "owned.txt"
    original.write_text("do not alter", encoding="utf-8")
    alias = tmp_path / "veto.sqlite"
    try:
        alias.symlink_to(original)
    except OSError:
        pytest.skip("symlinks unavailable on this runner")
    with pytest.raises(SyntheticContextRevocationRejected, match="symlink"):
        SyntheticContextRevocationLedger(alias)
    assert original.read_text(encoding="utf-8") == "do not alter"


def test_revocation_create_rejects_symlinked_ancestor(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(actual, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks unavailable on this runner")
    forbidden = actual / "veto.sqlite"
    with pytest.raises(SyntheticContextRevocationRejected, match="ancestor"):
        SyntheticContextRevocationLedger(alias / "veto.sqlite")
    assert not forbidden.exists()


def test_revocation_open_rejects_existing_hardlink_alias(tmp_path):
    original = tmp_path / "original.sqlite"
    SyntheticContextRevocationLedger(original)
    alias = tmp_path / "alias.sqlite"
    try:
        alias.hardlink_to(original)
    except OSError:
        pytest.skip("hardlinks unavailable on this runner")
    before = original.read_bytes()
    with pytest.raises(SyntheticContextRevocationRejected, match="regular-file link"):
        SyntheticContextRevocationLedger(alias)
    assert original.read_bytes() == before


def test_nonaliased_existing_revocation_database_remains_reopenable(tmp_path):
    original = tmp_path / "veto.sqlite"
    first = SyntheticContextRevocationLedger(original)
    reopened = SyntheticContextRevocationLedger(original)
    assert first.path == reopened.path
    assert original.is_file()


@pytest.mark.parametrize("relative", (False, True))
@pytest.mark.parametrize("existing_required", (False, True))
def test_revocation_traversal_denied_before_database_access(
    tmp_path, monkeypatch, relative, existing_required,
):
    from pathlib import Path

    folder = tmp_path / "sub"
    folder.mkdir()
    target = tmp_path / "veto.sqlite"
    if relative:
        monkeypatch.chdir(tmp_path)
        untrusted = Path("sub") / ".." / "veto.sqlite"
    else:
        untrusted = folder / ".." / "veto.sqlite"
    with pytest.raises(SyntheticContextRevocationRejected, match="traversal"):
        SyntheticContextRevocationLedger(
            untrusted, require_existing=existing_required,
        )
    assert not target.exists()


def test_nonaliased_relative_revocation_path_still_bootstraps(tmp_path, monkeypatch):
    from pathlib import Path

    monkeypatch.chdir(tmp_path)
    path = Path("relative-veto.sqlite")
    ledger = SyntheticContextRevocationLedger(path)
    assert path.is_file()
    ledger.assert_not_revoked((MemoryScope("offline-owner", "private"),))
