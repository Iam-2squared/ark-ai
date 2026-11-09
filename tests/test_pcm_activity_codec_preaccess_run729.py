"""Private PCM activity fixtures reject substituted codec functions before access.

These are disconnected consistency tests, not microphone provenance or consent.
"""

import hashlib
import re
import struct
from types import SimpleNamespace

import pytest

from ark import offline_pcm_activity_regions as activity


def _fixture():
    pcm = struct.pack("<hhhh", 1200, 1200, 0, 1200)
    digest = hashlib.sha256(pcm).hexdigest()
    return pcm, digest, activity.detect_activity_regions(pcm, digest, 8000)


@pytest.mark.parametrize("surface", [
    "hash_module", "hash_callback", "struct_module", "decode_callback",
    "rates", "sha_pattern", "size_limit",
])
@pytest.mark.parametrize("entry", ["detect", "verify"])
def test_pcm_codec_replacement_denied_before_private_input(monkeypatch, surface, entry):
    pcm, digest, report = _fixture()
    invoked = []

    def poisoned(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("private PCM reached an untrusted codec callback")

    with monkeypatch.context() as patch:
        if surface == "hash_module":
            patch.setattr(activity, "hashlib", SimpleNamespace(sha256=poisoned))
        elif surface == "hash_callback":
            patch.setattr(activity.hashlib, "sha256", poisoned)
        elif surface == "struct_module":
            patch.setattr(activity, "struct", SimpleNamespace(iter_unpack=poisoned))
        elif surface == "decode_callback":
            patch.setattr(activity.struct, "iter_unpack", poisoned)
        elif surface == "rates":
            patch.setattr(activity, "_RATES", set(activity._RATES))
        elif surface == "sha_pattern":
            patch.setattr(activity, "_SHA256", re.compile(".*"))
        else:
            patch.setattr(activity, "MAX_PCM_BYTES", activity.MAX_PCM_BYTES + 1)
        with pytest.raises(activity.OfflineActivityRejected, match="codec or digest"):
            if entry == "detect":
                activity.detect_activity_regions(pcm, digest, 8000)
            else:
                activity.verify_activity_regions(report, pcm, digest, 8000)
    assert invoked == []


def test_unmodified_activity_source_remains_verifiable():
    pcm, digest, report = _fixture()
    assert report.source_sha256 == digest
    assert report.total_samples == 4
    assert activity.verify_activity_regions(report, pcm, digest, 8000) is None
