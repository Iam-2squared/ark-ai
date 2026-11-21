"""V3 identity capture rejects callback-capable path carriers before coercion."""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.learning.identity as identity


class _CallbackPath:
    def __init__(self, target: Path) -> None:
        self.target = target
        self.calls = 0

    def __fspath__(self) -> str:
        self.calls += 1
        return str(self.target)


def _assert_rejected_without_fspath(value, operation) -> None:
    with pytest.raises(ValueError, match="exact native Path"):
        operation(value)
    assert value.calls == 0


def _write_hf_snapshot(root: Path) -> Path:
    root.mkdir()
    (root / "config.json").write_text("{}", encoding="utf-8")
    (root / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (root / "tokenizer.json").write_text("{}", encoding="utf-8")
    (root / "model.safetensors").write_bytes(b"synthetic weights")
    probe = root.parent / "probe.txt"
    probe.write_text("synthetic rendered probe", encoding="utf-8")
    return probe


def test_file_and_directory_identity_reject_pathlike_before_callback(tmp_path):
    payload = tmp_path / "payload.bin"
    payload.write_bytes(b"synthetic")
    file_value = _CallbackPath(payload)
    directory_value = _CallbackPath(tmp_path)

    _assert_rejected_without_fspath(file_value, identity.file_identity)
    _assert_rejected_without_fspath(directory_value, identity.directory_file_identities)


def test_code_tree_identity_rejects_pathlike_before_callback(tmp_path):
    value = _CallbackPath(tmp_path)
    _assert_rejected_without_fspath(value, identity.build_code_tree_identity)


def test_hf_snapshot_identity_rejects_pathlike_root_before_callback(tmp_path):
    root = tmp_path / "model"
    probe = tmp_path / "probe.txt"
    root_value = _CallbackPath(root)
    probe.write_text("synthetic probe", encoding="utf-8")

    _assert_rejected_without_fspath(
        root_value,
        lambda candidate: identity.build_hf_snapshot_identity(
            candidate,
            model_id="Qwen/Qwen3-4B-Instruct-2507",
            revision="a" * 40,
            chat_template_probe=probe,
        ),
    )


def test_hf_snapshot_identity_rejects_pathlike_probe_before_callback(tmp_path):
    root = tmp_path / "model"
    probe = _write_hf_snapshot(root)
    probe_value = _CallbackPath(probe)

    _assert_rejected_without_fspath(
        probe_value,
        lambda candidate: identity.build_hf_snapshot_identity(
            root,
            model_id="Qwen/Qwen3-4B-Instruct-2507",
            revision="b" * 40,
            chat_template_probe=candidate,
        ),
    )


def test_tool_identity_rejects_pathlike_before_callback(tmp_path):
    tool = tmp_path / "quantizer"
    tool.write_bytes(b"synthetic tool")
    value = _CallbackPath(tool)

    _assert_rejected_without_fspath(
        value,
        lambda candidate: identity.build_tool_identity(
            candidate,
            git_revision="c" * 40,
            role="quantizer",
        ),
    )


def test_path_subclass_override_is_rejected_before_fspath(tmp_path):
    target = tmp_path / "payload.bin"
    target.write_bytes(b"synthetic")
    calls: list[bool] = []
    native_path_type = type(Path("."))

    class _PathSubclass(native_path_type):
        def __fspath__(self) -> str:
            calls.append(True)
            return str(target)

    candidate = _PathSubclass(str(target))
    with pytest.raises(ValueError, match="exact native Path"):
        identity.file_identity(candidate)
    assert calls == []
