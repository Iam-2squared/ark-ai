"""Reject substituted multimodal source/result getters before private access.

Use uninitialized exact carriers so a malicious descriptor would execute on
the first real field read. No media, files, device capture or network involved.
"""

from __future__ import annotations

import pytest

from ark import offline_observation_transcript as review_module
from ark.offline_pcm_wav import OfflineWaveRequest
from ark.offline_png_inventory import OfflinePngRequest
from ark.offline_transcript_binding import TranscriptSegmentClaim

_SHA = "0" * 64


def _review_uninitialized():
    # Exact types pass the admission shape check; none of their private
    # fields exist. A preaccess guard must reject injected class descriptors
    # before any of those fields are touched.
    return review_module.review_disconnected_observation_transcript(
        object.__new__(OfflinePngRequest),
        object.__new__(OfflineWaveRequest),
        (object.__new__(TranscriptSegmentClaim),),
        retained_owner_sha256=_SHA,
        retained_privacy_sha256=_SHA,
        retained_png_sha256=_SHA,
        retained_wav_sha256=_SHA,
        retained_transcript_fingerprint=_SHA,
    )


@pytest.mark.parametrize(
    ("cls", "field_name"),
    (
        (OfflinePngRequest, "png_bytes"),
        (OfflinePngRequest, "source_sha256"),
        (OfflineWaveRequest, "wav_bytes"),
        (TranscriptSegmentClaim, "text"),
        (TranscriptSegmentClaim, "start_frame"),
        (review_module.OfflineObservationTranscript, "envelope_sha256"),
    ),
)
def test_injected_class_getter_is_not_executed(
    monkeypatch: pytest.MonkeyPatch, cls: type, field_name: str,
) -> None:
    invoked: list[str] = []

    def hostile(_self):
        invoked.append(field_name)
        raise AssertionError("private fixture field touched before descriptor guard")

    with monkeypatch.context() as patch:
        patch.setattr(cls, field_name, property(hostile))
        with pytest.raises(
            review_module.OfflineObservationTranscriptRejected,
            match="carrier or digest callback",
        ):
            _review_uninitialized()
    assert invoked == []


@pytest.mark.parametrize(
    "dependency", ("sha256", "dumps"),
)
def test_replaced_digest_or_json_callback_rejected_before_bytes(
    monkeypatch: pytest.MonkeyPatch, dependency: str,
) -> None:
    invoked: list[str] = []

    def hostile(*_args, **_kwargs):
        invoked.append(dependency)
        raise AssertionError("private fixture was passed to substituted callback")

    target = review_module.hashlib if dependency == "sha256" else review_module.json
    with monkeypatch.context() as patch:
        patch.setattr(target, dependency, hostile)
        with pytest.raises(
            review_module.OfflineObservationTranscriptRejected,
            match="carrier or digest callback",
        ):
            _review_uninitialized()
    assert invoked == []


def test_replaced_report_constructor_never_invoked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked: list[bool] = []

    def hostile(_self, *_args, **_kwargs):
        invoked.append(True)
        raise AssertionError("new report constructor executed")

    with monkeypatch.context() as patch:
        patch.setattr(review_module.OfflineObservationTranscript, "__init__", hostile)
        with pytest.raises(
            review_module.OfflineObservationTranscriptRejected,
            match="carrier or digest callback",
        ):
            _review_uninitialized()
    assert invoked == []
