"""READ manifest must prove actual post-publication file bytes, not only inode.

Synthetic temporary artifacts only. A failed verification remains UNKNOWN and
must not trigger cleanup, an automatic write retry, or backend execution.
"""

from __future__ import annotations

import os

import pytest

from ark.agency import disconnected_read_input_manifest as manifest

_REQUEST = "req_" + "a" * 32
_INPUTS = (("step_" + "1" * 16, "b" * 64),)


def test_successful_publication_reopens_named_bytes_on_every_platform(
    tmp_path, monkeypatch,
):
    target = tmp_path / "read-input.json"
    opened = []
    native = os.open

    def tracked(path, flags, *args, **kwargs):
        if os.fspath(path) == os.fspath(target):
            opened.append("write" if flags & os.O_WRONLY else "read")
        return native(path, flags, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(manifest.os, "open", tracked)
        result = manifest.write_read_input_manifest_once(
            target, _REQUEST, _INPUTS,
        )
    assert opened == ["write", "read"]
    assert manifest.load_read_input_manifest(
        target, expected_sha256=result.artifact_sha256,
    ) == result
    assert result.backend_dispatched is False
    assert result.automatic_replay_authorized is False


def test_failed_postpublication_read_quarantines_existing_file(
    tmp_path, monkeypatch,
):
    target = tmp_path / "read-input.json"
    native = os.fdopen
    attempted = []

    def unreadable(fd, mode="r", *args, **kwargs):
        if mode == "rb":
            attempted.append("readback")
            os.close(fd)  # Do not leak an open descriptor on Windows runners.
            raise OSError("injected post-publication read error")
        return native(fd, mode, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(manifest.os, "fdopen", unreadable)
        with pytest.raises(
            manifest.ReadInputManifestRejected,
            match="publication cannot be verified",
        ):
            manifest.write_read_input_manifest_once(target, _REQUEST, _INPUTS)
    assert attempted == ["readback"]
    assert target.is_file()
    first = target.read_bytes()
    with pytest.raises(
        manifest.ReadInputManifestRejected, match="creation refused",
    ):
        manifest.write_read_input_manifest_once(target, _REQUEST, _INPUTS)
    assert target.read_bytes() == first
    assert manifest.load_read_input_manifest(
        target,
    ).independent_custody_proven is False


def test_same_length_rewrite_during_publication_never_issues_receipt(
    tmp_path, monkeypatch,
):
    target = tmp_path / "read-input.json"
    native_sync = manifest._sync_created_manifest_directory
    observed = []

    def corrupt(path):
        payload = path.read_bytes()
        altered = b"X" + payload[1:]
        assert len(altered) == len(payload)
        path.write_bytes(altered)
        observed.append((payload, altered))
        native_sync(path)

    with monkeypatch.context() as patch:
        patch.setattr(manifest, "_sync_created_manifest_directory", corrupt)
        with pytest.raises(
            manifest.ReadInputManifestRejected,
            match="changed during publication",
        ):
            manifest.write_read_input_manifest_once(target, _REQUEST, _INPUTS)
    assert len(observed) == 1
    assert target.read_bytes() == observed[0][1]
    with pytest.raises(manifest.ReadInputManifestRejected):
        manifest.load_read_input_manifest(target)
