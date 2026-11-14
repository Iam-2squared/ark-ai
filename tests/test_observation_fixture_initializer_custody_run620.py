"""Disconnected Observation adapters reject hostile dataclass initializers.

No raw payload is retained by the returned envelope; no device, filesystem,
network, microphone, camera, disclosure or authenticated identity is involved.
"""

import hashlib

import pytest

from ark import observation_fixture_adapters as adapters
from ark.observations import ObservationEnvelope, ObservationKind


def _fixture(binary):
    if binary:
        return adapters.fixture_binary_observation(
            b"safe-fixture", kind=ObservationKind.IMAGE,
            source_id="offline", privacy_scope="private", ingested_at_ms=1,
        )
    return adapters.fixture_text_observation(
        "safe-fixture", kind=ObservationKind.TEXT,
        source_id="offline", privacy_scope="private", ingested_at_ms=1,
    )


@pytest.mark.parametrize("binary", (False, True))
@pytest.mark.parametrize("phase", ("before", "digest"))
def test_substituted_initializer_is_not_executed(
    monkeypatch, binary, phase,
):
    calls = []

    def hostile_init(*_args, **_kwargs):
        calls.append("entered")
        raise AssertionError("hostile Observation initializer executed")

    with monkeypatch.context() as patch:
        if phase == "before":
            patch.setattr(ObservationEnvelope, "__init__", hostile_init)
        else:
            old_sha256 = hashlib.sha256

            def changed_hash(data=b""):
                if data == b"safe-fixture":
                    patch.setattr(ObservationEnvelope, "__init__", hostile_init)
                return old_sha256(data)

            patch.setattr(adapters.hashlib, "sha256", changed_hash)
        expected = "digest implementation" if phase == "digest" else "non-envelope"
        with pytest.raises(ValueError, match=expected):
            _fixture(binary)

    assert calls == []


def test_postinit_initializer_replacement_is_rejected_at_return(monkeypatch):
    old_post_init = ObservationEnvelope.__post_init__
    calls = []

    def hostile_init(*_args, **_kwargs):
        calls.append("entered")
        raise AssertionError("hostile initializer must not run")

    with monkeypatch.context() as patch:
        def post_init_and_replace(self):
            old_post_init(self)
            patch.setattr(ObservationEnvelope, "__init__", hostile_init)

        patch.setattr(ObservationEnvelope, "__post_init__", post_init_and_replace)
        with pytest.raises(ValueError, match="changed during construction"):
            _fixture(False)

    assert calls == []


def test_original_fixture_remains_content_minimized():
    result = _fixture(False)
    assert type(result) is ObservationEnvelope
    assert result.content_sha256 == hashlib.sha256(b"safe-fixture").hexdigest()
    assert result.privacy_scope == "private"
    assert not hasattr(result, "raw_content")
