"""Exact UTF-8 byte budgets for disconnected observation identifiers.

A 1024-character non-ASCII label can occupy far more than 1024 serialized
bytes. The envelope and observation ID must share a bounded metadata image.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.observations import ObservationEnvelope, ObservationKind


def _envelope(**overrides):
    fields = {
        "kind": ObservationKind.TEXT,
        "source_id": "fixture-source",
        "adapter_id": "fixture:text:v1",
        "privacy_scope": "local:private",
        "ingested_at_ms": 100,
        "content_sha256": hashlib.sha256(b"synthetic").hexdigest(),
    }
    fields.update(overrides)
    return ObservationEnvelope(**fields)


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
@pytest.mark.parametrize(
    ("valid", "too_large"),
    [
        ("界" * 341, "界" * 342),  # 1023 vs 1026 UTF-8 bytes
        ("🗺" * 256, "🗺" * 257),  # 1024 vs 1028 UTF-8 bytes
    ],
)
def test_identifier_budget_counts_encoded_bytes_not_unicode_codepoints(
    field, valid, too_large,
):
    assert len(valid.encode("utf-8")) <= 1024
    assert len(too_large) < 1024
    accepted = _envelope(**{field: valid})
    assert getattr(accepted, field) == valid
    assert accepted.observation_id.startswith("obs_")
    with pytest.raises(ValueError, match="identifier budget"):
        _envelope(**{field: too_large})


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
def test_invalid_utf8_label_still_rejected_before_identity_hashing(field):
    with pytest.raises(ValueError, match="valid UTF-8"):
        _envelope(**{field: "bad" + chr(0xD800)})
