"""Disconnected PNG + WAV metadata envelope for explicit synthetic fixtures.

This passive join inspects no device, stores no pixels/samples and performs no
ASR or perception. Matching caller-supplied hashes do not authenticate owner,
provenance, consent or independent historical custody. It grants no actions.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .offline_pcm_wav import (
    OfflineWaveRejected,
    OfflineWaveRequest,
    OfflineWaveReview,
    inspect_local_pcm_wav,
)
from .offline_png_inventory import (
    OfflinePngInventory,
    OfflinePngRejected,
    OfflinePngRequest,
    inspect_disconnected_png,
)

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-offline-observation-pair-v1\0"
_DENIALS = (
    "camera_provenance_verified", "microphone_provenance_verified",
    "consent_verified", "external_disclosure_authorized",
    "tool_execution_authorized",
)


class OfflineObservationPairRejected(ValueError):
    """Untrusted local image/audio metadata cannot be joined safely."""


@dataclass(frozen=True, slots=True)
class OfflineObservationPair:
    owner_sha256: str
    privacy_sha256: str
    png_sha256: str
    wav_sha256: str
    width: int
    height: int
    image_idat_sha256: str
    sample_rate_hz: int
    audio_frames: int
    pcm_sha256: str
    pair_sha256: str

    @property
    def camera_provenance_verified(self) -> bool:
        return False

    @property
    def microphone_provenance_verified(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def external_disclosure_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


_RESULT = OfflineObservationPair
_ORIGINAL_RESULT_INIT = vars(_RESULT)["__init__"]
_ORIGINAL_DENIALS = tuple(vars(_RESULT)[name] for name in _DENIALS)


def _original_denials() -> None:
    # Static class-dict inspection never executes an injected __get__. A
    # forged initializer or a rebound class is equally unauthorized, even
    # if each returned property still appears to be False.
    if (
        OfflineObservationPair is not _RESULT
        or vars(_RESULT).get("__init__") is not _ORIGINAL_RESULT_INIT
        or any(
            vars(_RESULT).get(name) is not old
            for name, old in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise OfflineObservationPairRejected(
            "observation pair authority descriptor replaced"
        )


def inspect_disconnected_observation_pair(
    image: OfflinePngRequest,
    audio: OfflineWaveRequest,
    *,
    retained_owner_sha256: str,
    retained_privacy_sha256: str,
    retained_png_sha256: str,
    retained_wav_sha256: str,
) -> OfflineObservationPair:
    """Join two exact local fixture inventories without raw output or dispatch.

    All four retained hashes must come from independently retained evidence
    if they are to detect historical substitution. Reinspection is not a
    coherent cross-device transaction or proof of an actual capture.
    """
    _original_denials()
    if type(image) is not OfflinePngRequest or type(audio) is not OfflineWaveRequest:
        raise OfflineObservationPairRejected("exact observation requests required")
    retained = (
        retained_owner_sha256, retained_privacy_sha256,
        retained_png_sha256, retained_wav_sha256,
    )
    if any(type(x) is not str or _SHA.fullmatch(x) is None for x in retained):
        raise OfflineObservationPairRejected(
            "exact retained observation hashes required"
        )
    pinned_image = (
        image.owner_sha256, image.privacy_sha256,
        image.source_sha256, image.png_bytes,
    )
    pinned_audio = (
        audio.owner_sha256, audio.privacy_sha256,
        audio.wav_sha256, audio.wav_bytes,
    )

    def stable() -> None:
        _original_denials()
        if (
            type(image) is not OfflinePngRequest
            or type(audio) is not OfflineWaveRequest
            or any(a is not b for a, b in zip(
                (image.owner_sha256, image.privacy_sha256,
                 image.source_sha256, image.png_bytes),
                pinned_image, strict=True,
            ))
            or any(a is not b for a, b in zip(
                (audio.owner_sha256, audio.privacy_sha256,
                 audio.wav_sha256, audio.wav_bytes),
                pinned_audio, strict=True,
            ))
        ):
            raise OfflineObservationPairRejected("observation input carrier changed")

    stable()
    if pinned_image[:3] != retained[:3] or (
        pinned_audio[0], pinned_audio[1], pinned_audio[2]
    ) != (retained[0], retained[1], retained[3]):
        raise OfflineObservationPairRejected(
            "image/audio owner, privacy or source identity differs"
        )

    def measure() -> tuple[object, ...]:
        stable()
        try:
            png = inspect_disconnected_png(image)
            stable()
            wav = inspect_local_pcm_wav(audio)
        except (OfflinePngRejected, OfflineWaveRejected) as exc:
            raise OfflineObservationPairRejected(
                "untrusted media inventory rejected"
            ) from exc
        stable()
        if (
            type(png) is not OfflinePngInventory
            or type(wav) is not OfflineWaveReview
            or (png.owner_sha256, png.privacy_sha256, png.source_sha256)
            != pinned_image[:3]
            or (wav.owner_sha256, wav.privacy_sha256, wav.wav_sha256)
            != pinned_audio[:3]
        ):
            raise OfflineObservationPairRejected("media inventory identity changed")
        fields = (
            png.width, png.height, png.color_type, png.bit_depth,
            png.idat_chunks, png.total_idat_bytes, png.idat_sha256,
            wav.channel_count, wav.sample_rate_hz, wav.bits_per_sample,
            wav.frame_count, wav.pcm_sha256,
        )
        stable()
        return fields

    first = measure()
    if measure() != first:
        raise OfflineObservationPairRejected("observation inventories drifted")
    stable()
    payload = (
        retained[0], retained[1], retained[2], retained[3],
        first[0], first[1], first[6], first[8], first[10], first[11],
    )
    canonical = json.dumps(
        [retained, first], separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    digest = hashlib.sha256(_DOMAIN + canonical).hexdigest()
    stable()
    report = _RESULT(*payload, digest)
    expected = (*payload, digest)

    def stable_report() -> None:
        stable()
        if type(report) is not _RESULT or any(
            a is not b for a, b in zip(
                (report.owner_sha256, report.privacy_sha256, report.png_sha256,
                 report.wav_sha256, report.width, report.height,
                 report.image_idat_sha256, report.sample_rate_hz,
                 report.audio_frames, report.pcm_sha256, report.pair_sha256),
                expected, strict=True,
            )
        ):
            raise OfflineObservationPairRejected("observation pair report changed")

    stable_report()
    for name in _DENIALS:
        if getattr(report, name) is not False:
            raise OfflineObservationPairRejected("observation pair gained authority")
        stable_report()
    return report
