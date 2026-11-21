"""Run751: fixture byte budgets cannot expand across private hash boundaries.

Synthetic caller-provided data only; no capture, consent, or tool execution.
"""

import pytest

from ark import observation_fixture_adapters as adapter
from ark.observations import ObservationKind


def _make(binary):
    args = dict(
        kind=ObservationKind.IMAGE if binary else ObservationKind.TEXT,
        source_id="synthetic-local-source",
        privacy_scope="private:fixture",
        ingested_at_ms=1_234,
    )
    if binary:
        return adapter.fixture_binary_observation(b"private image bytes", **args)
    return adapter.fixture_text_observation("private local text", **args)


@pytest.mark.parametrize("binary", (False, True))
@pytest.mark.parametrize("replacement", (True, 0, 4 * 1024 * 1024 + 1, "unbounded"))
def test_preinstalled_byte_budget_rebinding_refused_before_hash(
    monkeypatch, binary, replacement,
):
    touched = []

    def poisoned_hash(_private):
        touched.append("payload")
        raise AssertionError("private payload reached substituted hash")

    with monkeypatch.context() as patch:
        patch.setattr(adapter, "_MAX_FIXTURE_BYTES", replacement)
        patch.setattr(adapter, "_hash_private_fixture", poisoned_hash)
        with pytest.raises(ValueError, match="fixture byte budget definition changed"):
            _make(binary)
    assert touched == []


@pytest.mark.parametrize("binary", (False, True))
def test_same_value_distinct_budget_object_is_not_original(binary, monkeypatch):
    initial = adapter._MAX_FIXTURE_BYTES
    replacement = int(str(initial))
    assert replacement == initial and replacement is not initial
    with monkeypatch.context() as patch:
        patch.setattr(adapter, "_MAX_FIXTURE_BYTES", replacement)
        with pytest.raises(ValueError, match="fixture byte budget definition changed"):
            _make(binary)


@pytest.mark.parametrize("binary", (False, True))
def test_budget_changed_after_metadata_preflight_is_rejected(
    monkeypatch, binary,
):
    original = adapter._preflight_fixture_metadata
    encountered = []

    def change_budget(*args, **kwargs):
        original(*args, **kwargs)
        encountered.append("preflight")
        monkeypatch.setattr(adapter, "_MAX_FIXTURE_BYTES", 2**30)

    monkeypatch.setattr(adapter, "_preflight_fixture_metadata", change_budget)
    with pytest.raises(ValueError, match="fixture byte budget definition changed"):
        _make(binary)
    assert encountered == ["preflight"]


@pytest.mark.parametrize("binary", (False, True))
def test_original_fixture_byte_budget_still_seals_without_raw_payload(binary):
    envelope = _make(binary)
    assert envelope.kind is (
        ObservationKind.IMAGE if binary else ObservationKind.TEXT
    )
    assert len(envelope.content_sha256) == 64
    assert not hasattr(envelope, "raw_bytes")
    assert not hasattr(envelope, "payload")
