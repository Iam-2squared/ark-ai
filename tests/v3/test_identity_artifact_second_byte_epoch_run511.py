"""V3 local JSON identity witnesses must survive a final actual byte rehash."""

import hashlib
import os
from pathlib import Path

import pytest

import ark.learning.identity_artifact_verify as mod
from ark.learning.execution import canonical_json


def _fixture(tmp_path):
    path = (tmp_path / "identity.json").resolve()
    data = canonical_json({"revision": "alpha"})
    path.write_bytes(data)
    return path, data, hashlib.sha256(data).hexdigest()


def test_clean_pinned_local_json_remains_readonly_and_denial_only(tmp_path):
    path, data, digest = _fixture(tmp_path)
    one = mod.verify_local_identity_artifact(path, retained_sha256=digest)
    two = mod.verify_local_identity_artifact(path, retained_sha256=digest)
    assert one == two
    assert one.artifact_sha256 == digest
    assert one.artifact_bytes == len(data)
    assert one.source_authenticated is False
    assert one.training_authorized is False
    assert one.candidate_generation_authorized is False
    assert one.protected_evaluation_authorized is False
    assert path.read_bytes() == data


@pytest.mark.parametrize("replacement", (b"bravo", b"delta"))
def test_constructor_same_size_rewrite_with_restored_mtime_is_rejected(
    tmp_path, monkeypatch, replacement,
):
    path, data, digest = _fixture(tmp_path)
    changed = data.replace(b"alpha", replacement)
    assert changed != data and len(changed) == len(data)
    initial = path.stat()
    original_init = mod.LocalIdentityArtifactWitness.__init__

    def rewrite_after_first_verified_read(self, *args):
        original_init(self, *args)
        path.write_bytes(changed)
        os.utime(path, ns=(initial.st_atime_ns, initial.st_mtime_ns))

    monkeypatch.setattr(
        mod.LocalIdentityArtifactWitness, "__init__", rewrite_after_first_verified_read,
    )
    with pytest.raises(mod.LocalIdentityArtifactRejected, match="bytes changed"):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)
    assert path.read_bytes() == changed


def test_second_byte_recheck_refuses_unavailable_file(tmp_path, monkeypatch):
    path, _, digest = _fixture(tmp_path)
    original_open = Path.open
    calls = 0

    def refuse_second_open(self, *args, **kwargs):
        nonlocal calls
        if self == path:
            calls += 1
            if calls == 2:
                raise OSError("simulated local file disappearance")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", refuse_second_open)
    with pytest.raises(mod.LocalIdentityArtifactRejected, match="final byte recheck"):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)
    assert calls == 2


def test_second_byte_recheck_refuses_truncated_file(tmp_path, monkeypatch):
    path, data, digest = _fixture(tmp_path)
    original_init = mod.LocalIdentityArtifactWitness.__init__
    initial = path.stat()

    def truncate_late(self, *args):
        original_init(self, *args)
        path.write_bytes(data[:-1])
        os.utime(path, ns=(initial.st_atime_ns, initial.st_mtime_ns))

    monkeypatch.setattr(
        mod.LocalIdentityArtifactWitness, "__init__", truncate_late,
    )
    with pytest.raises(mod.LocalIdentityArtifactRejected):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)


def test_second_read_preserves_local_artifact_path_identity(tmp_path):
    path, data, digest = _fixture(tmp_path)
    report = mod.verify_local_identity_artifact(path, retained_sha256=digest)
    assert report.top_level_keys == ("revision",)
    assert report.artifact_bytes == len(data)
    assert path.is_file()
    assert path.read_bytes() == data


def test_invalid_retained_checksum_fails_before_attempting_to_read(tmp_path):
    path, data, _ = _fixture(tmp_path)
    with pytest.raises(mod.LocalIdentityArtifactRejected):
        mod.verify_local_identity_artifact(path, retained_sha256="0" * 64)
    assert path.read_bytes() == data
