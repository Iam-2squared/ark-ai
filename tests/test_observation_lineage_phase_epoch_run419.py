"""Boundary-accurate offline lineage checks, without sensor or dispatch authority."""

import hashlib

import pytest

import ark.observation_lineage_review as lineage
from ark.observations import ObservationEnvelope, ObservationKind


def _sample():
    root = ObservationEnvelope(
        ObservationKind.TEXT, "source-long", "adapter-one", "private-only",
        100, hashlib.sha256(b"root").hexdigest(),
    )
    child = ObservationEnvelope(
        ObservationKind.TEXT, "source-long", "adapter-two", "private-only",
        101, hashlib.sha256(b"child").hexdigest(), root.content_sha256,
    )
    return root, child


def _review(root, child):
    return lineage.review_synthetic_observation_lineage(
        (root, child), privacy_scope="private-only", now_ms=110, max_age_ms=20,
    )


@pytest.mark.parametrize("field,bad", [
    ("source_id", "source-other"),
    ("adapter_id", "adapter-other"),
    ("privacy_scope", "different-scope"),
    ("parent_sha256", "f" * 64),
])
def test_interphase_json_metadata_retarget_restored_by_sha_is_denied(
    monkeypatch, field, bad,
):
    root, child = _sample()
    old = getattr(root, field)
    original_json = lineage.json.dumps
    original_sha = lineage.hashlib.sha256
    touched = []

    def json_hook(value, *args, **kwargs):
        encoded = original_json(value, *args, **kwargs)
        if type(value) is tuple and value and value[0] == 1:
            object.__setattr__(root, field, bad)
            touched.append("changed")
        return encoded

    def sha_hook(value):
        if value.startswith(b"ARK-observation-lineage-v1" + bytes([0])):
            object.__setattr__(root, field, old)
            touched.append("restored")
        return original_sha(value)

    monkeypatch.setattr(lineage.json, "dumps", json_hook)
    monkeypatch.setattr(lineage.hashlib, "sha256", sha_hook)
    with pytest.raises(lineage.SyntheticObservationLineageRejected, match="epoch"):
        _review(root, child)
    assert touched == ["changed"]


def test_hash_phase_tamper_cannot_be_hidden_by_result_constructor(monkeypatch):
    root, child = _sample()
    original_sha = lineage.hashlib.sha256
    original_constructor = lineage.SyntheticObservationLineageWitness
    old = root.source_id
    touched = []

    def sha_hook(value):
        result = original_sha(value)
        if value.startswith(b"ARK-observation-lineage-v1" + bytes([0])):
            object.__setattr__(root, "source_id", "redirected")
            touched.append("changed")
        return result

    def constructor(*args, **kwargs):
        object.__setattr__(root, "source_id", old)
        touched.append("restored")
        return original_constructor(*args, **kwargs)

    monkeypatch.setattr(lineage.hashlib, "sha256", sha_hook)
    monkeypatch.setattr(lineage, "SyntheticObservationLineageWitness", constructor)
    with pytest.raises(lineage.SyntheticObservationLineageRejected, match="epoch"):
        _review(root, child)
    assert touched == ["changed"]


def test_unchanged_parent_lineage_remains_deterministic_and_inert():
    root, child = _sample()
    first = _review(root, child)
    second = _review(child, root)
    assert first.lineage_digest == second.lineage_digest
    assert first.observation_count == 2
    assert first.media_capture_authorized is False
    assert first.disclosure_authorized is False
    assert first.dispatch_authorized is False
    assert "source-long" not in repr(first)
