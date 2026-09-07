import json
from pathlib import Path

from ark.benchmark import run


def test_benchmark_is_reproducible_and_machine_readable(tmp_path: Path) -> None:
    config = tmp_path / "ark.toml"
    config.write_text('[model]\nbackend="echo"\n')
    output = tmp_path / "result.json"
    result = run(str(config), output)
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert result["success_rate"] == 1.0
    assert saved["schema_version"] == 1
    assert len(saved["cases"]) == 4
