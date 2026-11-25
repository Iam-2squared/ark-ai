"""Run1349: training preflight reports reject ambiguous JSON before hydration."""

from pathlib import Path

import pytest

from ark.learning import training_cli as cli


@pytest.mark.parametrize(
    "payload",
    (
        b'{"kind":"NON_CANDIDATE_PREFLIGHT","kind":"OTHER"}',
        b'{"runtime_identity":{"device":"GPU-A","device":"GPU-B"}}',
    ),
)
def test_duplicate_preflight_report_keys_fail_before_runtime_identity_hydration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: bytes,
) -> None:
    hydrated: list[bool] = []
    monkeypatch.setattr(cli, "_verify_file", lambda *_args: payload)

    def forbidden_runtime_identity(**_values: object) -> None:
        hydrated.append(True)
        raise AssertionError("duplicate report keys must fail before identity hydration")

    monkeypatch.setattr(cli, "RuntimeIdentity", forbidden_runtime_identity)
    snapshot = {"hardware": {"preflight_report_sha256": "0" * 64}}
    with pytest.raises(RuntimeError, match="not valid canonical JSON"):
        cli._verify_preflight_report(tmp_path / "preflight.json", snapshot)

    assert hydrated == []


def test_preflight_parser_allows_same_member_name_in_distinct_objects() -> None:
    cli._ORIGINAL_PREFLIGHT_JSON_PARSER_GUARD()
    parsed = cli._ORIGINAL_PREFLIGHT_JSON_LOADS(
        b'{"left":{"device":"GPU-A"},"right":{"device":"GPU-B"}}',
        parse_constant=cli._ORIGINAL_PREFLIGHT_JSON_CONSTANT,
        parse_float=cli._ORIGINAL_PREFLIGHT_JSON_FLOAT,
        object_pairs_hook=cli._ORIGINAL_PREFLIGHT_JSON_PAIRS,
    )
    assert parsed == {
        "left": {"device": "GPU-A"},
        "right": {"device": "GPU-B"},
    }


def test_preflight_parser_rejects_overflowing_json_float() -> None:
    with pytest.raises(ValueError, match="nonfinite numeric value"):
        cli._ORIGINAL_PREFLIGHT_JSON_LOADS(
            b'{"vram_gib":1e9999}',
            parse_constant=cli._ORIGINAL_PREFLIGHT_JSON_CONSTANT,
            parse_float=cli._ORIGINAL_PREFLIGHT_JSON_FLOAT,
            object_pairs_hook=cli._ORIGINAL_PREFLIGHT_JSON_PAIRS,
        )


def test_replaced_json_loader_fails_before_report_parse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_verify_file", lambda *_args: b"{}")
    monkeypatch.setattr(cli.json, "loads", lambda *_args, **_kwargs: {})
    snapshot = {"hardware": {"preflight_report_sha256": "0" * 64}}

    with pytest.raises(RuntimeError, match="parser implementation changed"):
        cli._verify_preflight_report(tmp_path / "preflight.json", snapshot)


def test_replaced_parser_guard_fails_before_report_parse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_verify_file", lambda *_args: b"{}")
    monkeypatch.setattr(cli, "_require_original_preflight_json_parser", lambda: None)
    snapshot = {"hardware": {"preflight_report_sha256": "0" * 64}}

    with pytest.raises(RuntimeError, match="parser guard changed"):
        cli._verify_preflight_report(tmp_path / "preflight.json", snapshot)
