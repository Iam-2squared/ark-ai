import pytest

from ark.learning.identity import (
    build_code_tree_identity,
    build_hf_snapshot_identity,
    build_tool_identity,
)


def _write_complete_hf_snapshot(root):
    root.mkdir()
    (root / "config.json").write_text("{}", encoding="utf-8")
    (root / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (root / "tokenizer.json").write_text("{}", encoding="utf-8")
    (root / "model-00001-of-00001.safetensors").write_bytes(b"weights")


def test_hf_snapshot_identity_hashes_existing_bytes(tmp_path):
    root = tmp_path / "model"
    _write_complete_hf_snapshot(root)
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


def test_hf_snapshot_requires_tokenizer_json(tmp_path):
    root = tmp_path / "model"
    root.mkdir()
    (root / "config.json").write_text("{}", encoding="utf-8")
    (root / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (root / "model.safetensors").write_bytes(b"weights")
    probe = tmp_path / "probe.txt"
    probe.write_text("probe", encoding="utf-8")

    with pytest.raises(ValueError, match="tokenizer.json"):
        build_hf_snapshot_identity(
            root,
            model_id="Qwen/Qwen3-4B-Instruct-2507",
            revision="2" * 40,
            chat_template_probe=probe,
        )


def test_hf_snapshot_rejects_empty_weight_file(tmp_path):
    root = tmp_path / "model"
    _write_complete_hf_snapshot(root)
    (root / "model-00001-of-00001.safetensors").write_bytes(b"")
    probe = tmp_path / "probe.txt"
    probe.write_text("probe", encoding="utf-8")

    with pytest.raises(ValueError, match="empty safetensors"):
        build_hf_snapshot_identity(
            root,
            model_id="Qwen/Qwen3-4B-Instruct-2507",
            revision="3" * 40,
            chat_template_probe=probe,
        )


def test_hf_snapshot_rejects_empty_chat_template_probe(tmp_path):
    root = tmp_path / "model"
    _write_complete_hf_snapshot(root)
    probe = tmp_path / "probe.txt"
    probe.write_bytes(b"")

    with pytest.raises(ValueError, match="chat-template probe"):
        build_hf_snapshot_identity(
            root,
            model_id="Qwen/Qwen3-4B-Instruct-2507",
            revision="4" * 40,
            chat_template_probe=probe,
        )


def test_tool_identity_binds_bytes_to_git_revision(tmp_path):
    tool = tmp_path / "quantize"
    tool.write_bytes(b"binary")
    result = build_tool_identity(tool, git_revision="2" * 40, role="quantizer")
    assert result["git_revision"] == "2" * 40
    assert result["file"]["bytes"] == 6
    assert len(result["identity_sha256"]) == 64


def test_code_tree_identity_detects_runtime_source_change(tmp_path):
    required = {
        "pyproject.toml": "project-a",
        "src/ark/learning/execution.py": "execution-a",
        "src/ark/learning/hf_lora.py": "lora-a",
        "src/ark/learning/training_cli.py": "cli-a",
    }
    for relative, content in required.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    before = build_code_tree_identity(tmp_path)["manifest_sha256"]
    (tmp_path / "src/ark/learning/hf_lora.py").write_text("lora-b", encoding="utf-8")
    after = build_code_tree_identity(tmp_path)["manifest_sha256"]
    assert before != after
