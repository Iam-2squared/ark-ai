from pathlib import Path

import pytest

from ark.learning.identity import build_hf_snapshot_identity, build_tool_identity


def test_hf_snapshot_identity_hashes_existing_bytes(tmp_path):
    root = tmp_path / "model"
    root.mkdir()
    (root / "config.json").write_text("{}", encoding="utf-8")
    (root / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (root / "tokenizer.json").write_text("{}", encoding="utf-8")
    (root / "model-00001-of-00001.safetensors").write_bytes(b"weights")
    probe = tmp_path / "probe.txt"
    probe.write_text("rendered chat template probe", encoding="utf-8")

    result = build_hf_snapshot_identity(
        root,
        model_id="Qwen/Qwen3-4B-Instruct-2507",
        revision="1" * 40,
        chat_template_probe=probe,
    )
    assert result["revision"] == "1" * 40
    assert len(result["base_file_manifest_sha256"]) == 64
    assert len(result["tokenizer_file_manifest_sha256"]) == 64
    assert len(result["chat_template_probe_sha256"]) == 64
    assert any(
        row["path"].endswith(".safetensors") for row in result["base_file_manifest"]["files"]
    )


def test_hf_snapshot_requires_immutable_revision(tmp_path):
    root = tmp_path / "model"
    root.mkdir()
    (root / "config.json").write_text("{}", encoding="utf-8")
    (root / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (root / "model.safetensors").write_bytes(b"weights")
    probe = tmp_path / "probe.txt"
    probe.write_text("probe", encoding="utf-8")
    with pytest.raises(ValueError, match="40-hex"):
        build_hf_snapshot_identity(
            root,
            model_id="Qwen/Qwen3-4B-Instruct-2507",
            revision="main",
            chat_template_probe=probe,
        )


def test_tool_identity_binds_bytes_to_git_revision(tmp_path):
    tool = tmp_path / "quantize"
    tool.write_bytes(b"binary")
    result = build_tool_identity(tool, git_revision="2" * 40, role="quantizer")
    assert result["git_revision"] == "2" * 40
    assert result["file"]["bytes"] == 6
    assert len(result["identity_sha256"]) == 64
