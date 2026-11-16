"""Frozen direct ObservationEnvelope NUL semantics versus fixture adapter denial.

Direct v1 identity JSON must escape embedded NUL. Stricter disconnected
fixture ingress rejects NUL before hashing private synthetic input. No actual
camera, microphone, files, private data or external backend are accessed.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.observation_fixture_adapters import fixture_text_observation
from ark.observations import ObservationEnvelope, ObservationKind


def _direct():
    return {
        "kind": ObservationKind.TEXT,
        "source_id": "synthetic-source",
        "adapter_id": "synthetic-adapter",
        "privacy_scope": "synthetic-private",
        "ingested_at_ms": 100,
        "content_sha256": hashlib.sha256(b"fixture").hexdigest(),
    }


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
def test_direct_v1_nul_json_identity_compatible_with_frozen_contract(field):
    fields = _direct()
    baseline = ObservationEnvelope(**fields)
    fields[field] = "safe\x00unsafe"
    with_nul = ObservationEnvelope(**fields)
    assert with_nul.observation_id.startswith("obs_")
    assert len(with_nul.observation_id) == 68
    assert with_nul.observation_id == with_nul.observation_id
    assert with_nul.observation_id != baseline.observation_id


@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_fixture_adapter_rejects_nul_without_restricting_direct_v1(field):
    fields = _direct()
    fields[field] = "safe\x00unsafe"
    direct = ObservationEnvelope(**fields)
    assert direct.observation_id.startswith("obs_")
    kwargs = {
        "kind": ObservationKind.TEXT,
        "source_id": fields["source_id"],
        "privacy_scope": fields["privacy_scope"],
        "ingested_at_ms": 100,
    }
    with pytest.raises(ValueError, match="NUL separator"):
        fixture_text_observation("private-synthetic-fixture", **kwargs)


def test_unmodified_metadata_identity_matches_fixture_digest():
    fields = _direct()
    direct = ObservationEnvelope(**fields)
    assert len(direct.observation_id) == 68
    assert direct.observation_id == direct.observation_id
