import hashlib

import pytest

from ark.observations import ObservationEnvelope, ObservationKind


def _text_fixture(
    text,
    *,
    source_id="fixture-text",
    privacy_scope="local:test",
    ingested_at_ms=1,
    parent_sha256=None,
    adapter_id="fixture:text:v1",
):
    if type(text) is not str:
        raise TypeError("fixture text must be an exact string")
    return ObservationEnvelope(
        kind=ObservationKind.TEXT,
        source_id=source_id,
        adapter_id=adapter_id,
        privacy_scope=privacy_scope,
        ingested_at_ms=ingested_at_ms,
        content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        parent_sha256=parent_sha256,
    )


def _binary_fixture(
    payload,
    *,
    kind,
    source_id="fixture-binary",
    privacy_scope="local:test",
    ingested_at_ms=1,
    parent_sha256=None,
    adapter_id="fixture:binary:v1",
):
    if type(payload) is not bytes:
        raise TypeError("fixture payload must be exact bytes")
    if type(kind) is not ObservationKind or kind not in {
        ObservationKind.IMAGE,
        ObservationKind.SCREEN,
    }:
        raise ValueError("fixture kind must be exact IMAGE or SCREEN")
    return ObservationEnvelope(
        kind=kind,
        source_id=source_id,
        adapter_id=adapter_id,
        privacy_scope=privacy_scope,
        ingested_at_ms=ingested_at_ms,
        content_sha256=hashlib.sha256(payload).hexdigest(),
        parent_sha256=parent_sha256,
    )


def test_text_fixture_hashes_content_without_retaining_plaintext():
    envelope = _text_fixture("hello")
    assert envelope.content_sha256 == hashlib.sha256(b"hello").hexdigest()
    assert not hasattr(envelope, "text")
    assert not hasattr(envelope, "raw_bytes")


def test_text_fixture_rejects_string_subclasses():
    class TextAlias(str):
        pass

    with pytest.raises(TypeError, match="exact string"):
        _text_fixture(TextAlias("hello"))


def test_binary_fixture_accepts_image_and_screen_only():
    image = _binary_fixture(b"image", kind=ObservationKind.IMAGE)
    screen = _binary_fixture(b"screen", kind=ObservationKind.SCREEN)
    assert image.kind is ObservationKind.IMAGE
    assert screen.kind is ObservationKind.SCREEN

    with pytest.raises(ValueError, match="IMAGE or SCREEN"):
        _binary_fixture(b"text", kind=ObservationKind.TEXT)


def test_binary_fixture_rejects_bytes_subclasses():
    class BytesAlias(bytes):
        pass

    with pytest.raises(TypeError, match="exact bytes"):
        _binary_fixture(BytesAlias(b"image"), kind=ObservationKind.IMAGE)


def test_parent_digest_is_bound_into_fixture_identity():
    base = _text_fixture("hello")
    child = _text_fixture("hello", parent_sha256="a" * 64)
    assert child.observation_id != base.observation_id


def test_adapter_identity_is_bound_into_fixture_identity():
    left = _text_fixture("hello", adapter_id="fixture:a")
    right = _text_fixture("hello", adapter_id="fixture:b")
    assert left.observation_id != right.observation_id


def test_privacy_scope_is_bound_into_fixture_identity():
    left = _text_fixture("hello", privacy_scope="local:a")
    right = _text_fixture("hello", privacy_scope="local:b")
    assert left.observation_id != right.observation_id


def test_fixture_observations_grant_no_action_authority():
    envelope = _text_fixture("hello")
    for field in ("capability", "authorization", "token", "tool_call", "backend"):
        assert not hasattr(envelope, field)
