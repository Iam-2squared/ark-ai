"""Detached expected READ inputs refuse mutable format and parser authority.

Only disposable local manifest files are used. Rejection never grants live
execution, independent provenance, or automatic replay.
"""

from __future__ import annotations

import re

import pytest

from ark.agency import disconnected_read_input_manifest as manifest

REQUEST = "req_" + "a" * 32
STEP = "step_" + "1" * 16
INPUTS = ((STEP, "b" * 64),)


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("_SCHEMA", "ark.synthetic.read.input.manifest.unreviewed"),
        ("_DOMAIN", b"ARK-unreviewed-digest-domain\\0"),
        ("_MAX_BYTES", 8193),
        ("_MAX_STEPS", 25),
        ("_REQUEST", re.compile(r"req_.*\\Z")),
        ("_STEP", re.compile(r"step_.*\\Z")),
        ("_SHA", re.compile(r".*\\Z")),
    ),
)
@pytest.mark.parametrize("operation", ("write", "load"))
def test_mutable_format_contract_refused_before_file_access(
    tmp_path, monkeypatch, operation, name, replacement,
):
    target = tmp_path / "expected.json"
    if operation == "load":
        saved = manifest.write_read_input_manifest_once(target, REQUEST, INPUTS)
        original = target.read_bytes()
    else:
        saved = None
        original = None
    called = []
    real_open = manifest.os.open

    def watch_open(*args, **kwargs):
        called.append("filesystem")
        return real_open(*args, **kwargs)

    monkeypatch.setattr(manifest, name, replacement)
    monkeypatch.setattr(manifest.os, "open", watch_open)
    with pytest.raises(
        manifest.ReadInputManifestRejected,
        match="READ input manifest authority changed",
    ):
        if operation == "write":
            manifest.write_read_input_manifest_once(target, REQUEST, INPUTS)
        else:
            manifest.load_read_input_manifest(
                target, expected_sha256=saved.artifact_sha256,
            )
    assert called == []
    if operation == "write":
        assert not target.exists()
    else:
        assert target.read_bytes() == original


def test_format_rebinding_during_publication_quarantines_created_file(
    tmp_path, monkeypatch,
):
    target = tmp_path / "published_unknown.json"
    sync = manifest._sync_created_manifest_directory

    def mutate_after_write(path):
        sync(path)
        monkeypatch.setattr(manifest, "_DOMAIN", b"unreviewed-after-write\\0")

    monkeypatch.setattr(manifest, "_sync_created_manifest_directory", mutate_after_write)
    with pytest.raises(
        manifest.ReadInputManifestRejected,
        match="READ input manifest authority changed",
    ):
        manifest.write_read_input_manifest_once(target, REQUEST, INPUTS)
    # No untrusted implicit unlink/retry of a possibly published artifact.
    assert target.is_file()
    data = target.read_bytes()
    with pytest.raises(manifest.ReadInputManifestRejected):
        manifest.write_read_input_manifest_once(target, REQUEST, INPUTS)
    assert target.read_bytes() == data
