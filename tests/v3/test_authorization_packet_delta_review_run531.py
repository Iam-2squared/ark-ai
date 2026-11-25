"""Read-only comparison of unapproved V3 packets; no model or GPU work."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ark.learning import authorization as auth
from ark.learning import authorization_packet_delta_review as mod
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


def _save(tmp_path, tag, snapshot):
    packet = auth.build_preflight_authorization_packet(snapshot)
    path = tmp_path / (tag + ".json")
    auth._write_new_authorization_packet(path, packet)
    return path, sha256_bytes(path.read_bytes())


def _inputs(tmp_path, *, changed=True):
    old = _snapshot()
    new = deepcopy(old)
    if changed:
        new["budget"]["max_cost_jpy"] = 1500
    old_path, old_hash = _save(tmp_path, "old", old)
    new_path, new_hash = _save(tmp_path, "new", new)
    return old, new, old_path, new_path, old_hash, new_hash


def _compare(inputs):
    old, new, old_path, new_path, old_hash, new_hash = inputs
    return mod.review_unapproved_packet_delta(
        old, new, old_path, new_path,
        retained_old_file_sha256=old_hash,
        retained_new_file_sha256=new_hash,
    )


def test_unapproved_saved_packet_delta_reports_only_field_paths(tmp_path):
    inputs = _inputs(tmp_path)
    outcome = _compare(inputs)
    assert "budget.max_cost_jpy" in outcome.changed_paths
    assert "execution_snapshot_sha256" in outcome.changed_paths
    assert "packet_sha256" in outcome.changed_paths
    assert "1500" not in str(outcome.changed_paths)
    assert outcome.old_file_sha256 == inputs[4]
    assert outcome.new_file_sha256 == inputs[5]
    assert len(outcome.delta_sha256) == 64
    assert outcome.external_compute_authorized is False
    assert outcome.candidate_generation_authorized is False
    assert outcome.protected_evaluation_authorized is False
    assert outcome.main_merge_authorized is False


def test_identical_unapproved_packets_do_not_fabricate_changes(tmp_path):
    inputs = _inputs(tmp_path, changed=False)
    outcome = _compare(inputs)
    assert outcome.changed_paths == ()
    assert outcome.old_file_sha256 == outcome.new_file_sha256


def test_two_changed_identity_fields_are_both_disclosed_by_name_only(tmp_path):
    old = _snapshot()
    new = deepcopy(old)
    new["base"]["revision"] = "6" * 40
    new["dataset"]["canonical_sha256"] = "7" * 64
    old_path, old_hash = _save(tmp_path, "before", old)
    new_path, new_hash = _save(tmp_path, "after", new)
    result = _compare((old, new, old_path, new_path, old_hash, new_hash))
    assert "base.revision" in result.changed_paths
    assert "dataset.canonical_sha256" in result.changed_paths
    assert "6" * 40 not in str(result.changed_paths)
    assert "7" * 64 not in str(result.changed_paths)


@pytest.mark.parametrize("which", ("old", "new", "bool"))
def test_stale_or_noncanonical_retained_digest_fails_closed(tmp_path, which):
    values = list(_inputs(tmp_path))
    if which == "old":
        values[4] = "f" * 64 if values[4] != "f" * 64 else "0" * 64
    elif which == "new":
        values[5] = "f" * 64 if values[5] != "f" * 64 else "0" * 64
    else:
        values[5] = True
    with pytest.raises(mod.ReviewPacketDeltaRejected):
        _compare(values)


@pytest.mark.parametrize("which", ("old", "new"))
def test_mutated_packet_file_after_review_save_is_denied(tmp_path, which):
    values = _inputs(tmp_path)
    path = values[2 if which == "old" else 3]
    raw = path.read_bytes()
    path.write_bytes(b"X" + raw[1:])
    with pytest.raises(mod.ReviewPacketDeltaRejected):
        _compare(values)


def test_source_snapshot_mutation_during_comparison_denied(tmp_path, monkeypatch):
    inputs = _inputs(tmp_path)
    original = mod._leaf_bytes
    calls = 0

    def mutate_later(packet):
        nonlocal calls
        result = original(packet)
        calls += 1
        if calls == 2:
            inputs[1]["budget"]["max_cost_jpy"] = 1750
        return result

    monkeypatch.setattr(mod, "_leaf_bytes", mutate_later)
    with pytest.raises(mod.ReviewPacketDeltaRejected):
        _compare(inputs)


def test_file_changed_during_post_comparison_revalidation_denied(
    tmp_path, monkeypatch,
):
    inputs = _inputs(tmp_path)
    original = mod.verify_local_authorization_packet_file
    calls = 0

    def mutate_after_fourth(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == 4:
            raw = inputs[2].read_bytes()
            inputs[2].write_bytes(b"X" + raw[1:])
        return result

    monkeypatch.setattr(
        mod, "verify_local_authorization_packet_file", mutate_after_fourth,
    )
    with pytest.raises(mod.ReviewPacketDeltaRejected):
        _compare(inputs)


def test_delta_cannot_gain_merge_authority(tmp_path, monkeypatch):
    inputs = _inputs(tmp_path)
    monkeypatch.setattr(
        mod.ReviewPacketDelta, "main_merge_authorized",
        property(lambda self: True),
    )
    with pytest.raises(mod.ReviewPacketDeltaRejected):
        _compare(inputs)


def test_true_approval_flag_is_rejected_before_comparison(tmp_path):
    values = list(_inputs(tmp_path))
    values[1]["authorization"]["external_compute_authorized"] = True
    with pytest.raises(mod.ReviewPacketDeltaRejected):
        _compare(values)


def test_frozen_experiment_method_mutation_is_not_approved(tmp_path):
    values = list(_inputs(tmp_path))
    values[1]["method"]["rank"] = 16
    with pytest.raises(mod.ReviewPacketDeltaRejected):
        _compare(values)
