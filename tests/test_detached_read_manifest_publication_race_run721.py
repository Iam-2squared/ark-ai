"""Write-once expected READ input receipts must name the artifact just published.

All scenarios operate only on synthetic temporary files. A failed publication
is UNKNOWN, not permission to retry, remove evidence, or dispatch a READ.
"""

from __future__ import annotations

import os

import pytest

from ark.agency import disconnected_read_input_manifest as manifest

REQUEST = "req_" + "a" * 32
STEP = "step_" + "1" * 16
INPUTS = ((STEP, "b" * 64),)


def test_renamed_during_publication_refuses_successful_receipt(tmp_path, monkeypatch):
    target = tmp_path / "expected.json"
    moved = tmp_path / "quarantined.json"
    original_sync = manifest._sync_created_manifest_directory

    def rename_during_sync(path):
        os.rename(path, moved)
        original_sync(path)

    monkeypatch.setattr(manifest, "_sync_created_manifest_directory", rename_during_sync)
    with pytest.raises(
        manifest.ReadInputManifestRejected, match="publication cannot be verified",
    ):
        manifest.write_read_input_manifest_once(target, REQUEST, INPUTS)
    assert not target.exists()
    assert moved.is_file()
    assert manifest.load_read_input_manifest(moved).automatic_replay_authorized is False


def test_overwritten_during_publication_refuses_successful_receipt(
    tmp_path, monkeypatch,
):
    target = tmp_path / "expected.json"
    original_sync = manifest._sync_created_manifest_directory

    def overwrite_during_sync(path):
        path.write_bytes(b"synthetic corrupted publication")
        original_sync(path)

    monkeypatch.setattr(manifest, "_sync_created_manifest_directory", overwrite_during_sync)
    with pytest.raises(
        manifest.ReadInputManifestRejected, match="changed during publication",
    ):
        manifest.write_read_input_manifest_once(target, REQUEST, INPUTS)
    assert target.read_bytes() == b"synthetic corrupted publication"
    with pytest.raises(manifest.ReadInputManifestRejected):
        manifest.load_read_input_manifest(target)


def test_no_publication_swap_still_returns_a_deny_only_bound_manifest(tmp_path):
    target = tmp_path / "expected.json"
    written = manifest.write_read_input_manifest_once(target, REQUEST, INPUTS)
    reopened = manifest.load_read_input_manifest(
        target, expected_sha256=written.artifact_sha256,
    )
    assert written == reopened
    assert reopened.backend_dispatched is False
    assert reopened.independent_custody_proven is False
    assert reopened.automatic_replay_authorized is False
    assert reopened.external_result_proven is False
