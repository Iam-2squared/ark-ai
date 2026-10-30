"""Offline V3 runtime code manifest must recheck packaging after Python hashes."""

from __future__ import annotations

import pytest

import ark.learning.identity as identity


def _fake_project(tmp_path):
    learning = tmp_path / "src" / "ark" / "learning"
    learning.mkdir(parents=True)
    packaging = tmp_path / "pyproject.toml"
    packaging.write_text("[project]\nname = 'ark-fixture'\n", encoding="utf-8")
    (learning / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    (learning / "runtime.py").write_text("VALUE = 2\n", encoding="utf-8")
    return packaging


def test_unchanged_local_code_tree_manifest_is_deterministic(tmp_path):
    _fake_project(tmp_path)
    first = identity.build_code_tree_identity(tmp_path)
    second = identity.build_code_tree_identity(tmp_path)
    assert first == second
    assert first["manifest"]["schema_version"] == 1
    assert first["manifest"]["files"][0]["path"] == "pyproject.toml"
    assert len(first["manifest_sha256"]) == 64


@pytest.mark.parametrize("replacement", [
    "[project]\nname = 'changed'\n",
    "[project]\nname = 'othername'\n",
])
def test_packaging_content_change_during_python_hashes_is_rejected(
    tmp_path, monkeypatch, replacement,
):
    packaging = _fake_project(tmp_path)
    original = identity.file_identity
    mutated = False

    def change_after_python(path, *, label=None):
        nonlocal mutated
        result = original(path, label=label)
        if path.name == "core.py" and not mutated:
            packaging.write_text(replacement, encoding="utf-8")
            mutated = True
        return result

    monkeypatch.setattr(identity, "file_identity", change_after_python)
    with pytest.raises(ValueError, match="runtime packaging metadata changed"):
        identity.build_code_tree_identity(tmp_path)
    assert mutated


def test_python_change_and_unchanged_packaging_still_invalidate_tree(
    tmp_path, monkeypatch,
):
    _fake_project(tmp_path)
    original = identity.file_identity
    mutated = False

    def change_python_after_hash(path, *, label=None):
        nonlocal mutated
        result = original(path, label=label)
        if path.name == "core.py" and not mutated:
            path.write_text("VALUE = 99\n", encoding="utf-8")
            mutated = True
        return result

    monkeypatch.setattr(identity, "file_identity", change_python_after_hash)
    with pytest.raises(ValueError, match="snapshot entries changed"):
        identity.build_code_tree_identity(tmp_path)
    assert mutated


def test_not_a_candidate_or_runtime_authorization(tmp_path):
    _fake_project(tmp_path)
    result = identity.build_code_tree_identity(tmp_path)
    assert result["manifest"]["scope"] == "pyproject.toml+src/ark/learning/**/*.py"
    assert "training_authorized" not in result
    assert "candidate_created" not in result
