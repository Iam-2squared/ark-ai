"""Tests for detached local PCM metadata; all audio bytes are generated here."""

import dataclasses
import hashlib
import struct

import pytest

from ark.offline_pcm_wav import (
    OfflineWaveRejected,
    OfflineWaveRequest,
    inspect_local_pcm_wav,
)

SHA = "a" * 64
PRIVACY = "b" * 64


def wave(*, channels=1, rate=8000, bits=16, samples=80, audio=None,
         fmt_size=16, encoding=1, extras=b"", pad=True):
    width = channels * bits // 8
    pcm = audio if audio is not None else b"\x00" * (width * samples)
    fmt = struct.pack("<HHIIHH", encoding, channels, rate,
                      rate * width, width, bits)
    if fmt_size != 16:
        fmt += b"\x00" * (fmt_size - 16)
    fmt_chunk = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    data_chunk = b"data" + struct.pack("<I", len(pcm)) + pcm
    if pad and len(pcm) & 1:
        data_chunk += b"\x00"
    body = b"WAVE" + fmt_chunk + data_chunk + extras
    return b"RIFF" + struct.pack("<I", len(body)) + body


def request(data=None, **kwargs):
    if data is None:
        data = wave()
    values = dict(owner_sha256=SHA, privacy_sha256=PRIVACY,
                  wav_sha256=hashlib.sha256(data).hexdigest(), wav_bytes=data)
    values.update(kwargs)
    return OfflineWaveRequest(**values)


@pytest.mark.parametrize("channels,rate,bits,samples", [
    (1, 8000, 8, 1), (1, 8000, 16, 80), (2, 16000, 16, 320),
    (1, 44100, 24, 44), (2, 48000, 32, 48000), (1, 16000, 8, 1),
])
def test_valid_canonical_pcm(channels, rate, bits, samples):
    pcm = wave(channels=channels, rate=rate, bits=bits, samples=samples)
    out = inspect_local_pcm_wav(request(pcm))
    assert out.channel_count == channels and out.sample_rate_hz == rate
    assert out.bits_per_sample == bits and out.frame_count == samples
    assert out.duration_ms_floor == samples * 1000 // rate
    assert out.duration_ms_remainder == samples * 1000 % rate
    assert not out.consent_verified
    assert not out.microphone_provenance_verified
    assert not out.speech_recognized
    assert not out.authorized_to_disclose
    assert "wav_bytes" not in repr(out)


def test_deterministic_hash_no_samples_disclosed():
    pcm = wave(audio=b"secret" * 2 + b"\x00\x00")
    one = inspect_local_pcm_wav(request(pcm))
    assert one == inspect_local_pcm_wav(request(pcm))
    assert "secret" not in repr(one)
    assert one.pcm_sha256 == hashlib.sha256(b"secret" * 2 + b"\x00\x00").hexdigest()


def test_declared_riff_size_must_match():
    data = bytearray(wave())
    struct.pack_into("<I", data, 4, len(data) - 9)
    with pytest.raises(OfflineWaveRejected, match="length"):
        inspect_local_pcm_wav(request(bytes(data)))


def test_declared_checksum_must_match():
    with pytest.raises(OfflineWaveRejected, match="checksum"):
        inspect_local_pcm_wav(request(wav_sha256="0" * 64))


def test_duration_two_minutes_accepted():
    pcm = wave(rate=8000, bits=8, samples=8000 * 120)
    assert inspect_local_pcm_wav(request(pcm)).frame_count == 960_000


def test_duration_over_two_minutes_rejected():
    pcm = wave(rate=8000, bits=8, samples=8000 * 120 + 1)
    with pytest.raises(OfflineWaveRejected, match="duration"):
        inspect_local_pcm_wav(request(pcm))


def test_nonzero_padding_rejected():
    data = wave(bits=8, samples=1)
    assert data[-1] == 0
    tampered = data[:-1] + b"\x01"
    with pytest.raises(OfflineWaveRejected, match="pad byte"):
        inspect_local_pcm_wav(request(tampered))


def test_missing_odd_padding_rejected():
    data = wave(bits=8, samples=1, pad=False)
    with pytest.raises(OfflineWaveRejected, match="pad byte"):
        inspect_local_pcm_wav(request(data))


@pytest.mark.parametrize("bad", [
    b"", b"RIFF", b"RIFX" + wave()[4:], b"RF64" + wave()[4:],
    wave()[:43], wave() + b"extradata",
    wave(extras=b"LIST\x04\x00\x00\x00abcd"),
    wave(encoding=3), wave(channels=0), wave(channels=3),
    wave(rate=7999), wave(rate=48001), wave(bits=7), wave(bits=64),
    wave(bits=16, audio=b"\x00"), wave(bits=8, samples=0),
    wave(fmt_size=18),
])
def test_noncanonical_and_malformed_wave_rejected(bad):
    with pytest.raises(OfflineWaveRejected):
        inspect_local_pcm_wav(request(bad))


@pytest.mark.parametrize("overrides", [
    {"owner_sha256": "A" * 64}, {"privacy_sha256": "x"},
    {"wav_sha256": "0"}, {"wav_sha256": True},
    {"wav_bytes": bytearray(wave())}, {"wav_bytes": memoryview(wave())},
    {"wav_bytes": True}, {"wav_bytes": b"\x00" * (8 * 1024 * 1024 + 1)},
])
def test_request_types_and_bounds_rejected(overrides):
    with pytest.raises(OfflineWaveRejected):
        inspect_local_pcm_wav(request(**overrides))


def test_exact_request_type_rejected():
    with pytest.raises(OfflineWaveRejected):
        inspect_local_pcm_wav({})


def test_request_replacement_rejected(monkeypatch):
    import ark.offline_pcm_wav as module

    req = request()
    original_sha = module.hashlib.sha256
    changed = False

    def racing_sha(data):
        nonlocal changed
        if not changed:
            changed = True
            object.__setattr__(req, "wav_sha256", "".join(["a"] * 64))
        return original_sha(data)

    monkeypatch.setattr(module.hashlib, "sha256", racing_sha)
    with pytest.raises(OfflineWaveRejected):
        inspect_local_pcm_wav(req)


def test_metadata_edit_rejected_without_hidden_recovery():
    data = bytearray(wave())
    data[20:22] = b"\x02\x00"  # change PCM encoding to ADPCM-like unsupported code
    with pytest.raises(OfflineWaveRejected, match="format"):
        inspect_local_pcm_wav(request(bytes(data)))


def test_request_dataclass_is_frozen():
    req = request()
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.wav_bytes = b""
