"""Free-only runtime binding for the rendered V3 tokenizer probe.

Every tokenizer in this file is a tiny synthetic fixture. No Transformers
model, weights, GPU, external service, or training backend is loaded.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning.execution import canonical_json, sha256_bytes
from ark.learning.chat_template_probe import (
    ChatTemplateProbeRejected,
    build_chat_template_probe,
    verify_chat_template_probe,
)


class FakeTokenizer:
    chat_template = "fixture-template-v1"

    def apply_chat_template(
        self, messages, *, tokenize, add_generation_prompt,
    ):
        assert tokenize is False
        return (
            self.chat_template
            + "|generation="
            + str(add_generation_prompt)
            + "|messages="
            + json.dumps(messages, sort_keys=True, separators=(",", ":"))
        )


def _write_probe(path: Path, tokenizer: FakeTokenizer) -> str:
    payload = canonical_json(build_chat_template_probe(tokenizer))
    path.write_bytes(payload)
    return sha256_bytes(payload)


def test_runtime_tokenizer_reproduces_exact_rendered_probe(tmp_path):
    tokenizer = FakeTokenizer()
    path = tmp_path / "probe.json"
    digest = _write_probe(path, tokenizer)

    assert verify_chat_template_probe(tokenizer, path, digest) == digest
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["model_id"] == "Qwen/Qwen3-4B-Instruct-2507"
    assert [item["case_id"] for item in payload["cases"]] == [
        "generation_prompt_v1", "assistant_turn_v1",
    ]
    assert all(len(item["rendered_sha256"]) == 64 for item in payload["cases"])


@pytest.mark.parametrize("mutation", ("template", "rendering"))
def test_runtime_tokenizer_drift_is_rejected(tmp_path, mutation):
    tokenizer = FakeTokenizer()
    path = tmp_path / "probe.json"
    digest = _write_probe(path, tokenizer)
    if mutation == "template":
        tokenizer.chat_template = "fixture-template-v2"
    else:
        tokenizer.apply_chat_template = lambda *args, **kwargs: "different rendering"

    with pytest.raises(
        ChatTemplateProbeRejected,
        match="differs from frozen chat-template probe",
    ):
        verify_chat_template_probe(tokenizer, path, digest)


def test_bad_file_digest_is_rejected_before_tokenizer_callback(tmp_path):
    path = tmp_path / "probe.json"
    path.write_bytes(b"not the retained probe")

    class NeverRender:
        chat_template = "fixture"

        def apply_chat_template(self, *_args, **_kwargs):
            raise AssertionError("bad file digest must be rejected before rendering")

    with pytest.raises(ChatTemplateProbeRejected, match="file digest mismatch"):
        verify_chat_template_probe(NeverRender(), path, "0" * 64)


def test_probe_builder_rejects_mutating_or_nontext_tokenizer_output():
    class MutatingTokenizer(FakeTokenizer):
        def apply_chat_template(self, messages, **kwargs):
            messages[0]["content"] = "mutated"
            return "rendered"

    class NonTextTokenizer(FakeTokenizer):
        def apply_chat_template(self, *_args, **_kwargs):
            return [1, 2, 3]

    with pytest.raises(ChatTemplateProbeRejected, match="mutated probe messages"):
        build_chat_template_probe(MutatingTokenizer())
    with pytest.raises(ChatTemplateProbeRejected, match="bounded exact text"):
        build_chat_template_probe(NonTextTokenizer())


def test_probe_cli_uses_local_tokenizer_only_and_create_only_output(
    monkeypatch, tmp_path, capsys,
):
    from ark.learning import identity_cli

    tokenizer = FakeTokenizer()
    calls = []

    class FakeAutoTokenizer:
        @staticmethod
        def from_pretrained(path, *, local_files_only, trust_remote_code):
            calls.append((path, local_files_only, trust_remote_code))
            assert local_files_only is True
            assert trust_remote_code is False
            return tokenizer

    monkeypatch.setitem(
        sys.modules, "transformers",
        SimpleNamespace(AutoTokenizer=FakeAutoTokenizer),
    )
    root = tmp_path / "materialized"
    root.mkdir()
    output = tmp_path / "chat-template-probe.json"
    assert identity_cli.main([
        "chat-template-probe", "--root", str(root), "--output", str(output),
    ]) == 0

    expected = canonical_json(build_chat_template_probe(tokenizer))
    assert output.read_bytes() == expected
    digest = sha256_bytes(expected)
    assert calls == [(str(root), True, False)]
    assert f"chat_template_probe_sha256={digest}" in capsys.readouterr().out

    with pytest.raises(ValueError, match="new file"):
        identity_cli.main([
            "chat-template-probe", "--root", str(root), "--output", str(output),
        ])


def test_runtime_model_loader_rejects_probe_before_model_weights(
    monkeypatch, tmp_path,
):
    import ark.learning.hf_lora as module

    tokenizer = FakeTokenizer()
    probe = tmp_path / "probe.json"
    digest = _write_probe(probe, tokenizer)
    tokenizer.chat_template = "runtime-drift"

    class FakeCuda:
        @staticmethod
        def is_available():
            return True

        @staticmethod
        def is_bf16_supported():
            return True

    class FakeTorch:
        cuda = FakeCuda()
        bfloat16 = object()

    class FakeModel:
        def to(self, _device):
            return self

    model_loads = []

    class FakeAutoTokenizer:
        @staticmethod
        def from_pretrained(_path, **kwargs):
            assert kwargs == {
                "local_files_only": True, "trust_remote_code": False,
            }
            return tokenizer

    class FakeAutoModel:
        @staticmethod
        def from_pretrained(_path, **_kwargs):
            model_loads.append(True)
            return FakeModel()

    class FakeLoraConfig:
        def __init__(self, **_kwargs):
            pass

    def fake_get_peft_model(model, _config):
        return model

    monkeypatch.setattr(
        module, "_runtime_imports",
        lambda: (
            FakeTorch(), FakeLoraConfig, fake_get_peft_model,
            FakeAutoModel, FakeAutoTokenizer,
        ),
    )
    snapshot = {"tokenizer": {"chat_template_probe_sha256": digest}}

    with pytest.raises(module.LoRARuntimeError, match="runtime tokenizer"):
        module._build_model_and_tokenizer(snapshot, tmp_path, probe)
    assert model_loads == []
