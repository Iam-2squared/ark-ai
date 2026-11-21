"""V3 saved snapshot equality check never reads unbounded local evidence."""

from __future__ import annotations

import pytest

import ark.learning.run_manifest as manifest


def test_exact_saved_snapshot_bytes_pass(tmp_path):
    expected = b'{"experiment_id":"synthetic"}'
    path = tmp_path / "execution-snapshot.json"
    path.write_bytes(expected)
    assert manifest._require_expected_snapshot_bytes(path, expected) is None


@pytest.mark.parametrize("new_bytes", [b"", b"{}"])
def test_short_or_changed_snapshot_is_rejected(tmp_path, new_bytes):
    path = tmp_path / "execution-snapshot.json"
    path.write_bytes(new_bytes)
    with pytest.raises(manifest.CandidateRunManifestError, match="do not match"):
        manifest._require_expected_snapshot_bytes(path, b'{"a":1}')


@pytest.mark.parametrize("extra", [b"X", b"X" * 10000])
def test_appended_snapshot_never_matches_even_if_prefix_identical(tmp_path, extra):
    path = tmp_path / "execution-snapshot.json"
    expected = b'{"a":1}'
    path.write_bytes(expected + extra)
    with pytest.raises(manifest.CandidateRunManifestError, match="do not match"):
        manifest._require_expected_snapshot_bytes(path, expected)


def test_oversized_disk_file_is_not_fully_read(tmp_path, monkeypatch):
    path = tmp_path / "execution-snapshot.json"
    path.write_bytes(b"x" * (manifest._MAX_CANONICAL_JSON_BYTES + 4096))
    expected = b'{"a":1}'
    original = type(path).open
    requested = []

    class SizedReader:
        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            self.handle.__enter__()
            return self

        def __exit__(self, *args):
            return self.handle.__exit__(*args)

        def read(self, size=-1):
            requested.append(size)
            if size < 0 or size > len(expected) + 1:
                raise AssertionError("unbounded execution snapshot read")
            return self.handle.read(size)

    def guarded_open(self, *args, **kwargs):
        return SizedReader(original(self, *args, **kwargs))

    monkeypatch.setattr(type(path), "open", guarded_open)
    with pytest.raises(manifest.CandidateRunManifestError, match="do not match"):
        manifest._require_expected_snapshot_bytes(path, expected)
    assert requested == [len(expected) + 1]


def test_missing_snapshot_reports_domain_error(tmp_path):
    with pytest.raises(manifest.CandidateRunManifestError, match="cannot be read"):
        manifest._require_expected_snapshot_bytes(tmp_path / "missing.json", b"{}")


@pytest.mark.parametrize("expected", [bytearray(b"{}"), "{}", None])
def test_expected_snapshot_must_be_exact_bytes(tmp_path, expected):
    path = tmp_path / "execution-snapshot.json"
    path.write_bytes(b"{}")
    with pytest.raises(manifest.CandidateRunManifestError, match="byte budget"):
        manifest._require_expected_snapshot_bytes(path, expected)


def test_expected_snapshot_over_budget_denied_before_io(tmp_path):
    missing = tmp_path / "not-created.json"
    with pytest.raises(manifest.CandidateRunManifestError, match="byte budget"):
        manifest._require_expected_snapshot_bytes(
            missing, b"x" * (manifest._MAX_CANONICAL_JSON_BYTES + 1),
        )
    assert not missing.exists()
