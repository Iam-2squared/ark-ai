"""Run501 local identity custody checks, including post-read filesystem races.

Class rebinding now denies earlier, so path-race probes use the unmodified
witness type and a deterministic parse callback. No GPU, Candidate or training.
"""

import hashlib
import os

import pytest

import ark.learning.identity_artifact_verify as mod
from ark.learning.execution import canonical_json


def fixture(tmp_path):
    path = tmp_path / "identity.json"
    raw = canonical_json({"code_manifest_sha256": "a" * 64})
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest()


def test_unchanged_exact_path_still_verifies(tmp_path):
    path, digest = fixture(tmp_path)
    witness = mod.verify_local_identity_artifact(path, retained_sha256=digest)
    assert witness.artifact_sha256 == digest
    assert witness.artifact_bytes == path.stat().st_size
    assert witness.source_authenticated is False
    assert witness.training_authorized is False
    assert witness.candidate_generation_authorized is False
    assert witness.protected_evaluation_authorized is False


def test_path_replaced_during_witness_creation_is_rejected(tmp_path, monkeypatch):
    path, digest = fixture(tmp_path)
    original_canonical = mod.canonical_json

    def replace_after_read(parsed):
        path.rename(tmp_path / "old.json")
        path.write_bytes(canonical_json({"code_manifest_sha256": "b" * 64}))
        return original_canonical(parsed)

    monkeypatch.setattr(mod, "canonical_json", replace_after_read)
    with pytest.raises(mod.LocalIdentityArtifactRejected, match="changed after"):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)


def test_path_renamed_during_witness_creation_is_rejected(tmp_path, monkeypatch):
    path, digest = fixture(tmp_path)
    original_canonical = mod.canonical_json

    def rename_after_read(parsed):
        path.rename(tmp_path / "moved.json")
        return original_canonical(parsed)

    monkeypatch.setattr(mod, "canonical_json", rename_after_read)
    with pytest.raises(mod.LocalIdentityArtifactRejected, match="unavailable"):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)


def test_mtime_changed_after_parse_even_if_bytes_same_rejected(tmp_path, monkeypatch):
    path, digest = fixture(tmp_path)
    original_canonical = mod.canonical_json

    def touch_after_read(parsed):
        prior = path.stat()
        os.utime(path, ns=(prior.st_atime_ns, prior.st_mtime_ns + 2_000_000_000))
        return original_canonical(parsed)

    monkeypatch.setattr(mod, "canonical_json", touch_after_read)
    with pytest.raises(mod.LocalIdentityArtifactRejected, match="changed after"):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)


def test_subclass_witness_constructor_is_rejected(tmp_path, monkeypatch):
    path, digest = fixture(tmp_path)
    saved_type = mod.LocalIdentityArtifactWitness

    class ForgedWitness(saved_type):
        pass

    monkeypatch.setattr(mod, "LocalIdentityArtifactWitness", ForgedWitness)
    with pytest.raises(
        mod.LocalIdentityArtifactRejected, match="authority definition changed",
    ):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)


@pytest.mark.parametrize("field", [
    "source_authenticated",
    "training_authorized",
    "candidate_generation_authorized",
    "protected_evaluation_authorized",
])
def test_preinstalled_witness_authority_substitution_is_quarantined(tmp_path, monkeypatch, field):
    path, digest = fixture(tmp_path)
    monkeypatch.setattr(
        mod.LocalIdentityArtifactWitness, field, property(lambda self: True),
    )
    with pytest.raises(mod.LocalIdentityArtifactRejected, match="authority definition changed"):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)


def test_forged_exact_type_witness_fields_are_rejected(tmp_path, monkeypatch):
    path, digest = fixture(tmp_path)
    saved_type = mod.LocalIdentityArtifactWitness

    original_init = saved_type.__init__

    def corrupt_exact_type(self, *args):
        original_init(self, *args)
        object.__setattr__(self, "artifact_sha256", "f" * 64)

    monkeypatch.setattr(saved_type, "__init__", corrupt_exact_type)
    with pytest.raises(mod.LocalIdentityArtifactRejected, match="witness changed"):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)
