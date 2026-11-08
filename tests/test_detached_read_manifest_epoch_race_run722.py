"""Detached READ manifest load rejects concurrent same-size inode-epoch drift.

These simulated changes are local metadata signals, not authenticated custody
or proof of backend READ execution; never automatically replay a READ.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_read_input_manifest as manifest

REQUEST = "req_" + "a" * 32
INPUTS = (("step_" + "1" * 16, "b" * 64),)


class _ChangedStat:
    def __init__(self, original, changed_field):
        self._original = original
        self._changed_field = changed_field

    def __getattr__(self, name):
        value = getattr(self._original, name)
        if name == self._changed_field:
            return value + 1_000_000_000
        return value


@pytest.mark.parametrize("changed_field", ("st_mtime_ns", "st_ctime_ns"))
def test_same_inode_size_with_changed_fstat_epoch_is_rejected(
    tmp_path, monkeypatch, changed_field,
):
    target = tmp_path / "read-manifest.json"
    saved = manifest.write_read_input_manifest_once(target, REQUEST, INPUTS)
    untouched = target.read_bytes()
    original = manifest.os.fstat
    calls = []

    def fstat_with_concurrent_rewrite(fd):
        result = original(fd)
        calls.append(True)
        if len(calls) == 2:
            return _ChangedStat(result, changed_field)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(manifest.os, "fstat", fstat_with_concurrent_rewrite)
        with pytest.raises(
            manifest.ReadInputManifestRejected, match="changed during read",
        ):
            manifest.load_read_input_manifest(
                target, expected_sha256=saved.artifact_sha256,
            )

    assert len(calls) == 2
    assert target.read_bytes() == untouched
    assert manifest.load_read_input_manifest(target) == saved
    assert saved.automatic_replay_authorized is False


@pytest.mark.parametrize("changed_field", ("st_mtime_ns", "st_ctime_ns"))
def test_named_file_metadata_change_after_read_is_rejected(
    tmp_path, monkeypatch, changed_field,
):
    target = tmp_path / "read-manifest.json"
    saved = manifest.write_read_input_manifest_once(target, REQUEST, INPUTS)
    original_stat = manifest.Path.stat
    substituted = []

    def late_named_stat(self, *args, **kwargs):
        original = original_stat(self, *args, **kwargs)
        if self == target and kwargs.get("follow_symlinks") is False:
            substituted.append(True)
            # First named observation is the baseline; change only the late
            # named observation. This models an actual read-time rewrite on
            # Windows, where descriptor and path creation epochs may differ.
            if len(substituted) >= 2:
                return _ChangedStat(original, changed_field)
        return original

    with monkeypatch.context() as patch:
        patch.setattr(manifest.Path, "stat", late_named_stat)
        with pytest.raises(
            manifest.ReadInputManifestRejected, match="changed during read",
        ):
            manifest.load_read_input_manifest(
                target, expected_sha256=saved.artifact_sha256,
            )

    # A real after-baseline metadata race must be observed and refused.
    assert len(substituted) >= 2
    assert manifest.load_read_input_manifest(target) == saved
    assert saved.independent_custody_proven is False
    assert saved.external_result_proven is False
