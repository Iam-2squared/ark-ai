"""Free-only V3 snapshot evidence must be coherent through probe hashing.

All bytes below are tiny synthetic fixtures; no actual weights or training.
"""

from __future__ import annotations

import pytest

from ark.learning import identity


def _snapshot(tmp_path):
    root = tmp_path / "fake-model"
    root.mkdir()
    (root / "config.json").write_bytes(b"{}")
    (root / "tokenizer_config.json").write_bytes(b"{}")
    (root / "tokenizer.json").write_bytes(b"{}")
    (root / "model.safetensors").write_bytes(b"fake weights only")
    probe = tmp_path / "rendered-probe.txt"
    probe.write_bytes(b"fixture chat rendering")
    return root, probe


def _capture(root, probe):
    return identity.build_hf_snapshot_identity(
        root, model_id="Qwen/Qwen3-4B-Instruct-2507",
        revision="1" * 40, chat_template_probe=probe,
    )


def test_stable_fake_snapshot_still_has_coherent_manifest(tmp_path):
    root, probe = _snapshot(tmp_path)
    first = _capture(root, probe)
    assert first == _capture(root, probe)
    assert len(first["base_file_manifest"]["files"]) == 4


@pytest.mark.parametrize("changed_path", [
    "tokenizer.json", "config.json", "model.safetensors",
])
def test_probe_callback_cannot_replace_snapshot_bytes(tmp_path, monkeypatch, changed_path):
    root, probe = _snapshot(tmp_path)
    original = identity.file_identity
    touched = False

    def changed_probe(path, *, label=None):
        nonlocal touched
        if label == "chat-template-probe.txt" and not touched:
            touched = True
            (root / changed_path).write_bytes(b"changed-after-first-snapshot-identity")
        return original(path, label=label)

    monkeypatch.setattr(identity, "file_identity", changed_probe)
    with pytest.raises(ValueError, match="snapshot entries changed"):
        _capture(root, probe)
    assert touched


def test_probe_callback_cannot_add_unmanifested_file(tmp_path, monkeypatch):
    root, probe = _snapshot(tmp_path)
    original = identity.file_identity

    def add_file(path, *, label=None):
        if label == "chat-template-probe.txt":
            (root / "unmanifested-extra.txt").write_bytes(b"unapproved")
        return original(path, label=label)

    monkeypatch.setattr(identity, "file_identity", add_file)
    with pytest.raises(ValueError, match="snapshot entries changed"):
        _capture(root, probe)
