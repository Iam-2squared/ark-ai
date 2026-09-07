from pathlib import Path

from ark.config import load_config


def test_load_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ARK_MODEL_PATH", raising=False)
    path = tmp_path / "ark.toml"
    path.write_text('[model]\nbackend="echo"\n[logging]\ndirectory="tmp-logs"\n')
    config = load_config(path)
    assert config.backend == "echo"
    assert config.log_directory == "tmp-logs"
