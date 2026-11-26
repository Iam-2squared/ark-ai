"""Synthetic proactive SQLite paths reject malformed native names pre-open.

All cases use disposable local paths and provide no scheduling, consent,
external notification, real time, or execution authority.
"""

import pytest

from ark import proactive_synthetic_review as proactive


@pytest.mark.parametrize(
    "name",
    ("bad\x00name", "a" * 5000, "あ" * 1500),
    ids=("nul", "ascii-byte-budget", "multibyte-journal-budget"),
)
def test_malformed_native_path_denied_before_sqlite_connect(
    tmp_path, monkeypatch, name,
):
    def forbidden_connect(*_args, **_kwargs):
        raise AssertionError("SQLite connect reached before path admission")

    monkeypatch.setattr(proactive.sqlite3, "connect", forbidden_connect)
    with pytest.raises(
        proactive.SyntheticTriggerRejected, match="path exceeds SQLite limits",
    ):
        proactive.SyntheticProactiveLedger(tmp_path / name)


def test_normal_disposable_proactive_sqlite_path_still_initializes(tmp_path):
    path = tmp_path / "fixture.sqlite"
    ledger = proactive.SyntheticProactiveLedger(path)
    assert ledger.path == path
    assert path.is_file()
