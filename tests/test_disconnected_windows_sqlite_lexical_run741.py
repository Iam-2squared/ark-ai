"""Portable synthetic Windows path review; never open any actual file."""

from __future__ import annotations

from dataclasses import fields

import pytest

from ark import disconnected_windows_sqlite_lexical as reviewer

VALID = (
    r"C:\ark\memory.sqlite3",
    r"Z:\ark\memory_1.sqlite3",
    r"D:\ark\archive\memory.db.sqlite3",
)


@pytest.mark.parametrize("label", VALID)
def test_canonical_windows_drive_fixtures_are_stable_and_inert(label):
    first = reviewer.review_windows_sqlite_lexical_path(label)
    second = reviewer.review_windows_sqlite_lexical_path(label)
    assert first == second
    assert len(first.path_sha256) == 64
    assert len(first.lexical_fingerprint) == 64
    assert len(first.sidecar_sha256) == 3
    assert len(set(first.sidecar_sha256)) == 3
    assert all(len(value) == 64 for value in first.sidecar_sha256)
    assert first.filesystem_identity_verified is False
    assert first.symlink_or_reparse_safety_proven is False
    assert first.sqlite_snapshot_coherent is False
    assert first.actual_open_authorized is False
    assert first.tool_execution_authorized is False
    assert label not in repr(first)
    assert {item.name for item in fields(type(first))} == {
        "path_sha256", "sidecar_sha256", "lexical_fingerprint",
    }


def test_different_drive_and_filename_have_separate_synthetic_labels():
    a = reviewer.review_windows_sqlite_lexical_path(VALID[0])
    b = reviewer.review_windows_sqlite_lexical_path(
        r"D:\ark\memory.sqlite3",
    )
    c = reviewer.review_windows_sqlite_lexical_path(
        r"C:\ark\other.sqlite3",
    )
    assert len({a.path_sha256, b.path_sha256, c.path_sha256}) == 3
    assert len({a.lexical_fingerprint, b.lexical_fingerprint, c.lexical_fingerprint}) == 3


@pytest.mark.parametrize("label", (
    "",
    r"c:\ark\memory.sqlite3",
    r"C:ark\memory.sqlite3",
    r"C:\memory.sqlite3",
    r"C:\ARK\memory.sqlite3",
    r"C:\ark\memory.SQLITE3",
    r"\\server\share\memory.sqlite3",
    r"\\?\C:\ark\memory.sqlite3",
    r"\Device\HarddiskVolume1\ark\memory.sqlite3",
    r"C:/ark/memory.sqlite3",
    r"C:\ark\..\memory.sqlite3",
    r"C:\ark\.\memory.sqlite3",
    r"C:\ark\\memory.sqlite3",
    "C:\\ark\\memory.sqlite3\\",
    r"C:\ark\con.sqlite3",
    r"C:\ark\prn.sqlite3",
    r"C:\ark\aux.sqlite3",
    r"C:\ark\nul.sqlite3",
    r"C:\ark\com1.sqlite3",
    r"C:\ark\lpt9.sqlite3",
    r"C:\ark\file~1.sqlite3",
    r"C:\ark\memory.sqlite3:stream",
    r"C:\ark\memory.sqlite3.",
    r"C:\ark\memory.sqlite3 ",
    r"C:\ark\memory.sqlite",
    r"C:\ark\.sqlite3",
    r"C:\ark\memory?.sqlite3",
    r"C:\ark\memory*.sqlite3",
    r"C:\ark\memory|bad.sqlite3",
    r"C:\ark\memory<bad.sqlite3",
    r"C:\ark\メモリ.sqlite3",
    "C:\\ark\\memory.sqlite3\x00",
    "C:\\ark\\" + "a" * 81 + ".sqlite3",
    "C:\\ark\\" + "a" * 239 + ".sqlite3",
    17,
    None,
))
def test_ambiguous_windows_label_is_rejected_without_raw_path_logging(label):
    with pytest.raises(reviewer.WindowsSQLiteLexicalRejected) as exc:
        reviewer.review_windows_sqlite_lexical_path(label)
    assert "メモリ" not in str(exc.value)
    assert "ark" not in str(exc.value)
    assert "stream" not in str(exc.value)


def test_str_subclass_cannot_elevate_to_an_exact_path():
    class Surrogate(str):
        pass

    with pytest.raises(reviewer.WindowsSQLiteLexicalRejected):
        reviewer.review_windows_sqlite_lexical_path(
            Surrogate(r"C:\ark\memory.sqlite3")
        )


@pytest.mark.parametrize(("rule", "replacement"), (
    ("_MAX_PATH", 10_000),
    ("_MAX_PART", True),
    ("_SUFFIXES", ("-evil",)),
    ("_RESERVED", frozenset()),
    ("_DOMAIN", b"BAD"),
    ("_DRIVE", object()),
))
def test_protocol_mutation_fails_before_path_fingerprint(monkeypatch, rule, replacement):
    monkeypatch.setattr(reviewer, rule, replacement)
    with pytest.raises(
        reviewer.WindowsSQLiteLexicalRejected, match="protocol",
    ):
        reviewer.review_windows_sqlite_lexical_path(VALID[0])


def test_result_cannot_claim_live_windows_custody_or_consent():
    receipt = reviewer.review_windows_sqlite_lexical_path(VALID[0])
    for denial in (
        "filesystem_identity_verified", "symlink_or_reparse_safety_proven",
        "sqlite_snapshot_coherent", "actual_open_authorized",
        "tool_execution_authorized",
    ):
        assert getattr(receipt, denial) is False
