"""One-pass disconnected WAV -> mono16 -> 16 kHz energy-region preview.

Consumes only explicitly supplied bytes. No microphone, ASR, speaker identity,
network, logging, saved audio, consent inference, or external actions. The
output omits raw samples and is itself potentially sensitive local metadata.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .offline_pcm_activity_regions import (
    ActivityRegion,
    OfflineActivityRejected,
    detect_activity_regions,
)
from .offline_pcm_mono16 import (
    OfflinePcmConvertRejected,
    OfflinePcmConvertRequest,
    convert_offline_pcm_mono16,
)
from .offline_pcm_resample16 import OfflineResampleRejected, resample_pcm16
from .offline_pcm_wav import OfflineWaveRejected, OfflineWaveRequest, inspect_local_pcm_wav

_TARGET_RATE = 16_000
_DOMAIN = b"ARK-offline-wave-energy-pipeline-v1\0"


class OfflineWavePipelineRejected(ValueError):
    """An explicit offline fixture cannot be safely converted and inspected."""


@dataclass(frozen=True, slots=True)
class OfflineWaveEnergyPreview:
    owner_sha256: str
    privacy_sha256: str
    wav_sha256: str
    mono16_sha256: str
    normalized_sha256: str
    target_rate_hz: int
    normalized_samples: int
    active_frame_count: int
    regions: tuple[ActivityRegion, ...]
    preview_sha256: str

    @property
    def microphone_authorized(self) -> bool:
        return False

    @property
    def speaker_authenticated(self) -> bool:
        return False

    @property
    def speech_recognized(self) -> bool:
        return False

    @property
    def audio_disclosure_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


_FLAGS = (
    "microphone_authorized", "speaker_authenticated", "speech_recognized",
    "audio_disclosure_authorized", "tool_execution_authorized",
)


def preview_offline_wav_energy(
    request: OfflineWaveRequest,
    *,
    rms_threshold: int = 512,
) -> OfflineWaveEnergyPreview:
    """Preview activity frames after deterministic PCM normalization.

    The resampler is simple linear interpolation without anti-alias filtering.
    Thresholds are amplitude estimates, NOT voice activity/speech detection.
    No output should be interpreted as authorized audio processing or sending.
    """
    if (
        type(request) is not OfflineWaveRequest
        or type(rms_threshold) is not int
        or not 0 <= rms_threshold <= 32768
    ):
        raise OfflineWavePipelineRejected("exact offline pipeline inputs required")
    original = (
        request.owner_sha256, request.privacy_sha256,
        request.wav_sha256, request.wav_bytes,
    )

    def stable_request() -> None:
        if (
            type(request) is not OfflineWaveRequest
            or any(now is not previous for now, previous in zip(
                (
                    request.owner_sha256, request.privacy_sha256,
                    request.wav_sha256, request.wav_bytes,
                ),
                original, strict=True,
            ))
        ):
            raise OfflineWavePipelineRejected("WAV input carrier changed")

    stable_request()
    try:
        wave = inspect_local_pcm_wav(request)
        stable_request()
        owner, privacy, claimed_wav, payload = original
        if (
            wave.owner_sha256 != owner
            or wave.privacy_sha256 != privacy
            or wave.wav_sha256 != claimed_wav
            or type(payload) is not bytes
        ):
            raise OfflineWavePipelineRejected("WAV source identity mismatch")

        # The strict WAV inspector accepts exactly fmt(16) + data(PCM),
        # including the one trailing RIFF pad byte when the payload is odd.
        frame_width = wave.channel_count * wave.bits_per_sample // 8
        pcm_length = wave.frame_count * frame_width
        raw = payload[44:44 + pcm_length]
        if (
            not raw or len(raw) != pcm_length
            or hashlib.sha256(raw).hexdigest() != wave.pcm_sha256
        ):
            raise OfflineWavePipelineRejected("WAV PCM payload changed")

        converted = convert_offline_pcm_mono16(OfflinePcmConvertRequest(
            owner, privacy, wave.pcm_sha256, raw,
            wave.channel_count, wave.sample_rate_hz, wave.bits_per_sample,
        ))
        stable_request()
        if (
            converted.owner_sha256 != owner
            or converted.privacy_sha256 != privacy
            or converted.source_sha256 != wave.pcm_sha256
            or converted.frame_count != wave.frame_count
            or converted.sample_rate_hz != wave.sample_rate_hz
            or hashlib.sha256(converted.pcm16_mono).hexdigest()
            != converted.output_sha256
        ):
            raise OfflineWavePipelineRejected("mono PCM conversion inconsistent")
        normalized = resample_pcm16(
            converted.pcm16_mono, converted.output_sha256,
            wave.sample_rate_hz, _TARGET_RATE,
        )
        stable_request()
        if (
            normalized.source_sha256 != converted.output_sha256
            or normalized.output_samples * 2 != len(normalized.pcm)
            or hashlib.sha256(normalized.pcm).hexdigest()
            != normalized.output_sha256
        ):
            raise OfflineWavePipelineRejected("normalized PCM identity mismatch")
        reviewed = detect_activity_regions(
            normalized.pcm, normalized.output_sha256, _TARGET_RATE,
            frame_ms=20, rms_threshold=rms_threshold,
        )
        stable_request()
        if (
            reviewed.source_sha256 != normalized.output_sha256
            or reviewed.total_samples != normalized.output_samples
            or reviewed.sample_rate != _TARGET_RATE
            or type(reviewed.regions) is not tuple
        ):
            raise OfflineWavePipelineRejected("activity-region input mismatch")
        rows = tuple(reviewed.regions)
        if any(
            type(region) is not ActivityRegion
            or type(region.start_sample) is not int
            or type(region.end_sample) is not int
            or not 0 <= region.start_sample < region.end_sample
            <= normalized.output_samples
            for region in rows
        ):
            raise OfflineWavePipelineRejected("activity region is noncanonical")
        manifest = (
            owner, privacy, claimed_wav, converted.output_sha256,
            normalized.output_sha256, _TARGET_RATE,
            normalized.output_samples, reviewed.active_frame_count,
            tuple((r.start_frame, r.end_frame, r.start_sample,
                   r.end_sample, r.active_frames) for r in rows),
            rms_threshold,
        )
        manifest_bytes = json.dumps(
            manifest, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
        digest = hashlib.sha256(_DOMAIN + manifest_bytes).hexdigest()
        result = OfflineWaveEnergyPreview(
            owner, privacy, claimed_wav, converted.output_sha256,
            normalized.output_sha256, _TARGET_RATE,
            normalized.output_samples, reviewed.active_frame_count, rows, digest,
        )
        expected = (
            owner, privacy, claimed_wav, converted.output_sha256,
            normalized.output_sha256, _TARGET_RATE,
            normalized.output_samples, reviewed.active_frame_count, rows, digest,
        )
        stable_request()

        def stable_result() -> None:
            if (
                type(result) is not OfflineWaveEnergyPreview
                or any(value is not original for value, original in zip(
                    (
                        result.owner_sha256, result.privacy_sha256,
                        result.wav_sha256, result.mono16_sha256,
                        result.normalized_sha256, result.target_rate_hz,
                        result.normalized_samples, result.active_frame_count,
                        result.regions, result.preview_sha256,
                    ),
                    expected, strict=True,
                ))
            ):
                raise OfflineWavePipelineRejected("energy preview result changed")
            stable_request()

        stable_result()
        for flag in _FLAGS:
            if getattr(result, flag) is not False:
                raise OfflineWavePipelineRejected("energy preview gained authority")
            stable_result()
        return result
    except (
        OfflineWaveRejected, OfflinePcmConvertRejected,
        OfflineResampleRejected, OfflineActivityRejected,
    ) as exc:
        raise OfflineWavePipelineRejected("offline PCM pipeline rejected fixture") from exc
