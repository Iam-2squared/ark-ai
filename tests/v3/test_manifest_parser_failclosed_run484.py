"""Bounded, no-GPU V3 JSON evidence must reject parser/canonicalization faults."""

from __future__ import annotations

import pytest

import ark.learning.run_manifest as manifest
from ark.learning.execution import canonical_json


def _load(tmp_path, payload: bytes):
    path = tmp_path / "untrusted-evidence.json"
    path.write_bytes(payload)
    return manifest._load_canonical_json(path, "synthetic evidence")


@pytest.mark.parametrize("payload", (
    b'{"metric":1e99999}\n',
    b'{"metric":-1e99999}\n',
    b'{"metric":NaN}\n',
    b'{"metric":Infinity}\n',
    b'{"metric":-Infinity}\n',
))
def test_nonfinite_evidence_is_domain_rejected(tmp_path, payload):
    with pytest.raises(manifest.CandidateRunManifestError, match="canonical JSON"):
        _load(tmp_path, payload)


def test_extreme_nesting_cannot_escape_as_recursion_error(tmp_path):
    payload = b'{"nested":' + b"[" * 1600 + b"0" + b"]" * 1600 + b"}\n"
    with pytest.raises(manifest.CandidateRunManifestError, match="canonical JSON"):
        _load(tmp_path, payload)


@pytest.mark.parametrize("error", (
    OverflowError, RecursionError, TypeError, ValueError,
))
def test_canonical_serializer_exception_is_domain_rejected(tmp_path, monkeypatch, error):
    path = tmp_path / "evidence.json"
    path.write_bytes(b'{"safe":1}\n')

    def reject(_value):
        raise error("synthetic serialization fault")

    monkeypatch.setattr(manifest, "canonical_json", reject)
    with pytest.raises(manifest.CandidateRunManifestError, match="canonical JSON"):
        manifest._load_canonical_json(path, "synthetic evidence")


def test_exact_valid_canonical_bytes_still_accepted(tmp_path):
    payload = canonical_json({"kind": "offline", "values": [1, 2, 3]})
    parsed, observed = _load(tmp_path, payload)
    assert parsed == {"kind": "offline", "values": [1, 2, 3]}
    assert observed == payload


@pytest.mark.parametrize("payload", (
    b'[1,2,3]\n',
    b'"scalar"\n',
    b'{"z":1, "a":2}\n',
    b'\xff\xff\n',
))
def test_nonobject_noncanonical_or_invalid_unicode_is_refused(tmp_path, payload):
    with pytest.raises(manifest.CandidateRunManifestError, match="canonical JSON"):
        _load(tmp_path, payload)
