"""Passive V3 identity artifact rejects replacement denial code before local reads.

Only a synthetic JSON file is inspected; no GPU, Candidate, protected
evaluation, human approval or external action is permitted or implied.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.learning.identity_artifact_verify as artifact
from ark.learning.execution import canonical_json

_FLAGS = (
    "source_authenticated", "training_authorized",
    "candidate_generation_authorized", "protected_evaluation_authorized",
)


@pytest.mark.parametrize("name", _FLAGS)
def test_substituted_false_only_getter_denied_before_file_open(
    tmp_path, monkeypatch, name,
):
    path = tmp_path / "synthetic-identity.json"
    raw = canonical_json({"revision": "fixture"})
    path.write_bytes(raw)
    original_open = type(path).open
    calls = []

    def forbidden_open(self, *args, **kwargs):
        calls.append(self)
        raise AssertionError("identity data must not be opened")

    monkeypatch.setattr(type(path), "open", forbidden_open)
    monkeypatch.setattr(
        artifact.LocalIdentityArtifactWitness,
        name, property(lambda _self: False),
    )
    with pytest.raises(
        artifact.LocalIdentityArtifactRejected, match="authority definition changed",
    ):
        artifact.verify_local_identity_artifact(
            path, retained_sha256=hashlib.sha256(raw).hexdigest(),
        )
    assert not calls
    monkeypatch.setattr(type(path), "open", original_open)


def test_constructor_cannot_switch_denial_to_another_false_getter(
    tmp_path, monkeypatch,
):
    path = tmp_path / "synthetic-identity.json"
    raw = canonical_json({"revision": "fixture"})
    path.write_bytes(raw)
    cls = artifact.LocalIdentityArtifactWitness
    original_init = cls.__init__
    called = []

    def replace_during_constructor(self, *args):
        original_init(self, *args)
        called.append(True)
        monkeypatch.setattr(
            cls, "protected_evaluation_authorized",
            property(lambda _self: False),
        )

    monkeypatch.setattr(cls, "__init__", replace_during_constructor)
    with pytest.raises(
        artifact.LocalIdentityArtifactRejected, match="authority definition changed",
    ):
        artifact.verify_local_identity_artifact(
            path, retained_sha256=hashlib.sha256(raw).hexdigest(),
        )
    assert called == [True]
    assert path.read_bytes() == raw


def test_clean_local_artifact_remains_unapproved(tmp_path):
    path = tmp_path / "synthetic-identity.json"
    raw = canonical_json({"revision": "fixture"})
    path.write_bytes(raw)
    witness = artifact.verify_local_identity_artifact(
        path, retained_sha256=hashlib.sha256(raw).hexdigest(),
    )
    assert witness.top_level_keys == ("revision",)
    for name in _FLAGS:
        assert getattr(witness, name) is False
