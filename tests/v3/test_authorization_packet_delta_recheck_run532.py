"""Detached V3 packet-delta receipt rechecks remain validation-only."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ark.learning import authorization as auth
from ark.learning import authorization_packet_delta_recheck as mod
from ark.learning import authorization_packet_delta_review as base
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


def _fixture(tmp_path, *, change=True):
    old = _snapshot()
    new = deepcopy(old)
    if change:
        new["budget"]["max_cost_jpy"] = 1500
    paths = (tmp_path / "old-review.json", tmp_path / "new-review.json")
    for path, snapshot in zip(paths, (old, new), strict=True):
        packet = auth.build_preflight_authorization_packet(snapshot)
        auth._write_new_authorization_packet(path, packet)
    shas = tuple(sha256_bytes(path.read_bytes()) for path in paths)
    retained = base.review_unapproved_packet_delta(
        old, new, *paths,
        retained_old_file_sha256=shas[0],
        retained_new_file_sha256=shas[1],
    )
    return old, new, paths, shas, retained


def _check(fixture):
    old, new, paths, shas, receipt = fixture
    return mod.verify_detached_unapproved_packet_delta(
        receipt, old, new, *paths,
        retained_old_file_sha256=shas[0],
        retained_new_file_sha256=shas[1],
    )


@pytest.mark.parametrize("change", (False, True))
def test_detached_packet_delta_survives_fresh_local_file_review(tmp_path, change):
    fixture = _fixture(tmp_path, change=change)
    assert _check(fixture) is None
    receipt = fixture[4]
    assert receipt.changed_paths == (() if not change else (
        "budget.max_cost_jpy", "execution_core_sha256",
        "execution_snapshot_sha256", "packet_sha256",
    ))
    assert receipt.external_compute_authorized is False
    assert receipt.candidate_generation_authorized is False
    assert receipt.protected_evaluation_authorized is False
    assert receipt.main_merge_authorized is False


@pytest.mark.parametrize("field,value", (
    ("delta_sha256", "0" * 64),
    ("delta_sha256", "invalid"),
    ("old_file_sha256", True),
    ("new_file_sha256", "not-sha"),
    ("changed_paths", ["packet_sha256"]),
    ("changed_paths", ("packet_sha256", "packet_sha256")),
    ("changed_paths", ("bad\nfield",)),
))
def test_forged_detached_receipt_is_rejected(tmp_path, field, value):
    fixture = list(_fixture(tmp_path))
    object.__setattr__(fixture[4], field, value)
    with pytest.raises(mod.DetachedPacketDeltaRejected):
        _check(fixture)


@pytest.mark.parametrize("which", ("old", "new"))
def test_post_review_file_mutation_fails_closed(tmp_path, which):
    fixture = _fixture(tmp_path)
    path = fixture[2][0 if which == "old" else 1]
    data = path.read_bytes()
    path.write_bytes(b"X" + data[1:])
    with pytest.raises(mod.DetachedPacketDeltaRejected):
        _check(fixture)


def test_snapshot_change_without_matching_retained_file_is_denied(tmp_path):
    fixture = _fixture(tmp_path)
    fixture[1]["budget"]["max_cost_jpy"] = 1700
    with pytest.raises(mod.DetachedPacketDeltaRejected):
        _check(fixture)


def test_retained_packet_hash_input_cannot_be_swapped(tmp_path):
    fixture = list(_fixture(tmp_path))
    fixture[3] = (fixture[3][1], fixture[3][0])
    with pytest.raises(mod.DetachedPacketDeltaRejected, match="SHA mismatch"):
        _check(fixture)


def test_retained_false_getter_cannot_mutate_receipt(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path)
    retained = fixture[4]

    def mutate_before_false(self):
        if self is retained:
            object.__setattr__(self, "delta_sha256", "0" * 64)
        return False

    monkeypatch.setattr(
        base.ReviewPacketDelta, "main_merge_authorized",
        property(mutate_before_false),
    )
    with pytest.raises(mod.DetachedPacketDeltaRejected, match="changed"):
        _check(fixture)


def test_receipt_cannot_claim_payment_or_execution_authority(
    tmp_path, monkeypatch,
):
    fixture = _fixture(tmp_path)
    monkeypatch.setattr(
        base.ReviewPacketDelta, "external_compute_authorized",
        property(lambda self: True),
    )
    with pytest.raises(mod.DetachedPacketDeltaRejected):
        _check(fixture)


def test_arbitrary_object_is_not_detached_review_receipt(tmp_path):
    fixture = list(_fixture(tmp_path))
    fixture[4] = object()
    with pytest.raises(mod.DetachedPacketDeltaRejected, match="exact"):
        _check(fixture)


def _equal_new_string(value):
    copy = (value + "x")[:-1]
    assert copy == value and copy is not value
    return copy


@pytest.mark.parametrize("field", ("delta_sha256", "old_file_sha256", "changed_paths"))
def test_fresh_delta_false_getter_cannot_replace_equal_valued_carrier(
    tmp_path, monkeypatch, field,
):
    fixture = _fixture(tmp_path)
    seen = {}
    original = mod.review_unapproved_packet_delta

    def track_fresh(*args, **kwargs):
        result = original(*args, **kwargs)
        seen["fresh"] = result
        return result

    def reentrant_false(self):
        if self is seen.get("fresh"):
            value = getattr(self, field)
            replacement = (
                tuple(list(value)) if field == "changed_paths"
                else _equal_new_string(value)
            )
            assert replacement == value
            assert replacement is not value
            object.__setattr__(self, field, replacement)
        return False

    monkeypatch.setattr(mod, "review_unapproved_packet_delta", track_fresh)
    monkeypatch.setattr(
        base.ReviewPacketDelta, "main_merge_authorized",
        property(reentrant_false),
    )
    with pytest.raises(mod.DetachedPacketDeltaRejected, match="changed"):
        _check(fixture)


def test_fresh_review_callbacks_cannot_later_grant_retained_authority(
    tmp_path, monkeypatch,
):
    fixture = _fixture(tmp_path)
    retained = fixture[4]
    seen = {"armed": False}

    def reentrant_false(self):
        if self is retained:
            return seen["armed"]
        seen["armed"] = True
        return False

    monkeypatch.setattr(
        base.ReviewPacketDelta, "main_merge_authorized",
        property(reentrant_false),
    )
    with pytest.raises(mod.DetachedPacketDeltaRejected, match="authority"):
        _check(fixture)


def test_false_dataclass_equality_does_not_block_valid_passive_recheck(
    tmp_path, monkeypatch,
):
    fixture = _fixture(tmp_path)
    monkeypatch.setattr(
        base.ReviewPacketDelta, "__eq__", lambda self, other: False,
    )
    assert _check(fixture) is None
