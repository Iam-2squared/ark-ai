"""Direct observation IDs reject changed serializers before provenance access.

Only synthetic labels are used. An unreviewed hashing or JSON callback must
not receive private source, adapter, or privacy labels. A deterministic local
ID is not media consent, source attestation, or tool execution authority.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ark.observations as observations


def envelope():
    return observations.ObservationEnvelope(
        observations.ObservationKind.TRANSCRIPT,
        "private-fixture-source", "disconnected-adapter",
        "private", 123, "a" * 64,
    )


@pytest.mark.parametrize(
    "tamper",
    ("sha256-function", "sha256-module", "json-function", "json-module"),
)
def test_substituted_direct_identity_primitive_receives_no_provenance(
    monkeypatch, tamper,
):
    item = envelope()
    original_id = item.observation_id
    accessed = []

    def forbidden(*_args, **_kwargs):
        accessed.append(tamper)
        raise AssertionError("untrusted callback received private metadata")

    with monkeypatch.context() as patch:
        if tamper == "sha256-module":
            patch.setattr(
                observations, "hashlib", SimpleNamespace(sha256=forbidden),
            )
        elif tamper == "sha256-function":
            patch.setattr(observations.hashlib, "sha256", forbidden)
        elif tamper == "json-module":
            patch.setattr(
                observations, "json", SimpleNamespace(dumps=forbidden),
            )
        else:
            patch.setattr(observations.json, "dumps", forbidden)
        with pytest.raises(ValueError, match="digest implementation changed"):
            _ = item.observation_id

    assert accessed == []
    assert item.source_id == "private-fixture-source"
    assert item.privacy_scope == "private"
    assert item.observation_id == original_id
