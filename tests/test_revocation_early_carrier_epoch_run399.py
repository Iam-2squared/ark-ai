"""Independent revocation evidence must be pinned before the first callback.

These are local, disconnected, deny-only privacy fixtures. Equal-value
replacement is not consent, erasure, authorization or clock evidence.
"""

import pytest

import ark.personal_context_revocation_continuity_review as continuity
from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize(
    "phase",
    ("source_validation", "first_integrity", "sqlite_validation", "later_integrity"),
)
@pytest.mark.parametrize("replacement", ("outer_tuple", "nested_row"))
def test_retained_revocation_custody_starts_before_first_validation(
    tmp_path, monkeypatch, phase, replacement,
):
    ledger = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    ledger.revoke(MemoryScope("fixture-owner", "fixture-scope"), at_ms=42)
    retained = continuity.review_revocation_continuity(ledger)
    original_rows = retained.rows
    assert len(original_rows) == 1
    calls = 0

    def reflect_equal_history():
        if replacement == "outer_tuple":
            new_rows = tuple(list(original_rows))
        else:
            new_rows = (tuple(list(original_rows[0])),)
        assert new_rows == original_rows
        assert new_rows is not original_rows
        object.__setattr__(retained, "rows", new_rows)

    if phase == "source_validation":
        real_assert = ledger._assert_source_path

        def source_checked(path):
            nonlocal calls
            real_assert(path)
            calls += 1
            if calls == 1:
                reflect_equal_history()

        monkeypatch.setattr(ledger, "_assert_source_path", source_checked)
    elif phase in ("first_integrity", "later_integrity"):
        real_integrity = continuity.SyntheticRevocationWitness.assert_integrity
        target_call = 1 if phase == "first_integrity" else 2

        def integrity_checked(self):
            nonlocal calls
            real_integrity(self)
            if self is retained:
                calls += 1
                if calls == target_call:
                    reflect_equal_history()

        monkeypatch.setattr(
            continuity.SyntheticRevocationWitness,
            "assert_integrity",
            integrity_checked,
        )
    else:
        real_validate = continuity._validate

        def validate_checked(conn):
            nonlocal calls
            real_validate(conn)
            calls += 1
            if calls == 1:
                reflect_equal_history()

        monkeypatch.setattr(continuity, "_validate", validate_checked)

    with pytest.raises(
        SyntheticContextRevocationRejected, match="retained revocation evidence changed",
    ):
        continuity.review_revocation_continuity(ledger, retained=retained)
    assert calls >= 1
    assert retained.rows == original_rows

    # The failed diagnostic is read-only. Once the original carrier is
    # restored, the saved revocation marker still validates and remains a veto.
    monkeypatch.undo()
    object.__setattr__(retained, "rows", original_rows)
    checked = continuity.review_revocation_continuity(ledger, retained=retained)
    assert checked == retained
    assert len(checked.rows) == 1
