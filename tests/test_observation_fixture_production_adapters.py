"""Executable contracts for explicitly disconnected, payload-minimizing adapters."""

import hashlib
from dataclasses import fields

import pytest

from ark.observation_fixture_adapters import (
    fixture_binary_observation,
    fixture_text_observation,
)
from ark.observation_lineage_review import review_synthetic_observation_lineage
from ark.observations import ObservationEnvelope, ObservationKind


def text(content="hello", **overrides):
    options = {
        "kind": ObservationKind.TEXT,
        "source_id": "fixture-source",
        "privacy_scope": "offline:test",
        "ingested_at_ms": 100,
    }
    options.update(overrides)
    return fixture_text_observation(content, **options)


def binary(payload=b"image", **overrides):
    options = {
        "kind": ObservationKind.IMAGE,
        "source_id": "fixture-source",
        "privacy_scope": "offline:test",
        "ingested_at_ms": 100,
    }
    options.update(overrides)
    return fixture_binary_observation(payload, **options)


def test_unicode_text_and_transcript_have_content_minimized_deterministic_ids():
    payload = "日本語を含むローカルFixture"
    left = text(payload)
    repeat = text(payload)
    transcript = text(payload, kind=ObservationKind.TRANSCRIPT)
    assert left == repeat
    assert left.observation_id == repeat.observation_id
    assert left.content_sha256 == hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert transcript.content_sha256 == left.content_sha256
    assert transcript.observation_id != left.observation_id
    assert left.adapter_id == "fixture:text:v1"
    assert transcript.adapter_id == "fixture:transcript:v1"
    assert all(field.name not in {"content", "payload", "raw_bytes"} for field in fields(left))
    assert payload not in repr(left)


def test_image_and_screen_have_distinct_adapter_bound_identifiers():
    image = binary(b"synthetic-pixels")
    screen = binary(b"synthetic-pixels", kind=ObservationKind.SCREEN)
    assert image.content_sha256 == screen.content_sha256
    assert image.observation_id != screen.observation_id
    assert screen.adapter_id == "fixture:screen:v1"
    assert isinstance(image, ObservationEnvelope)


@pytest.mark.parametrize("kind", [ObservationKind.IMAGE, ObservationKind.SCREEN, "text", True])
def test_text_fixture_rejects_invalid_kind(kind):
    with pytest.raises(ValueError, match="TEXT or TRANSCRIPT"):
        text(kind=kind)


@pytest.mark.parametrize("kind", [ObservationKind.TEXT, ObservationKind.TRANSCRIPT, "image", True])
def test_binary_fixture_rejects_invalid_kind(kind):
    with pytest.raises(ValueError, match="IMAGE or SCREEN"):
        binary(kind=kind)


def test_fixture_rejects_subclasses_and_malformed_unicode():
    class UserText(str):
        pass

    class UserBytes(bytes):
        pass

    with pytest.raises(TypeError, match="exact string"):
        text(UserText("raw"))
    with pytest.raises(TypeError, match="exact bytes"):
        binary(UserBytes(b"raw"))
    with pytest.raises(ValueError, match="valid UTF-8"):
        text("\ud800")


@pytest.mark.parametrize(
    "factory,payload",
    [(text, "a" * (4 * 1024 * 1024 + 1)), (binary, b"a" * (4 * 1024 * 1024 + 1))],
    ids=("text-over-byte-limit", "binary-over-byte-limit"),
)
def test_fixture_rejects_oversized_payload(factory, payload):
    with pytest.raises(ValueError, match="byte budget exceeded"):
        factory(payload)


def test_multibyte_text_byte_budget_is_measured_after_encoding():
    with pytest.raises(ValueError, match="byte budget exceeded"):
        text("🚀" * (1024 * 1024 + 1))


def test_empty_payload_is_deterministic_and_never_implicit_consent():
    empty = text("")
    assert empty.content_sha256 == hashlib.sha256(b"").hexdigest()
    assert empty.observation_id.startswith("obs_")
    for field in ("authorization", "capability", "token", "backend", "tool_call"):
        assert not hasattr(empty, field)


def test_privacy_scope_source_and_parent_remain_bound_to_identity():
    base = text("private fixture")
    assert (
        text("private fixture", privacy_scope="offline:other").observation_id
        != base.observation_id
    )
    assert text("private fixture", source_id="other").observation_id != base.observation_id
    child = text("private fixture", parent_sha256="a" * 64)
    assert child.observation_id != base.observation_id


def test_parent_fixture_chain_can_be_checked_without_sensing_or_dispatch():
    parent = text("root", ingested_at_ms=100)
    child = text(
        "derived",
        kind=ObservationKind.TRANSCRIPT,
        ingested_at_ms=101,
        parent_sha256=parent.content_sha256,
    )
    review = review_synthetic_observation_lineage(
        (parent, child),
        privacy_scope="offline:test",
        now_ms=102,
        max_age_ms=10,
    )
    assert review.observation_count == 2
    assert not review.media_capture_authorized
    assert not review.disclosure_authorized
    assert not review.dispatch_authorized


def test_invalid_metadata_is_rejected_by_existing_envelope_contract():
    with pytest.raises(ValueError, match="exact string"):
        text("hello", privacy_scope="")
    with pytest.raises(ValueError, match="exact integer"):
        binary(b"fixture", ingested_at_ms=True)
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        text("hello", parent_sha256="not-a-digest")
