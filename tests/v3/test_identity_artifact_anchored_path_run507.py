"""A local V3 artifact may only be verified through an anchored bounded path."""

import hashlib
from pathlib import Path

import pytest

from ark.learning.execution import canonical_json
from ark.learning.identity_artifact_verify import (
    LocalIdentityArtifactRejected,
    verify_local_identity_artifact,
)


def test_absolute_existing_identity_stays_valid(tmp_path):
    path = tmp_path / "artifact.json"
    raw = canonical_json({"model": "fixture", "revision": 1})
    path.write_bytes(raw)
    witness = verify_local_identity_artifact(
        path, retained_sha256=hashlib.sha256(raw).hexdigest(),
    )
    assert witness.top_level_keys == ("model", "revision")
    assert witness.training_authorized is False


def test_relative_existing_artifact_is_not_an_identity_anchor(tmp_path, monkeypatch):
    path = tmp_path / "artifact.json"
    raw = canonical_json({"model": "fixture"})
    path.write_bytes(raw)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(LocalIdentityArtifactRejected, match="exact local path"):
        verify_local_identity_artifact(
            Path("artifact.json"),
            retained_sha256=hashlib.sha256(raw).hexdigest(),
        )


@pytest.mark.parametrize(
    "path",
    [
        Path("/" + "a" * 4100),
        Path("/tmp/folder/../artifact.json"),
    ],
)
def test_oversized_or_dotdot_artifact_path_is_denied(path):
    with pytest.raises(LocalIdentityArtifactRejected, match="exact local path"):
        verify_local_identity_artifact(path, retained_sha256="a" * 64)
