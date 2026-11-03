"""Review-only V3 packet output: anchored paths and immutable serializer epoch.

This suite does not run Candidate generation, external compute or evaluation.
"""

from pathlib import Path

import pytest

from ark.learning import authorization as mod
from ark.learning.execution import canonical_json


def test_exact_absolute_output_creates_only_inert_canonical_bytes(tmp_path):
    path = tmp_path / "review-only.json"
    packet = {"candidate_created": False, "authorization": {"approved": False}}
    mod._write_new_authorization_packet(path, packet)
    assert path.read_bytes() == canonical_json(packet)


def test_relative_packet_destination_is_not_a_stable_local_identity(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = Path("review-only.json")
    with pytest.raises(ValueError, match="non-aliased"):
        mod._write_new_authorization_packet(path, {"candidate_created": False})
    assert not path.exists()


def test_serializer_must_not_mutate_review_packet_before_output(tmp_path, monkeypatch):
    path = tmp_path / "review-only.json"
    packet = {"candidate_created": False, "budget": {"max_cost_jpy": 0}}
    original = mod.canonical_json

    def swap_after_encoding(value):
        raw = original(value)
        value["candidate_created"] = True
        return raw

    monkeypatch.setattr(mod, "canonical_json", swap_after_encoding)
    with pytest.raises(ValueError, match="changed"):
        mod._write_new_authorization_packet(path, packet)
    assert not path.exists()


def test_nested_list_mutation_after_serializing_is_rejected(tmp_path, monkeypatch):
    path = tmp_path / "review-only.json"
    packet = {"candidate_created": False, "review": ["non-candidate"]}
    original = mod.canonical_json

    def change_nested_after_encoding(value):
        raw = original(value)
        value["review"].append("TRAINING_APPROVED")
        return raw

    monkeypatch.setattr(mod, "canonical_json", change_nested_after_encoding)
    with pytest.raises(ValueError, match="changed"):
        mod._write_new_authorization_packet(path, packet)
    assert not path.exists()


def test_subclass_mapping_is_not_a_review_packet(tmp_path):
    class ForgedPacket(dict):
        pass

    path = tmp_path / "review-only.json"
    with pytest.raises(ValueError, match="exact"):
        mod._write_new_authorization_packet(
            path, ForgedPacket(candidate_created=False),
        )
    assert not path.exists()
