"""Disconnected PNG/WAV metadata joins must reject executable result substitutions.

Only in-memory synthetic fixture bytes are used. No device access, raw
media export, consent assertion, or ToolBackend execution is involved.
"""

import pytest
from test_offline_observation_pair_run563 import _case, _inspect

import ark.offline_observation_pair as pair


@pytest.mark.parametrize("moment", ("preinstalled", "after_first_png", "after_second_wav"))
def test_modified_pair_initializer_never_runs(monkeypatch, moment):
    image, audio, pins = _case()
    attempts = []

    def forbidden(*_args, **_kwargs):
        attempts.append("forged pair constructor executed")
        raise AssertionError("forged observation constructor should not run")

    with monkeypatch.context() as patch:
        if moment == "preinstalled":
            patch.setattr(pair.OfflineObservationPair, "__init__", forbidden)

            def no_png(*_args, **_kwargs):
                raise AssertionError("changed result class must fail before media parsing")

            patch.setattr(pair, "inspect_disconnected_png", no_png)
        elif moment == "after_first_png":
            native = pair.inspect_disconnected_png

            def after_png(value):
                measured = native(value)
                patch.setattr(pair.OfflineObservationPair, "__init__", forbidden)
                return measured

            patch.setattr(pair, "inspect_disconnected_png", after_png)
        else:
            native = pair.inspect_local_pcm_wav
            calls = []

            def after_second_wav(value):
                measured = native(value)
                calls.append(1)
                if len(calls) == 2:
                    patch.setattr(pair.OfflineObservationPair, "__init__", forbidden)
                return measured

            patch.setattr(pair, "inspect_local_pcm_wav", after_second_wav)

        with pytest.raises(pair.OfflineObservationPairRejected, match="descriptor replaced"):
            _inspect(image, audio, pins)

    assert attempts == []


@pytest.mark.parametrize("field", (
    "camera_provenance_verified", "microphone_provenance_verified",
    "consent_verified", "external_disclosure_authorized",
    "tool_execution_authorized",
))
def test_class_level_descriptor_getter_never_runs(monkeypatch, field):
    image, audio, pins = _case()
    invoked = []

    class CounterfeitDescriptor:
        def __get__(self, instance, owner=None):
            invoked.append((instance, owner))
            raise AssertionError("untrusted class-level descriptor executed")

    with monkeypatch.context() as patch:
        patch.setattr(pair.OfflineObservationPair, field, CounterfeitDescriptor())
        with pytest.raises(pair.OfflineObservationPairRejected, match="descriptor replaced"):
            _inspect(image, audio, pins)
    assert invoked == []


def test_rebound_pair_class_is_rejected_before_media_parsing(monkeypatch):
    image, audio, pins = _case()
    original = pair.OfflineObservationPair

    class Counterfeit(original):
        pass

    with monkeypatch.context() as patch:
        patch.setattr(pair, "OfflineObservationPair", Counterfeit)

        def no_png(*_args, **_kwargs):
            raise AssertionError("class replacement must fail before media parsing")

        patch.setattr(pair, "inspect_disconnected_png", no_png)
        with pytest.raises(pair.OfflineObservationPairRejected, match="descriptor replaced"):
            _inspect(image, audio, pins)


def test_original_pair_stays_metadata_only_and_deny_only():
    image, audio, pins = _case()
    review = _inspect(image, audio, pins)
    assert review.width == 1
    assert review.height == 1
    assert review.sample_rate_hz == 16000
    assert review.audio_frames == 16
    assert all(getattr(review, flag) is False for flag in pair._DENIALS)
    assert image.png_bytes.hex() not in repr(review)
    assert audio.wav_bytes.hex() not in repr(review)
