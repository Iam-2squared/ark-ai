"""Malformed Windows reparse metadata must not become a permissive export path."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import export_plan


@pytest.mark.parametrize("attributes", (True, None, "1024", 1024.0))
def test_malformed_reparse_attribute_carrier_fails_closed(attributes):
    metadata = SimpleNamespace(
        st_mode=stat.S_IFDIR | 0o755,
        st_file_attributes=attributes,
    )
    with pytest.raises(ValueError, match="reparse metadata is malformed"):
        export_plan._is_reparse_point(metadata)


def test_absent_platform_attribute_uses_non_reparse_default():
    metadata = SimpleNamespace(st_mode=stat.S_IFDIR | 0o755)
    assert export_plan._is_reparse_point(metadata) is False


def test_directory_admission_rejects_malformed_ancestor_before_resolution(
    tmp_path, monkeypatch,
):
    root = tmp_path / "model"
    root.mkdir()
    original_lstat = Path.lstat

    def lstat(path):
        if path == tmp_path:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR | 0o755,
                st_file_attributes="unknown",
            )
        return original_lstat(path)

    def forbidden_resolve(*args, **kwargs):
        raise AssertionError("export path resolved after malformed ancestry")

    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(Path, "resolve", forbidden_resolve)
    with pytest.raises(ValueError, match="reparse metadata is malformed"):
        export_plan._canonical_existing_directory(root, "base_dir")
