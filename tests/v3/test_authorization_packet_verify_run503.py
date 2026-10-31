"""Detached V3 authorization packet review tests: no paid or real model actions."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ark.learning import authorization as authorization
from ark.learning import authorization_packet_verify as mod
from ark.learning.execution import canonical_json, sha256_bytes

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
        "torch": "pinned", "transformers": "pinned",
        "peft": "pinned", "accelerate": "pinned",
        "cuda_runtime": "pinned",
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


def _inputs():
    snapshot = _snapshot()
    packet = authorization.build_preflight_authorization_packet(snapshot)
    retained = sha256_bytes(canonical_json(packet))
    return snapshot, packet, retained


def test_matching_packet_binds_only_inert_review_digest():
    snapshot, packet, retained = _inputs()
    result = mod.verify_detached_authorization_packet(
        snapshot, packet, retained_packet_file_sha256=retained,
    )
    assert result.snapshot_sha256 == packet["execution_snapshot_sha256"]
    assert result.internal_packet_sha256 == packet["packet_sha256"]
    assert result.packet_file_sha256 == retained
    assert mod.verify_detached_authorization_packet(
        snapshot, packet, retained_packet_file_sha256=retained,
    ) == result
    for flag in mod._DENIAL_FLAGS:
        assert getattr(result, flag) is False


@pytest.mark.parametrize("kind", [
    "budget", "scope", "candidate", "evaluation", "internal",
    "extra", "different_snapshot", "missing_internal",
])
def test_tampered_packet_or_snapshot_is_rejected(kind):
    snapshot, packet, retained = _inputs()
    packet = deepcopy(packet)
    if kind == "budget":
        packet["budget"]["max_cost_jpy"] = 5
    elif kind == "scope":
        packet["request_scope"] = "FULL_TRAINING"
    elif kind == "candidate":
        packet["preflight"]["candidate_created"] = True
    elif kind == "evaluation":
        packet["hard_stops_after_preflight"][
            "historical_v2_opening_requires_later_explicit_authorization"
        ] = False
    elif kind == "internal":
        packet["packet_sha256"] = "f" * 64
    elif kind == "extra":
        packet["export_authorized"] = True
    elif kind == "different_snapshot":
        snapshot["budget"]["max_cost_jpy"] = 2000
    else:
        packet.pop("packet_sha256")
    with pytest.raises((ValueError, KeyError)):
        mod.verify_detached_authorization_packet(
            snapshot, packet, retained_packet_file_sha256=retained,
        )


@pytest.mark.parametrize("retained", ["f" * 64, "x", "A" * 64, True])
def test_wrong_retained_full_file_digest_is_rejected(retained):
    snapshot, packet, _ = _inputs()
    with pytest.raises(mod.LocalPacketBindingRejected):
        mod.verify_detached_authorization_packet(
            snapshot, packet, retained_packet_file_sha256=retained,
        )


@pytest.mark.parametrize("flag", mod._DENIAL_FLAGS)
def test_forged_witness_authority_is_rejected(monkeypatch, flag):
    snapshot, packet, retained = _inputs()
    monkeypatch.setattr(
        mod.LocalPacketBindingWitness, flag,
        property(lambda _self: True),
    )
    with pytest.raises(mod.LocalPacketBindingRejected, match="authority"):
        mod.verify_detached_authorization_packet(
            snapshot, packet, retained_packet_file_sha256=retained,
        )


def test_packet_callback_mutating_snapshot_is_rejected(monkeypatch):
    snapshot, packet, retained = _inputs()
    original = mod.build_preflight_authorization_packet

    def mutate(source):
        generated = original(source)
        source["budget"]["max_cost_jpy"] = 1
        return generated

    monkeypatch.setattr(mod, "build_preflight_authorization_packet", mutate)
    with pytest.raises(ValueError, match="snapshot changed"):
        mod.verify_detached_authorization_packet(
            snapshot, packet, retained_packet_file_sha256=retained,
        )


def test_packet_type_is_exact_not_mapping_subclass():
    snapshot, packet, retained = _inputs()

    class UntrustedMapping(dict):
        pass

    with pytest.raises(mod.LocalPacketBindingRejected, match="exact"):
        mod.verify_detached_authorization_packet(
            snapshot, UntrustedMapping(packet),
            retained_packet_file_sha256=retained,
        )


@pytest.mark.parametrize("target", ["snapshot", "packet"])
def test_late_witness_digest_getter_cannot_mutate_review_inputs(monkeypatch, target):
    snapshot, packet, retained = _inputs()
    original_descriptor = mod.LocalPacketBindingWitness.snapshot_sha256
    calls = 0

    def late_getter(self):
        nonlocal calls
        calls += 1
        value = original_descriptor.__get__(self, type(self))
        # The third access happens during the final witness field check,
        # after the previous snapshot/packet epoch check already passed.
        if calls == 3:
            if target == "snapshot":
                snapshot["budget"]["max_cost_jpy"] = 999
            else:
                packet["request_scope"] = "FULL_TRAINING"
        return value

    def preserve_slot_setter(self, value):
        # A frozen slots dataclass initializes through object.__setattr__.
        # Keep construction intact so this tests the later *getter* epoch.
        original_descriptor.__set__(self, value)

    monkeypatch.setattr(
        mod.LocalPacketBindingWitness, "snapshot_sha256",
        property(late_getter, preserve_slot_setter),
    )
    with pytest.raises(ValueError, match="changed"):
        mod.verify_detached_authorization_packet(
            snapshot, packet, retained_packet_file_sha256=retained,
        )
    assert calls >= 3
