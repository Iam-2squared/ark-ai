"""Run1384: retain the preflight parser guard across simultaneous module rebinding."""

from pathlib import Path

import pytest

from ark.learning import training_cli as cli


def test_simultaneous_parser_guard_and_alias_replacement_fails_before_json_load(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser_calls: list[bool] = []
    monkeypatch.setattr(cli, "_verify_file", lambda *_args: b"{}")

    def substituted_guard() -> None:
        return None

    original_loads = cli._ORIGINAL_PREFLIGHT_JSON_LOADS

    def observed_loads(*args: object, **kwargs: object) -> object:
        parser_calls.append(True)
        return original_loads(*args, **kwargs)

    monkeypatch.setattr(cli, "_require_original_preflight_json_parser", substituted_guard)
    monkeypatch.setattr(cli, "_ORIGINAL_PREFLIGHT_JSON_PARSER_GUARD", substituted_guard)
    monkeypatch.setattr(cli, "_ORIGINAL_PREFLIGHT_JSON_LOADS", observed_loads)
    snapshot = {"hardware": {"preflight_report_sha256": "0" * 64}}

    with pytest.raises(RuntimeError, match="preflight JSON parser guard changed"):
        cli._verify_preflight_report(tmp_path / "preflight.json", snapshot)

    assert parser_calls == []
