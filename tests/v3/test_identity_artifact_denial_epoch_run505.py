"""Local V3 artifact witnesses stay inert after their final denial getter."""

import hashlib
from pathlib import Path

import pytest

import ark.learning.identity_artifact_verify as mod
from ark.learning.execution import canonical_json


def fixture(tmp_path: Path):
    path = tmp_path / "artifact.json"
    raw = canonical_json({"revision": "local-only"})
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("field,value", [
    ("artifact_sha256", "f" * 64),
    ("artifact_bytes", 99),
    ("artifact_bytes", True),
    ("top_level_keys", ("forged",)),
    ("top_level_keys", ["revision"]),
])
def test_final_denial_cannot_change_witness_fields(
    tmp_path, monkeypatch, field, value,
):
    path, digest = fixture(tmp_path)

    def denial(self):
        object.__setattr__(self, field, value)
        return False

    monkeypatch.setattr(
        mod.LocalIdentityArtifactWitness,
        "protected_evaluation_authorized", property(denial),
    )
    with pytest.raises(mod.LocalIdentityArtifactRejected, match="after authority"):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)


def test_final_denial_cannot_change_file_after_custody_read(tmp_path, monkeypatch):
    path, digest = fixture(tmp_path)

    def denial(_self):
        path.write_bytes(canonical_json({"changed": True}))
        return False

    monkeypatch.setattr(
        mod.LocalIdentityArtifactWitness,
        "protected_evaluation_authorized", property(denial),
    )
    with pytest.raises(mod.LocalIdentityArtifactRejected, match="changed after"):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)


def test_unchanged_artifact_witness_has_no_training_grant(tmp_path):
    path, digest = fixture(tmp_path)
    before = path.read_bytes()
    report = mod.verify_local_identity_artifact(path, retained_sha256=digest)
    assert report.artifact_sha256 == digest
    assert report.training_authorized is False
    assert report.candidate_generation_authorized is False
    assert report.protected_evaluation_authorized is False
    assert path.read_bytes() == before
