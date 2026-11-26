"""Fail closed on ambiguous, non-standard or private SQLite probe replies.

These tests do not execute a tool, use a private DB or trust a child receipt.
They protect aggregate diagnostics from json.loads last-key-wins behavior.
"""

from __future__ import annotations

import json
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "diagnose_memory_sidecar_startup.py"
)


def _load():
    spec = util.spec_from_file_location("ark_sidecar_strict_json_run828", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load()
_INVALID = {"status": "INVALID_CHILD_OUTPUT"}


@pytest.mark.parametrize(
    "raw",
    (
        '{"status":"OTHER_ERROR","status":"CREATED"}',
        '{"status":"CREATED","status":"OTHER_ERROR"}',
        '{"status":"CREATED","status":"CREATED"}',
        '{"status":"CREATED","private":"secret","private":"another"}',
        '{"status":"SIDECAR_REJECTED","phase":"WRITE",'
        '"suffix":"-wal","file_type":"0o100000","link_count":1,'
        '"link_count":0}',
        '{"status":"CREATED","nested":{"x":1,"x":2}}',
        '{"status":"CREATED","nested":{"x":{"a":1,"a":2}}}',
        '{"status":"CREATED","extra":NaN}',
        '{"status":"CREATED","extra":Infinity}',
        '{"status":"CREATED","extra":-Infinity}',
        '{"status":"CREATED"}{"status":"UPDATED"}',
        '{"status":"CREATED","private":"/home/private"}',
        '{"status":"CREATED","unclosed":',
        '',
    ),
)
def test_duplicate_or_nonstandard_child_json_never_claims_success(raw: str) -> None:
    assert _DIAG._parse_child_reply(raw) == _INVALID


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        ('{"status":"CREATED"}', {"status": "CREATED"}),
        ('{"status":"UPDATED"}', {"status": "UPDATED"}),
        ('{"status":"CONFLICT"}', {"status": "CONFLICT"}),
        ('{"status":"MEMORY_SCHEMA_REJECTED","phase":"BOOTSTRAP"}',
         {"status": "MEMORY_SCHEMA_REJECTED", "phase": "BOOTSTRAP"}),
        ('{"status":"SIDECAR_REJECTED","phase":"WRITE",'
         '"suffix":"-shm","file_type":"0o100000","link_count":0}',
         {"status": "SIDECAR_REJECTED", "phase": "WRITE",
          "suffix": "-shm", "file_type": "0o100000", "link_count": 0}),
    ),
)
def test_exact_unambiguous_child_json_preserves_bounded_evidence(
    raw: str, expected: dict[str, object],
) -> None:
    value = _DIAG._parse_child_reply(raw)
    assert value == expected
    assert "private" not in json.dumps(value)


@pytest.mark.parametrize(
    "raw",
    (
        "x" * 4097,
        "{",
        '{"status":"CREATED"}' + " " * 4090,
    ),
)
def test_parser_bounded_output_never_echoes_untrusted_bytes(raw: str) -> None:
    result = _DIAG._parse_child_reply(raw)
    assert result == _INVALID
    assert "x" not in json.dumps(result)


def test_parser_rejects_non_text_or_non_dict_without_invoking_repr() -> None:
    class Poison:
        def __repr__(self) -> str:
            raise AssertionError("raw child object must never be inspected")

    for item in (Poison(), None, 1, b'{"status":"CREATED"}'):
        assert _DIAG._parse_child_reply(item) == _INVALID
