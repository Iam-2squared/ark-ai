"""Read-only V3 identity JSON fixture verification never authorizes compute."""

import hashlib

import pytest

from ark.learning.execution import canonical_json
from ark.learning.identity_artifact_verify import (
    LocalIdentityArtifactRejected,
    verify_local_identity_artifact,
)
from ark.learning.identity_cli import _write_new_json


def test_exact_artifact_bytes_are_verified_without_compute(tmp_path):
    path = tmp_path / "identity.json"
    digest = _write_new_json(path, {"code_manifest_sha256": "a" * 64})
    witness = verify_local_identity_artifact(path, retained_sha256=digest)
    assert witness.artifact_sha256 == digest
    assert witness.artifact_bytes == path.stat().st_size
    assert witness.top_level_keys == ("code_manifest_sha256",)
    assert not witness.source_authenticated
    assert not witness.training_authorized
    assert not witness.candidate_generation_authorized
    assert not witness.protected_evaluation_authorized


@pytest.mark.parametrize("payload", [
    b'{"a":1, "b":2}\n',
    b'{"a":1,"a":2}\n',
    b'{"a":NaN}\n',
    b'[1,2]\n',
    b'{"a":1}',
    b'{"a":1}\n\n',
    b'{"a":1}\x00',
    b"[" * 130 + b"0" + b"]" * 130,
])
def test_noncanonical_or_unbounded_json_is_denied(tmp_path, payload):
    path = tmp_path / "bad.json"
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    with pytest.raises(LocalIdentityArtifactRejected):
        verify_local_identity_artifact(path, retained_sha256=digest)


@pytest.mark.parametrize("bad_digest", ["A" * 64, "f" * 63, True, None, ""])
def test_only_independently_pinned_exact_digest_is_accepted(tmp_path, bad_digest):
    path = tmp_path / "identity.json"
    path.write_bytes(canonical_json({"source": "fixture"}))
    with pytest.raises(LocalIdentityArtifactRejected):
        verify_local_identity_artifact(path, retained_sha256=bad_digest)


def test_rewritten_artifact_does_not_match_retained_witness(tmp_path):
    path = tmp_path / "identity.json"
    digest = _write_new_json(path, {"revision": "a" * 40})
    path.write_bytes(canonical_json({"revision": "b" * 40}))
    with pytest.raises(LocalIdentityArtifactRejected, match="SHA-256"):
        verify_local_identity_artifact(path, retained_sha256=digest)


def test_only_regular_existing_file_is_readable(tmp_path):
    empty = tmp_path / "empty.json"
    empty.touch()
    with pytest.raises(LocalIdentityArtifactRejected):
        verify_local_identity_artifact(
            empty, retained_sha256=hashlib.sha256(b"").hexdigest(),
        )
    with pytest.raises(LocalIdentityArtifactRejected):
        verify_local_identity_artifact(
            tmp_path, retained_sha256="a" * 64,
        )
    with pytest.raises(LocalIdentityArtifactRejected):
        verify_local_identity_artifact(
            tmp_path / "missing", retained_sha256="a" * 64,
        )


def test_symbolic_path_alias_is_rejected(tmp_path):
    real = tmp_path / "original.json"
    digest = _write_new_json(real, {"source": "fixture"})
    alias = tmp_path / "alias.json"
    try:
        alias.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is restricted")
    with pytest.raises(LocalIdentityArtifactRejected):
        verify_local_identity_artifact(alias, retained_sha256=digest)


def test_hardlink_alias_is_rejected(tmp_path):
    import os

    real = tmp_path / "original.json"
    digest = _write_new_json(real, {"source": "fixture"})
    alias = tmp_path / "alias.json"
    try:
        os.link(real, alias)
    except (OSError, NotImplementedError):
        pytest.skip("hardlinks restricted on this filesystem")
    with pytest.raises(LocalIdentityArtifactRejected):
        verify_local_identity_artifact(real, retained_sha256=digest)
