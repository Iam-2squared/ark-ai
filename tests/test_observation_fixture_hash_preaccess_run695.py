"""Hashing fixture-private bytes must use the import-time SHA-256 primitive.

Local synthetic content hashing is not source authentication, media consent,
or permission to access a camera/microphone, notify, or dispatch tools.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ark.observation_fixture_adapters as adapters
from ark.observations import ObservationKind


@pytest.mark.parametrize("binary", (False, True), ids=("text", "binary"))
@pytest.mark.parametrize("tamper", ("sha256", "module"))
def test_digest_substitution_never_receives_private_fixture_bytes(
    monkeypatch, binary, tamper,
):
    reads = []

    def forbidden_sha256(data=b""):
        reads.append(data)
        pytest.fail("untrusted digest callback received caller-private bytes")

    with monkeypatch.context() as patch:
        if tamper == "module":
            patch.setattr(
                adapters, "hashlib", SimpleNamespace(sha256=forbidden_sha256),
            )
        else:
            patch.setattr(adapters.hashlib, "sha256", forbidden_sha256)

        with pytest.raises(ValueError, match="digest implementation changed"):
            if binary:
                adapters.fixture_binary_observation(
                    b"private-image-fixture", kind=ObservationKind.IMAGE,
                    source_id="offline", privacy_scope="private", ingested_at_ms=11,
                )
            else:
                adapters.fixture_text_observation(
                    "private transcript fixture", kind=ObservationKind.TRANSCRIPT,
                    source_id="offline", privacy_scope="private", ingested_at_ms=11,
                )
    assert reads == []
