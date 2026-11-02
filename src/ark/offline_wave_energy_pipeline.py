"""One-pass disconnected WAV -> mono16 -> 16 kHz energy-region preview.

Consumes only explicitly supplied bytes. No microphone, ASR, speaker identity,
network, logging, saved audio, consent inference, or external actions. The
output omits raw samples and is itself potentially sensitive local metadata.
"""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass

from .offline_pcm_activity_regions import (
    ActivityRegion,
    ActivityRegions,
    OfflineActivityRejected,
    detect_activity_regions,
    verify_activity_regions,
)
from .offline_pcm_mono16 import (
    OfflinePcmConvertRejected,
    OfflinePcmConvertRequest,
    OfflinePcmMono16,
    convert_offline_pcm_mono16,
)
from .offline_pcm_resample16 import OfflineResampleRejected, resample_pcm16
from .offline_pcm_wav import (
    OfflineWaveRejected,
    OfflineWaveRequest,
    OfflineWaveReview,
    inspect_local_pcm_wav,
)

_TARGET_RATE = 16_000
_DOMAIN = b"ARK-offline-wave-energy-pipeline-v1\0"
_MONO_DOMAIN = b"ARK-offline-pcm-mono16-v1\0"
_MAX_MONO_INPUT_BYTES = 2 * 1024 * 1024


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


def _verify_mono_projection(
    raw: bytes, channels: int, bits: int, claimed: bytes,
) -> bool:
    """Independently bind claimed normalized samples to original PCM bytes.

    The source converter is a replaceable Python callback. A correct-looking
    digest over substituted output bytes cannot prove that a WAV was actually
    converted according to the fixed integer PCM rules.
    """
    width = bits // 8
    frame_width = channels * width
    if (
        type(claimed) is not bytes
        or not raw or len(raw) > _MAX_MONO_INPUT_BYTES
        or len(raw) % frame_width
        or len(claimed) != (len(raw) // frame_width) * 2
    ):
        return False
    independent = bytearray(len(claimed))
    cursor = 0
    for frame in range(len(raw) // frame_width):
        total = 0
        for _ in range(channels):
            value = int.from_bytes(
                raw[cursor:cursor + width], "little", signed=bits != 8,
            )
            cursor += width
            if bits == 8:
                normalized = (value - 128) << 8
            elif bits == 16:
                normalized = value
            else:
                normalized = value >> (bits - 16)
            total += normalized
        independent[frame * 2:frame * 2 + 2] = (
            total // channels
        ).to_bytes(2, "little", signed=True)
    return bytes(independent) == claimed


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
            type(wave) is not OfflineWaveReview
            or wave.owner_sha256 != owner
            or wave.privacy_sha256 != privacy
            or wave.wav_sha256 != claimed_wav
            or type(payload) is not bytes
        ):
            raise OfflineWavePipelineRejected("WAV source identity mismatch")

        # The inspector is a substitutable callback. Its claimed format can
        # preserve the WAV checksum while lying about the sample rate and
        # therefore changing normalization and activity boundaries. Parse the
        # canonical 44-byte header from the pinned original WAV independently.
        if (
            len(payload) < 44 or payload[12:20] != (b"fmt " + struct.pack("<I", 16))
            or payload[36:40] != b"data"
        ):
            raise OfflineWavePipelineRejected("WAV canonical header unavailable")
        encoding, channels, rate, byte_rate, header_width, bits = struct.unpack_from(
            "<HHIIHH", payload, 20,
        )
        if (
            encoding != 1 or channels not in (1, 2)
            or bits not in (8, 16, 24, 32)
            or not 8_000 <= rate <= 48_000
            or header_width != channels * bits // 8
            or byte_rate != rate * header_width
        ):
            raise OfflineWavePipelineRejected("WAV header is noncanonical")
        pcm_length = struct.unpack_from("<I", payload, 40)[0]
        if (
            not pcm_length or pcm_length % header_width
            or 44 + pcm_length + (pcm_length & 1) != len(payload)
        ):
            raise OfflineWavePipelineRejected("WAV data length inconsistent")
        frames = pcm_length // header_width
        millis, remainder = divmod(frames * 1000, rate)
        if (
            type(wave.channel_count) is not int
            or type(wave.sample_rate_hz) is not int
            or type(wave.bits_per_sample) is not int
            or type(wave.frame_count) is not int
            or type(wave.duration_ms_floor) is not int
            or type(wave.duration_ms_remainder) is not int
            or (wave.channel_count, wave.sample_rate_hz, wave.bits_per_sample,
                wave.frame_count, wave.duration_ms_floor,
                wave.duration_ms_remainder)
            != (channels, rate, bits, frames, millis, remainder)
        ):
            raise OfflineWavePipelineRejected("WAV callback format disagrees with header")

        # The strict WAV inspector accepts exactly fmt(16) + data(PCM),
        # including the one trailing RIFF pad byte when the payload is odd.
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
            type(converted) is not OfflinePcmMono16
            or converted.owner_sha256 != owner
            or converted.privacy_sha256 != privacy
            or converted.source_sha256 != wave.pcm_sha256
            or converted.frame_count != wave.frame_count
            or converted.sample_rate_hz != wave.sample_rate_hz
            or converted.source_channels != channels
            or converted.source_bits_per_sample != bits
            or not _verify_mono_projection(
                raw, channels, bits, converted.pcm16_mono,
            )
            or hashlib.sha256(converted.pcm16_mono).hexdigest()
            != converted.output_sha256
        ):
            raise OfflineWavePipelineRejected("mono PCM conversion inconsistent")
        mono_manifest = {
            "owner": owner, "privacy": privacy, "source": wave.pcm_sha256,
            "output": converted.output_sha256, "frames": frames,
            "channels": channels, "rate": rate, "bits": bits,
        }
        mono_canonical = json.dumps(
            mono_manifest, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
        if converted.inventory_sha256 != hashlib.sha256(
            _MONO_DOMAIN + mono_canonical
        ).hexdigest():
            raise OfflineWavePipelineRejected("mono PCM inventory identity mismatch")
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
        # The detector return is a replaceable callback result. Exact
        # data-shape checks alone cannot prove activity counts or timeline.
        # Independently derive every region from the pinned normalized bytes.
        if type(reviewed) is not ActivityRegions:
            raise OfflineWavePipelineRejected("exact activity report required")
        verify_activity_regions(
            reviewed, normalized.pcm, normalized.output_sha256, _TARGET_RATE,
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
        # A false-valued result getter can also reflectively retarget the
        # activity report. Recheck full frame/region recomputation afterward.
        verify_activity_regions(
            reviewed, normalized.pcm, normalized.output_sha256, _TARGET_RATE,
            frame_ms=20, rms_threshold=rms_threshold,
        )
        stable_result()
        return result
    except (
        OfflineWaveRejected, OfflinePcmConvertRejected,
        OfflineResampleRejected, OfflineActivityRejected,
    ) as exc:
        raise OfflineWavePipelineRejected("offline PCM pipeline rejected fixture") from exc
