"""Offline V3 file manifests must not enumerate or serialize unbounded names."""

from __future__ import annotations

import pytest

import ark.learning.identity as identity


def test_small_local_snapshot_is_deterministic(tmp_path):
    (tmp_path / "sample.txt").write_text("free local fixture", encoding="utf-8")
    first = identity.directory_file_identities(tmp_path)
    assert first == identity.directory_file_identities(tmp_path)
    assert [item.path for item in first] == ["sample.txt"]
    assert first[0].bytes == len(b"free local fixture")


def test_snapshot_enumeration_limit_applies_before_sorting(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_bytes(b"a")
    (tmp_path / "b.txt").write_bytes(b"b")
    monkeypatch.setattr(identity, "_MAX_SNAPSHOT_ENTRIES", 1)
    with pytest.raises(ValueError, match="entry count"):
        identity.directory_file_identities(tmp_path)


def test_snapshot_relative_path_budget(tmp_path, monkeypatch):
    (tmp_path / "too_long.txt").write_bytes(b"a")
    monkeypatch.setattr(identity, "_MAX_SNAPSHOT_PATH_BYTES", 8)
    with pytest.raises(ValueError, match="relative path"):
        identity.directory_file_identities(tmp_path)


@pytest.mark.parametrize("label", ["\ud800", "é" * 2100])
def test_manifest_label_rejects_invalid_or_oversized_utf8(
    tmp_path, label,
):
    artifact = tmp_path / "weights.txt"
    artifact.write_bytes(b"fixture only")
    with pytest.raises(ValueError, match="identity label"):
        identity.file_identity(artifact, label=label)
