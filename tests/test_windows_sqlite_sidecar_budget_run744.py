"""SQLite main and detached sidecar names share one strict lexical budget.

Inert Windows-path fixture: it opens no file and confers no storage authority.
"""

from __future__ import annotations

import pytest

from ark import disconnected_windows_sqlite_lexical as lexical


def _label(filename_stem_length: int) -> str:
    # 3-byte drive prefix, two 80-byte directories plus separators,
    # then the selected ASCII filename and ".sqlite3" extension.
    return (
        "C:\\" + "a" * 80 + "\\" + "b" * 80 + "\\"
        + "x" * filename_stem_length + ".sqlite3"
    )


def test_longest_legal_main_and_journal_sidecar_fit_limit():
    label = _label(59)
    assert len(label) == 232
    assert len(label + "-journal") == 240
    review = lexical.review_windows_sqlite_lexical_path(label)
    assert len(review.sidecar_sha256) == 3
    assert len(set(review.sidecar_sha256)) == 3
    assert review.filesystem_identity_verified is False
    assert review.sqlite_snapshot_coherent is False
    assert review.actual_open_authorized is False
    assert review.tool_execution_authorized is False


@pytest.mark.parametrize("stem", (60, 61, 64, 65, 66, 67))
def test_main_with_oversized_journal_sidecar_is_rejected(stem):
    label = _label(stem)
    assert len(label) <= 240
    assert len(label + "-journal") > 240
    with pytest.raises(lexical.WindowsSQLiteLexicalRejected) as exc:
        lexical.review_windows_sqlite_lexical_path(label)
    assert label not in str(exc.value)


def test_rejected_sidecar_budget_does_not_expand_with_rebound_max(monkeypatch):
    label = _label(60)
    monkeypatch.setattr(lexical, "_MAX_PATH", 1024)
    with pytest.raises(lexical.WindowsSQLiteLexicalRejected, match="protocol"):
        lexical.review_windows_sqlite_lexical_path(label)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_all_sidecars_have_distinct_fingerprints_inside_budget(suffix):
    label = _label(59)
    assert len(label + suffix) <= 240
    first = lexical.review_windows_sqlite_lexical_path(label)
    second = lexical.review_windows_sqlite_lexical_path(label)
    assert first == second
    assert first.symlink_or_reparse_safety_proven is False
