"""Run1252: V3 dataset CLI input files are bounded before JSON parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.learning.dataset_cli as dataset_cli


def test_input_byte_limit_accepts_exact_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dataset_cli, "MAX_DATASET_INPUT_BYTES", 16)
    path = tmp_path / "exact.json"
    payload = b"[{}]" + (b" " * 12)
    assert len(payload) == 16
    path.write_bytes(payload)

    assert dataset_cli._load_json_list(path, "candidates") == [{}]


@pytest.mark.parametrize("label", ("candidates", "flags", "decisions"))
def test_all_cli_json_inputs_reject_oversize_before_parser(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    label: str,
) -> None:
    monkeypatch.setattr(dataset_cli, "MAX_DATASET_INPUT_BYTES", 16)
    path = tmp_path / f"{label}.json"
    path.write_bytes(b"[{}]" + (b" " * 13))

    def forbidden_parser(_payload: str) -> object:
        pytest.fail("oversize input must be rejected before JSON parsing")

    monkeypatch.setattr(dataset_cli, "loads_unique_json", forbidden_parser)
    with pytest.raises(ValueError, match="exceeds 16 bytes"):
        dataset_cli._load_json_list(path, label)


def test_json_nesting_limit_counts_structure_not_string_contents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(dataset_cli, "MAX_JSON_NESTING", 2)
    path = tmp_path / "brackets-in-string.json"
    path.write_text('[{"text":"[[[[[[", "quote":"escaped \\" [ ]"}]', encoding="utf-8")

    assert dataset_cli._load_json_list(path, "candidates") == [
        {"text": "[[[[[[", "quote": 'escaped \\" [ ]'}
    ]


def test_json_nesting_over_limit_is_rejected_before_parser(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(dataset_cli, "MAX_JSON_NESTING", 2)
    path = tmp_path / "too-deep.json"
    path.write_text('[{"nested":[]}]', encoding="utf-8")

    def forbidden_parser(_payload: str) -> object:
        pytest.fail("over-nested input must be rejected before JSON parsing")

    monkeypatch.setattr(dataset_cli, "loads_unique_json", forbidden_parser)
    with pytest.raises(ValueError, match="nesting exceeds 2 levels"):
        dataset_cli._load_json_list(path, "candidates")


def test_invalid_utf8_is_rejected_as_input_error(tmp_path: Path) -> None:
    path = tmp_path / "invalid-utf8.json"
    path.write_bytes(b'[{"value":"\xff"}]')

    with pytest.raises(ValueError, match="must be UTF-8"):
        dataset_cli._load_json_list(path, "candidates")


def test_parser_recursion_error_is_converted_to_input_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "parser-recursion.json"
    path.write_text("[{}]", encoding="utf-8")

    def recursive_parser(_payload: str) -> object:
        raise RecursionError("synthetic parser depth")

    monkeypatch.setattr(dataset_cli, "loads_unique_json", recursive_parser)
    with pytest.raises(ValueError, match="parser capacity"):
        dataset_cli._load_json_list(path, "candidates")
