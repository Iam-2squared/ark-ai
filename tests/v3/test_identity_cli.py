import json

import pytest

from ark.learning.identity_cli import main


def _materialized_snapshot(tmp_path):
    root = tmp_path / "model"
    root.mkdir()
    (root / "config.json").write_text("{}", encoding="utf-8")
    (root / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (root / "tokenizer.json").write_text("{}", encoding="utf-8")
    (root / "model-00001-of-00001.safetensors").write_bytes(b"weights")
    probe = tmp_path / "probe.txt"
    probe.write_text("rendered probe", encoding="utf-8")
    return root, probe


def test_hf_identity_cli_writes_hash_bound_artifact(tmp_path, capsys):
    root, probe = _materialized_snapshot(tmp_path)
    output = tmp_path / "hf-identity.json"
    assert (
        main(
            [
                "hf-snapshot",
                "--root",
                str(root),
                "--revision",
                "a" * 40,
                "--chat-template-probe",
                str(probe),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["model_id"] == "Qwen/Qwen3-4B-Instruct-2507"
    assert payload["revision"] == "a" * 40
    assert len(payload["base_file_manifest_sha256"]) == 64
    stdout = capsys.readouterr().out
    assert f"base_file_manifest_sha256={payload['base_file_manifest_sha256']}" in stdout


def test_identity_cli_is_create_only(tmp_path):
    root, probe = _materialized_snapshot(tmp_path)
    output = tmp_path / "hf-identity.json"
    output.write_text("existing", encoding="utf-8")
    with pytest.raises(ValueError, match="new file"):
        main(
            [
                "hf-snapshot",
                "--root",
                str(root),
                "--revision",
                "b" * 40,
                "--chat-template-probe",
                str(probe),
                "--output",
                str(output),
            ]
        )


def test_tool_identity_cli_emits_frozen_tool_hash(tmp_path, capsys):
    tool = tmp_path / "quantize"
    tool.write_bytes(b"binary")
    output = tmp_path / "tool.json"
    assert (
        main(
            [
                "tool",
                "--path",
                str(tool),
                "--revision",
                "c" * 40,
                "--role",
                "quantizer",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["role"] == "quantizer"
    assert len(payload["identity_sha256"]) == 64
    assert f"tool_identity_sha256={payload['identity_sha256']}" in capsys.readouterr().out
