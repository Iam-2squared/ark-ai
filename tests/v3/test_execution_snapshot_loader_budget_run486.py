"""Free-only V3 snapshot ingestion limits: validation, never GPU or Candidate."""

from __future__ import annotations

import pytest

from ark.learning.execution import load_snapshot


def _read(tmp_path, data: bytes):
    path = tmp_path / "synthetic-execution.json"
    path.write_bytes(data)
    return load_snapshot(path)


@pytest.mark.parametrize("data", [
    b'{"x":1e99999}\n',
    b'{"x":-1e99999}\n',
])
def test_exponent_overflow_cannot_enter_snapshot(tmp_path, data):
    with pytest.raises(ValueError, match="nonfinite"):
        _read(tmp_path, data)


@pytest.mark.parametrize("data", [
    b'{"x":NaN}\n',
    b'{"x":Infinity}\n',
    b'{"x":-Infinity}\n',
])
def test_nonstandard_literals_still_rejected(tmp_path, data):
    with pytest.raises(ValueError, match="non-standard JSON constant"):
        _read(tmp_path, data)


@pytest.mark.parametrize("depth", [129, 200, 1600])
def test_deep_snapshot_is_rejected_before_json_parser(tmp_path, depth):
    raw = b'{"x":' + b"[" * depth + b"0" + b"]" * depth + b"}"
    with pytest.raises(ValueError, match="nesting budget"):
        _read(tmp_path, raw)


def test_bounded_depth_128_is_accepted_for_valid_object(tmp_path):
    raw = b'{"x":' + b"[" * 127 + b"0" + b"]" * 127 + b"}"
    assert "x" in _read(tmp_path, raw)


@pytest.mark.parametrize("text", [
    "[" * 300,
    "}" * 300,
    '\\"[' * 200,
])
def test_string_brackets_do_not_consume_container_depth(tmp_path, text):
    import json

    raw = json.dumps({"x": text}, ensure_ascii=True).encode("ascii")
    assert _read(tmp_path, raw) == {"x": text}


def test_beyond_one_mib_is_rejected_without_unbounded_read(tmp_path):
    raw = b'{"x":"' + b"a" * 1_048_576 + b'"}'
    with pytest.raises(ValueError, match="byte budget"):
        _read(tmp_path, raw)


def test_exact_one_mib_object_is_accepted(tmp_path):
    raw = b'{"x":"' + b"a" * (1_048_576 - 8) + b'"}'
    assert len(raw) == 1_048_576
    assert len(_read(tmp_path, raw)["x"]) == 1_048_576 - 8


@pytest.mark.parametrize("data", [
    b"[]", b"null", b"true", b"1", b'"scalar"',
])
def test_legacy_object_requirement_still_applies(tmp_path, data):
    with pytest.raises(ValueError, match="JSON object"):
        _read(tmp_path, data)


def test_noncanonical_but_valid_json_remains_loadable(tmp_path):
    raw = b'{  "b": 2, "a": 1 }\n'
    assert _read(tmp_path, raw) == {"b": 2, "a": 1}


def test_missing_snapshot_does_not_create_or_repair_file(tmp_path):
    path = tmp_path / "absent.json"
    with pytest.raises(ValueError, match="cannot be read"):
        load_snapshot(path)
    assert not path.exists()


def test_invalid_unicode_fails_without_truncated_result(tmp_path):
    with pytest.raises(ValueError, match="cannot be decoded"):
        _read(tmp_path, b'{"key":"\xff"}')


def test_no_data_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="cannot be decoded"):
        _read(tmp_path, b"")
