"""Run1380: the fixture text encoder survives simultaneous alias rebinding."""

from __future__ import annotations

import pytest

from ark import observation_fixture_adapters as adapters
from ark.observations import ObservationKind


@pytest.mark.parametrize(
    "replace_after_preflight",
    (False, True),
    ids=("preinstalled-replacement", "replacement-during-preflight"),
)
def test_simultaneous_encoder_alias_and_vector_replacement_is_denied(
    monkeypatch: pytest.MonkeyPatch,
    replace_after_preflight: bool,
) -> None:
    encoder_inputs: list[str] = []
    hash_inputs: list[bytes] = []
    original_preflight = adapters._preflight_fixture_metadata

    def forbidden_encoder(content: str, max_bytes: int) -> bytes:
        encoder_inputs.append(content)
        raise AssertionError("replacement encoder received private fixture text")

    def forbidden_hash(payload: bytes) -> str:
        hash_inputs.append(payload)
        raise AssertionError("private fixture bytes reached hashing after encoder drift")

    def replace_all_aliases(patch: pytest.MonkeyPatch) -> None:
        forged_vector = (forbidden_encoder,)
        patch.setattr(adapters, "_encode_fixture_text_bounded", forbidden_encoder)
        patch.setattr(adapters, "_ORIGINAL_BOUNDED_TEXT_ENCODER", forbidden_encoder)
        patch.setattr(
            adapters, "_ORIGINAL_BOUNDED_TEXT_ENCODER_VECTOR", forged_vector,
        )
        patch.setattr(
            adapters, "_ORIGINAL_BOUNDED_TEXT_ENCODER_VECTOR_EPOCH", forged_vector,
        )

    with monkeypatch.context() as patch:
        patch.setattr(adapters, "_hash_private_fixture", forbidden_hash)
        if replace_after_preflight:

            def preflight_then_replace(*args: object, **kwargs: object) -> None:
                original_preflight(*args, **kwargs)
                replace_all_aliases(patch)

            patch.setattr(
                adapters, "_preflight_fixture_metadata", preflight_then_replace,
            )
        else:
            replace_all_aliases(patch)

        with pytest.raises(ValueError, match="fixture text encoder identity changed"):
            adapters.fixture_text_observation(
                "synthetic private transcript",
                kind=ObservationKind.TRANSCRIPT,
                source_id="synthetic-source",
                privacy_scope="private:fixture",
                ingested_at_ms=1234,
            )

    assert encoder_inputs == []
    assert hash_inputs == []
