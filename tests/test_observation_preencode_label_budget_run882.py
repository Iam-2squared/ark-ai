"""Synthetic observation labels must be bounded before expensive text work.

No microphone, camera, screen, network, or real observer is activated.
"""

import pytest

from ark import observations


def _envelope(**fields: object) -> observations.ObservationEnvelope:
    values: dict[str, object] = {
        "kind": observations.ObservationKind.TEXT,
        "source_id": "local-source",
        "adapter_id": "disconnected-fixture",
        "privacy_scope": "local-private",
        "ingested_at_ms": 0,
        "content_sha256": "a" * 64,
    }
    values.update(fields)
    return observations.ObservationEnvelope(**values)


@pytest.mark.parametrize("field", ("source_id", "adapter_id", "privacy_scope"))
@pytest.mark.parametrize("value", ("x" * 1025, " " * 1025))
def test_oversized_text_refused_before_digest(
    monkeypatch: pytest.MonkeyPatch, field: str, value: str,
) -> None:
    def prohibited_digest(*args: object, **kwargs: object) -> None:
        raise AssertionError("oversized label reached content digest review")

    monkeypatch.setattr(observations, "_digest", prohibited_digest)
    with pytest.raises(ValueError, match="exceeds observation identifier budget"):
        _envelope(**{field: value})


@pytest.mark.parametrize(
    ("label", "allowed"),
    (
        ("x" * 1024, True),
        ("x" * 1025, False),
        ("é" * 512, True),
        ("é" * 513, False),
        ("🪐" * 256, True),
        ("🪐" * 257, False),
    ),
)
def test_character_and_utf8_byte_limits_remain_independent(
    label: str, allowed: bool,
) -> None:
    if allowed:
        assert _envelope(source_id=label).source_id == label
    else:
        with pytest.raises(ValueError, match="observation identifier budget"):
            _envelope(source_id=label)


def test_unpaired_surrogate_is_rejected_as_invalid_utf8() -> None:
    with pytest.raises(ValueError, match="not valid UTF-8 text"):
        _envelope(adapter_id="invalid" + chr(0xD800))
