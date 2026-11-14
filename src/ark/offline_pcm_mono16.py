"""Explicit-fixture, offline integer PCM conversion to signed 16-bit mono.

This is NOT resampling, ASR, a microphone reader, a provenance check, or
permission to persist, disclose, or execute anything. The output contains
sensitive raw audio and must remain in a separately authorized local context.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-offline-pcm-mono16-v1\0"
_MAX_INPUT = 2 * 1024 * 1024
_MAX_OUTPUT = 2 * 1024 * 1024
_MAX_DURATION = 120


class OfflinePcmConvertRejected(ValueError):
    """A requested offline PCM conversion is malformed or over budget."""


@dataclass(frozen=True, slots=True)
class OfflinePcmConvertRequest:
    owner_sha256: str
    privacy_sha256: str
    source_sha256: str
    pcm_bytes: bytes = field(repr=False)
    channels: int = 1
    sample_rate_hz: int = 16000
    bits_per_sample: int = 16


@dataclass(frozen=True, slots=True)
class OfflinePcmMono16:
    owner_sha256: str
    privacy_sha256: str
    source_sha256: str
    output_sha256: str
    inventory_sha256: str
    sample_rate_hz: int
    source_channels: int
    source_bits_per_sample: int
    frame_count: int
    pcm16_mono: bytes = field(repr=False)

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def audio_disclosure_authorized(self) -> bool:
        return False

    @property
    def speech_recognized(self) -> bool:
        return False


_RESULT_TYPE = OfflinePcmMono16
# Pin exact request slots before reading private PCM or owner/scope identity.
# Frozen dataclasses still permit executable class-level getter replacement.
_REQUEST_TYPE = OfflinePcmConvertRequest
_REQUEST_SLOTS = (
    "owner_sha256", "privacy_sha256", "source_sha256", "pcm_bytes",
    "channels", "sample_rate_hz", "bits_per_sample",
    "__init__", "__new__", "__getattribute__", "__getattr__",
)
_ORIGINAL_REQUEST_SLOTS = tuple(
    vars(_REQUEST_TYPE).get(name) for name in _REQUEST_SLOTS
)


def _require_original_request_carrier() -> None:
    if (
        OfflinePcmConvertRequest is not _REQUEST_TYPE
        or any(
            vars(_REQUEST_TYPE).get(name) is not original
            for name, original in zip(
                _REQUEST_SLOTS, _ORIGINAL_REQUEST_SLOTS, strict=True,
            )
        )
    ):
        raise OfflinePcmConvertRejected(
            "offline PCM request carrier changed before private bytes"
        )

# Source PCM is private. The codec/serializer are process-global mutable
# callbacks; pin their import-time identities before passing any private
# bytes or source/provenance labels to them. This is defensive in-process
# detection, NOT sandboxing or authenticated audio provenance.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_BOUNDS = (_MAX_INPUT, _MAX_OUTPUT, _MAX_DURATION)


def _require_original_codec() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _SHA is not _ORIGINAL_SHA_PATTERN
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or any(type(n) is not int for n in
               (_MAX_INPUT, _MAX_OUTPUT, _MAX_DURATION))
        or (_MAX_INPUT, _MAX_OUTPUT, _MAX_DURATION) != _ORIGINAL_BOUNDS
    ):
        raise OfflinePcmConvertRejected(
            "offline PCM codec authority changed before private bytes"
        )


def _sha(x: object) -> bool:
    return type(x) is str and _SHA.fullmatch(x) is not None


def convert_offline_pcm_mono16(request: OfflinePcmConvertRequest) -> OfflinePcmMono16:
    """Convert every input frame without truncation, dither, or resampling.

    8-bit input is unsigned (128 = zero). 16/24/32-bit input is signed LE.
    Higher precision inputs use an arithmetic right shift; stereo mixes
    per-channel signed-16 samples using floor division. This is a simple,
    deterministic fixture converter, NOT a production anti-aliased DSP stage.
    """
    if type(request) is not OfflinePcmConvertRequest:
        raise OfflinePcmConvertRejected("exact conversion request required")
    _require_original_codec()
    _require_original_request_carrier()
    pinned = (
        request.owner_sha256, request.privacy_sha256, request.source_sha256,
        request.pcm_bytes, request.channels, request.sample_rate_hz,
        request.bits_per_sample,
    )

    def epoch() -> None:
        _require_original_codec()
        _require_original_request_carrier()
        current = (
            request.owner_sha256, request.privacy_sha256, request.source_sha256,
            request.pcm_bytes, request.channels, request.sample_rate_hz,
            request.bits_per_sample,
        )
        _require_original_codec()
        if any(a is not b for a, b in zip(current, pinned, strict=True)):
            raise OfflinePcmConvertRejected("conversion request changed during processing")

    epoch()
    owner, privacy, claimed, raw, channels, rate, bits = pinned
    if (
        not all(_sha(x) for x in (owner, privacy, claimed))
        or type(raw) is not bytes or not 0 < len(raw) <= _MAX_INPUT
        or type(channels) is not int or channels not in (1, 2)
        or type(rate) is not int or not 8000 <= rate <= 48000
        or type(bits) is not int or bits not in (8, 16, 24, 32)
    ):
        raise OfflinePcmConvertRejected("invalid PCM format or input budget")
    width = bits // 8
    frame_width = channels * width
    if len(raw) % frame_width:
        raise OfflinePcmConvertRejected("partial PCM frame")
    frames = len(raw) // frame_width
    if frames > rate * _MAX_DURATION or frames * 2 > _MAX_OUTPUT:
        raise OfflinePcmConvertRejected("output bytes or duration budget exceeded")
    _require_original_codec()
    if hashlib.sha256(raw).hexdigest() != claimed:
        raise OfflinePcmConvertRejected("PCM source checksum mismatch")
    epoch()
    output = bytearray(frames * 2)
    cursor = 0
    for frame in range(frames):
        frame_value = 0
        for _ in range(channels):
            value = int.from_bytes(raw[cursor:cursor + width], "little", signed=bits != 8)
            cursor += width
            if bits == 8:
                normalized = (value - 128) << 8
            elif bits == 16:
                normalized = value
            else:
                normalized = value >> (bits - 16)
            frame_value += normalized
        mono = frame_value // channels
        output[frame * 2:frame * 2 + 2] = mono.to_bytes(2, "little", signed=True)
        # Periodically detect replacement of a frozen request carrier without
        # imposing a Python callback or revealing the original audio.
        if frame % 4096 == 0:
            epoch()
    epoch()
    output_bytes = bytes(output)
    _require_original_codec()
    output_sha = hashlib.sha256(output_bytes).hexdigest()
    manifest = {
        "owner": owner, "privacy": privacy, "source": claimed,
        "output": output_sha, "frames": frames,
        "channels": channels, "rate": rate, "bits": bits,
    }
    _require_original_codec()
    canonical = json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    _require_original_codec()
    inventory_sha = hashlib.sha256(_DOMAIN + canonical).hexdigest()
    epoch()
    result = OfflinePcmMono16(
        owner, privacy, claimed, output_sha, inventory_sha,
        rate, channels, bits, frames, output_bytes,
    )
    epoch()
    def assert_result_epoch() -> None:
        # A constructor or false-valued denial getter can reflectively edit
        # the frozen audio witness. The returned PCM must remain bound to
        # the *original* owner/privacy/source and exact output bytes.
        if (
            type(result) is not _RESULT_TYPE
            or result.owner_sha256 is not owner
            or result.privacy_sha256 is not privacy
            or result.source_sha256 is not claimed
            or result.output_sha256 is not output_sha
            or result.inventory_sha256 is not inventory_sha
            or result.sample_rate_hz is not rate
            or result.source_channels is not channels
            or result.source_bits_per_sample is not bits
            or result.frame_count is not frames
            or type(result.pcm16_mono) is not bytes
            or result.pcm16_mono is not output_bytes
        ):
            raise OfflinePcmConvertRejected("conversion result changed during creation")

    assert_result_epoch()
    epoch()
    if (
        result.source_authenticated is not False
        or result.consent_verified is not False
        or result.audio_disclosure_authorized is not False
        or result.speech_recognized is not False
    ):
        raise OfflinePcmConvertRejected("conversion result acquired authority")
    # The LAST denial getter is itself a callback. Do not return an audio
    # digest, scope, raw byte carrier or provenance marker from a mixed epoch.
    assert_result_epoch()
    epoch()
    return result
