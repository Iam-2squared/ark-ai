"""Read-only V3 file review must not return a forged detached witness.

All examples use synthetic review packets. No GPU, approval or billing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import authorization as auth
from ark.learning import authorization_packet_file_review as mod
from ark.learning.execution import sha256_bytes

_TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _fixture(tmp_path):
    snapshot = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    snapshot["code"].update({"git_sha": "1" * 40, "manifest_sha256": "0" * 64})
    snapshot["base"].update({
        "revision": "2" * 40, "file_sha256_manifest": "a" * 64,
    })
    snapshot["tokenizer"].update({
        "file_sha256_manifest": "b" * 64,
        "chat_template_probe_sha256": "c" * 64,
    })
    snapshot["dataset"].update({
        "canonical_sha256": "d" * 64,
        "provenance_manifest_sha256": "e" * 64,
        "contamination_report_sha256": "f" * 64,
    })
    snapshot["environment"].update({
        "os_or_image_digest": "image@sha256:abc", "python": "3.12.10",
        "torch": "pinned", "transformers": "pinned", "peft": "pinned",
        "accelerate": "pinned", "cuda_runtime": "pinned",
    })
    snapshot["hardware"].update({
        "device": "proposed-only", "vram_gib": 24, "driver": "pinned",
    })
    snapshot["budget"].update({
        "max_cost_jpy": 1000, "wall_clock_timeout_minutes": 60,
    })
    snapshot["export"].update({
        "llama_cpp_revision": "3" * 40,
        "converter_identity": "4" * 64,
        "quantizer_identity": "5" * 64,
    })
    packet = auth.build_preflight_authorization_packet(snapshot)
    path = tmp_path / "review.json"
    auth._write_new_authorization_packet(path, packet)
    return snapshot, path, sha256_bytes(path.read_bytes())


def test_detached_file_review_returns_non_authorizing_witness(tmp_path):
    snapshot, path, pin = _fixture(tmp_path)
    witness = mod.verify_local_authorization_packet_file(
        snapshot, path, retained_packet_file_sha256=pin,
    )
    assert type(witness) is mod.LocalPacketBindingWitness
    assert witness.packet_file_sha256 == pin
    assert witness.external_compute_authorized is False
    assert witness.candidate_generation_authorized is False
    assert witness.protected_evaluation_authorized is False
    assert witness.main_merge_authorized is False


@pytest.mark.parametrize("field", (
    "snapshot_sha256", "packet_file_sha256", "internal_packet_sha256",
))
def test_late_file_read_cannot_rewrite_returned_witness(
    tmp_path, monkeypatch, field,
):
    snapshot, path, pin = _fixture(tmp_path)
    original_verify = mod.verify_detached_authorization_packet
    original_read = mod._read_exact_local_packet
    witness = []
    calls = 0

    def remember(*args, **kwargs):
        value = original_verify(*args, **kwargs)
        witness.append(value)
        return value

    def reread(target):
        nonlocal calls
        data = original_read(target)
        calls += 1
        if calls == 2:
            object.__setattr__(witness[0], field, "0" * 64)
        return data

    monkeypatch.setattr(mod, "verify_detached_authorization_packet", remember)
    monkeypatch.setattr(mod, "_read_exact_local_packet", reread)
    with pytest.raises(mod.LocalPacketBindingRejected, match="witness changed"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=pin,
        )


def test_denial_getter_cannot_rewrite_returned_witness(tmp_path, monkeypatch):
    snapshot, path, pin = _fixture(tmp_path)
    original = mod.verify_detached_authorization_packet

    def install_false_valued_mutator(*args, **kwargs):
        witness = original(*args, **kwargs)

        def malicious_false(self):
            object.__setattr__(self, "internal_packet_sha256", "0" * 64)
            return False

        monkeypatch.setattr(
            mod.LocalPacketBindingWitness,
            "main_merge_authorized",
            property(malicious_false),
        )
        return witness

    monkeypatch.setattr(
        mod, "verify_detached_authorization_packet",
        install_false_valued_mutator,
    )
    with pytest.raises(mod.LocalPacketBindingRejected, match="witness changed"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=pin,
        )


def test_denial_getter_file_change_is_caught_after_callback(tmp_path, monkeypatch):
    snapshot, path, pin = _fixture(tmp_path)
    original = mod.verify_detached_authorization_packet

    def install_late_file_writer(*args, **kwargs):
        witness = original(*args, **kwargs)

        def malicious_false(_self):
            raw = path.read_bytes()
            path.write_bytes(b" " + raw[1:])
            return False

        monkeypatch.setattr(
            mod.LocalPacketBindingWitness,
            "main_merge_authorized",
            property(malicious_false),
        )
        return witness

    monkeypatch.setattr(
        mod, "verify_detached_authorization_packet",
        install_late_file_writer,
    )
    with pytest.raises(mod.LocalPacketBindingRejected, match="changed during binding"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=pin,
        )


def test_detached_callback_must_not_change_decoded_packet(tmp_path, monkeypatch):
    snapshot, path, pin = _fixture(tmp_path)
    original = mod.verify_detached_authorization_packet

    def mutate_decoded_packet(source, packet, **kwargs):
        witness = original(source, packet, **kwargs)
        packet["packet_sha256"] = "0" * 64
        return witness

    monkeypatch.setattr(
        mod, "verify_detached_authorization_packet", mutate_decoded_packet,
    )
    with pytest.raises(ValueError, match="snapshot changed"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=pin,
        )
