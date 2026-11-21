"""Strict privacy-safe parsing of untrusted disposable subprocess receipts."""

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
    spec = util.spec_from_file_location("ark_sidecar_untrusted_output_run827", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load()
_INVALID = {"status": "INVALID_CHILD_OUTPUT"}


@pytest.mark.parametrize(
    ("source", "expected"),
    (
        ({"status": "CREATED"}, {"status": "CREATED"}),
        ({"status": "UPDATED"}, {"status": "UPDATED"}),
        ({"status": "CONFLICT"}, {"status": "CONFLICT"}),
        ({"status": "CREATED", "path": "/private/memory.sqlite"}, _INVALID),
        ({"status": "CONFLICT", "token": "private"}, _INVALID),
        ({"status": "SIDECAR_REJECTED", "phase": "WRITE",
          "suffix": "-shm", "file_type": "0o100000", "link_count": 0},
         {"status": "SIDECAR_REJECTED", "phase": "WRITE",
          "suffix": "-shm", "file_type": "0o100000", "link_count": 0}),
        ({"status": "SIDECAR_REJECTED", "phase": "WRITE",
          "suffix": "-wal", "file_type": "0o120000", "link_count": 1},
         {"status": "SIDECAR_REJECTED", "phase": "WRITE",
          "suffix": "-wal", "file_type": "0o120000", "link_count": 1}),
        ({"status": "SIDECAR_REJECTED", "phase": "WRITE",
          "suffix": "-wal", "file_type": "0o100000", "link_count": True}, _INVALID),
        ({"status": "SIDECAR_REJECTED", "phase": "WRITE",
          "suffix": "-wal", "file_type": "0o100000", "link_count": -1}, _INVALID),
        ({"status": "SIDECAR_REJECTED", "phase": "WRITE",
          "suffix": "-wal", "file_type": "0o100000", "link_count": 1,
          "db_path": "/private/path"}, _INVALID),
        ({"status": "SIDECAR_REJECTED", "phase": "WRITE",
          "suffix": "-other", "file_type": "0o100000", "link_count": 1}, _INVALID),
        ({"status": "SIDECAR_REJECTED", "phase": "WRITE",
          "suffix": "-wal", "file_type": "0o100000/secret", "link_count": 1}, _INVALID),
        ({"status": "MEMORY_SCHEMA_REJECTED", "phase": "BOOTSTRAP"},
         {"status": "MEMORY_SCHEMA_REJECTED", "phase": "BOOTSTRAP"}),
        ({"status": "MEMORY_SCHEMA_REJECTED", "phase": "READ"}, _INVALID),
        ({"status": "OTHER_ERROR", "phase": "WRITE", "exception_type": "OperationalError"},
         {"status": "OTHER_ERROR", "phase": "WRITE",
          "exception_type": "OperationalError"}),
        ({"status": "OTHER_ERROR", "phase": "WRITE",
          "exception_type": "OperationalError /private"}, _INVALID),
        ({"status": "OTHER_ERROR", "phase": "WRITE",
          "exception_type": "ValueError", "message": "/private"}, _INVALID),
        ({"status": "EXIT_FAILURE"}, _INVALID),
        ({"status": "CREATED", "scope": "private"}, _INVALID),
        ({"status": 7}, _INVALID),
        (["CREATED"], _INVALID),
        (None, _INVALID),
    ),
)
def test_exact_child_reply_allowlist_never_reexports_private_values(
    source: object, expected: dict[str, object],
) -> None:
    result = _DIAG._sanitize_child_reply(source)
    assert result == expected
    for private in ("/private", "db_path", "token", "secret", "scope"):
        assert private not in json.dumps(result)


def test_receipt_sanitizer_is_independent_of_input_mapping_mutation() -> None:
    source = {"status": "SIDECAR_REJECTED", "phase": "WRITE",
              "suffix": "-journal", "file_type": "0o100000", "link_count": 0}
    sanitized = _DIAG._sanitize_child_reply(source)
    source["link_count"] = 17
    assert sanitized["link_count"] == 0


def test_real_child_receipts_are_accepted_without_private_paths(
    tmp_path: Path,
) -> None:
    results = _DIAG._probe(
        tmp_path / "memory.sqlite", "separate-owner", "sequential",
        "generation-cas", wal_keeper=True,
    )
    assert [result["status"] for result in results] == ["UPDATED", "UPDATED"]
    text = json.dumps(results, sort_keys=True)
    assert str(tmp_path) not in text
    assert "memory.sqlite" not in text
    assert "owner-a" not in text
