"""V3 identity readers pin import-original filesystem mode predicates."""

from __future__ import annotations

import hashlib
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.learning.identity as identity
import ark.learning.identity_artifact_verify as artifact
from ark.learning.execution import canonical_json


def _artifact(path: Path) -> str:
    raw = canonical_json({"fixture": "identity-only"})
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def test_identity_stat_module_rebinding_is_rejected_before_lstat(tmp_path, monkeypatch):
    payload = tmp_path / "identity.bin"
    payload.write_bytes(b"synthetic identity")

    monkeypatch.setattr(identity, "stat", SimpleNamespace())

    def forbidden_lstat(path):
        raise AssertionError("identity path inspected after stat module substitution")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(ValueError, match="reparse-point policy changed"):
        identity.file_identity(payload)


@pytest.mark.parametrize("predicate", ("S_ISDIR", "S_ISREG", "S_ISLNK"))
def test_identity_stat_predicate_rebinding_is_rejected_before_lstat(
    tmp_path, monkeypatch, predicate,
):
    payload = tmp_path / "identity.bin"
    payload.write_bytes(b"synthetic identity")
    monkeypatch.setattr(identity.stat, predicate, lambda mode: False)

    def forbidden_lstat(path):
        raise AssertionError("identity path inspected after stat predicate substitution")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(ValueError, match="reparse-point policy changed"):
        identity.file_identity(payload)


def test_identity_reparse_metadata_callback_cannot_replace_stat_predicate(monkeypatch):
    class MutatingMetadata:
        @property
        def st_file_attributes(self):
            monkeypatch.setattr(identity.stat, "S_ISLNK", lambda mode: False)
            return 0

        @property
        def st_mode(self):
            return stat.S_IFREG | 0o600

    with pytest.raises(ValueError, match="reparse-point policy changed"):
        identity._is_reparse_point(MutatingMetadata())


@pytest.mark.parametrize(
    ("helper", "predicate", "mode"),
    (
        (identity._is_directory, "S_ISDIR", stat.S_IFDIR | 0o700),
        (identity._is_regular_file, "S_ISREG", stat.S_IFREG | 0o600),
    ),
)
def test_identity_mode_metadata_callback_cannot_replace_stat_predicate(
    monkeypatch, helper, predicate, mode,
):
    class MutatingMetadata:
        @property
        def st_mode(self):
            monkeypatch.setattr(identity.stat, predicate, lambda value: False)
            return mode

    with pytest.raises(ValueError, match="reparse-point policy changed"):
        helper(MutatingMetadata())


def test_artifact_stat_module_rebinding_is_rejected_before_lstat(tmp_path, monkeypatch):
    path = tmp_path / "identity.json"
    digest = _artifact(path)
    monkeypatch.setattr(artifact, "stat", SimpleNamespace())

    def forbidden_lstat(candidate):
        raise AssertionError("artifact path inspected after stat module substitution")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(
        artifact.LocalIdentityArtifactRejected, match="stat policy changed",
    ):
        artifact.verify_local_identity_artifact(path, retained_sha256=digest)


@pytest.mark.parametrize("predicate", ("S_ISREG", "S_ISLNK"))
def test_artifact_stat_predicate_rebinding_is_rejected_before_lstat(
    tmp_path, monkeypatch, predicate,
):
    path = tmp_path / "identity.json"
    digest = _artifact(path)
    monkeypatch.setattr(artifact.stat, predicate, lambda mode: False)

    def forbidden_lstat(candidate):
        raise AssertionError("artifact path inspected after stat predicate substitution")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(
        artifact.LocalIdentityArtifactRejected, match="stat policy changed",
    ):
        artifact.verify_local_identity_artifact(path, retained_sha256=digest)


@pytest.mark.parametrize("predicate", ("S_ISREG", "S_ISLNK"))
def test_artifact_path_metadata_callback_cannot_replace_stat_predicate(
    tmp_path, monkeypatch, predicate,
):
    path = tmp_path / "identity.json"
    digest = _artifact(path)
    original_lstat = Path.lstat

    class MutatingMetadata:
        @property
        def st_mode(self):
            monkeypatch.setattr(artifact.stat, predicate, lambda mode: False)
            return stat.S_IFREG | 0o600

    def lstat(candidate):
        if candidate == path:
            return MutatingMetadata()
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        artifact.LocalIdentityArtifactRejected, match="stat policy changed",
    ):
        artifact.verify_local_identity_artifact(path, retained_sha256=digest)
