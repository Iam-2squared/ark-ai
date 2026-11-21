"""Detached on-disk V3 review custody, with no compute or paid actions."""

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


def _snapshot():
    value = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    value["code"].update({"git_sha": "1" * 40, "manifest_sha256": "0" * 64})
    value["base"].update({
        "revision": "2" * 40, "file_sha256_manifest": "a" * 64,
    })
    value["tokenizer"].update({
        "file_sha256_manifest": "b" * 64,
        "chat_template_probe_sha256": "c" * 64,
    })
    value["dataset"].update({
        "canonical_sha256": "d" * 64,
        "provenance_manifest_sha256": "e" * 64,
        "contamination_report_sha256": "f" * 64,
    })
    value["environment"].update({
        "os_or_image_digest": "image@sha256:abc", "python": "3.12.10",
        "torch": "pinned", "transformers": "pinned", "peft": "pinned",
        "accelerate": "pinned", "cuda_runtime": "pinned",
    })
    value["hardware"].update({
        "device": "proposed-only", "vram_gib": 24, "driver": "pinned",
    })
    value["budget"].update({
        "max_cost_jpy": 1000, "wall_clock_timeout_minutes": 60,
    })
    value["export"].update({
        "llama_cpp_revision": "3" * 40,
        "converter_identity": "4" * 64,
        "quantizer_identity": "5" * 64,
    })
    return value


def _saved_packet(tmp_path):
    snapshot = _snapshot()
    packet = auth.build_preflight_authorization_packet(snapshot)
    path = tmp_path / "review.json"
    auth._write_new_authorization_packet(path, packet)
    return snapshot, path, sha256_bytes(path.read_bytes())


def test_saved_review_packet_reopens_and_remains_non_authorizing(tmp_path):
    snapshot, path, digest = _saved_packet(tmp_path)
    witness = mod.verify_local_authorization_packet_file(
        snapshot, path, retained_packet_file_sha256=digest,
    )
    assert witness.packet_file_sha256 == digest
    assert witness.external_compute_authorized is False
    assert witness.candidate_generation_authorized is False
    assert witness.protected_evaluation_authorized is False
    assert witness.main_merge_authorized is False
    assert path.exists()


@pytest.mark.parametrize("kind", ("wrong_pin", "edited_bytes", "oversized"))
def test_stored_packet_byte_and_budget_drift_are_rejected(tmp_path, kind):
    snapshot, path, digest = _saved_packet(tmp_path)
    if kind == "wrong_pin":
        digest = "f" * 64 if digest != "f" * 64 else "0" * 64
    elif kind == "edited_bytes":
        content = path.read_bytes()
        path.write_bytes(b" " + content[1:])
    else:
        path.write_bytes(b"x" * (mod._MAX_PACKET_BYTES + 1))
    with pytest.raises(mod.LocalPacketBindingRejected):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )


@pytest.mark.parametrize(
    ("raw", "message"),
    (
        (b'{"same":1,"same":2}\n', "invalid"),
        (b'{ "noncanonical": 1 }\n', "not canonical"),
        (b'{"broken":', "invalid"),
        (b'{"number":NaN}\n', "invalid"),
    ),
)
def test_detached_parser_denies_ambiguous_or_noncanonical_bytes(
    tmp_path, raw, message,
):
    snapshot, path, _ = _saved_packet(tmp_path)
    path.write_bytes(raw)
    with pytest.raises(mod.LocalPacketBindingRejected, match=message):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=sha256_bytes(raw),
        )


@pytest.mark.parametrize(
    "kind", ("symlink", "linked_parent", "hardlink", "relative", "dotdot", "directory"),
)
def test_review_path_must_be_unaliased_local_file(tmp_path, kind):
    snapshot, path, digest = _saved_packet(tmp_path)
    candidate = tmp_path / "candidate.json"
    if kind == "symlink":
        try:
            candidate.symlink_to(path)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks unsupported on this filesystem")
    elif kind == "linked_parent":
        linked = tmp_path / "linked-parent"
        try:
            linked.symlink_to(tmp_path, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("directory symlinks unsupported")
        candidate = linked / path.name
    elif kind == "hardlink":
        try:
            candidate.hardlink_to(path)
        except (OSError, NotImplementedError):
            pytest.skip("hardlinks unsupported")
    elif kind == "relative":
        candidate = Path("review.json")
    elif kind == "dotdot":
        child = tmp_path / "child"
        child.mkdir()
        candidate = child / ".." / path.name
    else:
        candidate.mkdir()
    with pytest.raises(mod.LocalPacketBindingRejected):
        mod.verify_local_authorization_packet_file(
            snapshot, candidate, retained_packet_file_sha256=digest,
        )


def test_packet_replaced_during_detached_verification_is_rejected(
    tmp_path, monkeypatch,
):
    snapshot, path, digest = _saved_packet(tmp_path)
    real = mod.verify_detached_authorization_packet

    def mutate_after_verify(*args, **kwargs):
        result = real(*args, **kwargs)
        raw = path.read_bytes()
        path.write_bytes(b" " + raw[1:])
        return result

    monkeypatch.setattr(
        mod, "verify_detached_authorization_packet", mutate_after_verify,
    )
    with pytest.raises(
        mod.LocalPacketBindingRejected, match="changed during binding",
    ):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )


def test_packet_replaced_during_json_decode_is_rejected(tmp_path, monkeypatch):
    snapshot, path, digest = _saved_packet(tmp_path)
    real = json.loads

    def mutate_after_decode(*args, **kwargs):
        decoded = real(*args, **kwargs)
        path.write_bytes(b" " + path.read_bytes()[1:])
        return decoded

    monkeypatch.setattr(mod.json, "loads", mutate_after_decode)
    with pytest.raises(mod.LocalPacketBindingRejected, match="changed"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )


def test_review_callback_cannot_retarget_snapshot(tmp_path, monkeypatch):
    snapshot, path, digest = _saved_packet(tmp_path)
    real = mod._read_exact_local_packet

    def mutate_snapshot(target):
        result = real(target)
        snapshot["budget"]["max_cost_jpy"] = 50
        return result

    monkeypatch.setattr(mod, "_read_exact_local_packet", mutate_snapshot)
    with pytest.raises(ValueError, match="snapshot changed"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )
