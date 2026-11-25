"""Passive V3 identity-artifact final-byte and deny-only callback regression.

Synthetic local JSON only. No model download, protected V2 evaluation,
Candidate, user approval, GPU use, paid service or training is invoked.
"""

from __future__ import annotations

import hashlib
import os

import pytest

import ark.learning.identity_artifact_verify as mod
from ark.learning.execution import canonical_json


def _artifact(tmp_path):
    path = tmp_path / "synthetic-identity.json"
    raw = canonical_json({"revision": "alpha"})
    alternative = canonical_json({"revision": "omega"})
    assert len(raw) == len(alternative)
    path.write_bytes(raw)
    return path, raw, alternative


def test_same_size_rewrite_with_restored_mtime_is_caught_by_final_byte_read(
    tmp_path, monkeypatch,
):
    path, raw, alternative = _artifact(tmp_path)
    retained_digest = hashlib.sha256(raw).hexdigest()
    original_canonical = mod.canonical_json
    original = path.stat()
    triggered = False

    def postparse_rewrite(parsed):
        nonlocal triggered
        triggered = True
        path.write_bytes(alternative)
        # Simulate a same-size/timestamp-restored edit; inode remains stable.
        os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
        return original_canonical(parsed)

    monkeypatch.setattr(mod, "canonical_json", postparse_rewrite)
    with pytest.raises(
        mod.LocalIdentityArtifactRejected,
        match="identity file bytes changed after verified read",
    ):
        mod.verify_local_identity_artifact(path, retained_sha256=retained_digest)
    assert triggered
    assert path.stat().st_size == len(raw)
    assert hashlib.sha256(path.read_bytes()).hexdigest() != retained_digest


@pytest.mark.parametrize(
    "denial_name",
    (
        "source_authenticated", "training_authorized",
        "candidate_generation_authorized", "protected_evaluation_authorized",
    ),
)
def test_false_only_rebound_authority_is_rejected_before_filesystem(
    tmp_path, monkeypatch, denial_name,
):
    path, raw, _ = _artifact(tmp_path)
    actions = []

    def counterfeit_denial(_self):
        actions.append("counterfeit callback")
        return False

    def forbidden_lstat(_self):
        actions.append("filesystem")
        raise AssertionError("must reject counterfeit before filesystem access")

    monkeypatch.setattr(
        mod.LocalIdentityArtifactWitness, denial_name,
        property(counterfeit_denial),
    )
    monkeypatch.setattr(type(path), "lstat", forbidden_lstat)
    with pytest.raises(
        mod.LocalIdentityArtifactRejected,
        match="authority definition changed",
    ):
        mod.verify_local_identity_artifact(
            path, retained_sha256=hashlib.sha256(raw).hexdigest(),
        )
    assert actions == []
