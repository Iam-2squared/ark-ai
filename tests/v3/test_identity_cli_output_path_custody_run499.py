"""V3 preflight identity capture must not write through output aliases."""

import json

import pytest

from ark.learning.identity_cli import _write_new_json


def test_identity_artifact_exclusive_write_and_hash(tmp_path):
    path = tmp_path / "identity.json"
    digest = _write_new_json(path, {"source": "tiny-local-fixture"})
    assert len(digest) == 64
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "source": "tiny-local-fixture",
    }
    with pytest.raises(ValueError, match="new file"):
        _write_new_json(path, {"replacement": True})


def test_identity_artifact_rejects_parent_traversal(tmp_path):
    child = tmp_path / "sub"
    child.mkdir()
    output = child / ".." / "forbidden-identity.json"
    with pytest.raises(ValueError, match="new file"):
        _write_new_json(output, {"status": "should-not-exist"})
    assert not (tmp_path / "forbidden-identity.json").exists()


def test_identity_artifact_rejects_symbolic_parent(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "alias"
    try:
        link.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted on this OS")
    with pytest.raises(ValueError, match="new file"):
        _write_new_json(link / "identity.json", {"status": "alias"})
    assert not (real / "identity.json").exists()


def test_identity_artifact_rejects_symbolic_grandparent(tmp_path):
    real = tmp_path / "real"
    nested = real / "nested"
    nested.mkdir(parents=True)
    link = tmp_path / "alias"
    try:
        link.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted on this OS")
    with pytest.raises(ValueError, match="new file"):
        _write_new_json(link / "nested" / "identity.json", {"status": "alias"})
    assert not (nested / "identity.json").exists()
