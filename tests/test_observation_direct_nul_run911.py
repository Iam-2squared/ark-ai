"""Direct observation envelopes and fixture adapters share a NUL boundary.

Synthetic labels only; no camera, microphone, file acquisition, private
source, external authorization or real observation capture is involved.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.observations import ObservationEnvelope, ObservationKind


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
def test_direct_observation_refuses_embedded_native_nul(field):
    kwargs = {
        "kind": ObservationKind.TEXT,
        "source_id": "synthetic-source",
        "adapter_id": "synthetic-adapter",
        "privacy_scope": "synthetic-private",
        "ingested_at_ms": 100,
        "content_sha256": hashlib.sha256(b"fixture").hexdigest(),
    }
    kwargs[field] = "safe" + "\x00" + "unsafe"
    with pytest.raises(ValueError, match="NUL separator"):
        ObservationEnvelope(**kwargs)


def test_exact_boundary_labels_still_bind_inert_identity():
    receipt = ObservationEnvelope(
        kind=ObservationKind.TRANSCRIPT,
        source_id="synthetic-stream",
        adapter_id="mock-microphone-no-access",
        privacy_scope="private-fixture",
        ingested_at_ms=100,
        content_sha256=hashlib.sha256(b"synthetic-transcript").hexdigest(),
    )
    assert receipt.observation_id.startswith("obs_")
    assert len(receipt.observation_id) == 68
    assert receipt.observation_id == receipt.observation_id
