"""V3 local identity witness class substitution is denied before disk reads.

Passive synthetic JSON only: no GPU, Candidate, approval or external action.
"""

import hashlib

import pytest

import ark.learning.identity_artifact_verify as identity
from ark.learning.execution import canonical_json


@pytest.mark.parametrize("replacement", ("object", "counterfeit"))
def test_rebound_identity_witness_class_refused_before_file_read(
    tmp_path, monkeypatch, replacement,
):
    path = tmp_path / "fixture.json"
    raw = canonical_json({"revision": "synthetic"})
    path.write_bytes(raw)
    original = identity._WITNESS_TYPE
    called = []

    class Counterfeit:
        def __init__(self, *args, **kwargs):
            called.append("constructor")
            raise AssertionError("counterfeit constructor must never be called")

        source_authenticated = property(lambda self: False)
        training_authorized = property(lambda self: False)
        candidate_generation_authorized = property(lambda self: False)
        protected_evaluation_authorized = property(lambda self: False)

    def no_stat(self, *args, **kwargs):
        called.append("filesystem")
        raise AssertionError("no local file access before class validation")

    monkeypatch.setattr(
        identity, "LocalIdentityArtifactWitness",
        object if replacement == "object" else Counterfeit,
    )
    monkeypatch.setattr(type(path), "lstat", no_stat)
    with pytest.raises(
        identity.LocalIdentityArtifactRejected, match="authority definition changed",
    ):
        identity.verify_local_identity_artifact(
            path, retained_sha256=hashlib.sha256(raw).hexdigest(),
        )
    assert called == []
    assert identity._WITNESS_TYPE is original


def test_original_class_retains_no_authority(tmp_path):
    path = tmp_path / "fixture.json"
    raw = canonical_json({"revision": "synthetic"})
    path.write_bytes(raw)
    witness = identity.verify_local_identity_artifact(
        path, retained_sha256=hashlib.sha256(raw).hexdigest(),
    )
    assert type(witness) is identity._WITNESS_TYPE
    assert witness.training_authorized is False
    assert witness.candidate_generation_authorized is False
    assert witness.protected_evaluation_authorized is False
