"""Local V3 evidence reader byte budget: no training or Candidate artifacts."""

from __future__ import annotations

import pytest

import ark.learning.run_manifest as manifest
from ark.learning.execution import canonical_json


def test_small_canonical_json_round_trip(tmp_path):
    path = tmp_path / "synthetic.json"
    payload = canonical_json({"a": 1, "b": ["x"]})
    path.write_bytes(payload)
    decoded, observed = manifest._load_canonical_json(path, "synthetic")
    assert decoded == {"a": 1, "b": ["x"]}
    assert observed == payload


def test_exact_byte_limit_is_accepted(tmp_path):
    limit = manifest._MAX_CANONICAL_JSON_BYTES
    base = canonical_json({"data": ""})
    payload = canonical_json({"data": "x" * (limit - len(base))})
    assert len(payload) == limit
    path = tmp_path / "limit.json"
    path.write_bytes(payload)
    decoded, observed = manifest._load_canonical_json(path, "limit")
    assert len(decoded["data"]) == limit - len(base)
    assert observed == payload


@pytest.mark.parametrize("overage", [1, 4096])
def test_oversize_rejected_before_json_parser(tmp_path, monkeypatch, overage):
    path = tmp_path / "oversize.json"
    path.write_bytes(b" " * (manifest._MAX_CANONICAL_JSON_BYTES + overage))

    def must_not_parse(*_args, **_kwargs):
        raise AssertionError("oversized evidence must not enter JSON parser")

    monkeypatch.setattr(manifest.json, "loads", must_not_parse)
    with pytest.raises(manifest.CandidateRunManifestError, match="byte budget"):
        manifest._load_canonical_json(path, "oversize")


def test_existing_noncanonical_format_still_rejected(tmp_path):
    path = tmp_path / "noncanonical.json"
    path.write_bytes(b'{"a": 1}\n')
    with pytest.raises(manifest.CandidateRunManifestError, match="canonical"):
        manifest._load_canonical_json(path, "synthetic")


def test_missing_file_reports_domain_error(tmp_path):
    path = tmp_path / "missing.json"
    with pytest.raises(manifest.CandidateRunManifestError, match="cannot be read"):
        manifest._load_canonical_json(path, "synthetic")


def test_nonstandard_json_constant_still_rejected(tmp_path):
    path = tmp_path / "nan.json"
    path.write_bytes(b'{"a":NaN}\n')
    with pytest.raises(manifest.CandidateRunManifestError, match="canonical"):
        manifest._load_canonical_json(path, "synthetic")
